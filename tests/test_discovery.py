"""Tests for OIDC discovery document fetching."""

import pytest
import httpx
from pytest_httpx import HTTPXMock

from oidc_inspector.discovery import fetch_oidc_discovery


ISSUER = "https://idp.example.com/realms/test"
DISCOVERY_URL = f"{ISSUER}/.well-known/openid-configuration"


class TestFetchOidcDiscovery:
    def test_fetches_and_returns_json(self, httpx_mock: HTTPXMock, discovery_document):
        httpx_mock.add_response(url=DISCOVERY_URL, json=discovery_document)
        result = fetch_oidc_discovery(ISSUER)
        assert result["issuer"] == ISSUER
        assert "authorization_endpoint" in result
        assert "token_endpoint" in result

    def test_strips_trailing_slash_from_issuer(self, httpx_mock: HTTPXMock, discovery_document):
        httpx_mock.add_response(url=DISCOVERY_URL, json=discovery_document)
        result = fetch_oidc_discovery(ISSUER + "/")
        assert result["issuer"] == ISSUER

    def test_raises_on_404(self, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=DISCOVERY_URL, status_code=404)
        with pytest.raises(httpx.HTTPStatusError):
            fetch_oidc_discovery(ISSUER)

    def test_raises_on_server_error(self, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=DISCOVERY_URL, status_code=500)
        with pytest.raises(httpx.HTTPStatusError):
            fetch_oidc_discovery(ISSUER)
