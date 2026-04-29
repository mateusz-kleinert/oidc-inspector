"""OIDC Inspector CLI entry point."""

import sys
import webbrowser
from typing import Optional
from urllib.parse import urlencode

import click

from oidc_inspector import __version__
from oidc_inspector import display
from oidc_inspector.callback_server import wait_for_callback
from oidc_inspector.config import OIDCConfig
from oidc_inspector.discovery import fetch_oidc_discovery
from oidc_inspector.pkce import generate_code_challenge, generate_code_verifier, generate_nonce, generate_state
from oidc_inspector.token_client import exchange_code_for_tokens, get_client_credentials_token
from oidc_inspector.userinfo import fetch_userinfo


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(__version__, "-V", "--version")
# ── Identity ──────────────────────────────────────────────────────────────────
@click.option("--issuer", envvar="OIDC_ISSUER", required=True,
              help="OIDC issuer base URL (e.g. https://accounts.example.com). "
                   "The discovery document is fetched from <issuer>/.well-known/openid-configuration.")
@click.option("--client-id", envvar="OIDC_CLIENT_ID", required=True,
              help="OAuth 2.0 client identifier registered with the provider.")
@click.option("--client-secret", envvar="OIDC_CLIENT_SECRET", default=None,
              help="Client secret. Required for confidential clients and the "
                   "client_credentials flow. Omit for public PKCE clients.")
# ── Flow ──────────────────────────────────────────────────────────────────────
@click.option(
    "--flow", envvar="OIDC_FLOW", default="pkce", show_default=True,
    type=click.Choice(["pkce", "code", "client_credentials"], case_sensitive=False),
    help=(
        "Authorization flow to execute:\n\n"
        "  pkce              — Authorization Code + PKCE (RFC 7636). "
        "Recommended for public clients.\n\n"
        "  code              — Authorization Code without PKCE. "
        "Requires a client secret.\n\n"
        "  client_credentials — Machine-to-machine grant (RFC 6749 §4.4). "
        "No browser interaction."
    ),
)
# ── Redirect / callback ───────────────────────────────────────────────────────
@click.option("--redirect-uri", envvar="OIDC_REDIRECT_URI",
              default="http://localhost:8080/callback", show_default=True,
              help="Redirect URI registered with the provider. "
                   "Must match the --callback-port.")
@click.option("--callback-port", envvar="OIDC_CALLBACK_PORT",
              default=8080, show_default=True, type=int,
              help="Local port for the temporary callback HTTP server.")
@click.option("--callback-timeout", default=120, show_default=True, type=int,
              help="Seconds to wait for the browser callback before giving up.")
# ── Scopes & extras ───────────────────────────────────────────────────────────
@click.option("--scope", envvar="OIDC_SCOPE",
              default="openid profile email", show_default=True,
              help="Space-separated list of OAuth 2.0 scopes to request.")
@click.option("--extra-param", multiple=True, metavar="KEY=VALUE",
              help="Additional query parameters appended to the authorization URL. "
                   "Repeatable: --extra-param acr_values=urn:mace:incommon:iap:silver "
                   "--extra-param ui_locales=en")
# ── Network ───────────────────────────────────────────────────────────────────
@click.option("--no-verify-ssl", is_flag=True, default=False,
              help="Disable TLS certificate verification. "
                   "Useful for local providers with self-signed certs.")
@click.option("--timeout", envvar="OIDC_TIMEOUT",
              default=30, show_default=True, type=int,
              help="HTTP request timeout in seconds.")
# ── Behaviour ─────────────────────────────────────────────────────────────────
@click.option("--no-browser", is_flag=True, default=False,
              help="Print the authorization URL without opening a browser. "
                   "Useful in headless environments.")
@click.option("--skip-userinfo", is_flag=True, default=False,
              help="Do not call the /userinfo endpoint after obtaining tokens.")
