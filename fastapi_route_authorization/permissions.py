import logging
from fastapi.params import Param
from fastapi.routing import APIRoute
from pydantic import ValidationError, create_model
from fastapi_route_authorization.types import Policy, RoutePermission
from typing import Mapping, Annotated, Optional


def generate_param_validator(params: Mapping[str, Param]):
    """
    Generate a pydantic model for validating a set of query params.
    """
    prop_map = {}
    for k, v in params.items():
        prop_map[k] = (Annotated[str, v], ...)

    return create_model("Params", **prop_map)


def route_matches_permission(permission: RoutePermission, route: APIRoute, method: str):
    logging.debug(route.path)
    logging.debug(f"Checking route {route.path_format} against permission {permission}")
    return route.path_format in permission.paths and method in permission.methods


def params_match_permission(
    permission_params: Optional[Mapping[str, Param]], request_params: dict
):
    """
    Validate provided request parameters against the pydantic model defined on a policy.
    """

    if permission_params is None:
        logging.debug("No params defined on policy. Match.")
        return True
    else:
        param_validator = generate_param_validator(permission_params)
        logging.debug(f"Param validator: {param_validator}")
        try:
            logging.debug(f"Request params: {request_params}")
            param_validator(**request_params)
        except ValidationError as err:
            logging.error(err)
            logging.debug("Params do not match permission constraints.")
            return False
        else:
            logging.debug("Params do match permission constraints.")
            return True


def has_permission_for_route(
    policy: Policy, route: APIRoute, method: str, path_params: dict, query_params: dict
):
    """
    Validate that the policy grants access to the given route, method and query params.

    Validates query_params against the pydantic model defined on the policy for a given combination of route
    and method.
    """

    # TODO handle request body
    logging.debug(f"Path Params: {path_params}")

    logging.debug("Checking deny policy")
    for permission in policy.deny:
        if route_matches_permission(permission, route, method):
            logging.debug("Route and method found in deny policy")
            if permission.path_params is None and permission.query_params is None:
                logging.debug(
                    "No path or query params defined on deny policy. Denying access"
                    " since route and method match."
                )
                return False

            if permission.path_params:
                logging.debug("Path params defined on deny policy")
                if params_match_permission(permission.path_params, path_params):
                    logging.debug("Path params match deny policy. Denying access.")
                    return False
            if permission.query_params:
                logging.debug("Query params defined on deny policy")
                if params_match_permission(permission.query_params, query_params):
                    logging.debug("Query params match deny policy. Denying access.")
                    return False
            logging.debug("Path and query params did not match deny policy.")

    logging.debug("Checking allow policy")
    if not policy.allow:
        logging.debug("No allow policy defined. Granting access.")
        return True

    for permission in policy.allow:
        if route_matches_permission(permission, route, method):
            logging.debug("Route and method found in allow policy")
            if permission.path_params is None and permission.query_params is None:
                logging.debug(
                    "No path or query params defined on allow policy. Granting access"
                    " since route and method match."
                )
                return True
            if permission.path_params:
                logging.debug("Path params defined on allow policy")
                if params_match_permission(permission.path_params, path_params):
                    logging.debug("Path params match allow policy. Granting access.")
                    return True
                else:
                    return False
            if permission.query_params:
                logging.debug("Query params defined on allow policy")
                if params_match_permission(permission.query_params, query_params):
                    logging.debug("Query params match allow policy. Granting access.")
                    return True
            else:
                return False
    else:
        if policy.default_deny:
            logging.debug(
                "Route and method did not match any defined policy. Denying access due"
                " to default_deny setting."
            )
            return False
        else:
            logging.debug(
                "Route and method did not match any defined policy. Granting access due"
                " to default_deny setting."
            )
            return True
