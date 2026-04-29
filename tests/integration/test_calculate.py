def test_calculate_expression(client):
    res = client.post("/api/calculate", json={"expression": "1 + 2 * 3"})
    assert res.status_code == 200
    assert res.get_json() == {"result": 7}


def test_calculate_operation_add(client):
    res = client.post("/api/calculate", json={"operation": "add", "a": 2, "b": 3})
    assert res.status_code == 200
    assert res.get_json() == {"result": 5}


def test_calculate_operation_sqrt(client):
    res = client.post("/api/calculate", json={"operation": "sqrt", "a": 16})
    assert res.status_code == 200
    assert res.get_json() == {"result": 4}


def test_calculate_division_by_zero(client):
    res = client.post("/api/calculate", json={"expression": "1/0"})
    assert res.status_code == 400
    assert "Division" in res.get_json()["error"]


def test_calculate_forbidden(client):
    res = client.post("/api/calculate", json={"expression": "__import__('os')"})
    assert res.status_code == 400


def test_calculate_unknown_operation(client):
    res = client.post("/api/calculate", json={"operation": "foo", "a": 1, "b": 2})
    assert res.status_code == 400


def test_calculate_missing_payload(client):
    res = client.post("/api/calculate", json={})
    assert res.status_code == 400
