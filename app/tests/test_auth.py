from fastapi import FastAPI
from fastapi.testclient import TestClient
from ..main import app as FastAPP
from ..utils import VerifyBody
from eth_account import Account
from web3 import Web3
from .signer import signNonce
import time
w3 = Web3()

client = TestClient(FastAPP)

ACCOUNT = w3.eth.account.create(str(time.time()))

def test_create_secrets():
    with open("secrets.yaml","w") as f:
        f.write("""SECRET_KEY: "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGO: "HS256"
ACCESS_TOKEN_EXPIRE_MIN: 30
NONCE_EXPIRE_MIN: 5""")

# /api/v1/auth/challenge TESTS
def test_challenge_good():
    with TestClient(FastAPP) as client:
        res = client.get("/api/v1/auth/challenge",params={"address":ACCOUNT.address})
        
        assert res.status_code == 200
        assert res.json()["address"]  == ACCOUNT.address
        assert res.json()["timestamp"] > 0 

def test_challenge_invalid_address():
    res = client.get("/api/v1/auth/challenge",params={"address":"YEEHAW"})
    
    assert res.status_code == 422
    assert res.json()["detail"][0]["type"] == "string_too_short"

def test_challenge_empty():
    res = client.get("/api/v1/auth/challenge")

    assert res.status_code == 422
    assert res.json()["detail"][0]["type"] == "missing"


def test_challenge_remove():
    res = client.get("/api/v1/auth/remove",params={"address":ACCOUNT.address})

    assert res.status_code == 200

#  /api/v1/auth/verify TESTS

def test_verify_invalid_address():
    nonce = client.get("/api/v1/auth/challenge",params={"address":ACCOUNT.address}).json()["nonce"]
    sign = signNonce(nonce,ACCOUNT.key)
    verify_body = {"address":"YEEHAW","sig":sign,"nonce":nonce}

    res = client.post("/api/v1/auth/verify",data=verify_body)
    assert res.status_code == 422
    res = client.get("/api/v1/auth/remove",params={"address":ACCOUNT.address})



def test_verify_valid():
    nonce = client.get("/api/v1/auth/challenge",params={"address":ACCOUNT.address}).json()["nonce"]
    sign = signNonce(nonce,ACCOUNT.key)
    verify_body = {"address":ACCOUNT.address,"sig":sign,"nonce":nonce}

    res = client.post("/api/v1/auth/verify",json=verify_body)
    assert res.status_code == 200
    res = client.get("/api/v1/auth/remove",params={"address":ACCOUNT.address})
