import logging
from typing import Annotated
from fastapi import Depends, FastAPI, Request
from fastapi.routing import APIRoute
from fastapi_route_authorization.auth import (
    StacSearch,
    build_authorization_dependency,
    wrap_router,
)
from fastapi_route_authorization.types import (
    Policy,
    RoutePermission,
    RequestTransformation,
)
from pydantic import BaseModel


class TestData(BaseModel):
    name: str
    age: int


async def get_user(request: Request):
    return {"username": "test"}


async def policy_generator(
    request: Request, user: Annotated[dict, Depends(get_user)]
) -> Policy:
    """
    Define your policies here based on the requesting user or, really,
    whatever you like. This function will be injected as a dependency
    into the authorization dependency and must return a Policy.
    """
    logging.info("Generating policy")
    # We will generate some policies that cover all routes for the app,
    # so we need to enumerate them here.
    all_routes: list[APIRoute] = request.app.routes

    # A permission matching write access to all routes, with no constraints
    # on path or query parameters
    all_write = RoutePermission(
        paths=[route.path_format for route in all_routes],
        methods=["POST", "PUT", "PATCH", "DELETE"],
    )

    # a permission matching read access to all routes, with no constraints
    # on path or query parameters
    all_read = RoutePermission(
        paths=[route.path_format for route in all_routes], methods=["GET"]
    )

    request_transformations = [
        RequestTransformation(
            path_formats=["/search"],
            transform=transform_search,
        )
    ]

    # read only policy allows read requests on all routes and denies write requests
    # falling back to denying a request if it matches none of the permissions
    read_only_policy = Policy(allow=[all_read], deny=[all_write], default_deny=True)

    # a more permissive policy granting write and read access on all routes, falling back
    # to approving a request if it matches none of the permissions
    authorized_policy = Policy(
        allow=[all_write, all_read],
        request_transformations=request_transformations,
        default_deny=False,
    )

    if not user:
        # anonymous requests get read only permissions
        policy = read_only_policy
    else:
        logging.debug(f"User: {user}")
        # authenticated requests get full permissions
        policy = authorized_policy
    request.state.policy = policy
    logging.info(f"Policy: {policy}")
    return policy


def transform_search(policy: Policy, search_body: StacSearch, *args, **kwargs):
    logging.info("Transforming request")
    search_body.collection = "hello"


def change_age(request_body: bytes) -> bytes:
    """
    A function to mutate the request body to change the age of the test data
    """
    import json
    import logging

    decoded_body = json.loads(request_body)
    logging.info(decoded_body)
    if decoded_body.get("age", None):
        decoded_body["age"] = 100

    return json.dumps(decoded_body).encode("utf-8")


async def middleware_policy_generator(request: Request) -> Policy:
    """
    Define your policies here based on the requesting user or, really,
    whatever you like. This function will be injected as a dependency
    into the authorization dependency and must return a Policy.
    """

    # We will generate some policies that cover all routes for the app,
    # so we need to enumerate them here.
    all_routes: list[APIRoute] = request.app.routes

    # A permission matching write access to all routes, with no constraints
    # on path or query parameters
    all_write = RoutePermission(
        paths=[route.path_format for route in all_routes],
        methods=["POST", "PUT", "PATCH", "DELETE"],
    )

    # a permission matching read access to all routes, with no constraints
    # on path or query parameters
    all_read = RoutePermission(
        paths=[route.path_format for route in all_routes], methods=["GET"]
    )

    request_transformations = [
        RequestTransformation(
            path_formats=["/test/{test_id}"],
            transform=change_age,
        )
    ]

    # read only policy allows read requests on all routes and denies write requests
    # falling back to denying a request if it matches none of the permissions
    # read_only_policy = Policy(allow=[all_read], deny=[all_write], default_deny=True)

    # a more permissive policy granting write and read access on all routes, falling back
    # to approving a request if it matches none of the permissions
    write_only_policy = Policy(
        allow=[all_write],
        deny=[all_read],
        request_transformations=request_transformations,
        default_deny=False,
    )

    if not hasattr(request.state, "user"):
        # anonymous requests get read only permissions
        policy = write_only_policy
    else:
        # authenticated requests get full permissions
        policy = write_only_policy
    return policy


# build the authorization dependency
authorization = build_authorization_dependency(
    policy_generator=policy_generator,
)


app = FastAPI()  # dependencies=[Depends(authorization)])

# app.add_middleware(MutateRequestMiddlewareFastApi)
# app.add_middleware(AuthPolicyMiddleware, policy_generator=middleware_policy_generator)

# async def search_params(request_data: TestData):
#     return {"request_data": request_data}


@app.get("/test")
def test():
    return {"status": "ok"}


async def get_request_data(request: Request) -> TestData:
    logging.info("Getting request data")
    body = await request.body()
    logging.info(f"Request body: {body}")
    return TestData.parse_raw(body)


async def mutate_test_data(request: Request) -> TestData:
    logging.info("Mutating request data")
    body = await request.body()
    logging.info(f"Request body: {body}")
    data = StacSearch(collection="blah")
    return data


@app.post("/test")
async def create_test(request: Request, request_data: TestData):
    # body = await request.body()
    # logging.info(f"Request body: {body}")
    return {"status": "ok", "data": request_data}


@app.post("/test/{test_id}")
def update_test(request: Request, test_id: int, request_data: TestData):
    logging.info(f"Test ID: {test_id}")
    return {"status": "ok", "data": request_data}


@app.post("/search")
def search(request: Request, search_body: StacSearch) -> StacSearch:
    print(f"{search_body=}")
    return search_body


wrap_router(app.router, authorization_dependency=authorization)
