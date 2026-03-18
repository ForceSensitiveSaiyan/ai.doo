# License Key Activation

The ai.doo license system uses **offline-validated signed JWTs**. Once activated, the license is verified locally — no phone-home, no telemetry, no external network calls.

## How It Works

1. You receive a license key (a signed JWT) from ai.doo.
2. You paste it into Hub's admin panel.
3. Hub validates the signature against the bundled public key and stores the token.
4. All subsequent checks are local — the JWT is decoded and its claims are verified on the server.

!!! info
    ai.doo licenses are designed for air-gapped environments. The license key contains everything needed for validation.

## Activating a License

=== "Hub UI"

    1. Log in to Hub as an admin.
    2. Open the admin panel and navigate to the **License** section.
    3. Paste your license key into the input field.
    4. Click **Activate**.

=== "API"

    ```bash
    curl -X POST http://localhost:2000/api/license/activate \
      -H "Authorization: Bearer <admin-token>" \
      -H "Content-Type: application/json" \
      -d '{"key": "<your-license-jwt>"}'
    ```

    A successful response returns:

    ```json
    {
      "valid": true,
      "customer": "Acme Corp",
      "tier": "professional",
      "seats": 10,
      "products": ["pika", "vera"],
      "expires_at": 1742256000,
      "error": ""
    }
    ```

## Checking License Status

PIKA and VERA query this endpoint on startup and cache the result for 1 hour.

```bash
curl http://localhost:2000/api/license/status \
  -H "Authorization: Bearer <hub-auth-api-key>"
```

Response:

```json
{
  "valid": true,
  "customer": "Acme Corp",
  "tier": "professional",
  "seats": 10,
  "products": ["pika", "vera"],
  "expires_at": 1742256000,
  "error": ""
}
```

## License Claims

Each JWT contains these claims:

| Claim | Type | Description |
|---|---|---|
| `products` | `string[]` | Licensed products — e.g. `["pika", "vera"]` |
| `seats` | `int` | Maximum number of enabled user accounts |
| `customer` | `string` | Customer name |
| `tier` | `string` | License tier — `professional` or `enterprise` |
| `exp` | `datetime` | Expiry timestamp (standard JWT `exp` claim) |
| `iss` | `string` | Issuer — always `aidoo.biz` |
| `sub` | `string` | Customer identifier |

## Soft Enforcement

ai.doo uses **soft enforcement** — an unlicensed installation remains fully functional:

| Condition | Behaviour |
|---|---|
| No license activated | Hub shows a banner: *"No license — activate to remove this notice"*. All features work normally. |
| License expired | Hub shows a banner: *"License expired"*. All features continue to work. |
| Seat limit exceeded | Hub prevents creating new users but existing users are unaffected. |

!!! tip
    Soft enforcement means you can evaluate the full suite before purchasing. There are no feature gates or time-bombs.

## Seat Enforcement

Seats are counted as the number of **enabled** user accounts in Hub (both admin and user roles). Disabled accounts do not count against the seat limit.

If you reach the seat limit:

- Attempting to create a new user returns a `402` error.
- Existing users are unaffected.
- Disable or delete unused accounts to free seats, or upgrade your license.
