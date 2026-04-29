# OIDC Endpoints Reference

All endpoint URLs are discovered dynamically from the provider's discovery document.
No endpoint URL needs to be configured manually.

---

## Discovery Endpoint

**URL pattern**: `{issuer}/.well-known/openid-configuration`

**Method**: `GET`

**Specification**: [OpenID Connect Discovery 1.0 §4](https://openid.net/specs/openid-connect-discovery-1_0.html#ProviderConfig)

Returns a JSON document describing the provider's capabilities and all endpoint URLs.
`oidc-inspector` fetches this first on every run.

**Key fields returned:**

| Field | Description |
|-------|-------------|
| `issuer` | The provider's canonical identifier |
| `authorization_endpoint` | Where to send the browser for user authentication |
| `token_endpoint` | Where to exchange codes and credentials for tokens |
| `userinfo_endpoint` | Where to retrieve user claims with an access token |
| `jwks_uri` | JSON Web Key Set — public keys used to verify JWTs |
| `introspection_endpoint` | Optional: validate an opaque access token |
| `end_session_endpoint` | Optional: initiate logout |
| `response_types_supported` | Which `response_type` values the provider accepts |
| `grant_types_supported` | Supported OAuth 2.0 grant types |
| `code_challenge_methods_supported` | PKCE challenge methods (expect `S256`) |
| `scopes_supported` | Scopes the provider understands |

---

## Authorization Endpoint

**Method**: `GET` (browser redirect)

**Specification**: [RFC 6749 §3.1](https://www.rfc-editor.org/rfc/rfc6749#section-3.1) / [OpenID Connect Core §3.1.2.1](https://openid.net/specs/openid-connect-core-1_0.html#AuthRequest)

The user's browser is directed here. The provider authenticates the user and redirects back with an authorization code.

**Query parameters:**

| Parameter | Required | Description |
|-----------|----------|-------------|
| `response_type` | Yes | Always `code` for Authorization Code flow |
| `client_id` | Yes | The registered client identifier |
| `redirect_uri` | Yes | Must match a URI pre-registered with the provider |
| `scope` | Yes | Space-separated scopes; must include `openid` for OIDC |
| `state` | Recommended | Random value; returned verbatim in callback for CSRF protection |
| `nonce` | Recommended | Random value; embedded in `id_token` to prevent replay |
| `code_challenge` | PKCE | `BASE64URL(SHA256(code_verifier))` |
| `code_challenge_method` | PKCE | `S256` |
| `prompt` | Optional | `none` (silent), `login` (force re-auth), `consent`, `select_account` |
| `max_age` | Optional | Max seconds since last authentication |
| `acr_values` | Optional | Requested Authentication Context Class References |
| `ui_locales` | Optional | Preferred UI language(s) |

---

## Token Endpoint

**Method**: `POST` with `application/x-www-form-urlencoded` body

**Specification**: [RFC 6749 §3.2](https://www.rfc-editor.org/rfc/rfc6749#section-3.2) / [OpenID Connect Core §3.1.3.1](https://openid.net/specs/openid-connect-core-1_0.html#TokenRequest)

Used to exchange an authorization code for tokens, or to obtain a token directly via Client Credentials.

### Authorization Code grant

| Parameter | Required | Description |
|-----------|----------|-------------|
| `grant_type` | Yes | `authorization_code` |
| `code` | Yes | The code received in the callback |
| `redirect_uri` | Yes | Same URI used in the authorization request |
| `client_id` | Yes | The client identifier |
| `client_secret` | Confidential | Required for non-public clients |
| `code_verifier` | PKCE | The original random verifier used to derive `code_challenge` |

### Client Credentials grant

| Parameter | Required | Description |
|-----------|----------|-------------|
| `grant_type` | Yes | `client_credentials` |
| `client_id` | Yes | The client identifier |
| `client_secret` | Yes | The client secret |
| `scope` | Optional | Requested scopes |

**Response:**

```json
{
  "access_token": "eyJ…",
  "token_type": "Bearer",
  "expires_in": 300,
  "id_token": "eyJ…",
  "refresh_token": "eyJ…",
  "scope": "openid profile email"
}
```

---

## UserInfo Endpoint

**Method**: `GET` or `POST`

**Authorization**: `Authorization: Bearer <access_token>`

**Specification**: [OpenID Connect Core §5.3](https://openid.net/specs/openid-connect-core-1_0.html#UserInfo)

Returns claims about the authenticated user. The access token's scope determines which claims are returned.

**Standard claims:**

| Claim | Description |
|-------|-------------|
| `sub` | Subject identifier — unique, stable user ID |
| `name` | Full display name |
| `given_name` | First name |
| `family_name` | Last name |
| `email` | Email address |
| `email_verified` | Whether the email has been verified |
| `phone_number` | Phone number |
| `address` | Physical mailing address |
| `birthdate` | Date of birth |
| `zoneinfo` | Time zone |
| `locale` | Preferred locale |
| `updated_at` | Time the user's info was last updated |

**Specification reference for all standard claims**: [OpenID Connect Core §5.1](https://openid.net/specs/openid-connect-core-1_0.html#StandardClaims)

---

## JWKS Endpoint (JSON Web Key Set)

**Method**: `GET`

**Specification**: [RFC 7517](https://www.rfc-editor.org/rfc/rfc7517) / [RFC 7518](https://www.rfc-editor.org/rfc/rfc7518)

Returns the provider's public keys in JWK format. Clients use these to verify JWT signatures.

```json
{
  "keys": [
    {
      "kty": "RSA",
      "use": "sig",
      "kid": "key-identifier",
      "alg": "RS256",
      "n": "…",
      "e": "AQAB"
    }
  ]
}
```

> `oidc-inspector` decodes JWT payloads for display but does **not** verify signatures
> (this is a debugging tool). For production, always verify signatures before trusting claims.

---

## Further Reading

| Document | URL |
|----------|-----|
| OpenID Connect Core 1.0 | <https://openid.net/specs/openid-connect-core-1_0.html> |
| OpenID Connect Discovery 1.0 | <https://openid.net/specs/openid-connect-discovery-1_0.html> |
| RFC 6749 — OAuth 2.0 | <https://www.rfc-editor.org/rfc/rfc6749> |
| RFC 7636 — PKCE | <https://www.rfc-editor.org/rfc/rfc7636> |
| RFC 7517 — JWK | <https://www.rfc-editor.org/rfc/rfc7517> |
| RFC 7519 — JWT | <https://www.rfc-editor.org/rfc/rfc7519> |
| RFC 9700 — OAuth 2.1 (draft) | <https://www.rfc-editor.org/rfc/rfc9700> |
