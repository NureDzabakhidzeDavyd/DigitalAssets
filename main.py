from flask import Flask, request, render_template, session
from web3 import Web3
from cryptography.fernet import Fernet
import os

app = Flask(__name__)

key = Fernet.generate_key()
cipher_suite = Fernet(key)

app.secret_key = os.urandom(24)

web3 = Web3(Web3.HTTPProvider("https://sepolia.infura.io/v3/3c5b238bb8ae42e9a76ddd561cd51de8"))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    global wallet_address, private_key
    wallet_address = request.form['login']
    private_key = request.form['password']

    encrypted_private_key = cipher_suite.encrypt(private_key.encode())

    if web3.is_address(wallet_address):
        try:
            balance = web3.eth.get_balance(wallet_address)
            balance_eth = web3.from_wei(balance, 'ether')
            session['private_key'] = encrypted_private_key
            return render_template('dashboard.html', wallet_address=wallet_address, balance=balance_eth)
        except Exception as e:
            return f"Error accessing wallet: {e}", 400
    else:
        return "Invalid login credentials", 400

@app.route('/send', methods=['POST'])
def send():
    target_address = request.form['target_address']
    amount = float(request.form['amount'])
    amount_wei = web3.to_wei(amount, 'ether')

    if not web3.is_address(target_address):
        return "Invalid recipient address", 400

    nonce = web3.eth.get_transaction_count(wallet_address)

    decrypted_private_key = cipher_suite.decrypt(session['private_key']).decode()

    gas_price = web3.eth.gas_price

    tx = {
        'nonce': nonce,
        'to': target_address,
        'value': amount_wei,
        'gas': 25000,
        'gasPrice': gas_price,
        'chainId': 11155111
    }

    try:
        signed_tx = web3.eth.account.sign_transaction(tx, decrypted_private_key)
        tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
        return f"Transaction sent! Hash: {web3.to_hex(tx_hash)}"
    except Exception as e:
        return f"Transaction failed: {e}", 400

if __name__ == '__main__':
    app.run(debug=True)
