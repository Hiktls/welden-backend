from web3 import Web3 as w3, EthereumTesterProvider
from eth_account.messages import encode_defunct

w3 = w3(EthereumTesterProvider())


nonce = input("Nonce: ")


privateKey = input("Key: ")

msg = encode_defunct(text=nonce)

signed = w3.eth.account.sign_message(msg,private_key=privateKey)

print(signed)