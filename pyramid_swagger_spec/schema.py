from jsonschema import draft4_format_checker, validate
from jsonschema.exceptions import ValidationError
from jsonschema.validators import Draft4Validator

from pyramid_swagger_spec.errors import APIError


class Output:
    def __init__(self, d):
        self.d = d

    def __json__(self, *args, **kw):
        return self.d


class JSchema:
    def __init__(self, schema):
        self.schema = schema

    def get_json_schema(self):
        return self.schema

    def output(self, data):
        validator = Draft4Validator(
            schema=self.schema,
            format_checker=draft4_format_checker
        )
        try:
            validator.validate(data)
        except ValidationError as e:
            raise APIError(500, message="The server generated invalid output: %s" % (e.message,))
        else:
            return Output(data)
