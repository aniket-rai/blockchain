from uuid import uuid4
from flask import Flask
from flask import jsonify
from flask import request
from blockchain import Blockchain

import requests
import json

# Instantiate the node
app = Flask(__name__)

# Generate a unique id for this node
node_id = str(uuid4()).replace('-', '')

# Instantiate blockchain
blockchain = Blockchain()

# Host addresses of other members
peers = set()

@app.route('/transactions/new', methods=['POST'])
def new_trans():
    trans_data = request.get_json()
    required_fields = ['sender', 'recipient', 'amount']

    for field in required_fields:
        if not trans_data.get(field):
            return "Missing Values", 404

    blockchain.new_transaction(trans_data['sender'], trans_data['recipient'], trans_data['amount'])

    return "Sucessfully added transaction to block", 201

def announce_block(block):
    for peer in peers:
        url = f'{peer}/add_block'
        requests.post(url, data=json.dumps(block), sort_keys=True)

@app.route('/mine', methods=['GET'])
def mine():
    if not blockchain.current_transactions:
        return "No transactions to mine", 400
    else:
        current_len = len(blockchain.chain)
        consensus()

        if current_len == len(blockchain.chain):
            last_block = blockchain.last_block
            last_proof = last_block['proof']
            blockchain.new_transaction(sender='0', recipient=node_id, amount=1)
            print('leggo')
            proof = blockchain.proof_of_work(last_proof)

            block = blockchain.new_block(proof)

            response = {
                'message': "New block formed.",
                'index': block['index'],
                'transactions' : block['transactions'],
                'proof' : block['proof'],
                'prv_hash' : block['previous_hash']
            }

            announce_block(blockchain.last_block)
            return jsonify(response), 202

@app.route('/blockchain', methods=['GET'])
def full_chain():
    response = {
        'blockchain': blockchain.chain,
        'length': len(blockchain.chain)
    }
    
    return jsonify(response), 200

@app.route('/register_node', methods=['POST'])
def register_new_peer():
    if not request.get_json()["node_address"]:
        return "Invalid Data", 404

    node_address = request.get_json()["node_address"]
    peers.add(node_address)

    return full_chain()

def check_chain_valid(chain):
    result = True
    previous_hash = "0"

    for block in chain:
        block_hash = block['proof']
        block['proof'] = ""

        if block['index'] == 0:
            last_proof = 100
        else:
            last_block = chain[block["index"] - 1]
            last_proof = last_block["proof"]

        if not blockchain.proof_of_work(last_proof):
            result = False
            break
    
        block['proof'] = block_hash
    
    return result

def consensus():
    global chain

    longest_chain = None
    current_len = len(blockchain.chain)

    for node in peers:
        response = requests.get(f'{node}/blockchain')
        length = response.json()['length']
        chain = response.json()['blockchain']

        if check_chain_valid(chain):
            if length > current_len:
                current_len = length
                longest_chain = chain
    
    if longest_chain:
        if len(longest_chain) > len(blockchain.chain):
            blockchain.chain = longest_chain
            return False
    
    return True

@app.route('/add_block', methods=['POST'])
def verify_add_block():
    block_data = request.get_json()
    block = {
        'index': block_data['index'],
        'timestamp': block_data['timestamp'],
        'transactions': block_data['transactions'],
        'proof': block_data['proof'],
        'previous_hash': block_data['previous_hash']
    }

    if hash(blockchain.last_block) == block['previous_hash']:
        blockchain.chain.append(block)
        return "Block added to chain", 201
    else:
        return "Block was discarded", 400

app.run(debug=True, port=8000)