"""Tests for JWT decoding utilities."""

import base64
import json

import pytest

from oidc_inspector.jwt_decoder import decode_jwt, is_jwt


def _encode_b64(data: dict) -> str:
    return base64.urlsafe_b64encode(json.dumps(data).encode()).rstrip(b"=").decode()


def _make_jwt(header: dict, payload: dict, signature: str = "fakesig") -> str:
    return f"{_encode_b64(header)}.{_encode_b64(payload)}.{signature}"


class TestIsJwt:
    def test_three_part_token_is_jwt(self):
        assert is_jwt("a.b.c")

    def test_opaque_token_is_not_jwt(self):
        assert not is_jwt("someopaquetoken")
        assert not is_jwt("a.b")
        assert not is_jwt("a.b.c.d")


class TestDecodeJwt:
    def test_decodes_header(self, sample_jwt_payload):
        header = {"alg": "RS256", "typ": "JWT", "kid": "key-1"}
        token = _make_jwt(header, sample_jwt_payload)
        result = decode_jwt(token)
        assert result["header"] == header

    def test_decodes_payload(self, sample_jwt_payload):
        token = _make_jwt({"alg": "RS256"}, sample_jwt_payload)
        result = decode_jwt(token)
        assert result["payload"]["sub"] == sample_jwt_payload["sub"]
        assert result["payload"]["email"] == sample_jwt_payload["email"]

    def test_enriches_iat_timestamp(self, sample_jwt_payload):
        token = _make_jwt({"alg": "RS256"}, sample_jwt_payload)
        result = decode_jwt(token)
        assert "iat_human" in result["payload"]
        assert "2023" in result["payload"]["iat_human"]  # 1700000000 → 2023

    def test_enriches_exp_timestamp(self, sample_jwt_payload):
        token = _make_jwt({"alg": "RS256"}, sample_jwt_payload)
        result = decode_jwt(token)
        assert "exp_human" in result["payload"]

    def test_truncates_signature(self):
        token = _make_jwt({"alg": "RS256"}, {"sub": "user"}, "a" * 100)
        result = decode_jwt(token)
        assert "…" in result["signature_truncated"]
        assert len(result["signature_truncated"]) < 100

    def test_short_signature_not_truncated(self):
        token = _make_jwt({"alg": "RS256"}, {"sub": "user"}, "abc")
        result = decode_jwt(token)
        assert result["signature_truncated"] == "abc"

    def test_invalid_token_returns_error(self):
        result = decode_jwt("not.a.valid.jwt.at.all")
        assert "error" in result

    def test_raw_preserved(self, sample_jwt_payload):
        token = _make_jwt({"alg": "RS256"}, sample_jwt_payload)
        result = decode_jwt(token)
        assert result["raw"] == token
