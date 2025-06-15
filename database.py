import sqlite3
import utils
from fastapi import Depends
from sqlmodel import Field,Session,SQLModel,create_engine,select
from typing import Annotated




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

        sql_url = f"sqlite:///{dbPath}"
        self.engine = create_engine(sql_url,connect_args={"check_same_thread":False})
        with Session(self.engine) as session:
            self.session = session
        getSession = lambda : self.session
        self.SessionDep = Annotated[Session,Depends(getSession)]
        # self.orderBook = sqlite3.connect("orders.db")
        # self.orderCur = self.orderBook.cursor()
        # self.users = sqlite3.connect("users.db")
        # self.usersCur = self.users.cursor()

    def createDB(self):
        SQLModel.metadata.create_all(self.engine)
        # self.usersCur.execute(USERS_TABLE_DEFINITION)
        # self.users.commit()

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
        

