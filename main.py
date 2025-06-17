from fastapi import Depends, FastAPI, HTTPException, Query, Path
from sqlmodel import Field, Session, SQLModel, create_engine, select
from datetime import datetime
from typing import Annotated
from enum import Enum
import requests

class Item_Create(SQLModel):
    name: str = Field(index=True)
    parent_item_id: int | None = Field(default=None, foreign_key="item.id")
    secret_name: str
class Item(Item_Create, table=True):
    id: int | None = Field(default=None, primary_key=True, unique_items=True, nullable=False)

class Location_Create(SQLModel):
    name: str
    secret_name: str

class Location(Location_Create, table=True):
    id: int | None = Field(default=None, primary_key=True, unique_items=True, nullable=False)

class Transaction_Type(str, Enum):
    ADD = "ADD"
    REMOVE = "REMOVE"

class Transaction_Create(SQLModel):
    tr_item_id: int = Field(foreign_key="item.id", nullable=False)
    qty: int = Field(nullable=False)
    tr_location_id: int = Field(nullable=True, foreign_key= "location.id")
    transaction_type: Transaction_Type = Field(nullable=False)


class Transaction(Transaction_Create, table=True):
    transaction_id: int | None = Field(default=None, primary_key=True, unique_items=True, nullable=False)
    tr_timestamp: datetime = Field(default_factory=datetime.now, nullable=False) 

class BarcodeRequest(SQLModel):
    barcode: str

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
    db_item = Item(**item.dict())  
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return db_item

@app.get("/items/")
def read_items(
    session: SessionDep)-> list[Item]:
    items = session.exec(select(Item)).all()
    return items

@app.get("/locations/")
def read_locations(
    session: SessionDep)-> list[Location]:
    locations = session.exec(select(Location)).all()
    return locations

@app.post("/location/")
def add_location(location: Location_Create, session: SessionDep) -> Location:
    db_location = Location(**location.dict())
    session.add(db_location)
    session.commit()
    session.refresh(db_location)
    return db_location

@app.get("/transactions/")
def read_transactions(
    session: SessionDep) -> list[Transaction]:
    transactions = session.exec(select(Transaction)).all()
    return transactions

@app.post("/transaction/")
def add_transaction(
    transaction: Transaction_Create, session: SessionDep) -> Transaction:
    db_transaction = Transaction(**transaction.dict())
    session.add(db_transaction)
    session.commit()
    session.refresh(db_transaction)
    return db_transaction

@app.get("/inventory/")
def get_inventory(session: SessionDep) -> list[dict]:
    statement = (select(Transaction, Item).join(Item, Item.id == Transaction.tr_item_id))
    results = session.exec(statement).all()
##then calculate the total qty of each item
    ##if Transaction_type is add, then add the qty, if Transaction_type is remove, then subtract the qty
    inventory = {}
    for transaction, item in results:
        name = item.name
        item_id = transaction.tr_item_id
        qty = transaction.qty
        tr_type = transaction.transaction_type
        if item_id not in inventory:
            inventory[item_id] = {"item_name":name, "quantity":0}
        if tr_type == Transaction_Type.ADD:
            inventory[item_id]["quantity"] += qty
        elif tr_type == Transaction_Type.REMOVE:
            inventory[item_id]["quantity"] -= qty
    return [{"item_id": item_id, "item_name": data["item_name"], "quantity": data["quantity"]}
        for item_id, data in inventory.items()]

@app.get("/inventory/{location_id}")
def get_inventory_by_location(
    location_id: int,
    session: SessionDep) -> list[dict]:
    statement = (
        select(Transaction, Item)
        .join(Item, Item.id == Transaction.tr_item_id)
        .where(Transaction.tr_location_id == location_id)
    )
    results = session.exec(statement).all()
    inventory: dict[int, dict] = {}
    for transaction, item in results:
        item_id = transaction.tr_item_id
        item_name = item.name
        qty = transaction.qty
        tr_type = transaction.transaction_type
        if item_id not in inventory:
            inventory[item_id] = {"item_name": item_name, "quantity": 0}
        if tr_type == Transaction_Type.ADD:
            inventory[item_id]["quantity"] += qty
        elif tr_type == Transaction_Type.REMOVE:
            inventory[item_id]["quantity"] -= qty

    return [
        {"item_id": item_id, "item_name": data["item_name"], "quantity": data["quantity"]}
        for item_id, data in inventory.items() ]


def find_food_barcode(request: BarcodeRequest):
    url = f"https://staging.openfoodfacts.org/api/v0/product/{request.barcode}.json"

    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException as e:
        return {"error": f"Failed to fetch data: {str(e)}"}
    
    data = response.json()

    if data.get("status") != 1:
        return {"message": "No product found for this barcode"}

    product = data.get("product", {})
    return {
        "product_name": product.get("product_name"),
        "brands": product.get("brands"),
        "categories": product.get("categories"),
        "image_url": product.get("image_url"),
    }

@app.post("/barcode/")
def find_barcode(request: BarcodeRequest):
    url = "https://api.upcitemdb.com/prod/trial/lookup"
    parameters = {"upc": request.barcode}
    response = requests.get(url, params=parameters)
    if response.status_code != 200:
        return {"error": "Failed to fetch barcode data"}
    data = response.json()
    items = data.get("items",[])
    if data.get("items"):
        return data["items"][0]
    else:
        return find_food_barcode(request)
