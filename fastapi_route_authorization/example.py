from typing import Optional
from fastapi import Request
from fastapi.params import Path
from fastapi_route_authorization.types import Policy, RoutePermission


def example_policy_generator(request: Request, user: Optional[dict]) -> Policy:
    if not user:
        return Policy(
            allow=[
                RoutePermission(
                    path="/collections/{collection_id}",
                    method="GET",
                    path_params={
                        "collection_id": Path(pattern=r"^(collection1|collection2)$")
                    },
                ),
            ],
            deny=[],
        )
    return Policy(allow=[], deny=[])


async def get_user(request: Request):
    return {"username": "testuser"}
