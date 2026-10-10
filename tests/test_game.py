import pytest


def test_home_page_renders(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Fever-Dreams" in response.data


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {
        "application": "fever-dreams",
        "status": "ok",
    }


@pytest.mark.skip(reason="Implement the playthrough API in the interactive-game milestone.")
def test_choice_is_recorded_once(client):
    response = client.post("/api/playthroughs/1/choices", json={"choice_id": 1})
    assert response.status_code == 200

