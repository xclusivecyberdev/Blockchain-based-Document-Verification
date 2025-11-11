# Blockchain-Based Document Verification

This project demonstrates how a lightweight blockchain can be used to preserve the integrity of critical documents. The application lets you submit a document, store its cryptographic hash on a blockchain, and verify later that the document existed at a specific time. A REST API and a web dashboard are provided so that both developers and non-technical users can interact with the ledger.

## Features

- ✅ Minimal proof-of-work blockchain implemented in Python.
- ✅ Document hashing and proof-of-existence guarantees.
- ✅ Timestamp validation to prove a document existed prior to a given moment.
- ✅ REST API for document submission, verification, and blockchain inspection.
- ✅ Web interface for uploading and verifying documents without writing code.
- ✅ Persistent chain state stored on disk for repeatable demonstrations.

## Getting Started

### Prerequisites

- Python 3.10 or newer
- `pip` for dependency management

### Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Running the Application

```bash
flask --app app run
```

The development server listens on `http://127.0.0.1:5000` by default. Visit the root page to access the dashboard, or interact with the REST API using any HTTP client.

## REST API Overview

| Endpoint | Method | Description |
| --- | --- | --- |
| `/api/documents` | `POST` | Submit a document file (`multipart/form-data`) or JSON payload with `content` (base64) or a pre-computed `hash`. Returns the block that recorded the hash. |
| `/api/verify` | `POST` | Verify a document by uploading content or providing a hash. Returns whether the document exists on-chain. |
| `/api/proof` | `POST` | Accepts `{ "hash": "..." }` to check proof of existence without uploading content. |
| `/api/validate-timestamp` | `POST` | Validate `{ "hash": "...", "timestamp": "2024-01-01T00:00:00" }` to confirm the document existed before a timestamp. |
| `/api/chain` | `GET` | Retrieve the full blockchain. |
| `/api/health` | `GET` | Health check and chain validity indicator. |

### Example: Submit a Document Hash

```bash
curl -X POST http://127.0.0.1:5000/api/documents \
  -H "Content-Type: application/json" \
  -d '{"hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"}'
```

### Example: Verify a File

```bash
curl -X POST http://127.0.0.1:5000/api/verify \
  -F "file=@contracts/NDA.pdf"
```

## How It Works

### Core Concepts

1. **Blocks** – Each block contains:
   - An index to preserve ordering
   - The document hash that acts as a unique fingerprint
   - A timestamp representing when the block was mined
   - The previous block hash to link the chain
   - A nonce discovered by the proof-of-work process

2. **Blockchain** – A sequence of blocks where each block references the hash of the previous block. Altering a historic block changes its hash, breaking the chain. This immutability underpins tamper evidence.

3. **Hash Functions** – We use SHA-256 to produce deterministic fingerprints of documents. Even tiny changes in a document result in a completely different hash, making manipulation detectable.

4. **Proof of Existence** – Storing a document hash on-chain proves that the document existed at the time the block was mined without revealing the document itself. Anyone can recompute the hash later and compare.

5. **Timestamp Validation** – Because block timestamps are part of the immutable record, a verifier can confirm that a document was present before a specific moment by comparing timestamps.

### Consensus Mechanism

This demonstration uses a simplified **Proof-of-Work (PoW)** consensus algorithm:

- Miners search for a nonce that causes the block hash to start with a certain number of leading zeros (the difficulty target).
- The computational cost deters malicious actors from rewriting history because they would need to redo the work for all subsequent blocks.

Alternative consensus models used in production systems include:

- **Proof-of-Stake (PoS)** – Validators lock up tokens, and the probability of creating the next block correlates with their stake. This consumes less energy and offers faster finality.
- **Proof-of-Authority (PoA)** – A limited set of trusted validators sign blocks. This is common in permissioned networks where participants are known organizations.

Understanding multiple consensus strategies helps architects choose the best fit for regulated document ecosystems, balancing decentralization, performance, and governance.

### Document Authentication Use Cases

- **Legal Contracts** – Record contract versions to prove terms at signing time.
- **Intellectual Property** – Prove that a design, manuscript, or dataset existed before publication.
- **Compliance & Auditing** – Maintain tamper-evident records of policies, audit trails, or certificates.
- **Academic Credentials** – Universities can hash diplomas so employers verify authenticity without contacting the issuer.
- **Supply Chain Documentation** – Ensure bills of lading or inspection reports remain unaltered across partners.

## Project Structure

```
.
├── app.py                     # Flask application and REST endpoints
├── blockchain_app/
│   ├── __init__.py
│   ├── blockchain.py          # Block, Blockchain, and persistence logic
│   ├── document_service.py    # Hashing, verification, and timestamp helpers
│   └── templates/
│       ├── index.html         # Dashboard for submissions
│       └── result.html        # Result page for user interactions
├── data/
│   └── blockchain.json        # Persisted blockchain state (created after first run)
└── requirements.txt
```

## Development Notes

- The blockchain difficulty is intentionally low so that new blocks are created quickly during demos.
- Document hashes are lowercased before comparison to provide consistent lookups.
- The service persists chain data in `data/blockchain.json`; delete the file to reset the chain.

## Future Enhancements

- Replace the in-process blockchain with a distributed network of peers.
- Integrate digital signatures for authenticated submissions.
- Add role-based access control and audit trails for the web dashboard.

## License

This project is provided for educational purposes. Adapt and extend it to fit your organization’s document integrity requirements.
