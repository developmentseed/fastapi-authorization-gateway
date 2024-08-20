import inspect
import logging
from copy import copy
from typing import Any, Callable, Coroutine, Optional, Type

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.routing import APIRoute
from fastapi_authorization_gateway.permissions import has_permission_for_route
from fastapi_authorization_gateway.types import Policy
from fastapi_authorization_gateway.utils import get_route, query_params_to_dict

logger = logging.getLogger(__name__)


def get_transform_for_path_format(path_format: str, policy: Policy):
    """
    Look up request transformation function for a given path format.
    """
    for transformation in policy.request_transformations:
        if path_format in transformation.path_formats:
            return transformation.transform


def wrap_endpoint(endpoint, response_model: Type):
    """
    Wrap an endpoint with a function that will first check
    the authorization policy and optionally mutate the request.
    """

    async def wrapped_endpoint(
        request: Optional[Request] = None, *args, **kwargs
    ) -> Type:
        logger.debug("Calling wrapped endpoint")
        if request:
            if hasattr(request.state, "policy"):
                logger.debug("Policy found on request state")
                policy: Policy = request.state.policy
                # check if policy has a transform function for this route
                route = get_route(request)
                logger.debug(
                    f"Checking if route {route.path_format} has a transform function"
                )
                transform_func = get_transform_for_path_format(
                    route.path_format, policy
                )
                if transform_func:
                    logger.debug("Transform function found for this route")
                    transform_func(request, policy, *args, **kwargs)
                else:
                    logger.debug("No transform function found for this route")
            else:
                logger.debug("No policy found on request state")
        if inspect.iscoroutinefunction(endpoint):
            if request:
                return await endpoint(request, *args, **kwargs)
            else:
                return await endpoint(*args, **kwargs)
        else:
            if request:
                return endpoint(request, *args, **kwargs)
            else:
                return endpoint(*args, **kwargs)

    original_signature = inspect.signature(endpoint)
    # give the wrapper function the same signature as the original endpoint)
    wrapped_endpoint.__signature__ = original_signature  # type: ignore
    wrapped_endpoint.__name__ = endpoint.__name__

    return wrapped_endpoint


def wrap_router(router: APIRouter, authorization_dependency: Optional[Callable] = None):
    """
    Re-register all routes on a router with wrapped endpoints in order to apply
    authorization and request mutation prior to passing data to the original endpoints.
    """
    old_routes = copy(router.routes)

    for route in old_routes:
        if isinstance(route, APIRoute):
            logger.info(
                f"Wrapping route {route.path_format} {route.methods} with authorization dependency"
            )
            router.routes.remove(route)
            combined_responses = route.responses
            use_response_class = route.response_class
            current_tags = route.tags
            current_dependencies = route.dependencies
            current_dependencies.append(Depends(authorization_dependency))
            current_callbacks = route.callbacks
            current_generate_unique_id = (
                route.generate_unique_id_function or router.generate_unique_id_function
            )
            router.add_api_route(
                route.path,
                wrap_endpoint(route.endpoint, route.response_model),
                response_model=route.response_model,
                status_code=route.status_code,
                tags=current_tags,
                dependencies=current_dependencies,
                summary=route.summary,
                description=route.description,
                response_description=route.response_description,
                responses=combined_responses,
                deprecated=route.deprecated,
                methods=route.methods,
                operation_id=route.operation_id,
                response_model_include=route.response_model_include,
                response_model_exclude=route.response_model_exclude,
                response_model_by_alias=route.response_model_by_alias,
                response_model_exclude_unset=route.response_model_exclude_unset,
                response_model_exclude_defaults=route.response_model_exclude_defaults,
                response_model_exclude_none=route.response_model_exclude_none,
                include_in_schema=route.include_in_schema,
                response_class=use_response_class,
                name=route.name,
                route_class_override=type(route),
                callbacks=current_callbacks,
                openapi_extra=route.openapi_extra,
                generate_unique_id_function=current_generate_unique_id,
            )


async def evaluate_request(request: Request, policy: Policy) -> None:
    """
    Determine whether a request is authorized by the given policy.
    If not, raise a 403 Forbidden exception.
    """
    path = request.url.path
    method = request.method
    route_params = request.path_params
    route = get_route(request)

    # parse query params to dict ourselves to avoid squashing duplicate keys
    query_params = query_params_to_dict(request.url.query)

    logger.debug(f"Path: {path}")
    logger.debug(f"Method: {method}")
    logger.debug(f"Route params: {route_params}")
    logger.debug(f"Route: {route.path_format}")
    logger.debug(f"Query Params: {query_params}")

    if not has_permission_for_route(
        policy, route.path_format, method, route_params, query_params
    ):
        raise HTTPException(status_code=403, detail="Forbidden")


def build_authorization_dependency(
    policy_generator: Coroutine,
    policy_evaluator: Callable[
        [Any, Policy], Coroutine[Any, Any, Any]
    ] = evaluate_request,
) -> Callable[[Any, Policy], Coroutine[Any, Any, Any]]:
    async def authorization_dependency(
        request: Request,
        policy: Policy = Depends(policy_generator),
    ):
        logger.info("Evaluating authorization with policy dependency")
        if hasattr(request.state, "policy"):
            logger.warning(
                "Policy already exists on request state. Overwriting. This is likely a mistake "
                "and you should not be using both a policy dependency and a policy middleware."
            )

        request.state.policy = policy
        await policy_evaluator(request, policy)

    return authorization_dependency
