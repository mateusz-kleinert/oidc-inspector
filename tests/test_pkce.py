"""Tests for PKCE parameter generation (RFC 7636)."""

import base64
import hashlib

from oidc_inspector.pkce import (
    generate_code_challenge,
    generate_code_verifier,
    generate_nonce,
    generate_state,
)


class TestCodeVerifier:
    def test_is_string(self):
        assert isinstance(generate_code_verifier(), str)

    def test_length_within_rfc_bounds(self):
        # RFC 7636 §4.1: verifier must be 43–128 characters
        v = generate_code_verifier()
        assert 43 <= len(v) <= 128

    def test_only_unreserved_chars(self):
        # base64url uses A-Z a-z 0-9 - _
        verifier = generate_code_verifier()
        allowed = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_")
        assert set(verifier) <= allowed

    def test_unique_on_each_call(self):
        assert generate_code_verifier() != generate_code_verifier()


class TestCodeChallenge:
    def test_matches_s256_spec(self):
        verifier = "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk"
        digest = hashlib.sha256(verifier.encode("ascii")).digest()
        expected = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
        assert generate_code_challenge(verifier) == expected

    def test_no_padding(self):
        challenge = generate_code_challenge(generate_code_verifier())
        assert "=" not in challenge

    def test_deterministic(self):
        v = generate_code_verifier()
        assert generate_code_challenge(v) == generate_code_challenge(v)


class TestStateAndNonce:
    def test_state_unique(self):
        assert generate_state() != generate_state()

    def test_nonce_unique(self):
        assert generate_nonce() != generate_nonce()

    def test_state_is_url_safe(self):
        state = generate_state()
        assert " " not in state and "+" not in state

    def test_nonce_minimum_length(self):
        # secrets.token_urlsafe(32) produces ~43 chars
        assert len(generate_nonce()) >= 40
