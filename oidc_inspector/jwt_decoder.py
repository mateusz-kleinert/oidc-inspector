"""JWT decoding utilities.

Decodes tokens for display purposes only — signature verification is not performed
by default. Use ``verify_jwt`` when JWKS-based verification is needed.
"""

import base64
import json
from datetime import datetime, timezone
from typing import Any, Optional

import httpx


def _b64_decode(segment: str) -> bytes:
    """Decode a base64url segment, adding padding as needed."""
    padding = 4 - len(segment) % 4
    if padding != 4:
        segment += "=" * padding
    return base64.urlsafe_b64decode(segment)


def is_jwt(token: str) -> bool:
    """Return True if *token* looks like a three-part dot-separated JWT."""
    return token.count(".") == 2


def decode_jwt(token: str) -> dict[str, Any]:
    """Split and base64-decode the header and payload of a JWT without verifying the signature.

    Returns a dict with keys ``header``, ``payload``, ``signature_truncated``, and ``raw``.
    """
    parts = token.split(".")
    if len(parts) != 3:
        return {"error": "Not a valid JWT — expected exactly 3 dot-separated parts", "raw": token}

    header_b64, payload_b64, sig_b64 = parts

    try:
        header: Any = json.loads(_b64_decode(header_b64))
    except Exception as exc:
        header = {"decode_error": str(exc), "raw_b64": header_b64}

    try:
        payload: Any = json.loads(_b64_decode(payload_b64))
        payload = _enrich_timestamps(payload)
    except Exception as exc:
        payload = {"decode_error": str(exc), "raw_b64": payload_b64}

    return {
        "header": header,
        "payload": payload,
        "signature_truncated": sig_b64[:24] + "…" if len(sig_b64) > 24 else sig_b64,
        "raw": token,
    }


def _enrich_timestamps(payload: dict[str, Any]) -> dict[str, Any]:
    """Add human-readable ISO strings next to numeric UNIX timestamps."""
    enriched = dict(payload)
    for claim in ("iat", "exp", "nbf", "auth_time"):
        if claim in enriched and isinstance(enriched[claim], int):
            dt = datetime.fromtimestamp(enriched[claim], tz=timezone.utc)
            enriched[f"{claim}_human"] = dt.isoformat()
    return enriched


def fetch_jwks(jwks_uri: str, verify_ssl: bool = True, timeout: int = 30) -> dict[str, Any]:
    """Fetch the JSON Web Key Set from *jwks_uri*.

    Spec: https://www.rfc-editor.org/rfc/rfc7517
    """
    with httpx.Client(verify=verify_ssl, timeout=timeout) as client:
        response = client.get(jwks_uri)
        response.raise_for_status()
        return response.json()
