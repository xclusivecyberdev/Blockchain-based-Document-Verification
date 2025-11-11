"""Flask application exposing REST and web interfaces for document verification."""

from __future__ import annotations

import base64
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from flask import Flask, jsonify, redirect, render_template, request, url_for

from blockchain_app.document_service import DocumentService

app = Flask(__name__)
service = DocumentService(Path("data/blockchain.json"))


def _load_document_from_request(req: Any) -> bytes:
    """Extract raw document bytes from a multipart/form-data request."""
    if "file" in req.files:
        uploaded_file = req.files["file"]
        return uploaded_file.read()
    raise ValueError("No document content provided in request.")


@app.route("/")
def index() -> str:
    return render_template("index.html", chain=service.chain_state().chain)


@app.route("/upload", methods=["POST"])
def upload_document() -> str:
    file = request.files.get("document")
    if not file:
        return redirect(url_for("index", message="No file uploaded."))

    block = service.add_document(file.read())
    return render_template(
        "result.html",
        success=True,
        document_hash=block.document_hash,
        timestamp=service.format_timestamp(block.timestamp),
        block=block,
        message="Document recorded on the blockchain.",
    )


@app.route("/verify", methods=["POST"])
def verify_document() -> str:
    file = request.files.get("document")
    if not file:
        return redirect(url_for("index", message="No file uploaded for verification."))

    result = service.verify_document(file.read())
    timestamp = service.format_timestamp(result.block.timestamp) if result.block else None
    return render_template(
        "result.html",
        success=result.exists,
        document_hash=result.block.document_hash if result.block else None,
        timestamp=timestamp,
        block=result.block,
        message=result.message,
    )


def _decode_content(payload: Dict[str, Any]) -> bytes:
    try:
        return base64.b64decode(payload["content"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("content must be provided and base64 encoded") from exc


@app.route("/api/documents", methods=["POST"])
def api_add_document():
    if request.is_json:
        payload = request.get_json()
        if "hash" in payload:
            hash_value = payload["hash"].lower()
            existing = service.chain_state().find_document(hash_value)
            if existing:
                return (
                    jsonify(
                        {
                            "message": "Hash already recorded.",
                            "block": {
                                "index": existing.index,
                                "timestamp": existing.timestamp,
                                "document_hash": existing.document_hash,
                            },
                        }
                    ),
                    200,
                )
            block = service.add_hash(hash_value)
            return (
                jsonify(
                    {
                        "message": "Hash recorded on the blockchain.",
                        "block": {
                            "index": block.index,
                            "timestamp": block.timestamp,
                            "document_hash": block.document_hash,
                        },
                    }
                ),
                201,
            )
        if "content" in payload:
            try:
                contents = _decode_content(payload)
            except ValueError as exc:
                return jsonify({"error": str(exc)}), 400
        else:
            return jsonify({"error": "JSON payload must include hash or content."}), 400
    else:
        try:
            contents = _load_document_from_request(request)
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400

    block = service.add_document(contents)
    return (
        jsonify(
            {
                "message": "Document recorded on the blockchain.",
                "block": {
                    "index": block.index,
                    "timestamp": block.timestamp,
                    "document_hash": block.document_hash,
                },
            }
        ),
        201,
    )


@app.route("/api/verify", methods=["POST"])
def api_verify_document():
    if request.is_json:
        payload = request.get_json()
        if "hash" in payload:
            result = service.proof_of_existence(payload["hash"])
        elif "content" in payload:
            try:
                contents = _decode_content(payload)
            except ValueError as exc:
                return jsonify({"error": str(exc)}), 400
            result = service.verify_document(contents)
        else:
            return jsonify({"error": "JSON payload must include hash or content."}), 400
    else:
        try:
            contents = _load_document_from_request(request)
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400
        result = service.verify_document(contents)

    response: Dict[str, Any] = {
        "exists": result.exists,
        "message": result.message,
    }
    if result.block:
        response["block"] = {
            "index": result.block.index,
            "timestamp": result.block.timestamp,
            "document_hash": result.block.document_hash,
        }
    return jsonify(response)


@app.route("/api/proof", methods=["POST"])
def api_proof_of_existence():
    if not request.is_json:
        return jsonify({"error": "JSON payload required."}), 400
    payload = request.get_json()
    document_hash = payload.get("hash")
    if not document_hash:
        return jsonify({"error": "hash field is required."}), 400

    result = service.proof_of_existence(document_hash)
    response: Dict[str, Any] = {
        "exists": result.exists,
        "message": result.message,
    }
    if result.block:
        response["block"] = {
            "index": result.block.index,
            "timestamp": result.block.timestamp,
            "document_hash": result.block.document_hash,
        }
    return jsonify(response)


@app.route("/api/validate-timestamp", methods=["POST"])
def api_validate_timestamp():
    if not request.is_json:
        return jsonify({"error": "JSON payload required."}), 400
    payload = request.get_json()
    document_hash = payload.get("hash")
    timestamp_str = payload.get("timestamp")
    if not document_hash or not timestamp_str:
        return jsonify({"error": "hash and timestamp fields are required."}), 400

    try:
        timestamp = datetime.fromisoformat(timestamp_str)
    except ValueError:
        return jsonify({"error": "timestamp must be ISO 8601 formatted."}), 400

    result = service.validate_timestamp(document_hash, timestamp)
    response: Dict[str, Any] = {
        "valid": result.exists,
        "message": result.message,
    }
    if result.block:
        response["block"] = {
            "index": result.block.index,
            "timestamp": result.block.timestamp,
            "document_hash": result.block.document_hash,
        }
    return jsonify(response)


@app.route("/api/chain")
def api_chain():
    chain = service.chain_state()
    return jsonify(chain.to_dict())


@app.route("/api/health")
def api_health():
    return jsonify({"status": "ok", "valid_chain": service.chain_state().is_valid()})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
