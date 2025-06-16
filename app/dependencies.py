from fastapi import Request,Depends
from typing import Annotated
from .database import Database
from web3 import Web3


def get_db(request:Request):
    return request.app.state.db

def get_w3(request:Request):
    return request.app.state.w3

W3Dep = Annotated[Web3,Depends(get_w3)]
DBDep = Annotated[Database,Depends(get_db)]
