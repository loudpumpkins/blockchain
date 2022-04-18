import io
import msvcrt
import os
import socket
import hashlib
from datetime import datetime, timezone
from server import HEADER_SIZE


def block_to_dict(block):
    # convert block into a dictionary
    # unset values are set to 'None'
    slots = ('index', 'timestamp', 'nonce', 'prev_hash', 'hash', 'data', )
    return {s: getattr(block, s) if hasattr(block, s) else None for s in slots}


def hash(block):
    """ Get the hash value of a given block """
    return hashlib.sha256(repr(block).encode()).hexdigest()


def proof_of_work_is_valid(block):
    # assert block passed challenge
    if hash(block)[:4] == '0000':
        return True
    return False


def send_message_to_node(port, msg):
    # connect to a peer at a given port num
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(('localhost', int(port)))

    # send message
    msg = f'{len(msg):<{HEADER_SIZE}}{msg}'
    client.send(bytes(msg, 'utf-8'))

    # get response
    size = int(str(client.recv(HEADER_SIZE), 'utf-8'))
    response = str(client.recv(size), 'utf-8')
    return response


def get_blockchain_from_node(port):
    response = send_message_to_node(port, 'GET CHAIN')
    return Blockchain(response)


def timestamp_is_valid(timestamp: str):
    try:
        datetime.strptime(timestamp, "%d/%m/%Y, %H:%M:%S")
        return True
    except ValueError:
        return False


def valid_post_data(post_data):
    """
    loosely validate block data

    Valid post data =
    [
        {
            "transaction": {
                "from": "alice",    -+
                "to": "bob",         |-> mandatory fields
                "amount": 113       -+
            }
        },
        [...]
    ]
    :param post_data:
    :return:
    """
    for data in post_data:
        if 'transaction' not in data:
            return False
        tx = data['transaction']
        req_fields = ['from', 'to', 'amount']
        if any([f not in tx or not tx[f] for f in req_fields]):
            # req field missing or value is falsy (None, zero, blank)
            return False
        return True


class LockedOpen:
    """
    Context manager class for ensuring that all file operations are atomic.
    Windows OS will not enforce 'locked file'; all processes that try to write
    to a locked file must check to see if another process requested a lock on
    this file.

    Untested on linux; will likely fail.
    """
    def __init__(self, path, mode):
        # Open the file and acquire a lock on the file before operating
        self.file = open(path, mode)
        self.file.seek(0, io.SEEK_SET)

        # Lock the opened file
        msvcrt.locking(
            self.file.fileno(),
            msvcrt.LK_LOCK,
            os.path.getsize(os.path.realpath(self.file.name))
        )

    def __enter__(self, *args, **kwargs):
        return self.file

    def __exit__(self, exc_type=None, exc_value=None, traceback=None):

        # Flush to make sure all buffered contents are written to file.
        # self.file.flush()
        # os.fsync(self.file.fileno())

        # Release the lock on the file.
        msvcrt.locking(
            self.file.fileno(),
            msvcrt.LK_UNLCK,
            os.path.getsize(os.path.realpath(self.file.name))
        )

        self.file.close()
        if exc_type is not None:
            return False
        else:
            return True