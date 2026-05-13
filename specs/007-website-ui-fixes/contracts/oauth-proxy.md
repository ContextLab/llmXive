# Contract: Cloudflare-Worker OAuth proxy — new `/revoke` route (FR-011)

**Where**: the `simple-oauth-proxy` Cloudflare Worker (external to this repo; the deploy targets `https://context-lab.com/llmxive`'s configured `llmxive-oauth-proxy` meta URL). **Maps to**: FR-011; research D3. **This contract documents the adjunct change applied in that Worker's repo, plus the fallback if it can't be made.**

## The existing Worker (for context)

It already exposes one route — the OAuth code→token exchange — which receives `{ code, state }` from `web/js/auth.js` and calls `POST https://github.com/login/oauth/access_token` with the `client_id` + `client_secret` (held as Worker secrets), returning `{ access_token }`. So the Worker already (a) holds the client secret and (b) makes authenticated outbound calls to GitHub.

## New: `POST <PROXY>/revoke`

**Request** (from `web/js/auth.js` `signOut()`): `{ "token": "<the user's OAuth access token>" }`.

**Behavior**: the Worker calls GitHub's "Delete an app authorization" endpoint —
```
DELETE https://api.github.com/applications/{CLIENT_ID}/grant
Authorization: Basic base64(CLIENT_ID:CLIENT_SECRET)
Accept: application/vnd.github+json
Content-Type: application/json
{ "access_token": "<token>" }
```
— which revokes **all** tokens for that user↔app grant (so a subsequent `authorize` necessarily re-prompts at GitHub and a different account can be chosen). GitHub returns `204 No Content` on success (also treat `404` — "grant already gone" — as success).

**Response**: `204` (or a small JSON `{ ok: true }`) on success; a `5x`/`4xx` with a brief message on failure. The client treats any non-2xx as "revoke failed" → non-blocking warning (the user is still signed out locally per FR-010).

**CORS**: same `Access-Control-Allow-Origin` config as the existing route (the site's origin), plus an `OPTIONS` preflight handler if not already present.

**Security**: the route only accepts a token to revoke *that token's own grant* (it doesn't take a `client_secret` or a username from the caller — the secret stays in the Worker). It's safe for the caller to pass their token (they're about to discard it anyway).

## Fallback (if the Worker can't host `/revoke`)

If, for whatever Cloudflare-config reason, the `/revoke` route can't be added, FR-011 is satisfied entirely client-side instead: `web/js/auth.js` `startLogin()` forces GitHub's account-chooser by navigating to `https://github.com/logout` (which clears the github.com session) with a `return_to` back to the `authorize` URL — so the next sign-in always re-authenticates and the user picks an account. No Worker change; one extra redirect on each sign-in. The acceptance criterion (re-sign-in as a different user works) MUST pass via either path.

## Acceptance

- (Primary) Calling `POST <PROXY>/revoke` with a valid token revokes the grant — verified by a real test: sign in, capture the token, hit `/revoke`, then attempt a GitHub API call with the old token → it fails (401); then a fresh `authorize` re-prompts.
- (Fallback) The forced-account-chooser path is verified manually: sign out → sign in → GitHub shows its account/consent screen → choosing a different account signs in as that account.
- Either way, the Worker's existing code-exchange route still works (the new route doesn't break the old one).
