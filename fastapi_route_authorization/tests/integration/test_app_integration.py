"""
Test integration with a FastAPI app.

The example app defines a policy restricting access to GET on all
routes and POST only on the Search route. It also defines a
transformation function that filters the requested collections on the
search route to only those that the user has access to.
"""
from fastapi.testclient import TestClient
from fastapi_route_authorization.tests.integration.example_app import app

client = TestClient(app)


def test_get_test():
    """
    User can GET the test route.
    """
    response = client.get("/test")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_post_test():
    """
    User cannot POST to the test route.
    """
    response = client.post("/test", json={"name": "test"})
    assert response.status_code == 403


def test_get_test_id():
    """
    User can GET the test route with an ID.
    """
    response = client.get("/test/1")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "test_id": 1}


def test_search():
    """
    User can POST to the search route.
    """
    response = client.post(
        "/search",
        json={"collections": ["hello", "world"]},
    )
    assert response.status_code == 200
    assert response.json() == {"collections": ["hello", "world"]}


def test_search_filtering():
    """
    User can POST to the search route, but the collections are filtered
    by the policy.
    """
    response = client.post(
        "/search",
        json={"collections": ["hello", "world", "not_allowed"]},
    )
    assert response.status_code == 200
    assert response.json() == {"collections": ["hello", "world"]}