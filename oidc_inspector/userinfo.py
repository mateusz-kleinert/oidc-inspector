"""UserInfo endpoint client (OpenID Connect Core §5.3)."""

from typing import Any

import httpx


def fetch_userinfo(
    userinfo_endpoint: str,
    access_token: str,
    verify_ssl: bool = True,
    timeout: int = 30,
) -> dict[str, Any]:
    """GET the UserInfo endpoint using a Bearer access token.

    Spec: https://openid.net/specs/openid-connect-core-1_0.html#UserInfo
    The response may be JSON or a signed JWT depending on the provider's configuration.
    """
    headers = {"Authorization": f"Bearer {access_token}"}
    with httpx.Client(verify=verify_ssl, timeout=timeout) as client:
        response = client.get(userinfo_endpoint, headers=headers)
        response.raise_for_status()
        content_type = response.headers.get("content-type", "")
        if "json" in content_type:
            return response.json()
        # Some providers return a signed JWT
        return {"raw_response": response.text, "content_type": content_type}
