from fastapi import FastAPI
from fastapi.testclient import TestClient
from ..main import app as FastAPP
from web3 import Web3

w3 = Web3()

client = TestClient(FastAPP)

ACCOUNT = w3.eth.account.create()
TEST_AUTH_STR = "VALID_JWT_TEST"
client.headers = {"Authorization": f"Bearer {TEST_AUTH_STR}"}


def test_add_market_valid():
    res = client.post("/api/v1/market/add", json={
        "market_name": "Test Market",
        "market_desc": "A market for testing orders.",
        "market_owner": ACCOUNT.address
    })

    assert res.status_code == 200
    assert res.json()["market_name"] == "Test Market"
    assert res.json()["market_owner"] == ACCOUNT.address

def test_add_market_invalid_creds():
    res = client.post("/api/v1/market/add", json={
        "market_name": "Test Market",
        "market_desc": "A market for testing orders.",
        "market_owner": ACCOUNT.address
    },headers={"Authorization":"Bearer INVALID_JWT_TEST"})

    assert res.status_code == 401

def test_open_market_valid():
    res = client.post("/api/v1/market/add", json={
        "market_name": "Test Market",
        "market_desc": "A market for testing orders.",
        "market_owner": ACCOUNT.address
    })

    market_id = res.json()["id"]

    res = client.patch(f"/api/v1/market/open/{market_id}")

    assert res.status_code == 200
    assert res.json()["isOpen"] == True


def test_open_market_invalid_id():
    _ = client.post("/api/v1/market/add", json={
        "market_name": "Test Market",
        "market_desc": "A market for testing orders.",
        "market_owner": ACCOUNT.address
    })

    market_id = 9999999999999

    res = client.patch(f"/api/v1/market/open/{market_id}")

    assert res.status_code == 404


def test_open_market_already_open():
    res = client.post("/api/v1/market/add", json={
        "market_name": "Test Market",
        "market_desc": "A market for testing orders.",
        "market_owner": ACCOUNT.address
    })

    market_id = res.json()["id"]

    res = client.patch(f"/api/v1/market/open/{market_id}")

    res = client.patch(f"/api/v1/market/open/{market_id}")

    assert res.status_code == 423

def test_open_market_no_auth():
    res = client.post("/api/v1/market/add", json={
        "market_name": "Test Market",
        "market_desc": "A market for testing orders.",
        "market_owner": ACCOUNT.address
    })

    market_id = res.json()["id"]

    res = client.patch(f"/api/v1/market/open/{market_id}",headers={"Authorization": "Bearer INVALID_JWT_TEST"})

    assert res.status_code == 401
