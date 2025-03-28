from pydantic import BaseModel
from fastapi import FastAPI, status, HTTPException, Body
import sqlite3
from contextlib import contextmanager

app = FastAPI()


class TodoItem(BaseModel):
    item_id: int
    text: str


class Database:
    def __init__(self):
        self._init_db()

    @contextmanager
    def _get_cursor(self):
        conn = sqlite3.connect('todos.db')
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        finally:
            conn.close()

    def _init_db(self):
        with self._get_cursor() as cursor:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS todos (
                    item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    text TEXT NOT NULL
                )
            ''')
            print("Table created or already exists.")
            cursor.execute("SELECT COUNT(*) FROM todos")
            count = cursor.fetchone()[0]
            if count == 0:
                initial_items = [
                    ("Buy milk",),
                    ("Walk the dog",),
                    ("Do laundry",),
                    ("Call John",),
                    ("Finish project report",)
                ]
                cursor.executemany("INSERT INTO todos (text) VALUES (?)", initial_items)
                print("Initial items added.")

    def get_next_id(self):
        with self._get_cursor() as cursor:
            cursor.execute("SELECT seq FROM sqlite_sequence WHERE name='todos'")
            result = cursor.fetchone()
            return (result[0] + 1) if result else 1

    def reset(self):
        with self._get_cursor() as cursor:
            cursor.execute("DROP TABLE IF EXISTS todos")
        self._init_db()

    def get_all_items(self):
        with self._get_cursor() as cursor:
            cursor.execute("SELECT item_id, text FROM todos")
            return [TodoItem(item_id=row[0], text=row[1]) for row in cursor.fetchall()]

    def get_item_by_id(self, item_id: int):
        with self._get_cursor() as cursor:
            cursor.execute("SELECT item_id, text FROM todos WHERE item_id = ?", (item_id,))
            row = cursor.fetchone()
            return TodoItem(item_id=row[0], text=row[1]) if row else None

    def create_item(self, text: str):
        with self._get_cursor() as cursor:
            cursor.execute("INSERT INTO todos (text) VALUES (?)", (text,))
            item_id = cursor.lastrowid
            return TodoItem(item_id=item_id, text=text)

    def update_item(self, item_id: int, text: str):
        with self._get_cursor() as cursor:
            cursor.execute(
                "UPDATE todos SET text = ? WHERE item_id = ?",
                (text, item_id)
            )
            if cursor.rowcount == 0:
                return None
            return TodoItem(item_id=item_id, text=text)

    def delete_item(self, item_id: int):
        with self._get_cursor() as cursor:
            cursor.execute("DELETE FROM todos WHERE item_id = ?", (item_id,))
            return cursor.rowcount > 0


db = Database()


@app.get("/list", status_code=status.HTTP_200_OK)
def get_todo_list(page: int = 1, per_page: int = 10, filter_text: str = "") -> dict:
    page = max(1, page)
    per_page = max(1, per_page)

    all_items = db.get_all_items()

    # Фильтрация
    filtered_items = [
        item for item in all_items
        if filter_text.lower() in item.text.lower()
    ]

    # Сортировка
    filtered_items.sort(key=lambda x: x.item_id)

    total_pages = max(1, (len(filtered_items) + per_page - 1) // per_page)
    current_page = min(page, total_pages)

    start_idx = (current_page - 1) * per_page
    end_idx = start_idx + per_page
    current_items = filtered_items[start_idx:end_idx]

    return {
        "items": current_items,
        "total_pages": total_pages,
        "current_page": current_page,
        "per_page": per_page,
    }


@app.get("/item/{item_id}", status_code=status.HTTP_200_OK)
def get_todo_by_id(item_id: int) -> TodoItem:
    item = db.get_item_by_id(item_id)
    if item is None:
        raise HTTPException(
            status_code=404,
            detail=f"Todo item with id {item_id} not found"
        )
    return item


@app.post('/item', status_code=status.HTTP_201_CREATED)
def create_todo(text: str = Body(..., embed=True)) -> TodoItem:
    return db.create_item(text)


@app.put("/item/{item_id}")
def update_todo_by_id(item_id: int, text: str = Body(..., embed=True)) -> TodoItem:
    item = db.update_item(item_id, text)
    if item is None:
        raise HTTPException(
            status_code=404,
            detail=f"Todo item with id {item_id} not found"
        )
    return item


@app.delete("/item/{item_id}")
def delete_todo_by_id(item_id: int) -> dict:
    if not db.delete_item(item_id):
        raise HTTPException(
            status_code=404,
            detail=f"Todo item with id {item_id} not found"
        )
    return {"message": f"Todo item with id {item_id} deleted successfully"}
