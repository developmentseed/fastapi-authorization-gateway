import logging
from typing import Any, Dict, Mapping, Optional

from pydantic import ValidationError, create_model
from typing_extensions import Annotated

from fastapi.params import Param
from fastapi_authorization_gateway.types import Policy, RoutePermission

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
    request_params: Dict,
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
    logger.debug(f"Param validator: {param_validator}")

    logger.debug(f"Request params: {request_params}")
    try:
        param_validator(**request_params)
        logger.debug("Params match permission constraints.")
        return True
    except ValidationError as err:
        logger.debug(f"Params do not match permission constraints: {err}")
        return False


def policy_applies(permission: RoutePermission, path_params, query_params) -> bool:
    if not any([permission.path_params, permission.query_params]):
        logger.debug(
            "No path or query params defined on policy. Policy applies by default."
        )
        return True

    path_match = (
        params_match_permission(permission.path_params, path_params)
        if permission.path_params
        else False
    )
    query_match = (
        params_match_permission(permission.query_params, query_params)
        if permission.query_params
        else False
    )

    if permission.path_params and permission.query_params:
        logger.debug(f"Path params defined on policy: {path_match=}")
        logger.debug(f"Query params defined on policy: {query_match=}")
        return path_match and query_match

    if permission.path_params:
        logger.debug(f"Path params defined on policy: {path_match=}")
        return path_match

    if permission.query_params:
        logger.debug(f"Query params defined on policy: {query_match=}")
        return query_match

    # Should never get here
    raise SystemError("Unable to check policy by path or query params.")


def has_permission_for_route(
    policy: Policy,
    route_path_format: str,
    method: str,
    path_params: Dict,
    query_params: Dict,
) -> bool:
    """
    Validate that the policy grants access to the given route, method and query params.

    Validates query_params against the pydantic model defined on the policy for a given combination of route
    and method.
    """

    logger.debug("Looking for explicit denials...")
    if any(
        policy_applies(permission, path_params, query_params)
        for permission in policy.deny
        if route_matches_permission(permission, route_path_format, method)
    ):
        logger.info("Denied access.")
        return False

    logger.debug("Looking for explicit allows...")
    if any(
        policy_applies(permission, path_params, query_params)
        for permission in policy.allow
        if route_matches_permission(permission, route_path_format, method)
    ):
        logger.info("Granted access")
        return True

    is_allowed = not policy.default_deny
    logger.info(
        "Route and method did not match any defined policy."
        f" {'Grant' if is_allowed else 'Deny'}ing access due to default_deny setting."
    )
    return is_allowed
