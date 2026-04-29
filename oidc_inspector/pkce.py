"""PKCE (Proof Key for Code Exchange) helpers — RFC 7636."""

import base64
import hashlib
import os
import secrets


def generate_code_verifier(byte_length: int = 64) -> str:
    """Generate a cryptographically random code_verifier (43–128 chars per RFC 7636 §4.1)."""
    return base64.urlsafe_b64encode(os.urandom(byte_length)).rstrip(b"=").decode("ascii")


def generate_code_challenge(verifier: str) -> str:
    """Derive the S256 code_challenge from a code_verifier (RFC 7636 §4.2)."""
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")


def generate_state() -> str:
    """Generate a random opaque state value for CSRF protection (RFC 6749 §10.12)."""
    return secrets.token_urlsafe(32)


def generate_nonce() -> str:
    """Generate a random nonce for replay-attack mitigation (OpenID Connect Core §3.1.2.1)."""
    return secrets.token_urlsafe(32)
