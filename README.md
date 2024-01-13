# FastAPI Route Authorization

This is a basic library for configuring route-based permission policies on a FastAPI app. It was originally developed to serve the needs of [stac-fastapi](https://github.com/stac-utils/stac-fastapi) but may be generally useful, if your authorization policies can be evaluated against a combination of routes, request methods, path parameters and query parameters.

## Setup

Install via pip. Use the github URL until we get this up on pypi:

`pip install git+https://github.com/edkeeble/fastapi-route-authorization.git`

## Usage

If you are just starting out and want an end-to-end explanation of how this library works and how to integrate it into your app, please check out the [Tutorial](./docs/tutorial.md).

If you are looking for a recipe to solve a specific issue, please check out the [How To](./docs/howto.md).


## Quickstart

If you don't want the full tutorial and just want to plug this right into your app with minimal explanation, you can use the code snippet below.

```python
from fastapi import Depends, Request
from typing import Optional
from stac_fastapi_authorization.auth import build_authorization_dependency
from stac_fastapi_authorization.types import Policy, RoutePermission

async def get_user(request: Request):
    return {
        "username": "test"
    }


def policy_generator(request: Request, user: Depends[get_user]) -> Policy:
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

    # read only policy allows read requests on all routes and denies write requests
    # falling back to denying a request if it matches none of the permissions
    read_only_policy = Policy(allow=[all_read], deny=[all_write], default_deny=True)

    # a more permissive policy granting write and read access on all routes, falling back
    # to approving a request if it matches none of the permissions
    authorized_policy = Policy(allow=[all_write, all_read], default_deny=False)
    
    if not user:
        # anonymous requests get read only permissions
        return read_only_policy
    else:
        # authenticated requests get full permissions
        return authorized_policy


# build the authorization dependency
authorization = build_authorization_dependency(
    policy_generator=policy_generator,
)

# This library was originally built for stac-fastapi, so we provide an example for
# integrating with a StacApi app. If you are using a stock FastAPI app, you can inject
# the authorization dependency into the APIRouter or on any specific routes that
# you like.

StacApi(
    app=app,
    router=APIRouter(
        dependencies=[Depends(authorization)],
    ),
    # The routes defined on the APIRouter above cover the core StacAPI,
    # but not extensions. In order to inject the dependency on extension
    # routes (e.g. Transactions), we need to leverage the `route_dependencies`
    # mechanism below.
    # Alternatively, we might be able to provide the authorization dependency
    # as a middleware in order to make it universal.
    route_dependencies=[
        (
            [
                {
                    "path": "/collections",
                    "method": "GET",
                },
                {
                    "path": "/collections/{collectionId}",
                    "method": "PUT",
                },
                {
                    "path": "/collections/{collectionId}",
                    "method": "DELETE",
                },
                {
                    "path": "/collections/{collectionId}/items",
                    "method": "POST",
                },
                {
                    "path": "/collections/{collectionId}/items/{itemId}",
                    "method": "PUT",
                },
                {
                    "path": "/collections/{collectionId}/items/{itemId}",
                    "method": "DELETE",
                },
            ],
            [Depends(authorization)],
        ),
    ],
    # ...
    # the rest of your StacApi args go here
)


```