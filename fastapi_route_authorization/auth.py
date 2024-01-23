from copy import copy
import logging
import inspect
from typing import Callable, Coroutine, Optional, Type
from fastapi.routing import APIRoute

from fastapi_route_authorization.permissions import has_permission_for_route

from fastapi_route_authorization.types import Policy
from fastapi_route_authorization.utils import get_route, query_params_to_dict

from fastapi import (
    APIRouter,
    Depends,
    Request,
    HTTPException,
)


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
    ) -> response_model:
        if request:
            if hasattr(request.state, "policy"):
                policy: Policy = request.state.policy
                # check if policy has a transform function for this route
                route = get_route(request)
                transform_func = get_transform_for_path_format(
                    route.path_format, policy
                )
                if transform_func:
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
    wrapped_endpoint.__signature__ = original_signature
    wrapped_endpoint.__name__ = endpoint.__name__

    return wrapped_endpoint


def wrap_router(router: APIRouter, authorization_dependency: Optional[Callable] = None):
    """
    Re-register all routes on a router with wrapped endpoints in order to apply
    authorization and request mutation prior to passing data to the original endpoints.
    """
    old_routes = copy(router.routes)

    for route in old_routes:
        logger.debug(f"Route: {route}")
        if isinstance(route, APIRoute):
            logger.info(f"Wrapping route {route.path_format} {route.methods} with authorization dependency")
            router.routes.remove(route)
            router.add_api_route(
                route.path_format,
                wrap_endpoint(
                    endpoint=route.endpoint,
                    response_model=route.response_model,
                ),
                methods=route.methods,
                response_model=route.response_model,
                status_code=route.status_code,
                tags=route.tags,
                dependencies=route.dependencies + [Depends(authorization_dependency)]
                if authorization_dependency
                else [],
                summary=route.summary,
                description=route.description,
                response_description=route.response_description,
            )
        # elif isinstance(route, Route):
        #     # handle starlette routes
        #     router.routes.remove(route)
        #     router.add_route(
        #         route.path,
        #         wrap_endpoint(route.endpoint, transform_func=transform_request),
        #         methods=route.methods,
        #         name=route.name,
        #     )


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

    if not has_permission_for_route(policy, route, method, route_params, query_params):
        raise HTTPException(status_code=403, detail="Forbidden")


def build_authorization_dependency(
    policy_generator: Coroutine,
    policy_evaluator: Coroutine = evaluate_request,
) -> Coroutine:
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
