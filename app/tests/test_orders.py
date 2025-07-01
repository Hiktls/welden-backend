from fastapi import FastAPI
from fastapi.testclient import TestClient
from ..main import app as FastAPP
from web3 import Web3

w3 = Web3()

client = TestClient(FastAPP)

ACCOUNT = w3.eth.account.create()
TEST_AUTH_STR = "VALID_JWT_TEST"
client.headers = {"Authorization": f"Bearer {TEST_AUTH_STR}"}

# Create sample market for testing
with TestClient(FastAPP) as c:
    c.headers = {"Authorization": f"Bearer {TEST_AUTH_STR}"}
    VALID_MARKET_ID = c.post("/api/v1/market/add",json={
    "market_name":"Test Market",
    "market_desc":"A market for testing orders.",
    "market_owner":ACCOUNT.address 
    }).json()["id"]

    c.patch(f"/api/v1/market/open/{VALID_MARKET_ID}")
    

def test_add_order_valid():
    res = client.post("/api/v1/order/add",json={
        "market_id":VALID_MARKET_ID,
        "side":"buy",
        "contracts":10,
        "price":53,
        "outcome":"yes"
    })
    
    global VALID_ORDER_ID
    assert res.status_code == 200
    assert res.json()["status"] == "open" # For now this is always open. In reality, order can match with a maker.
    VALID_ORDER_ID = res.json()["order_id"]


def test_add_order_invalid_market():
    res = client.post("/api/v1/order/add",json={
        "market_id":"yeah",
        "side":"buy",
        "contracts":10,
        "price":53,
        "outcome":"yes"
    })

    assert res.status_code == 422


def test_add_order_invalid_side():
    res = client.post("/api/v1/order/add",json={
        "market_id":VALID_MARKET_ID,
        "side":"cuya",
        "contracts":10,
        "price":53,
        "outcome":"yes"
    })

    assert res.status_code == 422

def test_add_order_invalid_price():
    res = client.post("/api/v1/order/add",json={
        "market_id":VALID_MARKET_ID,
        "side":"buy",
        "contracts":10,
        "price":153,
        "outcome":"yes"
    })

    assert res.status_code == 422

def test_add_order_invalid_auth():

    res = client.post("/api/v1/order/add",json={
        "market_id":VALID_MARKET_ID,
        "side":"buy",
        "contracts":10,
        "price":53,
        "outcome":"yes"
    },headers={"Authorization": "Bearer INVALID_JWT_TEST"})
    
    assert res.status_code == 401

def test_get_order_valid():
    print(VALID_ORDER_ID)
    res = client.get(f"/api/v1/order/0/{VALID_ORDER_ID}")
    print(res.url)
    assert res.status_code == 200
    assert res.json()["order_id"] == VALID_ORDER_ID

def test_get_order_invalid():
    res = client.get(f"/api/v1/order/0/999999")

    assert res.status_code == 404
    assert res.json()["detail"] == "Order not found."


