# OIDC Inspector

A command-line tool for inspecting and debugging [OpenID Connect](https://openid.net/specs/openid-connect-core-1_0.html) authorization flows. It walks through an OIDC flow step by step, printing every parameter, token (decoded), and claim in a clean, readable format.

## Features

- **Three flows**: Authorization Code + PKCE (recommended), Authorization Code, Client Credentials
- **Auto-discovery**: fetches provider metadata from `/.well-known/openid-configuration`
- **JWT decoding**: displays header, payload, and human-readable timestamps for every JWT token
- **UserInfo**: calls `/userinfo` and prints all returned claims
- **State / nonce verification**: validates CSRF protection and replay-attack prevention parameters
- **Rich output**: colour-coded tables and syntax-highlighted JSON
- **Local OIDC provider**: Podman Compose setup with Keycloak for offline testing

## Requirements

- Python 3.14+
- [Poetry](https://python-poetry.org/) (dependency manager)
- A browser (for interactive flows)

## Installation

```bash
git clone <repo-url>
cd oidc-inspector
poetry install
```

After installation the `oidc-inspector` command is available inside the Poetry environment:

```bash
poetry run oidc-inspector --help
# or
poetry shell
oidc-inspector --help
```

## Quick Start

### With local Keycloak (see [`local-oidc/README.md`](local-oidc/README.md))

```bash
# 1. Start Keycloak
cd local-oidc && podman-compose up -d && cd ..

# 2. Run the Authorization Code + PKCE flow
poetry run oidc-inspector \
  --issuer http://localhost:8180/realms/oidc-inspector \
  --client-id oidc-inspector-public
```

Log in with `testuser` / `password`. The tool will print every step of the flow.

### Against any OIDC provider

```bash
poetry run oidc-inspector \
  --issuer https://accounts.example.com \
  --client-id my-app \
  --client-secret my-secret \
  --scope "openid profile email offline_access"
```

## Usage

```
oidc-inspector [OPTIONS]
```

### Required options

| Option | Env var | Description |
|--------|---------|-------------|
| `--issuer TEXT` | `OIDC_ISSUER` | OIDC issuer base URL |
| `--client-id TEXT` | `OIDC_CLIENT_ID` | Registered client identifier |

### Identity options

| Option | Env var | Default | Description |
|--------|---------|---------|-------------|
| `--client-secret TEXT` | `OIDC_CLIENT_SECRET` | — | Client secret (required for confidential clients and `client_credentials` flow) |

### Flow selection

| Option | Env var | Default | Description |
|--------|---------|---------|-------------|
| `--flow [pkce\|code\|client_credentials]` | `OIDC_FLOW` | `pkce` | Grant flow to execute |

| Value | Description |
|-------|-------------|
| `pkce` | Authorization Code + PKCE (RFC 7636) — recommended for public clients |
| `code` | Authorization Code without PKCE — requires `--client-secret` |
| `client_credentials` | Client Credentials (RFC 6749 §4.4) — no browser, machine-to-machine |

### Redirect / callback options

| Option | Env var | Default | Description |
|--------|---------|---------|-------------|
| `--redirect-uri TEXT` | `OIDC_REDIRECT_URI` | `http://localhost:8080/callback` | Redirect URI registered with the provider |
| `--callback-port INT` | `OIDC_CALLBACK_PORT` | `8080` | Port for the local callback server |
| `--callback-timeout INT` | — | `120` | Seconds to wait for browser callback |

### Scope and parameter options

| Option | Default | Description |
|--------|---------|-------------|
| `--scope TEXT` | `openid profile email` | Space-separated OAuth 2.0 scopes |
| `--extra-param KEY=VALUE` | — | Extra authorization parameters (repeatable) |

### Network options

| Option | Env var | Default | Description |
|--------|---------|---------|-------------|
| `--timeout INT` | `OIDC_TIMEOUT` | `30` | HTTP request timeout in seconds |
| `--no-verify-ssl` | — | off | Disable TLS certificate verification |

### Behaviour options

| Option | Default | Description |
|--------|---------|-------------|
| `--no-browser` | off | Print the authorization URL without opening a browser |
| `--skip-userinfo` | off | Skip the `/userinfo` endpoint call |
| `-V, --version` | — | Print version and exit |
| `-h, --help` | — | Show help and exit |

## Examples

```bash
# PKCE flow — public client, opens browser automatically
oidc-inspector \
  --issuer http://localhost:8180/realms/oidc-inspector \
  --client-id oidc-inspector-public

# Confidential client, Authorization Code flow
oidc-inspector \
  --issuer http://localhost:8180/realms/oidc-inspector \
  --client-id oidc-inspector-confidential \
  --client-secret test-secret-change-in-prod \
  --flow code

# Client Credentials — no browser required
oidc-inspector \
  --issuer http://localhost:8180/realms/oidc-inspector \
  --client-id oidc-inspector-confidential \
  --client-secret test-secret-change-in-prod \
  --flow client_credentials

# Headless environment — print URL, copy-paste manually
oidc-inspector \
  --issuer https://accounts.example.com \
  --client-id my-app \
  --no-browser

# Extra authorization parameters
oidc-inspector \
  --issuer https://accounts.example.com \
  --client-id my-app \
  --extra-param acr_values=urn:mace:incommon:iap:silver \
  --extra-param ui_locales=de

# Disable SSL verification (local provider with self-signed cert)
oidc-inspector \
  --issuer https://localhost:8443/realms/test \
  --client-id my-app \
  --no-verify-ssl

# Load settings from environment variables
export OIDC_ISSUER=https://accounts.example.com
export OIDC_CLIENT_ID=my-app
export OIDC_CLIENT_SECRET=my-secret
oidc-inspector
```

## Output Overview

The tool prints the following sections in order:

| Section | Description |
|---------|-------------|
| **Configuration** | All resolved parameters |
| **OIDC Discovery Document** | Summary table + full JSON |
| **PKCE & Security Parameters** | `code_verifier`, `code_challenge`, `state`, `nonce` (PKCE/code flows only) |
| **Authorization Request** | Every query parameter in a table + full URL |
| **Waiting for Callback** | Port and instructions |
| **Callback Parameters Received** | `code`, `state`, etc. returned by the provider |
| **Token Request** | POST body parameters |
| **Token Response** | Each token decoded: JWT header, payload (with readable timestamps), signature |
| **UserInfo Response** | JSON claims from `/userinfo` |

## Project Structure

```
oidc-inspector/
├── pyproject.toml               Poetry config & dependencies
├── README.md                    This file
├── docs/
│   ├── oidc-flow.md             OIDC flow diagrams and security notes
│   ├── endpoints.md             Endpoint reference with spec links
│   └── testing.md               Testing guide (unit + integration)
├── oidc_inspector/
│   ├── main.py                  CLI entry point (click)
│   ├── config.py                OIDCConfig dataclass
│   ├── discovery.py             Discovery document fetching
│   ├── pkce.py                  PKCE parameter generation (RFC 7636)
│   ├── callback_server.py       Local HTTP server for redirect capture
│   ├── token_client.py          Token endpoint client
│   ├── userinfo.py              UserInfo endpoint client
│   ├── jwt_decoder.py           JWT display decoding (no signature verification)
│   └── display.py               Rich-based terminal output
├── tests/
│   ├── conftest.py              Shared fixtures
│   ├── test_pkce.py
│   ├── test_jwt_decoder.py
│   ├── test_discovery.py
│   └── test_token_client.py
└── local-oidc/
    ├── compose.yaml             Podman Compose — Keycloak
    ├── keycloak-config/
    │   └── realm.json           Pre-configured realm import
    └── README.md
```

## Documentation

| Document | Description |
|----------|-------------|
| [`docs/oidc-flow.md`](docs/oidc-flow.md) | Flow diagrams, parameter explanations, security notes |
| [`docs/endpoints.md`](docs/endpoints.md) | Endpoint reference with links to OIDC/OAuth 2.0 specifications |
| [`docs/testing.md`](docs/testing.md) | Unit tests, integration test scenarios, Keycloak admin tips |
| [`local-oidc/README.md`](local-oidc/README.md) | Local provider setup and quick-start commands |

## Security Note

`oidc-inspector` is a **debugging and inspection tool**. JWT signatures are decoded and displayed but **not verified**. Do not use it to make trust decisions about token contents in production systems.

## License

Apache 2.0 — see [LICENSE](LICENSE).
