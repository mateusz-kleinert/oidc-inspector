# Testing Guide

## Unit Tests

Unit tests live in `tests/` and use [pytest](https://docs.pytest.org) with [pytest-httpx](https://github.com/Colin-b/pytest-httpx) to mock HTTP calls. No network access or running services are required.

### Run all tests

```bash
poetry run pytest
```

### Run with verbose output

```bash
poetry run pytest -v
```

### Run a specific test file

```bash
poetry run pytest tests/test_pkce.py -v
```

### Test coverage

```bash
poetry run pytest --cov=oidc_inspector --cov-report=term-missing
```

(Requires `pytest-cov`: `poetry add --group dev pytest-cov`)

---

## Test Modules

| File | What it tests |
|------|---------------|
| `tests/test_pkce.py` | PKCE parameter generation — verifier length, challenge derivation, uniqueness |
| `tests/test_jwt_decoder.py` | JWT base64 decoding, timestamp enrichment, error handling |
| `tests/test_discovery.py` | Discovery document fetching with mocked HTTP responses |
| `tests/test_token_client.py` | Token exchange and client credentials requests with mocked HTTP |

---

## Integration Testing with Local Keycloak

The `local-oidc/` directory provides a Podman Compose environment with Keycloak pre-configured with two clients and a test user.

### Start Keycloak

```bash
cd local-oidc
podman-compose up -d
# Wait ~30 s then verify:
curl -sf http://localhost:8180/realms/oidc-inspector/.well-known/openid-configuration | python3 -m json.tool
```

### Test scenarios

#### Scenario 1 — Authorization Code + PKCE (public client)

```bash
oidc-inspector \
  --issuer http://localhost:8180/realms/oidc-inspector \
  --client-id oidc-inspector-public
```

Log in with `testuser` / `password`. Verify:
- PKCE parameters (`code_verifier`, `code_challenge`) are printed.
- Authorization URL contains `code_challenge` and `code_challenge_method=S256`.
- Callback parameters include `code` and `state`.
- Token response contains `access_token` and `id_token` (both decoded as JWT).
- UserInfo response contains `sub`, `email`, `name`.

#### Scenario 2 — Authorization Code (confidential client)

```bash
oidc-inspector \
  --issuer http://localhost:8180/realms/oidc-inspector \
  --client-id oidc-inspector-confidential \
  --client-secret test-secret-change-in-prod \
  --flow code
```

Verify:
- No PKCE parameters in the output.
- Token request includes `client_secret`.

#### Scenario 3 — Client Credentials (no browser)

```bash
oidc-inspector \
  --issuer http://localhost:8180/realms/oidc-inspector \
  --client-id oidc-inspector-confidential \
  --client-secret test-secret-change-in-prod \
  --flow client_credentials
```

Verify:
- No browser is opened, no callback server is started.
- `access_token` is returned (typically no `id_token` or `refresh_token`).
- No UserInfo call (no user context).

#### Scenario 4 — Error handling

Trigger errors to verify they are displayed clearly:

```bash
# Invalid client secret
oidc-inspector \
  --issuer http://localhost:8180/realms/oidc-inspector \
  --client-id oidc-inspector-confidential \
  --client-secret WRONG \
  --flow client_credentials

# Wrong issuer URL
oidc-inspector \
  --issuer http://localhost:8180/realms/does-not-exist \
  --client-id oidc-inspector-public
```

#### Scenario 5 — Headless / CI mode

```bash
oidc-inspector \
  --issuer http://localhost:8180/realms/oidc-inspector \
  --client-id oidc-inspector-public \
  --no-browser
```

Copy the printed URL, open it manually in a browser, complete login, and verify the callback is still captured.

#### Scenario 6 — Extra authorization parameters

```bash
oidc-inspector \
  --issuer http://localhost:8180/realms/oidc-inspector \
  --client-id oidc-inspector-public \
  --extra-param ui_locales=de \
  --extra-param login_hint=testuser
```

Verify the extra parameters appear in the printed authorization URL.

---

## Keycloak Admin UI

Access the Keycloak Admin Console at <http://localhost:8180/> with credentials `admin` / `admin`.

Useful for:
- Inspecting issued tokens under **Sessions → Client Sessions**
- Adding custom claims via **Client Scopes → Mappers**
- Configuring additional clients
- Testing with different user attributes

---

## Stop Keycloak

```bash
cd local-oidc
podman-compose down
```
