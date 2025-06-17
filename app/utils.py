from fastapi import HTTPException,Depends,APIRouter,FastAPI,Request,Query
from fastapi.security import HTTPBearer,HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel,Field
from typing import Annotated,Tuple
import time
import jwt
import yaml
import uuid
from typing import List
from web3 import Web3, EthereumTesterProvider
from contextlib import asynccontextmanager

router = APIRouter()

secrets = yaml.safe_load(open("secrets.yaml","r"))

SECRET_KEY =secrets["SECRET_KEY"]

ALGO = secrets["ALGO"]

NONCE_EXPIRES = secrets["NONCE_EXPIRE_MIN"]

TOKEN_EXPIRES = secrets["ACCESS_TOKEN_EXPIRE_MIN"]

RESTRICTED_PATHS:List[str] = secrets["RESTRICTED_PATHS"]

SYSTEM_ADDRESS:str = secrets["SYSTEM_ADDRESS"]

AddressField = Field(title="Wallet address of the user.",min_length=42,max_length=42)



class Market(BaseModel):
    id:int = Field(ge=0,title="ID of the market")
    market_name:str = Field(title="Name of the market in full string",max_length=128,min_length=0)
    description: str = Field(title="Description of the market and its resolving condition.",max_length=3000)
    volume:int = Field(title="Current volume of the market",default=0)
    weights:int = Field(title="Probablity weights of the market options.",ge=0)
    ask:int = Field(title="Ask price of a single contract in cents.",ge=0)
    bid:int = Field(title="Current bid price of a single contract in cents.",ge=0)
    market_owner:str = AddressField
    isResolved:bool = Field(title="Whetever the market is resolved or not.",default=False)
    isOpen:bool = Field(title="Whetever the market is open or not. This can not be changed until the market is resolved.")


class NonceBase(BaseModel):
    nonce:str = Field()
    timestamp:int= Field(ge=0)

class Nonce(NonceBase):
    address:str = AddressField

class VerifyBody(BaseModel):
    address:str = AddressField
    sig:str = Field()
    nonce:str = Field()

class Token(BaseModel):
    access_token:str
    token_type:str

class JWTProps(BaseModel):
    address:str = AddressField
    exp: str = Field(title="Expiry of the token. Ignored in requests.")
    role:int = Field(title="Role of the user, permissions ascending, 0 being a normal user.",ge=-1,le=2)


BearerSec = HTTPBearer()

USER_ADD_RETURN = lambda msg,extra={} : {"status":"Success","message":msg,**extra}


AdressQuery = Annotated[str,Query(max_length=42,min_length=42)]
TokenDep = Annotated[HTTPAuthorizationCredentials,Depends(BearerSec)]

@asynccontextmanager
async def lifespan(app:FastAPI):
    from . import database
    app.state.w3 = Web3(EthereumTesterProvider())
    app.state.db = database.Database("manage.db")
    app.state.db.createDB()
    yield


def get_perm_raw(token:str) -> int:
    try:
        t =jwt.decode(token.credentials,SECRET_KEY,algorithms=ALGO)
        if t.get("role") is None:
            raise None
        return t.get("role")
    except jwt.InvalidTokenError:
        return None

def get_perm(token:TokenDep) -> int:
    try:
        t =jwt.decode(token.credentials,SECRET_KEY,algorithms=ALGO)
        if t.get("role") is None:
            raise HTTPException(401,"Invalid JWT token.")
        return t.get("role")
    except jwt.InvalidTokenError:
        raise HTTPException(401,"Invalid JWT token.")

RoleDep = Annotated[int,Depends(get_perm)]


def validate_jwt(token:TokenDep):
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
    to_encode.update({"exp":expires,"jti":uuid.uuid4().hex()})
    encoded_jwt = jwt.encode(to_encode,SECRET_KEY,ALGO)
    return encoded_jwt

def calculate_weights(yes:int,no:int) -> Tuple[List[int],str]:
    denom = yes**2 + no**2
    yes_weight = (yes**2)/denom
    no_weight = (no**2)/denom
    return ([yes_weight,no_weight],f"{yes_weight},{no_weight}")


def ReturnJson(content,status) -> JSONResponse:
    return JSONResponse(jsonable_encoder(content),status)
