# Local OIDC Provider

This directory contains a [Podman Compose](https://github.com/containers/podman-compose) configuration that starts a local [Keycloak](https://www.keycloak.org/) instance pre-configured for use with `oidc-inspector`.

## Prerequisites

| Tool | Version |
|------|---------|
| Podman | ≥ 4.0 |
| podman-compose | ≥ 1.0 |

## Start

```bash
cd local-oidc
podman-compose up -d
```

Wait for the health check to pass (≈ 30–60 s on first start):

```bash
podman-compose ps        # Status should show "healthy"
```

## Realm details

| Setting | Value |
|---------|-------|
| Issuer | `http://localhost:8180/realms/oidc-inspector` |
| Admin UI | <http://localhost:8180/> (admin / admin) |
| Test user | `testuser` / `password` |

### Clients

| Client ID | Type | Secret | Use for |
|-----------|------|--------|---------|
| `oidc-inspector-public` | Public | — | `pkce` flow |
| `oidc-inspector-confidential` | Confidential | `test-secret-change-in-prod` | `code` or `client_credentials` flow |

## Quick-start examples

```bash
# Authorization Code + PKCE (public client)
oidc-inspector \
  --issuer http://localhost:8180/realms/oidc-inspector \
  --client-id oidc-inspector-public

# Authorization Code (confidential client)
oidc-inspector \
  --issuer http://localhost:8180/realms/oidc-inspector \
  --client-id oidc-inspector-confidential \
  --client-secret test-secret-change-in-prod \
  --flow code

# Client Credentials (no browser)
oidc-inspector \
  --issuer http://localhost:8180/realms/oidc-inspector \
  --client-id oidc-inspector-confidential \
  --client-secret test-secret-change-in-prod \
  --flow client_credentials
```

## Stop

```bash
podman-compose down
```

## Customisation

Edit `keycloak-config/realm.json` to add scopes, mappers, or additional clients, then restart:

```bash
podman-compose down && podman-compose up -d
```

The realm file is imported fresh each time Keycloak starts in `start-dev` mode.
