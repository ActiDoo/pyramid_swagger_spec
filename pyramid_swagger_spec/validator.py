from collections import namedtuple

from jsonschema import draft4_format_checker, validate
from jsonschema.exceptions import ValidationError
from jsonschema.validators import Draft4Validator

from .errors import APIError
from .swagger import Types


def boolify(input):
    if input in (0, False, "False", "false", "0", None):
        return False
    else:
        return True


def _validate(spec, value):
    if spec["type"] == Types.number:
        value = int(value)
    if spec["type"] == Types.boolean:
        value = boolify(value)

    validate(schema={
        "type": spec["type"],
        "format": spec.get("format", None)
    }, instance=value)
    return value


ValidatedParams = namedtuple('ValidatedParams', ['path', 'query', 'body'])


def validate_request(request, api):
    path_values = dict()
    query_values = dict()
    body_values = dict()

    for x in api["parameters"]:
        if x["in"] == "body":
            validator = Draft4Validator(
                schema=x["schema"],
                format_checker=draft4_format_checker
            )
            try:
                validator.validate(request.json_body)
            except ValidationError as e:
                raise APIError(400, message="Body: %s" % (e.message,))
        elif x["in"] == "query":
            # query param
            try:
                query_values[x["name"]] = _validate(x, request.GET[x["name"]])
            except ValidationError as e:
                raise APIError(400, message="Query: %s invalid. %s" % (x["name"], e.message))
            except KeyError:
                raise APIError(400, message="Query: %s missing" % (x["name"],))
        elif x["in"] == "path":
            try:
                path_values[x["name"]] = _validate(x, request.matchdict[x["name"]])
            except ValidationError as e:
                raise APIError(400, message="Path: %s invalid. %s" % (x["name"], e.message))
            except KeyError:
                raise APIError(400, message="Path: %s missing" % (x["name"],))
    return ValidatedParams(
        path=path_values,
        query=query_values,
        body=body_values
    )