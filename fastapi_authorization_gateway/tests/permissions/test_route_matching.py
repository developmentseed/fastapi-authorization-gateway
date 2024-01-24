from fastapi_route_authorization.permissions import route_matches_permission
from fastapi_route_authorization.types import RoutePermission


def test_route_matches_permission_path_method_match():
    """
    Test route_has_permission function.
    """
    assert (
        route_matches_permission(
            RoutePermission(
                paths=["/collections/{collection_id}"],
                methods=["GET"],
            ),
            "/collections/{collection_id}",
            "GET",
        )
        is True
    )


def test_route_matches_permission_path_match_method_no_match():
    """
    Test that if the path matches but the method does not, the function returns False.
    """
    assert (
        route_matches_permission(
            RoutePermission(
                paths=["/collections/{collection_id}"],
                methods=["GET"],
            ),
            "/collections/{collection_id}",
            "POST",
        )
        is False
    )


def test_route_matches_permission_path_no_match_method_match():
    """
    Test that if the method matches but the path does not, the function returns False.
    """
    assert (
        route_matches_permission(
            RoutePermission(
                paths=["/collections/{collection_id}"],
                methods=["GET"],
            ),
            "/collections",
            "GET",
        )
        is False
    )


def test_route_matches_permission_path_no_match_method_no_match():
    """
    Test that if neither the method nor the path matches, the function returns False.
    """
    assert (
        route_matches_permission(
            RoutePermission(
                paths=["/collections/{collection_id}"],
                methods=["GET"],
            ),
            "/collections/{collection_id}/items",
            "POST",
        )
        is False
    )


def test_route_matches_permission_path_match_method_match_multiple():
    """
    Test that if the permission defines multiple methods and one
    of them matches and the path matches, the function returns True.
    """
    assert (
        route_matches_permission(
            RoutePermission(
                paths=["/collections/{collection_id}"],
                methods=["GET", "PUT"],
            ),
            "/collections/{collection_id}",
            "PUT",
        )
        is True
    )


def test_route_matches_permission_path_match_multiple():
    """
    Test that if the permission defines multiple paths and one
    of them matches and the method matches, the function returns True.
    """
    assert (
        route_matches_permission(
            RoutePermission(
                paths=["/collections/{collection_id}", "/collections"],
                methods=["GET"],
            ),
            "/collections",
            "GET",
        )
        is True
    )
