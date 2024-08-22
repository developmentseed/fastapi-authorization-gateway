# FastAPI Authorization Gateway

[![Python package CI](https://img.shields.io/github/actions/workflow/status/developmentseed/fastapi-authorization-gateway/test.yaml)](https://github.com/developmentseed/fastapi-authorization-gateway/actions/workflows/test.yaml)
[![PyPI - Version](https://img.shields.io/pypi/v/fastapi-authorization-gateway)](https://pypi.org/project/fastapi-authorization-gateway/)

This library enables route-level authorization for FastAPI apps. It is particularly useful in cases where you need to limit access to routes that you do not directly control. For example, if you make use of a library which sets up a range of routes on your behalf (it was designed with [stac-fastapi](https://github.com/stac-utils/stac-fastapi) in mind), you can use this library to restrict access to any of those routes using authorization policies. These policies can be evaluated against a combination of route paths, methods, path parameters and query parameters. It also provides a mechanism for mutating requests before passing them on to downstream endpoints, for cases where you need to pre-emptively filter a request.

## Setup

Install via pip

```bash
python -m pip install fastapi-authorization-gateway

# or from source
python -m pip install git+https://github.com/developmentseed/fastapi-authorization-gateway.git`
```

## Usage

If you are just starting out and want an end-to-end explanation of how this library works and how to integrate it into your app, please check out the [Tutorial](./docs/tutorial.md).

If you are looking for a recipe to solve a specific issue, please check out the [How To](./docs/howto.md).


## Quickstart

If you don't want the full tutorial and just want to plug this right into your app with minimal explanation, you can use the code snippet below.

```python
from fastapi import Depends, Request
from typing import Annotated, Optional
from fastapi_authorization_gateway.auth import build_authorization_dependency
from fastapi_authorization_gateway.types import Policy, RoutePermission


async def get_user(request: Request):
    """
    Replace this with a function to retrieve a real user
    (from a token, for example).
    """
    return {
        "username": "test"
    }


async def policy_generator(request: Request, user: Annotated[dict, Depends(get_user)]) -> Policy:
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


app = FastAPI(dependencies=[Depends(authorization)])


@app.get("/test")
def get_test(request: Request):
    return {"status": "ok"}


@app.post("/test")
def post_test(request: Request):
    print("Should not be able to reach this endpoint with read-only policy")
    return {"status": "ok"}
```
