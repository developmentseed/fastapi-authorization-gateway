"""
Test params_match_permission function.
"""
from typing import Annotated
from fastapi import Path, Query
from fastapi_authorization_gateway.permissions import params_match_permission


def test_params_match_permission_no_params():
    """
    Test that if no params are defined on the permission, the function returns True.
    """
    assert params_match_permission(None, {}) is True


def test_params_match_permission_no_user_params():
    """
    Test that if no user params are provided, the function returns False.
    """
    assert params_match_permission({"foo": Annotated[int, Query(le=10)]}, {}) is False


def test_params_match_permission_user_params_match():
    """
    Test that if user params match the permission, the function returns True.
    """
    assert (
        params_match_permission({"foo": Annotated[int, Query(le=10)]}, {"foo": 5})
        is True
    )


def test_params_match_permission_user_params_no_match():
    """
    Test that if user params do not match the permission, the function returns False.
    """
    assert (
        params_match_permission({"foo": Annotated[int, Query(le=10)]}, {"foo": 15})
        is False
    )


def test_params_match_permission_user_params_match_no_annotation():
    """
    Test that if user params match the permission but no annotation is provided, the
    function returns True.
    """
    assert params_match_permission({"foo": Annotated[int, Query()]}, {"foo": 5}) is True


def test_params_match_permission_user_params_no_match_annotation_type():
    """
    Test that if user params do not match the annotation type
    the function returns False.
    """
    assert (
        params_match_permission({"foo": Annotated[int, Query()]}, {"foo": "bar"})
        is False
    )


def test_params_match_permission_user_params_match_type_no_conditions():
    """
    Test that if user params match the annotation type and no Param conditions
    are specified, the function returns True.
    """
    assert (
        params_match_permission({"foo": Annotated[str, Query()]}, {"foo": "bar"})
        is True
    )


def test_path_param_with_pattern():
    """
    Test that if a path param with a pattern is provided and a matching string is provided,
    the function returns True.
    """
    assert (
        params_match_permission(
            {"foo": Annotated[str, Path(pattern="^foo$")]}, {"foo": "foo"}
        )
        is True
    )


def test_path_param_with_pattern_no_match():
    """
    Test that if a path param with a pattern is provided and a non-matching string is provided,
    the function returns False.
    """
    assert (
        params_match_permission(
            {"foo": Annotated[str, Path(pattern="^foo$")]}, {"foo": "bar"}
        )
        is False
    )
