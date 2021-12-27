from collections import deque
from datetime import datetime, timezone
import hashlib
import json


class Block(object):
    """
    A block in the blockchain implemented with slots for it's faster access/set
    time and reduced memory usage. Critical for a blockchain with 1_000_000+
    blocks.

    `timestamp`, `prev_hash` and `data` cannot be modified once set in a block.
    """

    __slots__ = ('index', 'timestamp', 'nonce', 'prev_hash', 'hash', 'data',)

    def __init__(self, prev_hash: str, data: dict):
        self.index = self.nonce = 0
        self.timestamp = datetime.now(timezone.utc).strftime("%d/%m/%Y, %H:%M:%S")
        self.prev_hash = prev_hash
        self.data = data
        self.hash = hashlib.sha256(repr(self).encode()).hexdigest()

    def __setattr__(self, key, value):
        """ Prevent the modification of key components of a block once set """
        if hasattr(self, key):
            # 'hasattr' will call getattr(object, name) and see whether it
            # raises an AttributeError or not. Unset slots will raise an
            # AttributeError if accessed before assignment. And so, if hasattr
            # returns true; the attribute has been set.
            if key in ['timestamp', 'prev_hash', 'data']:
                # key has already been set and modification is not allowed
                # once set
                raise RuntimeError(
                    f"Key '{key}' has already been set and cannot"
                    f" be modified.")
        super(Block, self).__setattr__(key, value)

    def __repr__(self):
        # used to serialise block for hashing
        return f'timestamp: {self.timestamp}\n' \
               f'nonce: {self.nonce}\n' \
               f'previous hash: {self.prev_hash}\n' \
               f'data: {json.dumps(self.data, sort_keys=True)}'

    def __str__(self):
        # used to analyse block
        return f'index: {self.index}\n' \
               f'timestamp: {self.timestamp}\n' \
               f'nonce: {self.nonce}\n' \
               f'previous hash: {self.prev_hash}\n' \
               f'current hash: {self.hash}\n' \
               f'data: {json.dumps(self.data, sort_keys=True)}'


class Blockchain(object):
    """
    A python based blockchain implementation.
    """

    def __init__(self):
        self.chain = deque()  # optimized for data accesses near its endpoints
        self.size = 0
        self._insert_into_chain(self.genesis_block)

    def add_block(self, data):
        prev_block = self.chain[-1]
        block = self.mine(Block(prev_hash=prev_block.hash, data=data))
        self._insert_into_chain(block)

    @property
    def genesis_block(self):
        if not hasattr(self, '_genesis_block'):
            genesis_block = Block(prev_hash='0000', data={})
            setattr(self, '_genesis_block', genesis_block)
        return getattr(self, '_genesis_block')

    def hash(self, block: Block):
        """ Get the hash value of a given block """
        return hashlib.sha256(repr(block).encode()).hexdigest()

    def is_valid(self):
        """ is the entire chain valid """
        prev_block = None
        for block in self.chain:
            if prev_block is None:
                # first block -- check genesis block
                if self.hash(block) != self.hash(self.genesis_block):
                    return False
            else:
                if any([
                    prev_block.hash != block.prev_hash,
                    block.hash != self.hash(block),
                    not self._timestamp_is_valid(block.timestamp),
                    not self._proof_of_work_is_valid(prev_block),
                ]):
                    return False
            prev_block = block
        return True

    def mine(self, block: Block):
        # mine a fresh block
        return block

    def _timestamp_is_valid(self, timestamp: str):
        try:
            datetime.strptime(timestamp, "%d/%m/%Y, %H:%M:%S")
            return True
        except ValueError:
            return False

    def _insert_into_chain(self, block: Block):
        block.index = self.size
        self.size += 1
        self.chain.append(block)

    def _proof_of_work_is_valid(self, block: Block):
        # assert block passed challenge
        if self.hash(block)[:4] == '0000':
            return True
        return False

    def proof_of_work(self, previous_proof):
        new_proof = 1
        check_proof = False
        while check_proof is False:
            hash_operation = hashlib.sha256(
                str(new_proof ** 2 - previous_proof ** 2).encode()).hexdigest()
            if hash_operation[:4] == '0000':
                check_proof = True
            else:
                new_proof += 1
        return new_proof
