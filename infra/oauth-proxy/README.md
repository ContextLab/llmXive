# llmXive OAuth proxy

A ~80-LOC Cloudflare Worker that exchanges a GitHub OAuth authorization
code for an access token, keeping the `client_secret` server-side.

## Deploy

```sh
cd infra/oauth-proxy
npm install
npx wrangler login
npx wrangler secret put GITHUB_CLIENT_SECRET   # paste the OAuth App's client secret
npx wrangler deploy
```

After deploy, set the live URL in `web/index.html`:

```html
<meta name="llmxive-oauth-proxy" content="https://llmxive-oauth.<sub>.workers.dev/authenticate" />
```

## Endpoints

- `POST /authenticate` `{code, state}` → `{access_token, scope, token_type}`
- `GET  /healthz` → `"ok"`

## Security

- `client_secret` is a Worker secret; never appears in the source.
- CORS allowlist restricts callers to `ALLOWED_ORIGIN` (configured in `wrangler.toml`).
- The browser is responsible for the OAuth `state` round-trip (CSRF check).
- Free tier: 100k requests/day, more than enough for a research site.
