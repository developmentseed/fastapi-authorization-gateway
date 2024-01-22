import logging
from typing import Annotated
from fastapi import Depends, FastAPI, Request
from fastapi.routing import APIRoute
from fastapi_route_authorization.auth import (
    build_authorization_dependency,
    wrap_router,
)
from fastapi_route_authorization.types import (
    Policy,
    RoutePermission,
    RequestTransformation,
)
from pydantic import BaseModel, Field


class StacSearch(BaseModel):
    collections: list[str] = Field(default_factory=list)


class TestData(BaseModel):
    name: str
    age: int


async def get_user(request: Request):
    return {"username": "test", "collections": ["hello", "world"]}


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
        metadata={"collections": user["collections"]},
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


def transform_search(
    request: Request, policy: Policy, search_body: StacSearch, *args, **kwargs
):
    """
    Filter the requested collections to only those that the user has access to.
    """
    search_body.collections = list(
        set(search_body.collections) & set(policy.metadata["collections"])
    )


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


app = FastAPI()


@app.get("/test")
def test():
    return {"status": "ok"}


@app.post("/test")
async def create_test(request: Request, request_data: TestData):
    return {"status": "ok", "data": request_data}


@app.post("/test/{test_id}")
def update_test(request: Request, test_id: int, request_data: TestData):
    logging.info(f"Test ID: {test_id}")
    return {"status": "ok", "data": request_data}


@app.post("/search")
def search(request: Request, search_body: StacSearch) -> StacSearch:
    print(f"{search_body=}")
    return search_body


# build the authorization dependency
authorization = build_authorization_dependency(
    policy_generator=policy_generator,
)

# Wrap existing routes in order to enable authorization
# and request mutation.
wrap_router(app.router, authorization_dependency=authorization)
