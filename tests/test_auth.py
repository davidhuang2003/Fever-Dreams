import pytest


@pytest.mark.skip(reason="Implement registration and login routes in the authentication milestone.")
def test_registration_creates_a_user(client):
    response = client.post(
        "/register",
        data={
            "username": "stormstudent",
            "email": "student@example.com",
            "password": "a-secure-test-password",
            "confirmation": "a-secure-test-password",
        },
    )
    assert response.status_code in (302, 303)


@pytest.mark.skip(reason="Implement authorization checks in the authentication milestone.")
def test_dashboard_requires_login(client):
    response = client.get("/dashboard")
    assert response.status_code in (302, 303)

