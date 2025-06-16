from ..utils import *
import uuid
from eth_account.messages import encode_defunct
from fastapi import APIRouter,Query,Request,Body
from ..dependencies import *

router = APIRouter()




@router.get("/challenge")
async def start_challenge(address:AdressQuery,db:DBDep) -> Nonce:
    nonce = str(uuid.uuid4())
    n = db.addNonce(nonce,address=address)
    return n


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
    
    role = 0
    u = db.getUser(sig.address)
    if u is not None:
        role = u.restriction

    token = create_jwt({"sub":sig.address,"role":0})
    db.removeNonce(sig.address)


    return Token(token_type="bearer",access_token=token)


@router.post("/role") # userJWT is the JWT properties of the user WITHOUT changes. Role parameters is the role of the user makign the request
async def change_role(role:RoleDep,userJWT:JWTProps,changed_role: Annotated[int,Body()]):
    if role == 2:
        create_jwt({"sub":userJWT.address,"role":changed_role})
        return 
    elif role > 0 and userJWT.role < 1: # Ensure the request source has permissions for the action
        create_jwt({"sub":userJWT.address,"role":changed_role})
    elif role < 1:
        raise HTTPException(401, "You are not authorized for this.")
    elif role > 0 and userJWT.role > 0:
        raise HTTPException(401, "You are not authorized enough to change roles of admins and headmasters.")


@router.get("/remove")
async def remove_nonce(address:AdressQuery,db:DBDep):
    db.removeNonce(address)
    
