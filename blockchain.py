import json
from collections import deque
from datetime import datetime, timezone
from typing import List, Union

from util import hash, timestamp_is_valid, proof_of_work_is_valid, block_to_dict


class Block(object):
    """
    A block in the blockchain implemented with slots for it's faster access/set
    time and reduced memory usage. Critical for a blockchain with 1_000_000+
    blocks.

    `timestamp`, `prev_hash` and `data` cannot be modified once set in a block.
    """

    __slots__ = ('index', 'timestamp', 'nonce', 'prev_hash', 'hash', 'data',)

    def __init__(self, prev_hash: str, data: dict, timestamp: str = None):
        self.index = self.nonce = 0
        self.timestamp = self._timestamp_or_default(timestamp)
        self.prev_hash = prev_hash
        self.data = data
        self.hash = hash(self)

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
                raise RuntimeError(f"Key '{key}' has already been set and "
                                   f"cannot be modified.")
        super(Block, self).__setattr__(key, value)

    def __repr__(self):
        # used to serialise block for hashing
        return f"timestamp:'{self.timestamp}'," \
               f"nonce:'{self.nonce}'," \
               f"previous hash:'{self.prev_hash}'," \
               f"data:'{json.dumps(self.data, sort_keys=True)}'"

    def __str__(self):
        # used to analyse block
        return f'index: {self.index}\n' \
               f'timestamp: {self.timestamp}\n' \
               f'nonce: {self.nonce}\n' \
               f'previous hash: {self.prev_hash}\n' \
               f'current hash: {self.hash}\n' \
               f'data: {json.dumps(self.data, sort_keys=True)}'

    def _timestamp_or_default(self, timestamp: str):
        if timestamp is None:
            return datetime.now(timezone.utc).strftime("%d/%m/%Y, %H:%M:%S")
        return timestamp


class Blockchain(object):
    """
    A python based blockchain implementation.
    """

    def __init__(self, blockchain: Union[List[dict], str] = None):
        """
        Initialise a blockchain with a single genesis block or build one from
        a list of
        :param blockchain:
        """
        self.chain = deque()  # optimized for data accesses near its endpoints
        self.size = 0
        if blockchain is not None:
            self.set_blockchain(blockchain)
        else:
            self.add_mined_block(self.genesis_block)

    @property
    def genesis_block(self):
        if not hasattr(self, '_genesis_block'):
            genesis_block = Block(prev_hash='0000', data={})
            setattr(self, '_genesis_block', genesis_block)
        return getattr(self, '_genesis_block')

    def add_mined_block(self, block: Block):
        # add a valid/mined block to the chain
        block.index = self.size
        self.size += 1
        self.chain.append(block)

    def is_valid(self, return_size=False):
        """
        if `return_size` flag is set, method will return the size of the chain
        if valid or -1 if invalid. Otherwise, simply returns `true` or `false`
        if the chain is valid.

        :param return_size: bool
        :return: int
        """
        size = self._is_valid()
        if return_size:
            return size
        if size <= 0:
            return False
        else:
            return True

    def JSONify(self):
        return json.dumps([block_to_dict(block) for block in self.chain])

    def mine_block(self, block: Block):
        # mine a fresh block
        for nonce in range(2**32):
            block.nonce = nonce
            if proof_of_work_is_valid(block):
                return block

    def mine_data(self, data: dict):
        # mine for a valid block using the given data and add it to the chain
        prev_block = self.chain[-1]
        mined_block = self.mine_block(Block(prev_hash=prev_block.hash, data=data))
        return mined_block

    def set_blockchain(self, blockchain):
        # initialise self with the given blockchain
        if type(blockchain) == str:
            blockchain = json.loads(blockchain)
        for block in blockchain:
            b = Block(prev_hash=block['prev_hash'], data=block['data'],
                      timestamp=block['timestamp'])
            b.nonce = block['nonce']
            b.hash = block['hash']
            self.add_mined_block(b)

    def _is_valid(self):
        """
        return the size of the chain if valid or -1 if invalid.
        """
        prev_block = None
        for block in self.chain:
            if prev_block is None:
                # first block -- check genesis block
                if hash(block) != hash(self.genesis_block):
                    return -1
            else:
                if any([
                    prev_block.hash != block.prev_hash,
                    block.hash != hash(block),
                    not timestamp_is_valid(block.timestamp),
                    not proof_of_work_is_valid(block),
                ]):
                    return -1
            prev_block = block
        return len(self.chain)
