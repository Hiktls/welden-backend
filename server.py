from fastapi import FastAPI,Depends,Query,Path,HTTPException
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi.security import OAuth2PasswordBearer
from typing import Annotated,List
from web3 import Web3, EthereumTesterProvider
import database
from utils import *


User = database.User

app = FastAPI()
oauth_scheme = OAuth2PasswordBearer(tokenUrl="token")

db = None

USER_ADD_RETURN = lambda msg,extra={} : {"status":"Success","message":msg,**extra}


@app.on_event("startup")
def on_startup():
    global db
    db = database.Database("manage.db")
    db.createDB()




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
    return User(address=user.address,restriction=user.restriction,totalContracts=user.totalContracts)    

@app.get("/users")
async def getUsers(limit:Annotated[int,Query(le=100,ge=0)] = 50) -> List[User]:
    users = db.getAllUsers(limit)
    return users

@app.post("/token")
async def token():
    return True
    

@app.get("/orders/{market_id}/{order_id}")
async def root(market_id,order_id):
    return {"message":"Hello World"}