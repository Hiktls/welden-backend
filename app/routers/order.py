from fastapi import APIRouter,Path,Body
from typing import Annotated
from ..utils import *



router = APIRouter()
from ..database import Order

@router.post("/add")
async def add_limit_order(market_id:Annotated[int,Body(title="ID of the market to which the order belongs.",ge=0)],
                   contracts:Annotated[int,Body(title="Amount of contracts to buy or sell.",ge=1)],
                   price:Annotated[int,Body(title="Price of a single contract in cents.",ge=1,le=99)],
                   outcome:Annotated[OutcomeEnum,Body(title="Outcome of the market to which the order belongs. 0 for first option, 1 for second option.")],
                   side:Annotated[SideEnum,Body(title="Side of the order. Either 'buy' or 'sell'.")],
                   db:DBDep,wallet:Annotated[int,Depends(validate_jwt)]) -> Order:
    if wallet is None:
        raise HTTPException(401,"You are not authorized to place an order. Please login first.")
    # Check if market exists and is open
    m = db.get_market(market_id)
    if m is None:
        raise HTTPException(404,"Market does not exist.")
    elif m is None:
        pass
    if m.isOpen is False:
        raise HTTPException(423,"You can not place an order in a closed market.")
    if m.isResolved is True:
        raise HTTPException(400,"You can not place an order in a resolved market.")

    if contracts <= 0:
        raise HTTPException(400,"Invalid amount of contracts. Must be greater than 0.")
    

    if price <= 0:
        raise HTTPException(400,"Invalid price. Must be greater than 0.")

    # Check if the order matches any standing orders in the book
    matches = try_match_order(Order(market_id=market_id,side=side,outcome=outcome,price=price,amount=contracts,address=wallet),db)

    if matches == []:
        pass
    else:
        # MAKE TRANSACTION HERE
        # The first order will trade with the orders it matched with. If the order is a buy order, the contracts will be transferred to the order holder and 
        # the money will be transferred to the maker
        # If the order is a sell order, the contracts will be transferred to the maker and the money will be transferred to the order holder.
        None

    return db.add_order(contracts=contracts,price=price,wallet=wallet,market_id=market_id,outcome=outcome,side=side)


@router.get("/orders",) # REMOVE FROM PROD
def get_orders(market_id:Annotated[int,Query(ge=0,)],db:DBDep) -> List[Order]:
    """
    Get all orders for a market.
    """
    if not IS_DEV:
        raise HTTPException(403,"This endpoint is not available in production.")
    orders = db.get_order(market_id=market_id)
    if orders is None:
        raise HTTPException(404,"No orders found for this market.")
    return orders

@router.get("/{market_id}/{order_id}")
async def get_order(market_id:Annotated[int,Path(ge=0)],order_id:Annotated[int,Path(ge=0)],db:DBDep) -> Order:
    order = db.get_order(order_id=order_id,market_id=market_id)
    if order is None:
        raise HTTPException(404,"Order not found.")
    return order

@router.get("/populate")
def populate_orders(db:DBDep):
    """
    This is a test function to populate the order book with some dummy data.
    """
    db.add_order(contracts=10,price=55,wallet="0x1234567890123456789012345678901234567890",market_id=1,outcome="yes",side="buy")
    db.add_order(contracts=5,price=90,wallet="0x1234567890123456789012345678901234567890",market_id=1,outcome="no",side="sell")
    db.add_order(contracts=5,price=10,wallet="0x1234567890123456789012345678901234567890",market_id=1,outcome="no",side="sell")
    db.add_order(contracts=10,price=20,wallet="0x1234567890123456789012345678901234567890",market_id=1,outcome="no",side="sell")

    return {"status":"success","message":"Orders populated."}

@router.post("/match")
def match_orders(order:Order,db:DBDep):
    orders = try_match_order(order,db)
    if orders is None:
        raise HTTPException(404,"No orders found for this market.")
    return orders