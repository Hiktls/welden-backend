from ..utils import *
import uuid
from eth_account.messages import encode_defunct
from fastapi import APIRouter,Query,Request
from ..dependencies import *

router = APIRouter()



@router.get("/challenge")
async def start_challenge(address:AdressQuery,db:DBDep) -> Nonce:
    nonce = str(uuid.uuid4())
    n = db.addNonce(nonce,address=address)
    return n

@router.get("/remove")
async def remove_nonce(address:AdressQuery,db:DBDep):
    db.removeNonce(address)
    

@router.post("/verify")
async def verify_sig(sig:VerifyBody,db:DBDep,w3:W3Dep) -> Token:
    nonce = db.getNonce(sig.address)
    if nonce is None:
        raise HTTPException(401, "Nonce does not exist.")
    if sig.nonce != nonce.nonce:
        raise HTTPException(401, "Signatures not matching.")
    msg = encode_defunct(text=sig.nonce)
    
    recv = w3.eth.account.recover_message(msg,signature=sig.sig)
    if recv != sig.address:
        raise HTTPException(401,"Signature not matching the nonce.")
    token = create_jwt({"sub":sig.address,"role":0})
    db.removeNonce(sig.address)
    return Token(token_type="bearer",access_token=token)

    
    