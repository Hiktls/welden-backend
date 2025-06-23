from fastapi import HTTPException,Depends,APIRouter,FastAPI,Request,Query
from fastapi.security import HTTPBearer,HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from typing import Annotated,Tuple
import time
import jwt
import uuid
from typing import List
from enum import Enum
from web3 import Web3, EthereumTesterProvider
from contextlib import asynccontextmanager
import yaml
from fastapi import Query
from pydantic import BaseModel
from sqlmodel import Field

router = APIRouter()


secrets = yaml.safe_load(open("secrets.yaml","r"))

SECRET_KEY =secrets["SECRET_KEY"]

ALGO = secrets["ALGO"]

NONCE_EXPIRES = secrets["NONCE_EXPIRE_MIN"]

TOKEN_EXPIRES = secrets["ACCESS_TOKEN_EXPIRE_MIN"]

RESTRICTED_PATHS:List[str] = secrets["RESTRICTED_PATHS"]

SYSTEM_ADDRESS:str = secrets["SYSTEM_ADDRESS"]

AddressField = Field(title="Wallet address of the user.",min_length=42,max_length=42)



class SideEnum(str,Enum):
    BUY = "buy"
    SELL = "sell"

class OutcomeEnum(str,Enum):
    YES = "yes"
    NO = "no"

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


class Order(BaseModel):
    id:int = Field(ge=0,title="ID of the order")
    market_id:int = Field(ge=0,title="ID of the market this order is for.")
    address:str = AddressField
    side:SideEnum = Field(title="Whetever this order is a buy order or not.")
    outcome:OutcomeEnum = Field(title="Outcome of the market to which the order belongs. 0 for first option, 1 for second option.")
    price:int = Field(title="Price of the order in cents.",ge=0)
    amount:int = Field(title="Amount of contracts in this order.",ge=1)
    timestamp:int = Field(title="Timestamp of the order creation.",ge=0)

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


def get_db(request:Request):
    return request.app.state.db

def get_w3(request:Request):
    return request.app.state.w3

W3Dep = Annotated[Web3,Depends(get_w3)]
from .database import Database
DBDep = Annotated[Database,Depends(get_db)]

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


def validate_jwt(token:TokenDep) -> str:
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
    to_encode.update({"exp":expires,"jti":uuid.uuid4().hex})
    encoded_jwt = jwt.encode(to_encode,SECRET_KEY,ALGO)
    return encoded_jwt

def calculate_weights(yes:int,no:int) -> Tuple[List[int],str]:
    denom = yes**2 + no**2
    yes_weight = (yes**2)/denom
    no_weight = (no**2)/denom
    return ([yes_weight,no_weight],f"{yes_weight},{no_weight}")


def try_match_order(order:Order,db:DBDep) -> List[Order]:
    priceToMatch = order.price
    print("SIDE: ","buy" if "sell" == order.side else "sell")
    matched_orders = db.get_order(price=priceToMatch,market_id=order.market_id,outcome=order.outcome,side="buy" if "sell" == order.side else "sell",)

    if matched_orders is None:
        return []

    if matched_orders[0].contracts >= order.amount:
        return [(matched_orders[0],order.amount)]  
    

    orders = []
    contracts_to_fill = order.amount
    print(matched_orders)
    for matched_order in matched_orders:
        if contracts_to_fill <= 0:
            break
        print("TRYING")
        print(contracts_to_fill)
        take = min(matched_order.contracts,contracts_to_fill)
        orders.append((matched_order,take))
        contracts_to_fill -= take
    return orders


def ReturnJson(content,status) -> JSONResponse:
    return JSONResponse(jsonable_encoder(content),status)
