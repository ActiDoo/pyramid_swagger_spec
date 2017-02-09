from jsonschema.validators import Draft4Validator
from pyramid.response import Response
from pyramid.settings import asbool
from .namespace import IRouteRegistry


def generate_swagger(title, version, basePath, paths, schemes=["https",]):
    return {
        "swagger": "2.0",
        "info": {
            "description": "",
            "version": version,
            "title": title,
            "contact": {},
            "license": {
                "name": "Proprietary"
            },
        },
        "schemes": schemes,
        "basePath": basePath,
        "paths": {
            itemUrl: {
                itemMethod: {
                    "operationId": methodParams.get("operationId", ""),
                    "parameters": methodParams.get("parameters", []),
                    "consumes": methodParams.get("consumes", ["application/json", ]),
                    "produces": methodParams.get("produces", ["application/json", ]),
                    "summary": methodParams.get("summary", ""),
                    "description": methodParams.get("description", ""),
                    "responses": methodParams.get("responses", {}),
                } for itemMethod, methodParams in itemMethods.items()
            } for itemUrl, itemMethods in paths.items()
        }
    }


def create_swagger_view(config, namespace, title, version):
    namespace = namespace.strip("/")
    route_name = namespace+"_swagger"
    route_url = namespace + "/_swagger"
    config.add_route(route_name, route_url, request_method="GET")

    def view(request, *args, **kw):
        registry = request.registry
        route_registry = registry.getUtility(IRouteRegistry)
        registrations = route_registry.registrations[namespace]
        request.response.headers['Access-Control-Allow-Origin'] = '*'
        allow_http = asbool(request.registry.settings.get("swagger.enable_http_scheme",0))
        schemes = ["https"]
        if allow_http:
            schemes += ["http"]
        return generate_swagger(title=title, version=version, basePath="/"+namespace, paths=registrations, schemes=schemes)

    config.add_view(view, route_name=route_name, request_method="GET", renderer="json")

    html_tmpl = """
<!DOCTYPE html>
<html>
  <head>
    <title>ReDoc</title>
    <!-- needed for adaptive design -->
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="robots" content="noindex" />

    <!--
    ReDoc doesn't change outer page styles
    -->
    <style>
      body {
        margin: 0;
        padding: 0;
      }
    </style>
  </head>
  <body>
    <redoc spec-url='%(url)s'></redoc>
    <script src="https://rebilly.github.io/ReDoc/releases/latest/redoc.min.js"> </script>
  </body>
</html>
    """

    html_route_name = namespace + "_swagger.html"
    html_route_url = namespace + "/_swagger.html"
    config.add_route(html_route_name, html_route_url, request_method="GET")

    def html_view(request, *args, **kw):
        return Response(body=html_tmpl % {
            "url": request.route_url(route_name)
        }, content_type="text/html")

    config.add_view(html_view, route_name=html_route_name, request_method="GET", renderer="json")


class Types:
    null = "null"
    boolean = "boolean"
    object = "object"
    array = "array"
    number = "number"
    string = "string"


class Formats:
    hostname = "hostname"
    ipv4 = "ipv4"
    ipv6 = "ipv6"
    email = "email"
    uri = "uri"  # requires rfc3987
    datetime = "date-time"  # requires strict-rfc3339
    date = "date"
    time = "time"
    regex = "regex"
    color = "color"  # required webcolors


def api(operation_id,
        summary,
        parameters=[],
        consumes=["application/json"],
        produces=["application/json"],
        description="",
        responses={}):
    return {
        'operationId': operation_id,
        'summary': summary,
        'parameters': parameters,
        'consumes': consumes,
        'produces': produces,
        'description': description,
        'responses': responses,
    }


def path_parameter(name, parameter_type, format="", description=""):
    return {
        "name": name,
        "in": "path",
        "required": True,
        "type": parameter_type,
        "description": description,
        "format": format
    }


def query_parameter(name, parameter_type, format="", required=False, description=""):
    return {
        "name": name,
        "in": "query",
        "required": required,
        "type": parameter_type,
        "description": description,
        "format": format
    }


def property(type, format="", nullable=True):
    return {
        "type": type,
        "format": format,
        "x-nullable": nullable
    }


def body_parameter(schema, description=""):
    schema = {
        "$schema": "http://json-schema.org/schema#",
        "type": "object",
        "properties": schema
    }

    Draft4Validator.check_schema(schema)

    return {
        "name": "body",
        "in": "body",
        "required": True,
        "description": description,
        "schema": schema
    }


def response(schema, description=""):
    schema = {
        "$schema": "http://json-schema.org/schema#",
        "type": "object",
        "properties": schema
    }

    Draft4Validator.check_schema(schema)

    return {
        "description": description,
        "schema": schema
    }


