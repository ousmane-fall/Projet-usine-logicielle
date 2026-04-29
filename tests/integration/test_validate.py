def test_validate_email_ok(client):
    res = client.post("/api/validate", json={"email": "user@example.com"})
    assert res.status_code == 200
    body = res.get_json()
    assert body["valid"] is True
    assert body["email"] == "user@example.com"


def test_validate_username_ok(client):
    res = client.post("/api/validate", json={"username": "alice42"})
    assert res.status_code == 200
    assert res.get_json()["username"] == "alice42"


def test_validate_email_ko(client):
    res = client.post("/api/validate", json={"email": "not-an-email"})
    assert res.status_code == 400


def test_validate_username_ko(client):
    res = client.post("/api/validate", json={"username": "1bad"})
    assert res.status_code == 400


def test_validate_missing(client):
    res = client.post("/api/validate", json={})
    assert res.status_code == 400


def test_create_task_invalid_assignee_email(client):
    res = client.post(
        "/api/tasks",
        json={"title": "T", "assignee_email": "bad"},
    )
    assert res.status_code == 400


def test_create_task_invalid_assignee_username(client):
    res = client.post(
        "/api/tasks",
        json={"title": "T", "assignee_username": "1bad"},
    )
    assert res.status_code == 400


def test_create_task_valid_assignees(client):
    res = client.post(
        "/api/tasks",
        json={
            "title": "T",
            "assignee_email": "u@e.io",
            "assignee_username": "alice",
        },
    )
    assert res.status_code == 201
