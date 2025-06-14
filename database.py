import sqlite3

USERS_TABLE_DEFINITION = """

CREATE TABLE Users(address,restriction,totalContracts)

"""
ADD_USER_DEFINITION = """
INSERT INTO Users VALUES (?,?,0)
"""
GET_USER_DEFINITION = """
SELECT address FROM Users WHERE address=?
"""


class Database:
    def __init__(self):
        self.orderBook = sqlite3.connect("orders.db")
        self.orderCur = self.orderBook.cursor()
        self.users = sqlite3.connect("users.db")
        self.usersCur = self.users.cursor()

    def createUsers(self):
        self.usersCur.execute(USERS_TABLE_DEFINITION)


    def addUser(self,address,restriction):
        exists = self.usersCur.execute(GET_USER_DEFINITION,address).fetchone() is None
        if exists is True:
            return ("Address already exists.",-1)
        self.usersCur.execute(ADD_USER_DEFINITION,address,restriction)
        return ("Address has been added.",0)
        

