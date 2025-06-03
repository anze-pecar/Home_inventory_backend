from fastapi import Depends, FastAPI, HTTPException, Query
from sqlmodel import Field, Session, SQLModel, create_engine, select
from typing import Annotated
from enum import Enum

class Item_Create(SQLModel):
    name: str = Field(index=True)
    parent_item_id: int | None = Field(default=None, foreign_key="item.id")
    secret_name: str
class Item(Item_Create, table=True):
    id: int | None = Field(default=None, primary_key=True, unique_items=True, nullable=False)

class Transaction_Type(str, Enum):
    ADD = "ADD"
    REMOVE = "REMOVE"

class Transaction_Create(SQLModel):
    tr_item_id: int = Field(foreign_key="item.id", nullable=False)
    qty: int = Field(nullable=False)
    tr_location_id: int = Field(nullable=True)
    transaction_type = Transaction_Type

class Transaction(Transaction_Create, table=True):
    transaction_id: int | None = Field(default=None, primary_key=True, unique_items=True, nullable=False)

sqllite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqllite_file_name}"

connect_args = {"check_same_thread" : False}
engine = create_engine(sqlite_url, connect_args=connect_args)
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
def get_session():
    with Session(engine) as session:
        yield session
SessionDep = Annotated[Session, Depends(get_session)]

app = FastAPI()

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

@app.post("/item/")
def add_item(item: Item_Create, session: SessionDep) -> Item:
    db_item = Item(**item.dict())  # ✅ Unpack fields from Item_Create into Item
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return db_item

@app.get("/items/")
def read_items(
    session: SessionDep)-> list[Item]:
    items = session.exec(select(Item)).all()
    return items


