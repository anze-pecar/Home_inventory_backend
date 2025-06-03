from fastapi import FastAPI

app = FastAPI()

item_db = [{"item_name": "Spaget", "item_qty":15, "location": "Spajza"} , {"item_name":"Mleko", "item_qty": 5, "location":"Hladilnik"}]

@app.get("/")
async def read_root():
    return {"message": "Hello, World!"}

@app.get("/item/{item_name}")
async def item_details(item_name):
    for item in item_db:
        if item["item_name"] == item_name:
         return {"item_name":item["item_name"],
            "item_qty":item["item_qty"]}
    return("item not found")

@app.get("/inventory")
async def get_inventory(location: str = None):
    if location == None:
        return item_db
    else:
        items = []
        for item in item_db:
            if item.get("location") == location:
                items.append(item)
        return items


