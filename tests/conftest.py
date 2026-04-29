"""Shared pytest fixtures."""

import pytest


ISSUER = "https://idp.example.com/realms/test"
CLIENT_ID = "test-client"
CLIENT_SECRET = "test-secret"


@pytest.fixture()
def discovery_document():
    return {
        "issuer": ISSUER,
        "authorization_endpoint": f"{ISSUER}/protocol/openid-connect/auth",
        "token_endpoint": f"{ISSUER}/protocol/openid-connect/token",
        "userinfo_endpoint": f"{ISSUER}/protocol/openid-connect/userinfo",
        "jwks_uri": f"{ISSUER}/protocol/openid-connect/certs",
        "end_session_endpoint": f"{ISSUER}/protocol/openid-connect/logout",
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code", "client_credentials", "refresh_token"],
        "scopes_supported": ["openid", "profile", "email"],
        "id_token_signing_alg_values_supported": ["RS256"],
        "code_challenge_methods_supported": ["S256"],
        "token_endpoint_auth_methods_supported": ["client_secret_post", "client_secret_basic"],
    }


@pytest.fixture()
def sample_jwt_payload():
    """A realistic OIDC ID token payload."""
    return {
        "sub": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "iss": ISSUER,
        "aud": CLIENT_ID,
        "iat": 1700000000,
        "exp": 1700003600,
        "nonce": "random-nonce-value",
        "email": "testuser@example.com",
        "email_verified": True,
        "name": "Test User",
        "preferred_username": "testuser",
    }
