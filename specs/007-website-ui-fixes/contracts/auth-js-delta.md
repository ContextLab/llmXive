# Contract: `web/js/auth.js` delta — sign-out fix + submission helpers

**File**: `web/js/auth.js` (the `LlmxiveAuth` IIFE). **Maps to**: FR-010, FR-011, FR-012, FR-013, FR-013b, FR-014, FR-015; data-model E5, E6. **Related**: `contracts/oauth-proxy.md` (the Worker's new `/revoke` route).

## `signOut()` — FR-010 + FR-011

```js
async function signOut() {
  // FR-010: unconditional local clear, FIRST.
  localStorage.removeItem(KEY_TOKEN);
  localStorage.removeItem(KEY_USER);
  sessionStorage.removeItem(KEY_STATE);   // <-- the current code forgets this
  renderSlot();                           // UI now shows signed-out
  // FR-011: revoke the OAuth grant via the proxy (best-effort, non-blocking).
  const t = /* the token captured before the clear */;
  if (PROXY && t) {
    try {
      const r = await fetch(PROXY + "/revoke", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token: t }),
      });
      if (!r.ok) throw new Error("revoke " + r.status);
    } catch (err) {
      console.warn("OAuth grant revocation failed:", err);
      // show a small non-blocking notice: "Signed out. You may need to sign out of github.com to switch accounts."
    }
  }
}
```

- The local clear MUST happen before, and independent of, the revoke call (so a Worker outage still signs the user out locally).
- A page reload after `signOut()` MUST keep the user signed out (no resurrection — guaranteed by the `localStorage` removal).
- **Fallback path** (if the Cloudflare Worker can't host `/revoke`): instead of the revoke call, modify `startLogin()` to force GitHub's account-chooser — navigate to `https://github.com/logout` with a `return_to` to the `authorize` URL (or the GitHub-honored prompt-equivalent). This is purely client-side. The acceptance test (re-sign-in as a different user) MUST pass via *either* path.

## `submitFeedback({ target_id, target_kind, target_stage, content })` — FR-012, FR-013

Creates a GitHub issue: `POST /repos/{OWNER}/{REPO}/issues` with `labels: ["human-submission", "feedback"]`, a structured body (blockquote summary; `target_id`/`target_kind`/`target_stage`; `submitter` = `user()?.login || "anonymous"`; the `content`; a footer). Returns the created issue (`{ html_url, number, ... }`). Mirrors the existing `submitIdea` shape (no new HTTP layer — uses `ghFetch`). Validates `content` non-empty before the call; on failure throws (the caller shows the error + preserves the form).

## `submitPaper({ url } | { pdfFile })` — FR-014, FR-015

- `{ url }`: `POST .../issues` with `labels: ["human-submission", "new-paper"]`, the URL in the body. Returns the issue.
- `{ pdfFile }` (a `File`): client-side size check (≤ 10 MB; over → throw "PDF too large; please submit a URL instead"); `PUT /repos/{OWNER}/{REPO}/contents/submissions/inbox/<ISO-timestamp>-<slug>.pdf` (base64 content, `branch: main`) → then `POST .../issues` with `labels: ["human-submission","new-paper"]` and the body referencing `submissions/inbox/<…>.pdf`. Returns the issue. (GitHub's REST API has no issue-attachment endpoint — staging via the Contents API is the only browser-doable way; the `submission_intake` agent moves the file to its canonical home and deletes the inbox copy.)

## `LlmxiveAuth` exports

Adds `submitFeedback`, `submitPaper` to the existing `{ mount, handleCallback, startLogin, signOut, isSignedIn, user, token, submitIdea, submitReview }` export object.

## Caller behavior (FR-013b)

The UI code that calls `submitFeedback` / `submitPaper` (and `submitIdea` / `submitReview` — i.e. *any* artifact-submission path) MUST, on success, render in the modal: a confirmation that a new GitHub issue was created **with a clickable link to it** (`html_url`) **and** the text that the contribution will be processed within the next hour. On failure: an inline error + the form's input preserved for retry. (This applies to the existing `submitIdea`/`submitReview` flows too — they currently lack the "within the hour" message.)

## Acceptance

- Sign-out: `localStorage` has no `llmxive_gh_token`/`llmxive_gh_user`, `sessionStorage` has no `llmxive_gh_oauth_state`, UI shows signed-out, reload keeps it; the proxy `/revoke` is called (verified via the Worker's logs / a real test) — or the fallback account-chooser path is taken.
- After sign-out, completing the OAuth flow signs in as a *different* GitHub user (manual visual verification — Constitution III's UI clause).
- `submitFeedback` / `submitPaper` create correctly-labelled issues with the right body context (verified via a real GitHub-API test against the repo, then cleaned up); a PDF submission stages a file under `submissions/inbox/`.
- The confirmation message (issue link + "within the hour") appears on a successful submission of each type.
