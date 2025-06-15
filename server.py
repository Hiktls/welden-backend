from fastapi import FastAPI,Depends,Query,Path,HTTPException
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi.security import HTTPBearer
from typing import Annotated,List
from web3 import Web3 as w3,EthereumTesterProvider
from eth_account.messages import encode_defunct
import database
import uuid
import jwt
from utils import *
import redis





User = database.User

w3 = w3(EthereumTesterProvider())

app = FastAPI()

db = None

USER_ADD_RETURN = lambda msg,extra={} : {"status":"Success","message":msg,**extra}


@app.on_event("startup")
def on_startup():
    global db
    db = database.Database("manage.db")
    db.createDB()



@app.post("/user/add/{address}")
async def addUser(address:Annotated[str, Path(min_length=42,max_length=42)],authAddress:Annotated[str,Depends(validate_jwt)]) -> JSONResponse:
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

@app.get("/auth/challenge")
async def startChallenge(address:str) -> Nonce:
    nonce = str(uuid.uuid4())
    n = db.addNonce(nonce,address=address)
    return n

@app.post("/auth/verify")
async def verifySig(sig:VerifyBody) -> Token:
    nonce = db.getNonce(sig.address)
    if nonce is None:
        raise HTTPException(401, "Nonce does not exist.")
    if sig.nonce != nonce.nonce:
        raise HTTPException(401, "Signatures not matching.")
    msg = encode_defunct(text=sig.nonce)
    
    recv = w3.eth.account.recover_message(msg,signature=sig.sig)
    print(recv)
    if recv != sig.address:
        raise HTTPException(401,"Signature not matching the nonce.")
    token = create_jwt({"sub":sig.address,"role":0})

    return Token(token_type="bearer",access_token=token)

    
    
@app.get("/orders/{market_id}/{order_id}")
async def root(market_id,order_id):
    return {"message":"Hello World"}