from web3 import Web3 as w3, EthereumTesterProvider
from eth_account.messages import encode_defunct

w3 = w3(EthereumTesterProvider())



def signNonce(nonce,priv_key):
    msg = encode_defunct(text=nonce)

    signed = w3.eth.account.sign_message(msg,private_key=priv_key)
    return "0x"+signed.signature.hex()
