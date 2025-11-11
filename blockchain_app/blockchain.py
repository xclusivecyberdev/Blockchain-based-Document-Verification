"""Core blockchain data structures and consensus logic for document verification."""
from __future__ import annotations

from dataclasses import dataclass, asdict
from hashlib import sha256
from pathlib import Path
from time import time
from typing import Dict, List, Optional
import json


@dataclass
class Block:
    """Represents a single block in the blockchain."""

    index: int
    timestamp: float
    document_hash: str
    previous_hash: str
    nonce: int

    def compute_hash(self) -> str:
        """Create a deterministic hash for the block using SHA-256."""
        block_string = json.dumps(asdict(self), sort_keys=True)
        return sha256(block_string.encode("utf-8")).hexdigest()


class Blockchain:
    """Simple proof-of-work blockchain for document integrity."""

    difficulty: int
    difficulty_prefix: str

    def __init__(self, difficulty: int = 3) -> None:
        if difficulty < 1:
            raise ValueError("difficulty must be positive")
        self.difficulty = difficulty
        self.difficulty_prefix = "0" * difficulty
        self.chain: List[Block] = []
        self._create_genesis_block()

    def _create_genesis_block(self) -> None:
        """Initialize chain with a genesis block."""
        genesis_block = Block(
            index=0,
            timestamp=time(),
            document_hash="GENESIS",
            previous_hash="0" * 64,
            nonce=0,
        )
        # Force the genesis block to satisfy the hash requirement
        genesis_block.nonce = self._proof_of_work(genesis_block)
        self.chain.append(genesis_block)

    @property
    def last_block(self) -> Block:
        return self.chain[-1]

    def _proof_of_work(self, block: Block) -> int:
        """Perform proof-of-work by finding a nonce that satisfies difficulty."""
        nonce = 0
        while True:
            block.nonce = nonce
            computed_hash = block.compute_hash()
            if computed_hash.startswith(self.difficulty_prefix):
                return nonce
            nonce += 1

    def add_document_hash(self, document_hash: str) -> Block:
        """Add a new block containing the provided document hash."""
        document_hash = document_hash.lower()
        new_block = Block(
            index=len(self.chain),
            timestamp=time(),
            document_hash=document_hash,
            previous_hash=self.last_block.compute_hash(),
            nonce=0,
        )
        new_block.nonce = self._proof_of_work(new_block)
        self.chain.append(new_block)
        return new_block

    def is_valid(self) -> bool:
        """Validate the entire blockchain."""
        for index in range(1, len(self.chain)):
            current = self.chain[index]
            previous = self.chain[index - 1]

            if current.previous_hash != previous.compute_hash():
                return False

            if not current.compute_hash().startswith(self.difficulty_prefix):
                return False

        return True

    def find_document(self, document_hash: str) -> Optional[Block]:
        """Return the block containing the document hash if it exists."""
        normalized = document_hash.lower()
        for block in self.chain:
            if block.document_hash == normalized:
                return block
        return None

    def to_dict(self) -> Dict[str, List[Dict[str, str]]]:
        return {
            "difficulty": self.difficulty,
            "chain": [asdict(block) for block in self.chain],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, List[Dict[str, str]]]) -> "Blockchain":
        chain_data = data.get("chain", [])
        if not chain_data:
            return cls(difficulty=data.get("difficulty", 3))

        # Instantiate without auto-creating the genesis block
        blockchain = cls.__new__(cls)  # type: ignore[misc]
        blockchain.difficulty = data.get("difficulty", 3)
        blockchain.difficulty_prefix = "0" * blockchain.difficulty
        blockchain.chain = []
        for block_data in chain_data:
            block = Block(**block_data)
            blockchain.chain.append(block)
        if not blockchain.is_valid():
            raise ValueError("Loaded blockchain data is invalid")
        return blockchain


class BlockchainStorage:
    """Persist blockchain data to the local filesystem."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def save(self, blockchain: Blockchain) -> None:
        self.path.write_text(json.dumps(blockchain.to_dict(), indent=2))

    def load(self) -> Blockchain:
        if not self.path.exists():
            return Blockchain()
        data = json.loads(self.path.read_text())
        return Blockchain.from_dict(data)
