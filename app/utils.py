from fastapi import HTTPException,Depends,APIRouter,FastAPI,Request,Query
from fastapi.security import HTTPBearer,HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel,Field
from typing import Annotated
import time
import jwt
import yaml
from . import database
from web3 import Web3, EthereumTesterProvider
from contextlib import asynccontextmanager

router = APIRouter()

secrets = yaml.safe_load(open("secrets.yaml","r"))

SECRET_KEY =secrets["SECRET_KEY"]

ALGO = secrets["ALGO"]

NONCE_EXPIRES = secrets["NONCE_EXPIRE_MIN"]

TOKEN_EXPIRES = secrets["ACCESS_TOKEN_EXPIRE_MIN"]



class NonceBase(BaseModel):
    nonce:str = Field()
    timestamp:int= Field(ge=0)

class Nonce(NonceBase):
    address:str = Field(primary_key=True,title="Wallet address of the user.",min_length=42,max_length=42)

class VerifyBody(BaseModel):
    address:str = Field(primary_key=True,title="Wallet address of the user.",min_length=42,max_length=42)
    sig:str = Field()
    nonce:str = Field()

class Token(BaseModel):
    access_token:str
    token_type:str

BearerSec = HTTPBearer()

USER_ADD_RETURN = lambda msg,extra={} : {"status":"Success","message":msg,**extra}


AdressQuery = Annotated[str,Query(max_length=42,min_length=42)]

@asynccontextmanager
async def lifespan(app:FastAPI):
    app.state.w3 = Web3(EthereumTesterProvider())
    app.state.db = database.Database("manage.db")
    app.state.db.createDB()
    yield




def validate_jwt(token:Annotated[HTTPAuthorizationCredentials,Depends(BearerSec)]):
    try:
        t =jwt.decode(token.credentials,SECRET_KEY,algorithms=ALGO)
        if t.get("sub") is None:
            raise HTTPException(401,"Invalid JWT token.")
        return t.get("sub")
    except jwt.InvalidTokenError:
        raise HTTPException(401,"Invalid JWT token.")


def create_jwt(data:dict):
    to_encode = data.copy()
    expires = int(time.time() + ( TOKEN_EXPIRES* 3600))
    to_encode.update({"exp":expires})
    encoded_jwt = jwt.encode(to_encode,SECRET_KEY,ALGO)
    return encoded_jwt

def ReturnJson(content,status) -> JSONResponse:
    return JSONResponse(jsonable_encoder(content),status)
