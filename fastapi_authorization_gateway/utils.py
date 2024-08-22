from typing import Dict
from urllib.parse import parse_qs

from fastapi import Request
from fastapi.routing import APIRoute


def get_route(request: Request):
    """
    Get route object for a given request.
    """
    return next(
        item
        for item in request.app.routes
        if isinstance(item, APIRoute)
        and item.dependant.cache_key[0] == request.scope["endpoint"]
    )


def query_params_to_dict(querystring: str) -> Dict:
    """
    Convert a querystring to a dict.
    """
    query_params = parse_qs(querystring, keep_blank_values=True)
    return {k: v if len(v) > 1 else v[0] for k, v in query_params.items()}
