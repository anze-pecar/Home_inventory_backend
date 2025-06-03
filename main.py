from fastapi import Depends, FastAPI, HTTPException, Query
from sqlmodel import Field, Session, SQLModel, create_engine, select
from typing import Annotated

class Item(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True, unique_items=True)
    name: str = Field(index=True)
    parent_item_id: None = Field(default=None, foreign_key=True)
    secret_name: str

sqllite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqllite_file_name}"

connect_args = {"check_same_thread" : False}
engine = create_engine(sqlite_url, connect_args=connect_args)
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
def get_session():
    with Session(engine) as sesstion:
        yield sesstion
SessionDep = Annotated[Session, Depends(get_session)]

app = FastAPI()

@app.lifespan("startup")
def on_startup():
    create_db_and_tables()
@app.post("/item/")
def add_item(item: Item, session: SessionDep) -> Item:
    session.add(item)
    session.commit()
    session.refresh(item)
    return item
@app.get("/items/")
def read_items(
    session: SessionDep)-> list[Item]:
    items = session.exec(select(Item).all())
    return items

