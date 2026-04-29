"""Fetch and parse the OIDC Discovery Document (RFC 8414 / OpenID Connect Discovery 1.0)."""

from typing import Any

import httpx


def fetch_oidc_discovery(issuer: str, verify_ssl: bool = True, timeout: int = 30) -> dict[str, Any]:
    """GET /.well-known/openid-configuration and return the parsed JSON document.

    Spec: https://openid.net/specs/openid-connect-discovery-1_0.html#ProviderConfig
    """
    url = f"{issuer.rstrip('/')}/.well-known/openid-configuration"
    with httpx.Client(verify=verify_ssl, timeout=timeout) as client:
        response = client.get(url)
        response.raise_for_status()
        return response.json()
