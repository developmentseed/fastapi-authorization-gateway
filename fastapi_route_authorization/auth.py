from copy import copy
import logging
import inspect
from typing import Callable, Coroutine, Optional, Type
from fastapi.routing import APIRoute

from pydantic import BaseModel
from fastapi_route_authorization.permissions import has_permission_for_route

from fastapi_route_authorization.types import Policy
from fastapi_route_authorization.utils import get_route, query_params_to_dict

from fastapi import (
    APIRouter,
    Depends,
    Request,
    HTTPException,
)


class StacSearch(BaseModel):
    collection: Optional[str] = None


def get_transform_for_path_format(path_format: str, policy: Policy):
    for transformation in policy.request_transformations:
        if path_format in transformation.path_formats:
            return transformation.transform


def wrap_endpoint(endpoint, response_model: Type):
    """
    Wrap an endpoint with a function that will mutate specified
    request parameters.
    """

    async def wrapped_endpoint(
        request: Optional[Request] = None, *args, **kwargs
    ) -> response_model:
        if request:
            if hasattr(request.state, "policy"):
                policy: Policy = request.state.policy
                # check if policy has a transform function for this route
                route = get_route(request)
                transform_func = get_transform_for_path_format(route.path_format, policy)
                if transform_func:
                    transform_func(policy, *args, **kwargs)
                else:
                    logging.info("No transform function found for this route")
            else:
                logging.info("No policy found on request state")
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
    old_routes = copy(router.routes)

    for route in old_routes:
        logging.info(
            f"Route {route.name}: {route.path_format} with methods: {route.methods}"
        )
        if isinstance(route, APIRoute):
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


async def evaluate_request(request: Request, policy: Policy):
    """
    Determine whether a request is authorized by the given policy.
    If not, raise a 403 Forbidden exception.
    """
    path = request.url.path
    method = request.method
    route_params = request.path_params
    route = get_route(request)

    logging.info(f"Dependencies: {route.body_field}")
    # parse query params to dict ourselves to avoid squashing duplicate keys
    query_params = query_params_to_dict(request.url.query)

    logging.debug(f"Path: {path}")
    logging.debug(f"Method: {method}")
    logging.debug(f"Route params: {route_params}")
    logging.debug(f"Route: {route.path_format}")
    logging.debug(f"Query Params: {query_params}")

    if not has_permission_for_route(policy, route, method, route_params, query_params):
        raise HTTPException(status_code=403, detail="Forbidden")


def build_authorization_dependency(
    policy_generator: Coroutine,
    policy_evaluator: Coroutine = evaluate_request,
) -> Coroutine:
    async def stac_authorization(
        request: Request,
        policy: Policy = Depends(policy_generator),
    ):
        logging.info("Evaluating authorization with policy dependency")
        if hasattr(request.state, "policy"):
            logging.warning(
                "Policy already exists on request state. Overwriting. This is likely a mistake "
                "and you should not be using both a policy dependency and a policy middleware."
            )

        request.state.policy = policy
        await policy_evaluator(request, policy)

    # else:

    #     async def stac_authorization(
    #         request: Request,
    #     ):
    #         logging.info("Evaluating authorization with policy middleware")
    #         if hasattr(request.state, "policy"):
    #             policy = request.state.policy
    #             await policy_evaluator(request, policy)
    #         else:
    #             logging.info("No policy found on request state")

    return stac_authorization
