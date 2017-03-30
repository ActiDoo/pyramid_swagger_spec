import time

from .errors import APIError, json_exception_view
from .namespace import RouteRegistry
from .validator import validate_request

def includeme(config):
    # Add a view-deriver to allow the "api" parameter to add_view
    # Also measure the performance and add CORS header
    def api_view_deriver(view, info):
        api = info.options.get('api')
        if api:
            def wrapper_view(context, request):
                if request.method.upper() != "OPTIONS":
                    start = time.time()
                    request.api = api
                    request.validated_params = validate_request(request, api)
                    response = view(context, request)
                    end = time.time()
                    response.headers['Access-Control-Allow-Origin'] = '*'
                    response.headers['X-View-Performance'] = '%.3f' % (end - start,)
                elif request.method.upper() == "OPTIONS":
                    response = view(context, request)
                return response

            return wrapper_view
        return view

    api_view_deriver.options = ('api',)
    config.add_view_deriver(api_view_deriver)

    # Register the RouteRegistry that will be used to store the api spec
    config.registry.registerUtility(RouteRegistry())

    config.add_view(view=json_exception_view, context=APIError)

