from fastapi import FastAPI,Depends,Query,Path,HTTPException
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi.security import OAuth2PasswordBearer
from typing import Annotated
from web3 import Web3, EthereumTesterProvider
import database
from utils import *



app = FastAPI()
oauth_scheme = OAuth2PasswordBearer(tokenUrl="token")

db = database.Database()

USER_ADD_RETURN = lambda msg,extra={} : {"status":"Success","message":msg,**extra}



@app.post("/user/add/{address}")
async def addUser(address:Annotated[str, Path(min_length=42,max_length=42)]) -> JSONResponse:
    res = db.addUser(address,0)
    if res[1] == -1:
        raise HTTPException("Address has already been added.",409)
    return ReturnJson(USER_ADD_RETURN("Address has been added."),200)


@app.get("/user/{address}")
async def getUser(address:Annotated[str,Path(min_length=42,max_length=42)]) -> User:
    user = db.getUser(address)
    if user is None:
        raise HTTPException(404,"User does not exist.")
    return User(address=user[0],restriction=user[1],totalContracts=user[2])    

@app.post("/token")
async def token():
    return True
    

@app.get("/orders/{market_id}/{order_id}")
async def root(market_id,order_id):
    return {"message":"Hello World"}