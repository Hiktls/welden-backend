from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel,Field

def ReturnJson(content,status) -> JSONResponse:
    return JSONResponse(jsonable_encoder(content),status)
