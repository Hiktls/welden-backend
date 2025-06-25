from fastapi import Depends,HTTPException,Body
from sqlmodel import Field,Session,SQLModel,create_engine,select
from typing import Annotated
import time
import redis
from .utils import *

print(AddressField)

class Order(SQLModel,table=True):
    order_id:int = Field(primary_key=True,ge=0)
    market_id:int = Field(ge=0)
    contracts:int = Field(gt=0)
    price:int = Field(ge=0)
    outcome:OutcomeEnum = Field()
    side:SideEnum = Field()
    wallet:str = AddressField
    ts:int = Field(ge=0)
    status:str = Field()

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
        #SQLModel.metadata.drop_all(self.engine) # REMOVE AT PROD
        SQLModel.metadata.create_all(self.engine)


    def add_market(self,market_name:str,
                  market_desc:str,
                  market_owner:str) -> Market:

        m = Market(market_name=market_name,description=market_desc,volume = 0,weights="50,50",ask=50,bid=50,market_owner=market_owner)
        self.session.add(m)
        self.session.commit()
        self.session.refresh(m)
        return 
    
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

    def get_order(self,order_id:int | None=None, market_id:int | None=None,price: int | None=None,side:str | None=None,outcome:str | None = None) -> Order | None | List[Order]:
        if order_id is not None:
            return self.session.get(Order,order_id)
        query = select(Order).where(
                (Order.market_id == market_id) if market_id is not None else True,
                (Order.price <= price) if price is not None else True,
                (Order.side == side) if side is not None else True,
                (Order.outcome == outcome) if outcome is not None else True,
                (Order.status == "open") if Order.status is not None else True
            ).order_by(Order.ts,Order.price,Order.contracts)

        if price is not None and side == "buy":
            query = select(Order).where(
                (Order.market_id == market_id) if market_id is not None else True,
                (Order.price >= price) if price is not None else True,
                (Order.side == side) if side is not None else True,
                (Order.outcome == outcome) if outcome is not None else True,
                (Order.status == "open") if Order.status is not None else True

            ).order_by(Order.ts,Order.price,Order.contracts)
        elif price is not None and side == "sell":
            query = select(Order).where(
                (Order.market_id == market_id) if market_id is not None else True,
                (Order.price <= price) if price is not None else True,
                (Order.side == side) if side is not None else True,
                (Order.outcome == outcome) if outcome is not None else True,
                (Order.status == "open") if Order.status is not None else True
            ).order_by(Order.ts,Order.price,Order.contracts)

        orders = self.session.exec(query).all()

        return orders if orders else None
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
        

