# -*- coding: utf-8 -*-
from pyramid.view import view_config
from pyramid.response import Response
import json


class APIError(Exception):
    def __init__(self, code, status="err", message=""):
        self.code = code
        self.status = status
        self.message = message


@view_config(context=APIError)
def json_exception_view(exc, request):
    s = json.dumps({
        "status": exc.status,
        "message": exc.message,
    })
    response = Response(s)
    response.status_int = exc.code
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response
