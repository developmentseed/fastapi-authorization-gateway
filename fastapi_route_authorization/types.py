from datetime import datetime
from fastapi.params import Path, Query
from pydantic import BaseModel
from typing import Optional, Mapping, Sequence


class DateWindow(BaseModel):
    start: datetime
    end: datetime


class SearchConstraints(BaseModel):
    """
    A set of constraints on search requests.

    None indicates no constraint. An empty list indicates no access.
    """

    collections: Optional[list[str]] = None
    geometries: Optional[list[dict]] = None
    date_windows: Optional[list[DateWindow]] = None


class RoutePermission(BaseModel):
    """
    A set of constraints on a route.

    Route access can be constrained by paths, request methods,
    path params, query params and request body.
    """

    paths: Sequence[str]
    methods: Sequence[str]
    path_params: Optional[Mapping[str, Path]] = None
    query_params: Optional[Mapping[str, Query]] = None
    body: Optional[BaseModel] = None

    class Config:
        arbitrary_types_allowed = True


class Policy(BaseModel):
    """
    A policy for defining model-level and object-level permissions for Collections and Items.

    Consists of an allow and deny permissions boundary and a global permission to allow or deny
    creating collections.

    The deny permissions boundary takes precedence over the allow permissions boundary.
    """

    allow: list[RoutePermission] = []
    deny: list[RoutePermission] = []
    search: SearchConstraints = SearchConstraints()
    default_deny: bool = True
