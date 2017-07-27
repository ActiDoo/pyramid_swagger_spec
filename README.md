Pyramid Swagger Specifier
===============================

version number: 0.0.7
author: Marcel Sander

Overview
--------

Defines APIs, generates a Swagger specification, and validates inputs

Installation / Usage
--------------------

To install use pip:

    $ pip install pyramid_swagger_spec


Or clone the repo:

    $ git clone https://github.com/ActiDoo/pyramid_swagger_spec.git
    $ python setup.py install
    
Setup the view-deriver and RouteRegistry in your configuration by including

```python
config.include('pyramid_swagger_spec')
```

Create an API namespace, e.g. in your routes.py:

```python
from pyramid_swagger_spec import create_api_namespace
api_route = create_api_namespace(namespace="api")
```

Setup the views. They return the swagger spec as json at /{namespace}/_swagger and as HTML at /{namespace}/_swagger.html.

```python
from pyramid_swagger_spec.swagger import create_swagger_view
create_swagger_view(config, namespace="api", title="Server Api", version="0.1")
```

To specify API calls:
 
```python
import pyramid_swagger_spec.swagger as sw
# The traversal hierarchy has to match the subpath (i.e. /api/echo must return an EchoRessource instance)
from myproject.ressources import EchoRessource
from myproject.routes import api_route
 
 
@api_route(path="/echo/{x}", request_method="GET", name="test", context=EchoRessource, renderer='json', api=sw.api(
    operation_id="echo_test",
    summary="echos the input",
    parameters=[
        sw.path_parameter("x", sw.Types.number),
        sw.query_parameter("o", sw.Types.number)
    ],
    responses={
        200: sw.response(schema={
            "status": sw.property(sw.Types.string)
        })
    }
))
def echo_test_view(request, *args, **kw):
    return {
        'x': request.validated_params.path["x"],
        'o': request.validated_params.query["o"],
        'status': "ok"
    }
```
    
Contributing
------------

Everything is welcome. For example tests, output validation, etc.
