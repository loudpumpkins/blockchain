import sys
from flask import Flask, jsonify, request
from util import (block_to_dict, valid_post_data, send_message_to_node,
                  get_blockchain_from_node)

app = Flask(__name__)



@app.route('/mine_block/<port>', methods=['POST'])
def mine_block(port):
    post_data = request.get_json(force=True)
    if not valid_post_data(post_data):
        response = {'message': 'invalid post data'}
    else:
        # get chain from network to work on
        blockchain = get_blockchain_from_node(port)
        mined_block = blockchain.mine_data(post_data)
        blockchain.add_mined_block(mined_block)
        # update network with new block
        send_message_to_node(port, blockchain.JSONify())
        response = {'message': 'block inserted into blockchain',
                    'hash': mined_block.hash,
                    'prev_hash': mined_block.previous_hash}
    return jsonify(response), 200


# Getting the full Blockchain
@app.route('/get_chain/<port>', methods=['GET'])
def get_chain(port):
    blockchain = get_blockchain_from_node(port)
    response = {
        'chain': [block_to_dict(block) for block in blockchain.chain],
        'length': blockchain.size}
    return jsonify(response), 200


# Checking if the Blockchain is valid
@app.route('/validate/<port>', methods=['GET'])
def validate(port):
    blockchain = get_blockchain_from_node(port)
    if blockchain.is_valid():
        response = {'message': 'is valid.'}
    else:
        response = {'message': 'not valid.'}
    return jsonify(response), 200


@app.route('/shutdown/<port>', methods=['GET'])
def shutdown(port):
    response = send_message_to_node(port, 'SHUTDOWN')
    if response == 'EXITING':
        return jsonify({'message': 'server is shutdown'}, 200)
    else:
        return jsonify({'message': f'failed to shutdown server: {response}'}, 200)


if __name__ == '__main__':

    app.run(host='0.0.0.0', port=8080, debug=True)

    # Udemy - Build a Blockchain and a Cryptocurrency from Scratch
    # 027 Handle Messages from Peers.mp4
    # 027 Handle Messages from Peers.mp4
    # 027 Handle Messages from Peers.mp4
    # 027 Handle Messages from Peers.mp4
