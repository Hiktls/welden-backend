from fastapi import FastAPI,Depends,Query,Path,HTTPException,Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from fastapi.encoders import jsonable_encoder
from typing import Annotated,List
from web3 import Web3 as w3,EthereumTesterProvider
from eth_account.messages import encode_defunct
from .utils import *
from .routers import auth,users,market,order


app = FastAPI(lifespan=lifespan)
app.include_router(auth.router,tags=["auth"],prefix="/api/v1/auth")
app.include_router(users.router,tags=["user"],prefix="/api/v1/user")
app.include_router(market.router,tags=["market"],prefix="/api/v1/market")
app.include_router(order.router,tags=["order"],prefix="/api/v1/order")


app.mount("/.well-known",StaticFiles(directory=".well-known"),name="well-known")

# Pre-check for restricted API addresses against banned users.
@app.middleware("http")
async def check_ban(request:Request,call_next):
    path = request.url.components.path
    print(path)
    if path in settings.RESTRICTED_PATHS:
        authHeader = request.headers.get("Authorization")
        if authHeader == None or not authHeader.startswith("Bearer"):
            return JSONResponse(status_code=401,content={"detail":"Authorization required in the form of a Bearer header."})
        token = authHeader[7:]
        role = get_perm_raw(token)    
        if role is None:
            return JSONResponse(status_code=401,content={"detail":"Invalid token."})
        if role == -1:
            return JSONResponse(status_code=401,content={"detail":"Your address is banned."})
    
    r = await call_next(request)
    return r

@app.get("/")
async def main_page():
    return RedirectResponse("/docs")
