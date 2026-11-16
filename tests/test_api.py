import random as rnd

import pytest
import requests

from tests.conftest import BASE_URL

# integration tests for the API endpoints
# happy paths

ROOT = BASE_URL + "/api"


def test_health_endpoint_returns_healthy():  # noqa: ANN201, D103
    response = requests.get(ROOT + "/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
    }


def test_register_user_creates_new_user():
    def create_new():
        rnd_joe = "john_doe" + str(rnd.randint(0, 100000))  # noqa: S311
        return requests.post(
            ROOT + "/auth/register",
            json={
                "username": rnd_joe,
                "password": "securepassword123",
            },
        ), rnd_joe

    # the very first user in a fresh DB becomes admin, so make sure it exists
    create_new()

    response, rnd_joe = create_new()
    if response.status_code == 400:  # could be bad rnd luck
        response, rnd_joe = create_new()

    assert response.status_code == 201
    res = response.json()
    assert res["message"] == "User created successfully"
    assert res["user"]["id"]
    assert res["user"]["username"] == rnd_joe
    assert not res["user"]["is_admin"]
    assert res["user"]["created_at"]


def test_register_existing_username_throws():
    def create_new():
        return requests.post(
            ROOT + "/auth/register",
            json={
                "username": "john_doe3",
                "password": "securepassword123",
            },
        )

    response = create_new()
    if response.status_code != 400:
        response = create_new()

    assert response.status_code == 400
    res = response.json()
    assert res["error"] == "Username already exists"


def helper_login_user():
    john = {
        "username": "john_doe",
        "password": "securepassword123",
    }
    response = requests.post(
        ROOT + "/auth/register",
        json=john,
    )

    assert response.status_code in (201, 400)  # new / existing

    response = requests.post(
        ROOT + "/auth/login",
        json=john,
    )

    assert response.status_code == 200

    return response.json()


def test_login_returns_jwt_token():
    import jwt

    from config import Config

    res = helper_login_user()

    token = res["access_token"]
    user = res["user"]

    jwt_res = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=["HS256"])
    assert jwt_res["sub"] == str(user["id"])


def test_invalid_auth_on_protected_endpoint():
    response = requests.post(ROOT + "/events", json={"invalid_evt": "hurtz"})
    assert response.status_code == 401


def test_token_is_accepted_by_protected_endpoint():
    res = helper_login_user()
    token = res["access_token"]

    response = requests.post(
        ROOT + "/events",
        json={"invalid_evt": "hurtz"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 400
    assert response.json()["error"] == "Title is required"


def helper_auth_headers():
    return {"Authorization": f"Bearer {helper_login_user()['access_token']}"}


def helper_create_event(**overrides):
    body = {
        "title": "Test Meetup",
        "description": "pytest generated",
        "date": "2030-01-15T18:00:00",
        "location": "Berlin",
        "is_public": True,
    }
    body.update(overrides)
    return body, requests.post(
        ROOT + "/events",
        json=body,
        headers=helper_auth_headers(),
    )


def test_create_event_with_token_succeeds():
    body, response = helper_create_event()
    assert response.status_code == 201
    res = response.json()
    assert res["id"]
    assert res["title"] == body["title"]
    assert res["description"] == body["description"]
    assert res["location"] == body["location"]
    assert res["date"].startswith("2030-01-15T18:00:00")


def test_rsvp_to_public_event_without_auth_succeeds():
    _, created = helper_create_event(is_public=True)
    event_id = created.json()["id"]

    response = requests.post(ROOT + f"/rsvps/event/{event_id}", json={})
    assert response.status_code == 201
    res = response.json()
    assert res["event_id"] == event_id
    assert res["attending"] is True


def test_rsvp_to_non_public_event_without_auth_is_rejected():
    _, created = helper_create_event(is_public=False)
    event_id = created.json()["id"]

    response = requests.post(ROOT + f"/rsvps/event/{event_id}", json={})
    assert response.status_code == 401
    assert response.json()["error"] == "Authentication required for this event"


if __name__ == "__main__":
    pytest.main(["test_api.py", "-s"])