def main(
    issuer: str,
    client_id: str,
    client_secret: Optional[str],
    flow: str,
    redirect_uri: str,
    callback_port: int,
    callback_timeout: int,
    scope: str,
    extra_param: tuple,
    no_verify_ssl: bool,
    timeout: int,
    no_browser: bool,
    skip_userinfo: bool,
) -> None:
    """OIDC Inspector — inspect and debug OpenID Connect authorization flows.

    Fetches the provider's discovery document, executes the selected grant flow,
    displays every token decoded (including JWT header, payload and claims), then
    calls the /userinfo endpoint and prints the response.

    \b
    Environment variable equivalents are listed beside each option so you can
    store non-sensitive settings in a .env file or shell profile.

    \b
    Examples
    --------
    # Authorization Code + PKCE against Keycloak (public client)
    oidc-inspector \\
        --issuer http://localhost:8180/realms/oidc-inspector \\
        --client-id oidc-inspector-public

    # Authorization Code against Keycloak (confidential client)
    oidc-inspector \\
        --issuer http://localhost:8180/realms/oidc-inspector \\
        --client-id oidc-inspector-confidential \\
        --client-secret test-secret-change-in-prod \\
        --flow code

    # Client Credentials (machine-to-machine, no browser)
    oidc-inspector \\
        --issuer http://localhost:8180/realms/oidc-inspector \\
        --client-id oidc-inspector-confidential \\
        --client-secret test-secret-change-in-prod \\
        --flow client_credentials
    """
    display.print_banner()

    # ── Parse extra params ────────────────────────────────────────────────────
    extra_params: dict[str, str] = {}
    for param in extra_param:
        if "=" not in param:
            display.print_error(
                f"Invalid --extra-param value {param!r}: expected KEY=VALUE format."
            )
            sys.exit(1)
        k, _, v = param.partition("=")
        extra_params[k.strip()] = v.strip()

    config = OIDCConfig(
        issuer=issuer,
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        scope=scope,
        callback_port=callback_port,
        flow=flow,
        verify_ssl=not no_verify_ssl,
        timeout=timeout,
        callback_timeout=callback_timeout,
        extra_params=extra_params,
    )
    display.print_config(config)

    # ── Discovery ─────────────────────────────────────────────────────────────
    try:
        discovery = fetch_oidc_discovery(config.issuer, config.verify_ssl, config.timeout)
    except Exception as exc:
        display.print_error("Failed to fetch OIDC discovery document", str(exc))
        sys.exit(1)

    display.print_discovery(discovery)
    token_endpoint: str = discovery["token_endpoint"]

    # ── Client Credentials ────────────────────────────────────────────────────
    if flow == "client_credentials":
        if not client_secret:
            display.print_error("--client-secret is required for the client_credentials flow.")
            sys.exit(1)

        try:
            tokens, req_params = get_client_credentials_token(
                token_endpoint=token_endpoint,
                client_id=client_id,
                client_secret=client_secret,
                scope=scope,
                verify_ssl=config.verify_ssl,
                timeout=config.timeout,
            )
        except Exception as exc:
            display.print_error("Token request failed", str(exc))
            sys.exit(1)

        display.print_token_request(token_endpoint, req_params)
        display.print_token_response(tokens)

    # ── Authorization Code (with or without PKCE) ─────────────────────────────
    else:
        authorization_endpoint: str = discovery.get("authorization_endpoint", "")
        if not authorization_endpoint:
            display.print_error("Discovery document does not contain an authorization_endpoint.")
            sys.exit(1)

        state = generate_state()
        nonce = generate_nonce()

        auth_params: dict[str, str] = {
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "scope": scope,
            "state": state,
            "nonce": nonce,
            **extra_params,
        }

        code_verifier: Optional[str] = None
        if flow == "pkce":
            code_verifier = generate_code_verifier()
            code_challenge = generate_code_challenge(code_verifier)
            auth_params["code_challenge"] = code_challenge
            auth_params["code_challenge_method"] = "S256"
            display.print_pkce_params(code_verifier, code_challenge, state, nonce)

        display.print_auth_request(authorization_endpoint, auth_params)

        auth_url = f"{authorization_endpoint}?{urlencode(auth_params)}"
        if no_browser:
            display.console.print(
                "\n[yellow]--no-browser set.[/yellow] Open the URL above manually."
            )
        else:
            webbrowser.open(auth_url)

        # Start callback server and wait
        display.print_waiting(callback_port)
        try:
            callback_params = wait_for_callback(callback_port, timeout=callback_timeout)
        except TimeoutError as exc:
            display.print_error(str(exc))
            sys.exit(1)
        except Exception as exc:
            display.print_error("Callback server error", str(exc))
            sys.exit(1)

        display.print_callback_params(callback_params)

        # CSRF check
        if callback_params.get("state") != state:
            display.print_error(
                "State parameter mismatch — possible CSRF attack. Aborting.",
                f"Expected: {state}\nReceived: {callback_params.get('state')}",
            )
            sys.exit(1)

        if "error" in callback_params:
            display.print_error(
                f"Authorization error: {callback_params['error']}",
                callback_params.get("error_description", ""),
            )
            sys.exit(1)

        code = callback_params.get("code")
        if not code:
            display.print_error("No authorization code received in the callback.")
            sys.exit(1)

        # Token exchange
        try:
            tokens, req_params = exchange_code_for_tokens(
                token_endpoint=token_endpoint,
                code=code,
                redirect_uri=redirect_uri,
                client_id=client_id,
                client_secret=client_secret,
                code_verifier=code_verifier,
                verify_ssl=config.verify_ssl,
                timeout=config.timeout,
            )
        except Exception as exc:
            display.print_error("Token exchange failed", str(exc))
            sys.exit(1)

        display.print_token_request(token_endpoint, req_params)
        display.print_token_response(tokens)

        # UserInfo
        if not skip_userinfo:
            userinfo_endpoint = discovery.get("userinfo_endpoint")
            access_token = tokens.get("access_token")

            if not userinfo_endpoint:
                display.console.print(
                    "\n[yellow]Provider does not expose a userinfo_endpoint — skipping.[/yellow]"
                )
            elif not access_token:
                display.console.print(
                    "\n[yellow]No access_token in token response — cannot call userinfo.[/yellow]"
                )
            else:
                try:
                    userinfo = fetch_userinfo(
                        userinfo_endpoint=userinfo_endpoint,
                        access_token=access_token,
                        verify_ssl=config.verify_ssl,
                        timeout=config.timeout,
                    )
                    display.print_userinfo(userinfo)
                except Exception as exc:
                    display.print_error("UserInfo request failed", str(exc))

    display.print_success("Flow complete.")


if __name__ == "__main__":
    main()
