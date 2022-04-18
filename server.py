import datetime
import json
import socket
import sys
from json.decoder import JSONDecodeError

from blockchain import Blockchain
from util import LockedOpen

HEADER_SIZE = 10
MAX_CONNECTIONS = 5


class P2PServer(object):

    P2P_SERVERS_LIST = 'nodes.json'

    def __init__(self, port):
        self.blockchain = Blockchain()
        self.port = port

    def listen(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind(('localhost', self.port))
        self.socket.listen(MAX_CONNECTIONS)
        self.subscribe()  # attach self to P2P network

        # cycle = (1) connect, (2) get msg, (3) process msg, (4) respond
        while True:

            # accept connections
            client, addr = self.socket.accept()
            self.log(f"Connected to '{addr}'")

            # get message
            size = int(str(client.recv(HEADER_SIZE), 'utf-8'))
            data = str(client.recv(size), 'utf-8')
            self.log(f"Receiving message ({size} chars) -> {data[:100]}")

            # process request
            resp = self.process_request(data)
            self.log(f"Server response -> {resp[:100]}")

            # respond
            client.send(bytes(f'{len(resp):<{HEADER_SIZE}}{resp}', 'utf-8'))
            client.close()
            self.log(f"Client '{addr}' disconnected")

            if resp == 'EXITING':
                self.log("Terminating server")
                self.unsubscribe()  # detash self to P2P network
                exit(0)

    def log(self, msg):
        print(f"{datetime.datetime.today()} :: ({self.port}) :: {msg}")

    def notify_nodes(self, blockchain):
        """
        notify each node in the network of a change in the blockchain

        :param blockchain: Blockchain
        :return: NoReturn
        """
        servers = self._open_servers_list()
        for port, address in servers.items():
            response = self.send(int(port), blockchain.JSONify())

    def process_request(self, data):
        """
        Process the incoming request. Valid requests are:

            GET CHAIN -> Returns this nodes blockchain as a JSON parsable string
            SHUTDOWN -> Unsubscribe this node from the P2P network and exit process
            [{block}, ...] -> A JSON parsable string implies that a blockchain
                              candidate is sent our way

        :param data: str
        :return: str
        """
        if data.upper() == 'GET CHAIN':
            return self.blockchain.JSONify()
        if data.upper() == 'SHUTDOWN':
            return 'EXITING'

        try:
            blockchain = Blockchain(json.loads(data))
        except JSONDecodeError:
            return 'INVALID JSON'

        size = blockchain.is_valid(return_size=True)
        if size <= self.blockchain.size:
            return 'BLOCKCHAIN REJECTED'
        else:
            self.blockchain = blockchain
            return 'BLOCKCHAIN ACCEPTED'

    def send(self, port: int, msg: str):
        """
        Send a message to another peer on the given port.

        :param msg: str
        :param port: int
        :return:
        """
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(('localhost', port))

        msg = f'{len(msg):<{HEADER_SIZE}}{msg}'
        self.log(f"Sending msg to '{port}' -> {msg[:100]}")
        client.send(bytes(msg, 'utf-8'))

        # get response
        size = int(str(client.recv(HEADER_SIZE), 'utf-8'))
        response = str(client.recv(size), 'utf-8')
        self.log(f"Receiving response ({size} chars) -> {response[:100]}")
        return response

    def sync_nodes(self):
        """
        Get longest valid chain on the network
        """
        servers = self._open_servers_list()
        for port, address in servers.items():
            response = self.send(int(port), 'GET CHAIN')
            peer_blockchain = Blockchain(response)
            size = peer_blockchain.is_valid(return_size=True)
            if size > self.blockchain.size:
                self.blockchain.set_blockchain(peer_blockchain)

    def subscribe(self):
        # subscribe self as a listening P2P node / connect to network
        with LockedOpen(self.P2P_SERVERS_LIST, 'w') as fd:
            servers = json.load(fd)
            servers[port] = 'localhost'  # everything is on localhost
            fd.write(json.dumps(servers, indent=2))

    def unsubscribe(self):
        # unsubscribe self as a listening P2P node / disconnect from network
        with LockedOpen(self.P2P_SERVERS_LIST, 'w') as fd:
            servers = json.load(fd)
            del servers[port]
            fd.write(json.dumps(servers, indent=2))

    def _open_servers_list(self):
        try:
            with LockedOpen(self.P2P_SERVERS_LIST, 'r') as fd:
                return json.load(fd)
        except FileNotFoundError:
            return []


if __name__ == '__main__':
    # python server.py 1> localhost_port.log 2>&1
    try:
        port = int(sys.argv[1])
    except IndexError:
        print(f"{datetime.datetime.today()} :: Port number argument missing. "
              f"Try 'python server.py 6001'.")
        exit(1)
    except ValueError:
        print(f"{datetime.datetime.today()} :: 'Port' argument is not a valid "
              f"integer. Try 'python server.py 6001'.")
        exit(1)




PADDING = 10

msg = "Welcome to the server!"
msg = f'{len(msg):<{PADDING}}{msg}'
