from datetime import datetime
from fastapi import Request
from fastapi.params import Path, Query
from pydantic import BaseModel, Field
from typing import Annotated, Any, Callable, Optional, Mapping, Sequence


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
    path_params: Optional[Mapping[str, Annotated[Any, Path]]] = None
    query_params: Optional[Mapping[str, Annotated[Any, Query]]] = None

    class Config:
        arbitrary_types_allowed = True


class RequestTransformation(BaseModel):
    """
    A transformation function to apply to the request body before
    passing it along to the route handler.

    The transform function is passed the request, the policy and any
    additional arguments passed to the route handler. It is expected
    to mutate values in place and not return anything.
    """

    path_formats: list[str]
    transform: Callable[[Request, "Policy", ...], None]  # type: ignore


class Policy(BaseModel):
    """
    A policy for defining model-level and object-level permissions for Collections and Items.

    Consists of an allow and deny permissions boundary and a global permission to allow or deny
    creating collections.

    The deny permissions boundary takes precedence over the allow permissions boundary.
    """

    allow: list[RoutePermission] = Field(default_factory=list)
    deny: list[RoutePermission] = Field(default_factory=list)
    request_transformations: list[RequestTransformation] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)
    default_deny: bool = True
