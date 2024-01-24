"""
Test the has_permission_for_route function.
"""

from typing import Annotated
from fastapi import Path, Query
from fastapi_route_authorization.permissions import has_permission_for_route
from fastapi_route_authorization.types import RoutePermission, Policy


def test_has_permission_for_route_no_permissions():
    """
    Test that if no permissions are defined, the function returns False.
    """
    assert (
        has_permission_for_route(Policy(allow=[], deny=[]), "/search", "GET", {}, {})
        is False
    )


def test_default_deny_false():
    """
    Test that if no permissions are defined and default_deny is False, the function
    returns True.
    """
    assert (
        has_permission_for_route(
            Policy(allow=[], deny=[], default_deny=False), "/search", "GET", {}, {}
        )
        is True
    )


def test_has_permission_for_route_no_matching_permissions():
    """
    Test that if no permissions match the route, the function returns False.
    """
    assert (
        has_permission_for_route(
            Policy(
                allow=[
                    RoutePermission(
                        paths=["/collections/{collection_id}"],
                        methods=["GET"],
                    ),
                ],
                deny=[],
            ),
            "/search",
            "GET",
            {},
            {},
        )
        is False
    )


def test_has_permission_for_route_matching_permission():
    """
    Test that if a permission matches the route, the function returns True.
    """
    assert (
        has_permission_for_route(
            Policy(
                allow=[
                    RoutePermission(
                        paths=["/collections/{collection_id}"],
                        methods=["GET"],
                    ),
                ],
                deny=[],
            ),
            "/collections/{collection_id}",
            "GET",
            {},
            {},
        )
        is True
    )


def test_has_permission_for_route_matching_permission_path_params():
    """
    Test that if a permission matches the route and the path params match, the function
    returns True.
    """
    assert (
        has_permission_for_route(
            Policy(
                allow=[
                    RoutePermission(
                        paths=["/collections/{collection_id}"],
                        methods=["GET"],
                        path_params={
                            "collection_id": Annotated[
                                str, Path(pattern=r"^(collection1|collection2)$")
                            ]
                        },
                    ),
                ],
                deny=[],
            ),
            "/collections/{collection_id}",
            "GET",
            {"collection_id": "collection1"},
            {},
        )
        is True
    )


def test_has_permission_for_route_matching_permission_path_params_no_match():
    """
    Test that if a permission matches the route but the path params do not match, the
    function returns False.
    """
    assert (
        has_permission_for_route(
            Policy(
                allow=[
                    RoutePermission(
                        paths=["/collections/{collection_id}"],
                        methods=["GET"],
                        path_params={
                            "collection_id": Annotated[
                                str, Path(pattern=r"^(collection1|collection2)$")
                            ]
                        },
                    ),
                ],
                deny=[],
            ),
            "/collections/{collection_id}",
            "GET",
            {"collection_id": "collection3"},
            {},
        )
        is False
    )


def test_has_permission_for_route_matching_permission_query_params():
    """
    Test that if a permission matches the route and the query params match, the function
    returns True.
    """
    assert (
        has_permission_for_route(
            Policy(
                allow=[
                    RoutePermission(
                        paths=["/collections/{collection_id}"],
                        methods=["GET"],
                        query_params={"foo": Annotated[int, Query(le=10)]},
                    ),
                ],
                deny=[],
            ),
            "/collections/{collection_id}",
            "GET",
            {},
            {"foo": 5},
        )
        is True
    )


def test_has_permission_for_route_matching_permission_query_params_no_match():
    """
    Test that if a permission matches the route but the query params do not match, the
    function returns False.
    """
    assert (
        has_permission_for_route(
            Policy(
                allow=[
                    RoutePermission(
                        paths=["/collections/{collection_id}"],
                        methods=["GET"],
                        query_params={"foo": Annotated[int, Query(le=10)]},
                    ),
                ],
                deny=[],
            ),
            "/collections/{collection_id}",
            "GET",
            {},
            {"foo": 15},
        )
        is False
    )


def test_has_permission_for_route_matching_permission_path_and_query_params():
    """
    Test that if a permission matches the route and the path and query params match, the
    function returns True.
    """
    assert (
        has_permission_for_route(
            Policy(
                allow=[
                    RoutePermission(
                        paths=["/collections/{collection_id}"],
                        methods=["GET"],
                        path_params={
                            "collection_id": Annotated[
                                str, Path(pattern=r"^(collection1|collection2)$")
                            ]
                        },
                        query_params={"foo": Annotated[int, Query(le=10)]},
                    ),
                ],
                deny=[],
            ),
            "/collections/{collection_id}",
            "GET",
            {"collection_id": "collection1"},
            {"foo": 5},
        )
        is True
    )


