"""Rich-based display helpers for OIDC Inspector output."""

import json
from typing import Any, Optional
from urllib.parse import urlencode

from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.syntax import Syntax
from rich.table import Table

from oidc_inspector import __version__

console = Console()

_THEME = "monokai"


# ---------------------------------------------------------------------------
# Layout helpers
# ---------------------------------------------------------------------------


def print_banner() -> None:
    console.print(
        Panel.fit(
            f"[bold blue]OIDC Inspector[/bold blue]  [dim]v{__version__}[/dim]\n"
            "[dim]OpenID Connect flow analyzer and debugger[/dim]",
            border_style="blue",
            padding=(0, 2),
        )
    )


def _section(title: str) -> None:
    console.print()
    console.print(Rule(f"[bold]{title}[/bold]", style="blue"))


def _table(*columns: str) -> Table:
    t = Table(show_header=True, header_style="bold cyan", box=None, padding=(0, 1))
    for col in columns:
        t.add_column(col)
    return t


# ---------------------------------------------------------------------------
# Section printers
# ---------------------------------------------------------------------------


def print_config(config: Any) -> None:
    _section("Configuration")
    t = _table("Parameter", "Value")
    t.add_row("issuer", config.issuer)
    t.add_row("client_id", config.client_id)
    t.add_row(
        "client_secret",
        f"[dim]{config.client_secret[:4]}…[/dim]" if config.client_secret else "[dim]not set[/dim]",
    )
    t.add_row("redirect_uri", config.redirect_uri)
    t.add_row("scope", config.scope)
    t.add_row("flow", config.flow)
    t.add_row(
        "ssl_verification",
        "enabled" if config.verify_ssl else "[yellow]disabled[/yellow]",
    )
    t.add_row("timeout", f"{config.timeout}s")
    if config.extra_params:
        for k, v in config.extra_params.items():
            t.add_row(f"extra: {k}", v)
    console.print(t)


def print_discovery(discovery: dict[str, Any]) -> None:
    _section("OIDC Discovery Document")

    # Key fields shown in a summary table
    SUMMARY_FIELDS = [
        "issuer",
        "authorization_endpoint",
        "token_endpoint",
        "userinfo_endpoint",
        "jwks_uri",
        "introspection_endpoint",
        "end_session_endpoint",
        "response_types_supported",
        "grant_types_supported",
        "scopes_supported",
        "id_token_signing_alg_values_supported",
        "code_challenge_methods_supported",
        "token_endpoint_auth_methods_supported",
    ]

    t = _table("Field", "Value")
    for field in SUMMARY_FIELDS:
        if field not in discovery:
            continue
        val = discovery[field]
        if isinstance(val, list):
            val = "  ".join(str(v) for v in val)
        t.add_row(f"[cyan]{field}[/cyan]", str(val))
    console.print(t)

    console.print()
    console.print("[dim]Full discovery document:[/dim]")
    console.print(Syntax(json.dumps(discovery, indent=2), "json", theme=_THEME))


def print_pkce_params(verifier: str, challenge: str, state: str, nonce: str) -> None:
    _section("PKCE & Security Parameters")
    t = _table("Parameter", "Value")
    t.add_row("code_verifier", verifier)
    t.add_row("code_challenge", challenge)
    t.add_row("code_challenge_method", "S256")
    t.add_row("state", state)
    t.add_row("nonce", nonce)
    console.print(t)


def print_auth_request(authorization_endpoint: str, params: dict[str, str]) -> None:
    _section("Authorization Request")

    t = _table("Parameter", "Value")
    for k, v in params.items():
        t.add_row(f"[cyan]{k}[/cyan]", v)
    console.print(t)

    url = f"{authorization_endpoint}?{urlencode(params)}"
    console.print()
    console.print("[bold]Full authorization URL:[/bold]")
    console.print(f"[link={url}]{url}[/link]")


def print_waiting(port: int) -> None:
    _section("Waiting for Callback")
    console.print(
        f"Listening on [bold]http://127.0.0.1:{port}/callback[/bold] — complete the login in your browser."
    )


def print_callback_params(params: dict[str, Any]) -> None:
    _section("Callback Parameters Received")
    t = _table("Parameter", "Value")
    for k, v in params.items():
        if k == "code":
            display_val = f"{str(v)[:12]}…  [dim](truncated for display)[/dim]"
        else:
            display_val = str(v)
        t.add_row(f"[cyan]{k}[/cyan]", display_val)
    console.print(t)


def print_token_request(endpoint: str, params: dict[str, str]) -> None:
    _section("Token Request")
    console.print(f"[bold]POST[/bold] {endpoint}")
    t = _table("Parameter", "Value")
    for k, v in params.items():
        masked = v
        if k in ("client_secret", "code", "code_verifier") and len(v) > 12:
            masked = v[:8] + "…"
        t.add_row(f"[cyan]{k}[/cyan]", masked)
    console.print(t)


def print_token_response(tokens: dict[str, Any]) -> None:
    _section("Token Response")

    from oidc_inspector.jwt_decoder import decode_jwt, is_jwt

    # Print JWT tokens with decoded sections
    for token_key in ("access_token", "id_token", "refresh_token"):
        if token_key not in tokens:
            continue

        raw = tokens[token_key]
        console.print(f"\n[bold cyan]{token_key}:[/bold cyan]")

        if is_jwt(raw):
            decoded = decode_jwt(raw)
            console.print(f"[dim]Raw (truncated):[/dim] {raw[:64]}…")
            console.print()
            console.print("[bold]Header:[/bold]")
            console.print(Syntax(json.dumps(decoded["header"], indent=2), "json", theme=_THEME))
            console.print("[bold]Payload:[/bold]")
            console.print(Syntax(json.dumps(decoded["payload"], indent=2), "json", theme=_THEME))
            console.print(f"[dim]Signature (truncated):[/dim] {decoded['signature_truncated']}")
            console.print(
                "[dim italic]Note: JWT signature is NOT verified — for inspection only.[/dim italic]"
            )
        else:
            console.print(f"[dim](opaque token, not a JWT)[/dim]")
            console.print(raw[:80] + ("…" if len(raw) > 80 else ""))

    # Print all other fields in a table
    other = {k: v for k, v in tokens.items() if k not in ("access_token", "id_token", "refresh_token")}
    if other:
        console.print("\n[bold cyan]Other fields:[/bold cyan]")
        t = _table("Field", "Value")
        for k, v in other.items():
            t.add_row(f"[cyan]{k}[/cyan]", str(v))
        console.print(t)


def print_userinfo(userinfo: dict[str, Any]) -> None:
    _section("UserInfo Response")

    from oidc_inspector.jwt_decoder import decode_jwt, is_jwt

    raw_response = userinfo.get("raw_response")
    if raw_response and is_jwt(raw_response):
        console.print("[dim]UserInfo returned as a signed JWT — decoded below:[/dim]")
        decoded = decode_jwt(raw_response)
        console.print("[bold]Header:[/bold]")
        console.print(Syntax(json.dumps(decoded["header"], indent=2), "json", theme=_THEME))
        console.print("[bold]Payload:[/bold]")
        console.print(Syntax(json.dumps(decoded["payload"], indent=2), "json", theme=_THEME))
    else:
        console.print(Syntax(json.dumps(userinfo, indent=2), "json", theme=_THEME))


def print_error(message: str, details: Optional[str] = None) -> None:
    console.print(f"\n[bold red]Error:[/bold red] {message}")
    if details:
        console.print(f"[dim]{details}[/dim]")


def print_success(message: str) -> None:
    console.print(f"\n[bold green]✓[/bold green] {message}")
