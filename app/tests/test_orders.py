from fastapi import FastAPI
from fastapi.testclient import TestClient
from ..main import app as FastAPP
from web3 import Web3

w3 = Web3()

client = TestClient(FastAPP)

ACCOUNT = w3.eth.account.create()


