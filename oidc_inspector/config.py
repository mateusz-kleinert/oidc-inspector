from dataclasses import dataclass, field
from typing import Optional


@dataclass
class OIDCConfig:
    issuer: str
    client_id: str
    client_secret: Optional[str] = None
    redirect_uri: str = "http://localhost:8080/callback"
    scope: str = "openid profile email"
    callback_port: int = 8080
    flow: str = "pkce"  # pkce | code | client_credentials
    verify_ssl: bool = True
    timeout: int = 30
    callback_timeout: int = 120
    extra_params: dict = field(default_factory=dict)
