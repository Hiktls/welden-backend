from fastapi import Depends,HTTPException,Body
from sqlmodel import Field,Session,SQLModel,create_engine,select
from typing import Annotated
import time
import redis
from .utils import *

print(AddressField)

class Order(SQLModel,table=True):
    order_id:int = Field(primary_key=True,ge=0)
    market_id:int = Field(ge=0,foreign_key="market.id",title="ID of the market this order belongs to.")
    contracts:int = Field(gt=0)
    price:int = Field(ge=0)
    outcome:OutcomeEnum = Field()
    side:SideEnum = Field()
    wallet:str = AddressField
    ts:int = Field(ge=0)
    status:str = Field()

class Share(SQLModel,table=True):
    share_id:int = Field(primary_key=True,ge=0)
    market_id:int = Field(ge=0,foreign_key="market.id",title="ID of the market this share belongs to.")
    user_id:str = Field(foreign_key="user.address",title="Address of the user this share belongs to.",min_length=42,max_length=42)
    outcome:OutcomeEnum = Field(title="Outcome of the share, YES or NO.")
    amount:int = Field(gt=0,title="Amount of shares in this outcome.")

class Market(SQLModel,table=True):
    id:int = Field(primary_key=True,ge=0,title="ID of the market")
    market_name:str = Field(title="Name of the market in full string",max_length=128,min_length=0)
    description: str = Field(title="Description of the market and its resolving condition.",max_length=3000)
    volume:int = Field(title="Current volume of the market",default=0)
    weights:str = Field(title="Probablity weights of the market options.",ge=0)
    ask:int = Field(title="Ask price of a single contract in cents.",ge=0)
    bid:int = Field(title="Current bid price of a single contract in cents.",ge=0)
    market_owner:str = AddressField
    isResolved:bool = Field(title="Whetever the market is resolved or not.",default=False)
    isOpen:bool = Field(title="Whetever the market is open or not. This can not be changed until the market is resolved.",default=False)
class User(SQLModel, table=True):
    address:str = Field(primary_key=True,title="Wallet address of the user.",min_length=42,max_length=42)
    restriction:int = Field(title="Restriction digit of the user.",ge=-1,le=2)
    totalContracts:int = Field(default=0,title="Total amount of contracts the user holds, in every market the user is participating.",ge=0)
    balance:int = Field(default=0,title="Balance of the user in cents.",ge=0)

