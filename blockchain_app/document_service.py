"""Document hashing and verification utilities."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
from pathlib import Path
from typing import Optional

from .blockchain import Block, Blockchain, BlockchainStorage


@dataclass
class VerificationResult:
    exists: bool
    block: Optional[Block]
    message: str


class DocumentService:
    """High level service that coordinates blockchain persistence and verification."""

    def __init__(self, storage_path: Path) -> None:
        self.storage = BlockchainStorage(storage_path)
        self.blockchain = self.storage.load()

    @staticmethod
    def hash_document(contents: bytes) -> str:
        return sha256(contents).hexdigest()

    def add_document(self, contents: bytes) -> Block:
        document_hash = self.hash_document(contents)
        block = self.blockchain.add_document_hash(document_hash)
        self.storage.save(self.blockchain)
        return block

    def add_hash(self, document_hash: str) -> Block:
        block = self.blockchain.add_document_hash(document_hash)
        self.storage.save(self.blockchain)
        return block

    def verify_document(self, contents: bytes) -> VerificationResult:
        document_hash = self.hash_document(contents)
        block = self.blockchain.find_document(document_hash)
        if block:
            message = "Document exists on the blockchain."
        else:
            message = "Document not found in the blockchain."
        return VerificationResult(exists=block is not None, block=block, message=message)

    def proof_of_existence(self, document_hash: str) -> VerificationResult:
        block = self.blockchain.find_document(document_hash)
        if block:
            message = "Hash recorded on the blockchain."
        else:
            message = "Hash not recorded on the blockchain."
        return VerificationResult(exists=block is not None, block=block, message=message)

    @staticmethod
    def format_timestamp(timestamp: float) -> str:
        return datetime.fromtimestamp(timestamp).isoformat()

    def validate_timestamp(self, document_hash: str, latest_valid_timestamp: datetime) -> VerificationResult:
        block = self.blockchain.find_document(document_hash)
        if not block:
            return VerificationResult(False, None, "Hash not recorded on the blockchain.")

        block_time = datetime.fromtimestamp(block.timestamp)
        if block_time <= latest_valid_timestamp:
            message = "Document existed prior to the provided timestamp."
            return VerificationResult(True, block, message)

        message = "Document was recorded after the provided timestamp."
        return VerificationResult(False, block, message)

    def chain_state(self) -> Blockchain:
        return self.blockchain
