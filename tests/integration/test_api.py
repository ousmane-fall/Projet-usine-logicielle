def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json["status"] == "ok"


def test_create_task(client):
    r = client.post("/api/tasks", json={"title": "Acheter du lait"})
    assert r.status_code == 201
    assert r.json["title"] == "Acheter du lait"
    assert r.json["status"] == "todo"
    assert "id" in r.json


def test_create_task_missing_title(client):
    r = client.post("/api/tasks", json={})
    assert r.status_code == 400
    assert "error" in r.json


def test_create_task_invalid_status(client):
    r = client.post("/api/tasks", json={"title": "Task", "status": "invalid"})
    assert r.status_code == 400


def test_get_tasks_empty(client):
    r = client.get("/api/tasks")
    assert r.status_code == 200
    assert r.json == []


def test_get_tasks(client):
    client.post("/api/tasks", json={"title": "Task 1"})
    client.post("/api/tasks", json={"title": "Task 2"})
    r = client.get("/api/tasks")
    assert r.status_code == 200
    assert len(r.json) == 2


def test_get_task_by_id(client):
    r = client.post("/api/tasks", json={"title": "Task"})
    task_id = r.json["id"]
    r = client.get(f"/api/tasks/{task_id}")
    assert r.status_code == 200
    assert r.json["id"] == task_id


def test_get_task_not_found(client):
    r = client.get("/api/tasks/999")
    assert r.status_code == 404


def test_update_task(client):
    r = client.post("/api/tasks", json={"title": "Ancien titre"})
    task_id = r.json["id"]
    r = client.put(
        f"/api/tasks/{task_id}", json={"title": "Nouveau titre", "status": "done"}
    )
    assert r.status_code == 200
    assert r.json["title"] == "Nouveau titre"
    assert r.json["status"] == "done"


def test_update_task_invalid_status(client):
    r = client.post("/api/tasks", json={"title": "Task"})
    task_id = r.json["id"]
    r = client.put(f"/api/tasks/{task_id}", json={"status": "invalid"})
    assert r.status_code == 400


def test_delete_task(client):
    r = client.post("/api/tasks", json={"title": "À supprimer"})
    task_id = r.json["id"]
    r = client.delete(f"/api/tasks/{task_id}")
    assert r.status_code == 204
    r = client.get(f"/api/tasks/{task_id}")
    assert r.status_code == 404


def test_filter_by_status(client):
    client.post("/api/tasks", json={"title": "T1", "status": "todo"})
    client.post("/api/tasks", json={"title": "T2", "status": "done"})
    client.post("/api/tasks", json={"title": "T3", "status": "done"})
    r = client.get("/api/tasks?status=done")
    assert r.status_code == 200
    assert len(r.json) == 2
    assert all(t["status"] == "done" for t in r.json)
