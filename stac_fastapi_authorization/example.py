from typing import Optional
from fastapi import Request
from fastapi.params import Path
from stac_fastapi_authorization.types import Policy, RoutePermission


def example_policy_generator(request: Request, user: Optional[dict]) -> Policy:
    if not user:
        return Policy(
            approve=[
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
    return Policy(approve=[], deny=[])


async def get_user(request: Request):
    return {"username": "testuser"}
