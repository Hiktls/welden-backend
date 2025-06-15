from fastapi import FastAPI,Depends,Query,Path,HTTPException
from fastapi.responses import RedirectResponse
from fastapi.encoders import jsonable_encoder
from fastapi.security import HTTPBearer
from typing import Annotated,List
from web3 import Web3 as w3,EthereumTesterProvider
from eth_account.messages import encode_defunct
from .database import User
from .utils import *

from .routers import auth,users


app = FastAPI(lifespan=lifespan)
app.include_router(auth.router,tags=["auth"],prefix="/api/v1/auth")
app.include_router(users.router,tags=["user"],prefix="/api/v1/user")



@app.get("/")
async def main_page():
    return RedirectResponse("/docs")