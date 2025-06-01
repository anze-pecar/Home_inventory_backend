from fastapi import FastAPI

app = FastAPI()
##test za update kode, ker neznam drugače testirati lp
@app.get("/")
async def read_root():
    return {"message": "Hello, World!"}

def test():
    print("zaplet")