class Database:
    def __init__(self,dbPath):
        self.redis = redis.Redis(host="localhost",port=6379,decode_responses=True)
        sql_url = f"sqlite:///{dbPath}"
        self.engine = create_engine(sql_url,connect_args={"check_same_thread":False})
        with Session(self.engine) as session:
            self.session = session
        getSession = lambda : self.session
        self.SessionDep = Annotated[Session,Depends(getSession)]

    def addNonce(self,nonce,address) -> Nonce:
        print(self.getNonce(address) == {})
        if self.getNonce(address) is not None:
            raise HTTPException(409,"Nonce for address already exists.")
        ts = int(time.time())
        nonce = NonceBase(nonce=nonce,timestamp=ts) 
        self.redis.hset(name=address,mapping=nonce.model_dump())
        self.redis.expire(address,settings.NONCE_EXPIRE_MIN*3600)
        return Nonce(address=address,nonce=nonce.nonce,timestamp=ts)
    
    def removeNonce(self,address):
        self.redis.delete(address)
        return "OK"

    def getNonce(self,address) -> Nonce:
        n = self.redis.hgetall(name=address)
        if len(n) == 0:
            return None
        return Nonce(address=address,nonce=n["nonce"],timestamp=n["timestamp"])
    

    def createDB(self):
        SQLModel.metadata.drop_all(self.engine) # REMOVE AT PROD
        SQLModel.metadata.create_all(self.engine)

    def open_market(self,market_id:int) -> Market:
        m = self.get_market(market_id)
        m.isOpen = True
        self.session.add(m)
        self.session.commit()
        self.session.refresh(m)
        return m


    def add_market(self,market_name:str,
                  market_desc:str,
                  market_owner:str) -> Market:

        m = Market(market_name=market_name,description=market_desc,volume = 0,weights="50,50",ask=50,bid=50,market_owner=market_owner)
        self.session.add(m)
        self.session.commit()
        self.session.refresh(m)
        return m
    
    def resolve_market(self,market_id):
        m = self.get_market(market_id)
        m.isResolved = True
        self.session.add(m)
        self.session.commit()
        self.session.refresh(m)

    def get_market(self,id:int) -> Market | None:
        return self.session.get(Market,id)
    
    def add_order(self,contracts:int,price:int,wallet:str,market_id:int,outcome:int,side:str):
        ts = int(time.time())
        o = Order(market_id=market_id, contracts=contracts,price=price,outcome=outcome,side=side,filled=0,wallet=wallet,ts=ts,status="open")
        self.session.add(o)
        self.session.commit()
        self.session.refresh(o)
        return o

    def get_order(self,order_id:int | None=None, market_id:int | None=None,price: int | None=None,side:str | None=None,outcome:str | None = None,status:str | None = "open") -> Order | None | List[Order]:
        if order_id is not None:
            return self.session.get(Order,order_id)
        query = select(Order).where(
                (Order.market_id == market_id) if market_id is not None else True,
                (Order.price <= price) if price is not None else True,
                (Order.side == side) if side is not None else True,
                (Order.outcome == outcome) if outcome is not None else True,
                (Order.status == status) if status is not None else True
            ).order_by(Order.ts,Order.price,Order.contracts)

        if price is not None and side == "buy":
            query = select(Order).where(
                (Order.market_id == market_id) if market_id is not None else True,
                (Order.price >= price) if price is not None else True,
                (Order.side == side) if side is not None else True,
                (Order.outcome == outcome) if outcome is not None else True,
                (Order.status == status) if status is not None else True

            ).order_by(Order.ts,Order.price,Order.contracts)
        elif price is not None and side == "sell":
            query = select(Order).where(
                (Order.market_id == market_id) if market_id is not None else True,
                (Order.price <= price) if price is not None else True,
                (Order.side == side) if side is not None else True,
                (Order.outcome == outcome) if outcome is not None else True,
                (Order.status == status) if status is not None else True
            ).order_by(Order.ts,Order.price,Order.contracts)

        orders = self.session.exec(query).all()

        if len(orders) == 1:
            return orders[0]

        return orders if orders else None
    
    def close_order(self,order_id:int) -> Order | None:
        o = self.get_order(order_id=order_id)
        if o is None:
            raise HTTPException(404,"Order does not exist.")
        if o.status != "open":
            raise HTTPException(423,"Order is already closed.")
        o.status = "closed"
        self.session.add(o)
        self.session.commit()
        self.session.refresh(o)
        return o
    
    def transfer_share(self,market_id:int,owner_id:int,recp_id:int,outcome:int,amount:int) -> Share:
        m = self.get_market(market_id)
        if m is None:
            raise HTTPException(404,"Market does not exist.")
        if m.isResolved is True:
            raise HTTPException(423,"You can not add shares to a resolved market.")
        
        original_share = self.session.get(Share,(market_id,owner_id,outcome))
        if original_share is None:
            raise HTTPException(404,"User does not own shares of this market outcome.")
        
        if original_share.amount < amount:
            raise HTTPException(400,"User does not have enough shares to transfer.")
        if original_share.amount == amount:
            original_share.user_id = recp_id
            self.session.add(original_share)
            self.session.commit()
            self.session.refresh(original_share)
            return original_share
        
        original_share.amount -= amount
        self.session.add(original_share)
        self.session.commit()
        self.session.refresh(original_share)

        new_share = Share(market_id=market_id,user_id=recp_id,outcome=outcome,amount=amount)
        self.session.add(new_share)
        self.session.commit()
        self.session.refresh(new_share)
        return new_share

        

    def remove_share(self,market_id:int,user_id:int,outcome:int,amount:int) -> Share:
        m = self.get_market(market_id)
        if m is None:
            raise HTTPException(404,"Market does not exist.")
        if m.isResolved is True:
            raise HTTPException(423,"You can not add shares to a resolved market.")
        
        share = self.session.get(Share,(market_id,user_id,outcome))
        if share is None:
            raise HTTPException(404,"User does not own shares of this market outcome.")
        if (share.amount - amount) <= 0:
            share.amount = 0
            self.session.delete(share)
            self.session.commit()
            return share
        
        share.amount -= amount
        self.session.add(share)
        self.session.commit()
        self.session.refresh(share)
        return share

    def add_share(self,market_id:int,user_id:int,outcome:int,amount:int) -> Share:
        m = self.get_market(market_id)
        if m is None:
            raise HTTPException(404,"Market does not exist.")
        if m.isResolved is True:
            raise HTTPException(423,"You can not add shares to a resolved market.")
        
        share = self.session.get(Share,(market_id,user_id,outcome))

        if share is None:
            share = Share(market_id=market_id,user_id=user_id,outcome=outcome,amount=amount)
            self.session.add(share)
            self.session.commit()
            self.session.refresh(share)
            return share

        if share.outcome != outcome:
            share = Share(market_id=market_id,user_id=user_id,outcome=outcome,amount=amount)
            self.session.add(share)
            self.session.commit()
            self.session.refresh(share)
            return share
        
        share.amount += amount

        self.session.add(share)
        self.session.commit()
        self.session.refresh(share)
        return m

    def getUser(self,address) -> User | None:
        return self.session.get(User,address)
    def getAllUsers(self,limit):
        return self.session.exec(select(User).limit(limit)).all()
    def addUser(self,address,restriction):
        if self.getUser(address) is not None:
            return ("Address already exists.",-1)
        u = User(address=address,restriction=restriction,totalContracts=0)
        self.session.add(u)
        self.session.commit()
        self.session.refresh(u)
        return ("Address has been added.",0)
        

