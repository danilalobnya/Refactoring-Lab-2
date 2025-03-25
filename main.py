from typing import List
from pydantic import BaseModel
from fastapi import FastAPI, status, HTTPException, Body

app = FastAPI()


class TodoItem(BaseModel):
    item_id: int
    text: str


class Database:
    def __init__(self):
        self.items = [
            TodoItem(item_id=1, text="Buy milk"),
            TodoItem(item_id=2, text="Walk the dog"),
            TodoItem(item_id=3, text="Do laundry"),
            TodoItem(item_id=4, text="Call John"),
            TodoItem(item_id=5, text="Finish project report"),
        ]

    def get_next_id(self):
        return max(item.item_id for item in self.items) + 1 if self.items else 1

    def reset(self):
        self.__init__()


db = Database()


@app.get("/list", status_code=status.HTTP_200_OK)
def get_todo_list(page: int = 1, per_page: int = 10, filter_text: str = "") -> dict:
    page = max(1, page)
    per_page = max(1, per_page)

    filtered_db = [item for item in db.items if filter_text.lower() in item.text.lower()]
    filtered_db.sort(key=lambda x: x.item_id)

    total_pages = max(1, (len(filtered_db) + per_page - 1) // per_page)
    current_page = min(page, total_pages)

    start_idx = (current_page - 1) * per_page
    end_idx = start_idx + per_page
    current_items = filtered_db[start_idx:end_idx]

    return {
        "items": current_items,
        "total_pages": total_pages,
        "current_page": current_page,
        "per_page": per_page,
    }


@app.get("/item/{item_id}", status_code=status.HTTP_200_OK)
def get_todo_by_id(item_id: int) -> TodoItem:
    for item in db.items:
        if item.item_id == item_id:
            return item
    raise HTTPException(status_code=404, detail=f"Todo item with id {item_id} not found")


@app.post('/item', status_code=status.HTTP_201_CREATED)
def create_todo(text: str = Body(..., embed=True)) -> TodoItem:
    new_todo = TodoItem(item_id=db.get_next_id(), text=text)
    db.items.append(new_todo)
    return new_todo


@app.put("/item/{item_id}")
def update_todo_by_id(item_id: int, text: str = Body(..., embed=True)) -> TodoItem:
    for item in db.items:
        if item.item_id == item_id:
            item.text = text
            return item
    raise HTTPException(status_code=404, detail=f"Todo item with id {item_id} not found")


@app.delete("/item/{item_id}")
def delete_todo_by_id(item_id: int) -> dict:
    for i, item in enumerate(db.items):
        if item.item_id == item_id:
            del db.items[i]
            return {"message": f"Todo item with id {item_id} deleted successfully"}
    raise HTTPException(status_code=404, detail=f"Todo item with id {item_id} not found")
