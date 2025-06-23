from fastapi import APIRouter,Path,Query
from ..database import User
from ..utils import *
from typing import Annotated,List

router = APIRouter()

@router.post("/add/{address}")
async def addUser(address:Annotated[str,Path(title="Address of the user",min_length=42,max_length=42)],tokenAddr:Annotated[str,Depends(validate_jwt)], db:DBDep) -> JSONResponse:
    if tokenAddr != address:
        raise HTTPException(401, f"You can not create an account owned by someone else. Your address is {tokenAddr}")
    res = db.addUser(address,0)
    if res[1] == -1:
        raise HTTPException("Address has already been added.",409)
    return ReturnJson(USER_ADD_RETURN("Address has been added."),200)


@router.get("/{address}")
async def getUser(address:Annotated[str,Path(min_length=42,max_length=42)],db:DBDep) -> User:
    user = db.getUser(address)
    if user is None:
        raise HTTPException(404,"User does not exist.")
    return User(address=user.address,restriction=user.restriction,totalContracts=user.totalContracts)    

@router.get("/users")
async def getUsers(db:DBDep,limit:Annotated[int,Query(le=100,ge=0)] = 50) -> List[User]:
    users = db.getAllUsers(limit)
    return users
