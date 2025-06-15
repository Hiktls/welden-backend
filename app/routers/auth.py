from ..utils import *
import uuid
from web3 import Web3 as w3,EthereumTesterProvider
from eth_account.messages import encode_defunct
from fastapi import APIRouter


router = APIRouter()

@router.get("/challenge")
async def startChallenge(address:str) -> Nonce:
    nonce = str(uuid.uuid4())
    n = db.addNonce(nonce,address=address)
    return n

@router.post("/verify")
async def verifySig(sig:VerifyBody) -> Token:
    nonce = db.getNonce(sig.address)
    if nonce is None:
        raise HTTPException(401, "Nonce does not exist.")
    if sig.nonce != nonce.nonce:
        raise HTTPException(401, "Signatures not matching.")
    msg = encode_defunct(text=sig.nonce)
    
    recv = w3.eth.account.recover_message(msg,signature=sig.sig)
    print(recv)
    if recv != sig.address:
        raise HTTPException(401,"Signature not matching the nonce.")
    token = create_jwt({"sub":sig.address,"role":0})

    return Token(token_type="bearer",access_token=token)

    
    