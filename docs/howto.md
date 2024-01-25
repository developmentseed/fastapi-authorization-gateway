# How To

This document will provide brief examples of how to implement common requirements.

## Route-by-route integration

`build_authorization_dependency` returns a function which can be treated as a FastAPI depdendency, so you can use it exactly as you would any other dependency. If you want to only invoke the authorization dependency on a specific route:

```python
authorization = build_authorization_dependency(
    policy_generator=policy_generator,
)

app = FastAPI()

@app.get("/")
def home(self, request: Request, auth: Depends(authorization)):
    return "Hello"

```

## Global Integration

If we want to make use of the authorization dependency on every request, we can define it as a dependency on our FastAPI app:

```python
# define our policy generator up here

authorization = build_authorization_dependency(
    policy_generator=policy_generator,
)

app = FastAPI(dependencies=[Depends(authorization)])
```

## Path Parameter Matching

We can enable a kind of object-level permissions using Path matching in our Policies. For example:

```python
from fastapi import Request
from fastapi.params import Path
from fastapi_authorization_gateway.types import RoutePermission

def generate_policy(request: Request, Annotated[dict, Depends(get_user)]):
    allowed_collection_regex = r"^(collectionA|collectionB)$"
    user_collections = RoutePermission(
        paths=["/collections/{collection_id}"],
        methods=["GET", "PUT", "PATCH", "POST"],
        path_params={"collecton_id": Annotated[str, Path(pattern=user_collection_regex)]}
    )
    return Policy(allow=[user_collections])
```

The policy defined above will limit access to the `/collections/{collection_id}` endpoint to only requests where the `collection_id` path parameter matches the specified regex (either "collectionA" or "collectionB" in this case). Any other requests to that endpoint will be denied.

You can make use of the full conditional capabilities of FastAPIs Path class here, so in addition to `pattern`, you could leverage `lt`, `gt`, etc to add conditions on numerical values.

## Query Parameter Matching

We can also restrict access based on Query parameter values, in much the same way as we do with Path parameters.

```python
from fastapi import Request
from fastapi.params import Query
from fastapi_authorization_gateway.types import RoutePermission

def generate_policy(request: Request, Annotated[dict, Depends(get_user)]):
    allowed_collection_regex = r"^(collectionA|collectionB)$"
    user_collections = RoutePermission(
        paths=["/collections"],
        methods=["GET"],
        query_params={"collecton_id": Annotated[str, Query(pattern=user_collection_regex)]}
    )
    return Policy(allow=[user_collections])
```

In this case, we are restricting requests to the `/collections` to only those where the Query paramter `collection_id` matches the provided regex. For example, `/collections?collection_id=collectionA` would be allowed, but `/collections?collection_id=collectionC` would be denied.

## Request Transformation

## Request Transformation

Authorization is not only about allowing or denying access to a route. In some cases, it makes sense to mutate a request in order to only return data that the user is allowed to access. For example, we may want to filter queries passed to a Search endpoint in order to avoid returning unauthorized data. fastapi-authorization-gateway enables this functionality, but it does require that we set up our authorization layer a bit differently.

In order to mutate a request before passing it on to the underlying endpoint, we wrap all endpoints in a generic receiving function, which runs the usual authorization dependency and then executes any desired request transformations prior to passing everything on to the original endpoing. In order to accomplish this, we need to re-register all endpoints on the router, replacing them with their wrapped counterparts. In practice, what this means for you is the code to add fastapi-authorization-gateway to your app will change from this:

```python
class SearchBody(BaseModel):
    collections: list[str] = Field(default_factory=list)


def transform_search(
    request: Request, policy: Policy, search_body: SearchBody, *args, **kwargs
):
    """
    Filter the requested collections to only those that the user has access to.
    """
    search_body.collections = [
        collection
        for collection in search_body.collections
        if collection in policy.metadata["collections"]
    ]


async def policy_generator(
    request: Request, user: Annotated[dict, Depends(get_user)]
) -> Policy:
    """
    Return a Policy allowing POST requests to /search, but
    modifying incoming requests to restrict access to specific
    collections.
    """
    search = RoutePermission(
        paths=["/search"],
        methods=["POST"],
    )

    request_transformations = [
        RequestTransformation(
            path_formats=["/search"],
            transform=transform_search,
        )
    ]

    policy = Policy(
        allow=[search],
        request_transformations=request_transformations,
        metadata={"collections": user["collections"]},
    )

    return policy

authorization = build_authorization_dependency(
    policy_generator=policy_generator,
)

app = FastAPI(dependencies=[Depends(authorization)])
```

to this:

```python
from fastapi_authorization_gateway.auth import wrap_router
authorization = build_authorization_dependency(
    policy_generator=policy_generator,
)

app = FastAPI()

# define all routes
@app.post("/search")
def search(request: Request, search_body: SearchBody):
    return search_body

# after defining all routes, we can wrap the router, replacing
# all routes with wrapped versions
wrap_router(app.router, authorization_dependency=authorization)
```

### RequestTransformation

A `RequestTransformation` object determines how specific routes will have their incoming request data transformed. They are pretty simple in structure: we define a list of `path_formats` which will be matched against the `path_format` of the Route for a request. If they match, the `transform` function will be passed the `Request`, the active `Policy` and any other arguments defined on the original endpoint.

### Transform functions

A transform function should accept a `Request` object, a `Policy` and any other parameters passed to the original endpoint, if they are useful for the transformation. The transform function returns nothing. Any mutations should be done in-place, since the objects being modified are later passed on to the original endpoint. In the example above, our transform function accepts the `search_body` parameter and modifieds its `collections` property in-place.