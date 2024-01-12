# STAC FastAPI Authorization

This is a basic framework for configuring permission policies on a STAC API.

## Setup

Install via pip

## Usage

```python
from fastapi import Request
from typing import Optional
from stac_fastapi_authorization.auth import build_stac_authorization_dependency
from stac_fastapi_authorization.types import Policy, RoutePermission

async def get_user(request: Request):
    return {
        "username": "test"
    }


def policy_generator(request: Request, user: Optional[dict]):
    """
    Define your policies here based on the requesting user, maybe.
    """
    all_routes: list[APIRoute] = request.app.routes

    all_write = RoutePermission(
        paths=[route.path_format for route in all_routes],
        methods=["POST", "PUT", "PATCH", "DELETE"],
    )

    all_read = RoutePermission(
        paths=[route.path_format for route in all_routes], methods=["GET"]
    )

    read_only_policy = Policy(approve=[all_read], deny=[all_write], default_deny=True)
    authorized_policy = Policy(approve=[all_write, all_read], default_deny=False)
    
    if not user:
        return read_only_policy
    else:
        return authorized_policy


authorization = build_stac_authorization_dependency(
    get_user_dependency=get_user,
    policy_generator=policy_generator,
)

# ...
# setting up other dependencies of your StacApi, including the FastAPI app

StacApi(
    app=app,
    router=APIRouter(
        prefix=f"{_settings.path_prefix}",
        dependencies=[Depends(authorization)],
    ),
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