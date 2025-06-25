from fastapi import APIRouter,Path,Body
from typing import Annotated
from ..utils import *



router = APIRouter()

@router.post("/add")
async def add_market(market_name:Annotated[str,Body(title="Name of the market",max_length=128)],
                  market_desc:Annotated[str,Body(title="Description and resolve condition of the market.",max_length=3000)] ,
                  permission:Annotated[int,Depends(get_perm)],
                  db:DBDep,
                  market_owner:Annotated[str,Body(title="Address of the market owner. This could be a user, or the system itself. In general, whoever submitted the market gets it.")]=settings.SYSTEM_ADDRESS) -> Market:
    if permission <= 0:
        raise HTTPException(403, "You are not permitted to add a market.")
    return db.add_market(market_name,market_desc,market_owner)

@router.patch("/open/{market_id}")
async def open_market(market_id:Annotated[int,Path(title="ID of the market")],db:DBDep,perm:RoleDep) -> Market:
    if perm <= 1:
        raise HTTPException(403,"You are not authorized for this.")
    m = db.get_market(market_id)
    if m is None:
        raise HTTPException(404,"Market does not exist.")
    if m.isOpen is True:
        raise HTTPException(423,"Market is already open.")
    if m.isResolved is True:
        raise HTTPException(400,"You can not open a resolved market.")
    return db.open_market(market_id)


@router.post("/resolve/{market_id}")
async def resolve_market(market_id:Annotated[int,Path(title="Access ID of the market.")],db:DBDep,perm:Annotated[int,Depends(get_perm)]):
    if perm <= 0:
        raise HTTPException(403, "You are not authorized to resolve the market.")
    # Check if market exists and get info if it does
    m = db.get_market(market_id)
    if m is None:
        raise HTTPException(404,"Market does not exist.")
    if m.isOpen is False:
        raise HTTPException(423,"You can not resolve an already closed market.")
    if m.isResolved is True:
        raise HTTPException(400,"You can not resolve an already resolved market.")
    
    db.resolve_market(market_id)
    #TODO: ADD FUNCTION TO CREATE A 4 HOUR TIMER. THE TIMER WILL THEN DISTRIBUTE EACH WINNER WITH A DOLLAR.    

@router.get("/{market_id}")
async def get_market(market_id:Annotated[int,Path(ge=0,title="Access ID of the market, auto assigned at creation.")],db:DBDep) -> Market | None:
    return  db.get_market(market_id)