"""Tests for token endpoint interactions."""

import base64
import json

import httpx
import pytest
from pytest_httpx import HTTPXMock

from oidc_inspector.token_client import exchange_code_for_tokens, get_client_credentials_token

TOKEN_ENDPOINT = "https://idp.example.com/realms/test/protocol/openid-connect/token"


def _make_jwt(payload: dict) -> str:
    header = base64.urlsafe_b64encode(b'{"alg":"RS256","typ":"JWT"}').rstrip(b"=").decode()
    body = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b"=").decode()
    return f"{header}.{body}.fakesig"


@pytest.fixture()
def token_response():
    return {
        "access_token": _make_jwt({"sub": "user1", "iat": 1700000000, "exp": 1700003600}),
        "id_token": _make_jwt({"sub": "user1", "email": "user@example.com", "iat": 1700000000, "exp": 1700003600}),
        "token_type": "Bearer",
        "expires_in": 3600,
        "scope": "openid profile email",
    }


class TestExchangeCodeForTokens:
    def test_returns_tokens_and_params(self, httpx_mock: HTTPXMock, token_response):
        httpx_mock.add_response(url=TOKEN_ENDPOINT, json=token_response)
        tokens, params = exchange_code_for_tokens(
            token_endpoint=TOKEN_ENDPOINT,
            code="auth-code-xyz",
            redirect_uri="http://localhost:8080/callback",
            client_id="test-client",
        )
        assert "access_token" in tokens
        assert params["grant_type"] == "authorization_code"
        assert params["code"] == "auth-code-xyz"

    def test_includes_client_secret_when_provided(self, httpx_mock: HTTPXMock, token_response):
        httpx_mock.add_response(url=TOKEN_ENDPOINT, json=token_response)
        _, params = exchange_code_for_tokens(
            token_endpoint=TOKEN_ENDPOINT,
            code="code",
            redirect_uri="http://localhost:8080/callback",
            client_id="client",
            client_secret="secret",
        )
        assert params["client_secret"] == "secret"

    def test_includes_code_verifier_for_pkce(self, httpx_mock: HTTPXMock, token_response):
        httpx_mock.add_response(url=TOKEN_ENDPOINT, json=token_response)
        _, params = exchange_code_for_tokens(
            token_endpoint=TOKEN_ENDPOINT,
            code="code",
            redirect_uri="http://localhost:8080/callback",
            client_id="client",
            code_verifier="my-verifier",
        )
        assert params["code_verifier"] == "my-verifier"

    def test_omits_secret_and_verifier_when_not_provided(self, httpx_mock: HTTPXMock, token_response):
        httpx_mock.add_response(url=TOKEN_ENDPOINT, json=token_response)
        _, params = exchange_code_for_tokens(
            token_endpoint=TOKEN_ENDPOINT,
            code="code",
            redirect_uri="http://localhost:8080/callback",
            client_id="client",
        )
        assert "client_secret" not in params
        assert "code_verifier" not in params

    def test_raises_on_error_response(self, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=TOKEN_ENDPOINT, status_code=400, json={"error": "invalid_grant"})
        with pytest.raises(httpx.HTTPStatusError):
            exchange_code_for_tokens(
                token_endpoint=TOKEN_ENDPOINT,
                code="expired-code",
                redirect_uri="http://localhost:8080/callback",
                client_id="client",
            )


class TestGetClientCredentialsToken:
    def test_returns_tokens_and_params(self, httpx_mock: HTTPXMock, token_response):
        httpx_mock.add_response(url=TOKEN_ENDPOINT, json=token_response)
        tokens, params = get_client_credentials_token(
            token_endpoint=TOKEN_ENDPOINT,
            client_id="client",
            client_secret="secret",
        )
        assert params["grant_type"] == "client_credentials"
        assert params["client_id"] == "client"
        assert params["client_secret"] == "secret"
        assert "access_token" in tokens

    def test_raises_on_unauthorized(self, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=TOKEN_ENDPOINT, status_code=401, json={"error": "unauthorized_client"})
        with pytest.raises(httpx.HTTPStatusError):
            get_client_credentials_token(
                token_endpoint=TOKEN_ENDPOINT,
                client_id="bad-client",
                client_secret="wrong",
            )
