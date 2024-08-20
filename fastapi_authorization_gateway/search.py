from typing import Dict

from fastapi_authorization_gateway.types import SearchConstraints


def apply_permission_boundary_to_search_body(
    search_body: Dict, search_constraints: SearchConstraints
):
    """
    Generate a CQL2 clause to AND against the original search body,
    constraining the results to the permissions boundary.
    Mutate the original search body and return it.
    """
    args = []
    if search_constraints.collections is not None:
        args.append(
            {
                "op": "in",
                "args": [
                    {
                        "property": "collection",
                    },
                    search_constraints.collections,
                ],
            }
        )

    # TODO: do the same for geometries and date windows

    user_filter = search_body.get("filter")
    constrained_filter = {
        "op": "and",
        "args": [user_filter, *args],
    }
    search_body["filter"] = constrained_filter
    return search_body