def test_has_permission_for_route_matching_permission_path_and_query_params_no_match():
    """
    Test that if a permission matches the route but the path and query params do not match,
    the function returns False.
    """
    assert (
        has_permission_for_route(
            Policy(
                allow=[
                    RoutePermission(
                        paths=["/collections/{collection_id}"],
                        methods=["GET"],
                        path_params={
                            "collection_id": Annotated[
                                str, Path(pattern=r"^(collection1|collection2)$")
                            ]
                        },
                        query_params={"foo": Annotated[int, Query(le=10)]},
                    ),
                ],
                deny=[],
            ),
            "/collections/{collection_id}",
            "GET",
            {"collection_id": "collection3"},
            {"foo": 15},
        )
        is False
    )


def test_has_permission_for_route_matching_permission_path_and_query_params_no_match_path():
    """
    Test that if a permission matches the route but the path params do not match, the
    function returns False.
    """
    assert (
        has_permission_for_route(
            Policy(
                allow=[
                    RoutePermission(
                        paths=["/collections/{collection_id}/items"],
                        methods=["GET"],
                        path_params={
                            "collection_id": Annotated[
                                str, Path(pattern=r"^(collection1|collection2)$")
                            ]
                        },
                        query_params={"foo": Annotated[int, Query(le=10)]},
                    ),
                ],
                deny=[],
            ),
            "/collections/{collection_id}/items",
            "GET",
            {"collection_id": "collection3"},
            {"foo": 5},
        )
        is False
    )


def test_has_permission_for_route_matching_permission_path_and_query_params_no_match_query():
    """
    Test that if a permission matches the route but the query params do not match, the
    function returns False.
    """
    assert (
        has_permission_for_route(
            Policy(
                allow=[
                    RoutePermission(
                        paths=["/collections/{collection_id}/items"],
                        methods=["GET"],
                        path_params={
                            "collection_id": Annotated[
                                str, Path(pattern=r"^(collection1|collection2)$")
                            ]
                        },
                        query_params={"foo": Annotated[int, Query(le=10)]},
                    ),
                ],
                deny=[],
            ),
            "/collections/{collection_id}/items",
            "GET",
            {"collection_id": "collection1"},
            {"foo": 15},
        )
        is False
    )


def test_has_permission_for_route_matching_permission_path_and_path_params_match_no_query():
    """
    Test that if a permission matches the route and the path params match but no query
    params are defined, the function returns True.
    """
    assert (
        has_permission_for_route(
            Policy(
                allow=[
                    RoutePermission(
                        paths=["/collections/{collection_id}/items"],
                        methods=["GET"],
                        path_params={
                            "collection_id": Annotated[
                                str, Path(pattern=r"^(collection1|collection2)$")
                            ]
                        },
                    ),
                ],
                deny=[],
            ),
            "/collections/{collection_id}/items",
            "GET",
            {"collection_id": "collection1"},
            {},
        )
        is True
    )


def test_has_permission_for_route_matching_permission_path_and_query_params_match_no_path():
    """
    Test that if a permission matches the route and the query params match but no path
    params are defined, the function returns True.
    """
    assert (
        has_permission_for_route(
            Policy(
                allow=[
                    RoutePermission(
                        paths=["/collections"],
                        methods=["GET"],
                        query_params={"foo": Annotated[int, Query(le=10)]},
                    ),
                ],
                deny=[],
            ),
            "/collections",
            "GET",
            {},
            {"foo": 5},
        )
        is True
    )


def test_deny_overrides_allow():
    """
    Test that if a permission in the deny list matches the route and the same permission
    is in the allow list, the function returns False.
    """
    assert (
        has_permission_for_route(
            Policy(
                allow=[
                    RoutePermission(
                        paths=["/collections"],
                        methods=["GET"],
                        query_params={"foo": Annotated[int, Query(le=10)]},
                    ),
                ],
                deny=[
                    RoutePermission(
                        paths=["/collections"],
                        methods=["GET"],
                        query_params={"foo": Annotated[int, Query(le=10)]},
                    ),
                ],
            ),
            "/collections",
            "GET",
            {},
            {"foo": 5},
        )
        is False
    )

