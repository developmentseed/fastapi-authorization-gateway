import logging
from typing import Callable
from stac_fastapi_authorization.permissions import has_permission_for_route

from stac_fastapi_authorization.types import Policy
from stac_fastapi_authorization.utils import get_route, query_params_to_dict

from fastapi import (
    Depends,
    Request,
    HTTPException,
)


def evaluate_request(request: Request, policy: Policy):
    """
    Determine whether a request is authorized by the given policy.
    In cases where the policy requires a request to be mutated to filter
    out unauthorized data, mutate the request.
    """
    path = request.url.path
    method = request.method
    route_params = request.path_params
    route = get_route(request)
    # parse query params to dict ourselves to avoid squashing duplicate keys
    query_params = query_params_to_dict(request.url.query)

    logging.debug(f"Path: {path}")
    logging.debug(f"Method: {method}")
    logging.debug(f"Route params: {route_params}")
    logging.debug(f"Route: {route.path_format}")
    logging.debug(f"Query Params: {query_params}")

    if not has_permission_for_route(policy, route, method, route_params, query_params):
        raise HTTPException(status_code=403, detail="Forbidden")

    # TODO going to need to do something funky here to mutate the search
    # request body
    # if method == "GET":
    #     request.query_params = apply_permission_boundary_to_search_body(
    #         query_params, policy.approve.search
    #     )
    # elif method == "POST":
    #     request.body = apply_permission_boundary_to_search_body(
    #         request.body, policy.approve.search
    #     )


def build_stac_authorization_dependency(
    policy_generator: Callable,
    # search_request_model: Type[BaseModel],
    policy_evaluator: Callable = evaluate_request,
) -> Callable:
    def stac_authorization(
        request: Request,
        # request_data: Optional[search_request_model] = None,
        policy: Policy = Depends(policy_generator),
    ):
        logging.info("Evaluating authorization")
        policy_evaluator(request, policy)

    return stac_authorization
