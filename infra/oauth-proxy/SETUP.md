# OAuth proxy: one-time setup

This Worker holds your GitHub OAuth `client_secret` so the static
GitHub Pages site can let users sign in with GitHub.

## Prerequisites

- A Cloudflare account (free tier is enough — 100k requests/day).
- A GitHub OAuth App: https://github.com/settings/developers
  - **Authorization callback URL**: `https://context-lab.com/llmXive/`
  - **Application name / homepage**: anything sensible.
  - The OAuth App's **Client ID** is already committed in
    `web/index.html` (`<meta name="llmxive-oauth-client-id">`).

## Steps

```bash
cd infra/oauth-proxy
npm install
npx wrangler login                  # opens a browser; one-time
npx wrangler secret put GITHUB_CLIENT_SECRET
# paste the OAuth App's Client Secret when prompted

npx wrangler deploy
# wrangler prints the deployed URL, e.g.
#   https://llmxive-oauth.<your-subdomain>.workers.dev
```

## Wire the URL into the site

After `wrangler deploy` prints the live URL, update the meta tag in
`web/index.html`:

```html
<meta name="llmxive-oauth-proxy"
      content="https://llmxive-oauth.<your-subdomain>.workers.dev/authenticate" />
```

Commit + push to `main`; the Pages workflow will sync `web/` → `docs/`
and the live site will start using the new proxy on the next push.

## Verify

1. Visit https://context-lab.com/llmXive/ in a private window.
2. Click **Sign in**; the OAuth consent screen should appear.
3. After approving, the topbar should show your GitHub avatar +
   login + a "sign out" affordance.

If sign-in fails, open browser devtools → Network and inspect the
`POST /authenticate` request. The Worker's `/healthz` endpoint
returns `"ok"` and is a useful liveness check:

```
curl https://llmxive-oauth.<your-subdomain>.workers.dev/healthz
```

## Cost

The Cloudflare Workers free tier covers 100,000 requests/day. A
sign-in uses 1 request to the Worker; healthchecks and CORS preflights
add a few more. Even with thousands of contributors a day, you'll
sit comfortably under the free quota.

## What if you do NOT deploy the Worker?

Then the **Sign in** button still appears, but clicking it will:
1. Redirect to GitHub successfully (no Worker needed for the auth
   request itself).
2. Return with `?code=...&state=...`.
3. Fail at the code-exchange step (the proxy URL returns 404 / DNS
   error). The browser console will log the failure; the user stays
   signed-out.

Read-only browsing (every tab on the site) works fully without
authentication. Submitting ideas + posting reviews requires the
Worker to be deployed.
