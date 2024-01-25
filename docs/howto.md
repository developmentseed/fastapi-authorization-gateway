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

## StacAPI Integration

If we only want to use the authorization dependency on specific StacApi routes, we can do so using one of two mechanisms provided by stac-fastapi. The first is to define the dependency on the `APIRouter` for the app. This will invoke it on any request handled by the core APIRouter.

```python
# define our policy generator up here

authorization = build_authorization_dependency(
    policy_generator=policy_generator,
)

StacApi(
    app=app,  # our FastAPI app
    router=APIRouter(
        dependencies=[Depends(authorization)],
    ),
```

*However*, the core router only seems to cover routes from the core STAC Spec and does not cover common extensions, such as Transactions. In order to support depenency injection on routes provided by extensions, the `StacApi` class provides a `route_dependencies` argument, which allow us to define a list of routes and dependencies to inject for them.

```python
# define our policy generator up here

authorization = build_authorization_dependency(
    policy_generator=policy_generator,
)

StacApi(
    app=app,  # our FastAPI app
    router=APIRouter(
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
    ]
```

You can use one or both of these mechanisms, depending on your needs. If you don't want to mess around with defining each route covered by each extension and want to protect the entire app, you can use the Global Integration above.