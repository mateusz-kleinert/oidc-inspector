"""Token endpoint interactions (RFC 6749)."""

from typing import Any, Optional

import httpx


def exchange_code_for_tokens(
    token_endpoint: str,
    code: str,
    redirect_uri: str,
    client_id: str,
    client_secret: Optional[str] = None,
    code_verifier: Optional[str] = None,
    verify_ssl: bool = True,
    timeout: int = 30,
) -> tuple[dict[str, Any], dict[str, str]]:
    """Exchange an authorization code for tokens (RFC 6749 §4.1.3).

    Returns ``(token_response, request_params)`` so callers can display what was sent.
    """
    params: dict[str, str] = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "client_id": client_id,
    }
    if client_secret:
        params["client_secret"] = client_secret
    if code_verifier:
        params["code_verifier"] = code_verifier

    with httpx.Client(verify=verify_ssl, timeout=timeout) as client:
        response = client.post(token_endpoint, data=params)
        response.raise_for_status()
        return response.json(), params


def get_client_credentials_token(
    token_endpoint: str,
    client_id: str,
    client_secret: str,
    scope: str = "openid",
    verify_ssl: bool = True,
    timeout: int = 30,
) -> tuple[dict[str, Any], dict[str, str]]:
    """Obtain a token via the Client Credentials grant (RFC 6749 §4.4).

    Returns ``(token_response, request_params)``.
    """
    params: dict[str, str] = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": scope,
    }

    with httpx.Client(verify=verify_ssl, timeout=timeout) as client:
        response = client.post(token_endpoint, data=params)
        response.raise_for_status()
        return response.json(), params
