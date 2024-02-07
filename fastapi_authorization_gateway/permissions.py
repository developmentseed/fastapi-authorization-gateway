import logging
from fastapi.params import Param
from pydantic import ValidationError, create_model
from fastapi_authorization_gateway.types import Policy, RoutePermission
from typing import Any, Mapping, Annotated, Optional


logger = logging.getLogger(__name__)


def generate_param_validator(params: Mapping[str, Annotated[Any, Param]]):
    """
    Generate a pydantic model for validating a set of query params.
    """
    prop_map = {}
    for k, v in params.items():
        prop_map[k] = (v, ...)
    return create_model("Params", **prop_map)


def route_matches_permission(
    permission: RoutePermission, path_format: str, method: str
):
    """
    Check if a given route and method are covered by a given permission.
    """
    logger.debug(
        f"Checking route {path_format} and method {method} against permission {permission}"
    )
    return path_format in permission.paths and method in permission.methods


def params_match_permission(
    permission_params: Optional[Mapping[str, Annotated[Any, Param]]],
    request_params: dict,
):
    """
    Validate provided request parameters against the pydantic model defined on a policy.
    """
    if permission_params is None:
        logger.debug("No params defined on policy. Match.")
        return True
    
    if not request_params:
        logger.debug("No request_params provided. No match.")
        return False
    
    logger.debug(f"Request params: {request_params}")
    
    param_validator = generate_param_validator(permission_params)
    try:
        param_validator(**request_params)
    except ValidationError as err:
        logger.debug(
            "Params do not match permission constraints.", extra={"error": err}
        )
        return False
    
    logger.debug("Params match permission constraints.")
    return True


def has_permission_for_route(
    policy: Policy,
    route_path_format: str,
    method: str,
    path_params: dict,
    query_params: dict,
):
    """
    Validate that the policy grants access to the given route, method and query params.

    Validates query_params against the pydantic model defined on the policy for a given combination of route
    and method.
    """
    logger.debug("Checking deny policy")
    for permission in policy.deny:
        if route_matches_permission(permission, route_path_format, method):
            logger.debug("Route and method found in deny policy")
            if permission.path_params is None and permission.query_params is None:
                logger.debug(
                    "No path or query params defined on deny policy. Denying access"
                    " since route and method match."
                )
                return False

            if permission.path_params:
                logger.debug("Path params defined on deny policy")
                if params_match_permission(permission.path_params, path_params):
                    logger.debug("Path params match deny policy. Denying access.")
                    return False
            if permission.query_params:
                logger.debug("Query params defined on deny policy")
                if params_match_permission(permission.query_params, query_params):
                    logger.debug("Query params match deny policy. Denying access.")
                    return False
            logger.debug("Path and query params did not match deny policy.")

    logger.debug("Checking allow policy")
    for permission in policy.allow:
        if route_matches_permission(permission, route_path_format, method):
            logger.debug("Route and method found in allow policy")
            if permission.path_params is None and permission.query_params is None:
                logger.debug(
                    "No path or query params defined on allow policy. Granting access"
                    " since route and method match."
                )
                return True
            if permission.path_params:
                logger.debug("Path params defined on allow policy")
                if params_match_permission(permission.path_params, path_params):
                    logger.debug("Path params match allow policy.")
                else:
                    return False
            if permission.query_params:
                logger.debug("Query params defined on allow policy")
                if params_match_permission(permission.query_params, query_params):
                    logger.debug("Query params match allow policy. Granting access.")
                    return True
            else:
                return True

    if policy.default_deny:
        logger.debug(
            "Route and method did not match any defined policy. Denying access due"
            " to default_deny setting."
        )
        return False
    else:
        logger.debug(
            "Route and method did not match any defined policy. Granting access due"
            " to default_deny setting."
        )
        return True
