from fastapi import FastAPI,Depends
from typing_extensions import Annotated
from fastapi.security import OAuth2PasswordBearer
from web3 import Web3, EthereumTesterProvider
import database

app = FastAPI()
oauth_scheme = OAuth2PasswordBearer(tokenUrl="token")


db = database.Database()


SUCCESS_JSON = lambda msg,extra={} : {"status":"Success","message":msg}.update(extra)
FAILED_JSON = lambda msg,extra={} : {"status":"Failed","message":msg}.update(extra)

@app.post("/user/add/{address}")
async def addUser(address:str,restriction:int = 0):
    res = db.addUser(address,restriction)
    if res[1] == -1:
        return FAILED_JSON("Address already exists.")
    return SUCCESS_JSON("Address has been added.")




@app.post("/token")
async def token():
    

@app.get("/orders/{market_id}/{order_id}")
async def root(market_id,order_id,token:Annotated[str,Depends(oauth_scheme)]):
    return {"message":"Hello World"}