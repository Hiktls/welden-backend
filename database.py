from utils import *
from fastapi import Depends,HTTPException
from sqlmodel import Field,Session,SQLModel,create_engine,select
from typing import Annotated
import time
import redis




USERS_TABLE_DEFINITION = """

CREATE TABLE Users(address,restriction,totalContracts)

"""
ADD_USER_DEFINITION = """
INSERT INTO Users VALUES (?,?,0)
"""
GET_USER_DEFINITION = """
SELECT address,restriction,totalContracts FROM Users WHERE address=?
"""


class User(SQLModel, table=True):
    address:str = Field(primary_key=True,title="Wallet address of the user.",min_length=42,max_length=42)
    restriction:int = Field(title="Restriction digit of the user.",ge=-1,le=2)
    totalContracts:int = Field(default=0,title="Total amount of contracts the user holds, in every market the user is participating.",ge=0,)

class OrderBook(SQLModel,table=True):
    order_id:int = Field(primary_key=True,ge=0)
    contracts:int = Field(ge=0)
    cost:int = Field(ge=0)
    limit:int = Field(ge=0)



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
        self.redis.expire(address,NONCE_EXPIRES*3600)
        return Nonce(address=address,nonce=nonce,timestamp=ts)
    
    def removeNonce(self,address):
        self.redis.delete(address)

    def getNonce(self,address) -> Nonce:
        n = self.redis.hgetall(name=address)
        if n is {}:
            return None
        return Nonce(address=address,nonce=n["nonce"],timestamp=n["timestamp"])
    

    def createDB(self):
        SQLModel.metadata.create_all(self.engine)


    def getUser(self,address):
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
        

