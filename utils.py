from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel,Field

class User(BaseModel):
    address:str = Field(title="Wallet address of the user.",min_length=42,max_length=42,examples=["0x8e35150473630E960B5909476A5167f3F224D89d"])
    restriction:int = Field(title="Restriction digit of the user.",ge=-1,le=2)
    totalContracts:int = Field(default=0,title="Total amount of contracts the user holds, in every market the user is participating.",ge=0,)



def ReturnJson(content,status) -> JSONResponse:
    return JSONResponse(jsonable_encoder(content),status)
