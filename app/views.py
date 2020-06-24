import datetime
import json
import requests
import time

from flask import render_template, redirect, request, Flask

posts = []

host = 'http://127.0.0.1:8000'

app = Flask(__name__)

def fetch_posts():
    get_chain_address = f'{host}/chain'
    response = requests.get(get_chain_address)
    if response.status_code == 200:
        content = []
        chain = json.loads(reponse.content)
        for block in chain["chain"]:
            for tx in block["transactions"]:
                tx["index"] = block["index"]
                tx["hash"] = block["previous_hash"]
                content.append(tx)

        global posts
        posts = sorted(content,
                key=lambda k: k['timestamp'],
                reverse=True)
        
@app.route('/')
def index():
    fetch_posts()
    return render_template('index.html',
                            title='YourNet: Decentralised',
                            posts = posts,
                            node_address=host,
                            readable_time=datetime.datetime.fromtimestamp(int(time.time())).strftime('%H:%M'))

@app.route('/submit', methods=['POST'])
def submit_textarea():
    post_content = request.form["content"]
    author = request.form["author"]

    post_object = {
        'author': author,
        'content': post_content
    }

    new_tx_address = f'{host}/new_transaction'
    requests.post(new_tx_address,
                    json=post_object,
                    headers={'Content-type': 'application/json'})
    
    return redirect('/')

app.run(debug=True)