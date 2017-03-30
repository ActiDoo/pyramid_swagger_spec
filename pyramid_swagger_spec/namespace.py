from collections import defaultdict
from pyramid.path import DottedNameResolver
import functools
import inspect
import venusian
import zope.interface
from pyramid.renderers import render_to_response
from zope.interface.declarations import implementer

# copied from tomb_routes, modified

ACCEPT_RENDERER_MAP = {
    'json': 'application/json',
    'string': 'text/plain',
}


class MatchdictMapper(object):
    def __init__(self, **kwargs):
        self.view_settings = kwargs
        self.attr = self.view_settings.get('attr')
        self.blacklist = [
            'optional_slash',
        ]

    def __call__(self, view):
        @functools.wraps(view)
        def wrapper(context, request):
            kwargs = request.matchdict.copy()
            for k in self.blacklist:
                if k in kwargs:
                    del kwargs[k]

            if inspect.isclass(view):
                arg_len = len(inspect.getargspec(view.__init__).args)
                if arg_len == 2:
                    inst = view(request)
                elif arg_len == 3:
                    inst = view(context, request)
                else:
                    raise Exception("Class should accept `context` and "
                                    "`request` args only")
                meth = getattr(inst, self.attr)
                return meth(**kwargs)
            else:
                return view(request, **kwargs)

        return wrapper





def add_simple_route(
        config, path, target,
        append_matchdict=True,
        default_accept='text/html',
        route_kwargs={},
        *args, **kwargs
):
    """Configuration directive that can be used to register a simple route to
    a view.

    Examples:

    with view callable::

        config.add_simple_route(
            '/path/to/view', view_callable,
            renderer='json'
        )

    with dotted path to view callable::

        config.add_simple_route(
            '/path/to/view', 'dotted.path.to.view_callable',
            renderer='json'
        )
    """

    target = DottedNameResolver().maybe_resolve(target)
    mapper = config.get_routes_mapper()
    route_name = target.__name__
    route_name_count = 0

    if 'accept' in kwargs:
        val = kwargs.pop('accept')
        route_kwargs['accept'] = val
    else:
        # Disable */* by default, only accept 'text/html'
        renderer = kwargs.get('renderer', 'html')
        acceptor = ACCEPT_RENDERER_MAP.get(renderer, default_accept)
        route_kwargs['accept'] = acceptor

    if 'attr' in kwargs:
        route_name += '.' + kwargs['attr']

    routes = {route.name: route for route in mapper.get_routes()}
    orig_route_name = route_name

    while route_name in routes:
        route_name = '%s_%s' % (orig_route_name, route_name_count)
        route_name_count += 1

    current_pregen = kwargs.pop('pregenerator', None)

    orig_route_prefix = config.route_prefix
    # We are nested with a route_prefix but are trying to
    # register a default route, so clear the route prefix
    # and register the route there.
    if (path == '/' or path == '') and config.route_prefix:
        path = config.route_prefix
        config.route_prefix = ''

    config.add_route(
        route_name, path, pregenerator=current_pregen,
        **route_kwargs
    )

    kwargs['route_name'] = route_name

    if append_matchdict and 'mapper' not in kwargs:
        kwargs['mapper'] = MatchdictMapper

    config.add_view(target, *args, **kwargs)
    request_method = kwargs.get("request_method", "GET")
    if request_method != "OPTIONS":
        config.add_view(options_view, *args, **dict(kwargs, request_method="OPTIONS"))
    config.commit()
    config.route_prefix = orig_route_prefix


def options_view(request, *args, **kw):
    request.response.headers['Access-Control-Allow-Origin'] = '*'
    return {}


def create_api_namespace(namespace):
    namespace = namespace.strip("/")

    class DRoute(object):
        def __init__(self, path, *args, **kwargs):
            """Constructor just here to accept parameters for decorator"""
            self.path = path
            view_name = kwargs.get("name", "")
            self.route_path = self.path.rstrip("/") + "/" + view_name.lstrip("/") if view_name else self.path
            self.prefixed_route_path = "/" + namespace + "/" + self.route_path.lstrip("/")
            self.args = args
            self.kwargs = kwargs

        def __call__(self, wrapped):
            """Attach the decorator with Venusian"""
            args = self.args
            kwargs = self.kwargs

            def callback(scanner, _name, wrapped):
                """Register a view; called on config.scan"""
                config = scanner.config

                # pylint: disable=W0142
                add_simple_route(config, self.prefixed_route_path, wrapped, *args, route_kwargs=dict(traverse=self.prefixed_route_path), **kwargs)

                request_method = kwargs.get("request_method", "GET")
                registry = config.registry
                registry.getUtility(IRouteRegistry).register(namespace, self.route_path, request_method, kwargs.get("api",{}))

            info = venusian.attach(wrapped, callback)

            if info.scope == 'class':  # pylint:disable=E1101
                # if the decorator was attached to a method in a class, or
                # otherwise executed at class scope, we need to set an
                # 'attr' into the settings if one isn't already in there
                if kwargs.get('attr') is None:
                    kwargs['attr'] = wrapped.__name__
            return wrapped

    return DRoute


class IRouteRegistry(zope.interface.Interface):
    registrations = zope.interface.Attribute("""blahblah""")

    def register(namespace, url, method, params):
        """bar blah blah"""


@implementer(IRouteRegistry)
class RouteRegistry:
    def __init__(self):
        self.registrations = defaultdict(lambda: defaultdict(dict))

    def register(self, namespace, url, method, params):
        self.registrations[namespace][url][method.lower()] = params
