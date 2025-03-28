import pytest
from fastapi.testclient import TestClient
from main import app, db

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_db():
    db.reset()


def test_get_todo_list_basic():
    response = client.get("/list")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 5
    assert all("item_id" in item for item in data["items"])


def test_get_todo_list_pagination():
    response = client.get("/list?page=2&per_page=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    assert data["total_pages"] == 3


def test_get_todo_list_filtering():
    response = client.get("/list?filter_text=milk")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["text"] == "Buy milk"


def test_get_todo_list_edge_cases():
    response = client.get("/list?page=0")
    assert response.status_code == 200
    assert response.json()["current_page"] == 1


def test_get_todo_by_id_success():
    response = client.get("/item/1")
    assert response.status_code == 200
    data = response.json()
    assert data["text"] == "Buy milk"
    assert data["item_id"] == 1


def test_get_todo_by_id_not_found():
    response = client.get("/item/999")
    assert response.status_code == 404


def test_create_todo_success():
    initial_items = client.get("/list").json()["items"]
    initial_length = len(initial_items)
    response = client.post("/item", json={"text": "New task"})
    assert response.status_code == 201
    new_items = client.get("/list").json()["items"]
    assert len(new_items) == initial_length + 1
    assert response.json()["text"] == "New task"


def test_create_todo_empty_text():
    response = client.post("/item", json={"text": ""})
    assert response.status_code == 201
    assert response.json()["text"] == ""


def test_update_todo_success():
    response = client.put("/item/1", json={"text": "Updated text"})
    assert response.status_code == 200
    data = response.json()
    assert data["text"] == "Updated text"
    assert data["item_id"] == 1

    response = client.get("/item/1")
    assert response.json()["text"] == "Updated text"


def test_update_todo_not_found():
    response = client.put("/item/999", json={"text": "New text"})
    assert response.status_code == 404


def test_delete_todo_success():
    initial_items = client.get("/list").json()["items"]
    initial_length = len(initial_items)
    response = client.delete("/item/1")
    assert response.status_code == 200
    assert response.json() == {"message": "Todo item with id 1 deleted successfully"}
    new_items = client.get("/list").json()["items"]
    assert len(new_items) == initial_length - 1

    response = client.get("/item/1")
    assert response.status_code == 404


def test_delete_todo_not_found():
    response = client.delete("/item/999")
    assert response.status_code == 404