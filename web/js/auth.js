// llmXive — GitHub OAuth client (Cloudflare Worker proxy).
// Configure via meta tags in index.html.

(function () {
  const meta = name => document.querySelector('meta[name="' + name + '"]')?.getAttribute("content") || "";

  const PROXY     = meta("llmxive-oauth-proxy");
  const CLIENT_ID = meta("llmxive-oauth-client-id");
  const OWNER     = meta("llmxive-github-owner");
  const REPO      = meta("llmxive-github-repo");

  const KEY_TOKEN = "llmxive_gh_token";
  const KEY_USER  = "llmxive_gh_user";
  const KEY_STATE = "llmxive_gh_oauth_state";

  function token() { return localStorage.getItem(KEY_TOKEN); }
  function user()  { try { return JSON.parse(localStorage.getItem(KEY_USER) || "null"); } catch { return null; } }
  function isSignedIn() { return !!token() && !!user(); }

  let _slot = null;

  function escapeHtml(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
  }

  function renderSlot() {
    if (!_slot) return;
    _slot.replaceChildren();
    const u = user();
    if (u) {
      const html =
        '<span class="auth-chip" title="signed in as ' + escapeHtml(u.login) + '">' +
        '<img src="' + escapeHtml(u.avatar_url) + '" alt="" />' +
        '<span>' + escapeHtml(u.login) + '</span>' +
        '<span class="signout" data-action="signout">sign out</span>' +
        '</span>';
      _slot.insertAdjacentHTML("beforeend", html);
      _slot.querySelector("[data-action='signout']").addEventListener("click", signOut);
    } else {
      _slot.insertAdjacentHTML("beforeend",
        '<button class="btn ghost" data-action="signin"><i class="fa-brands fa-github"></i> Sign in</button>');
      _slot.querySelector("[data-action='signin']").addEventListener("click", startLogin);
    }
  }

  function mount(el) { _slot = el; renderSlot(); }

  function _randomState() {
    const buf = new Uint8Array(16);
    crypto.getRandomValues(buf);
    return [...buf].map(b => b.toString(16).padStart(2, "0")).join("");
  }

  function _authorizeUrl() {
    const params = new URLSearchParams({
      client_id: CLIENT_ID,
      redirect_uri: location.origin + location.pathname,
      scope: "public_repo",
      state: sessionStorage.getItem(KEY_STATE) || "",
    });
    return "https://github.com/login/oauth/authorize?" + params.toString();
  }

  function startLogin() {
    if (!CLIENT_ID) {
      console.warn("OAuth client id not configured");
      return;
    }
    const state = _randomState();
    sessionStorage.setItem(KEY_STATE, state);
    const authorize = _authorizeUrl();
    // FR-011 (account-switching): route through github.com/logout first so the
    // user is presented with GitHub's account/consent screen and a *different*
    // account can be chosen. This works regardless of whether the OAuth proxy's
    // /revoke route is deployed (it's the no-Worker-change fallback path); when
    // /revoke IS deployed, signOut() also revokes the grant for good measure.
    const logoutUrl = "https://github.com/logout?return_to=" + encodeURIComponent(authorize);
    location.href = logoutUrl;
  }

  // Non-blocking, dismissible notice (used when grant-revocation fails).
  function _notice(msg) {
    try {
      const root = document.getElementById("banners");
      if (!root) return;
      const div = document.createElement("div");
      div.className = "shell banner warn";
      div.innerHTML = '<i class="fa-solid fa-circle-info"></i> ' + escapeHtml(msg) +
        ' <span class="x" title="dismiss"><i class="fa-solid fa-xmark"></i></span>';
      div.querySelector(".x").addEventListener("click", () => div.remove());
      root.appendChild(div);
    } catch { /* never throw from a notice */ }
  }

  async function signOut() {
    // FR-010: unconditional local clear, FIRST — so a proxy outage still
    // signs the user out locally, and a reload can't resurrect the session.
    const t = token();
    localStorage.removeItem(KEY_TOKEN);
    localStorage.removeItem(KEY_USER);
    sessionStorage.removeItem(KEY_STATE);   // the OAuth-state nonce — was forgotten
    renderSlot();
    // FR-011: best-effort grant revocation via the proxy's /revoke route
    // (the Worker holds the client secret and calls
    // DELETE /applications/{client_id}/grant). Non-blocking; never throws.
    if (PROXY && t) {
      try {
        const r = await fetch(PROXY + "/revoke", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ token: t }),
        });
        if (!r.ok) throw new Error("revoke " + r.status);
      } catch (err) {
        console.warn("OAuth grant revocation failed (will fall back to the account-chooser on next sign-in):", err);
        _notice("Signed out. You may need to sign out of github.com to switch accounts.");
      }
    }
  }

  async function handleCallback() {
    const params = new URLSearchParams(location.search);
    const code = params.get("code");
    const state = params.get("state");
    if (!code) return;

    const expected = sessionStorage.getItem(KEY_STATE);
    sessionStorage.removeItem(KEY_STATE);
    if (!expected || expected !== state) {
      console.warn("OAuth state mismatch");
      _stripQuery(); return;
    }
    if (!PROXY) { console.warn("OAuth proxy not configured"); _stripQuery(); return; }
    try {
      const r = await fetch(PROXY, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ code, state }),
      });
      if (!r.ok) throw new Error("proxy " + r.status);
      const data = await r.json();
      if (!data.access_token) throw new Error("no access_token");
      localStorage.setItem(KEY_TOKEN, data.access_token);
      const u = await ghFetch("/user");
      localStorage.setItem(KEY_USER, JSON.stringify({
        login: u.login, avatar_url: u.avatar_url, name: u.name, html_url: u.html_url,
      }));
      renderSlot();
    } catch (err) {
      console.error("OAuth code exchange failed:", err);
    } finally {
      _stripQuery();
    }
  }

  function _stripQuery() { history.replaceState(null, "", location.pathname + location.hash); }

  async function ghFetch(path, init) {
    const t = token();
    const headers = Object.assign(
      { "Accept": "application/vnd.github+json" },
      (init && init.headers) || {},
    );
    if (t) headers["Authorization"] = "Bearer " + t;
    const r = await fetch("https://api.github.com" + path, { ...init, headers });
    if (!r.ok) {
      const txt = await r.text();
      throw new Error("GitHub " + r.status + ": " + txt.slice(0, 200));
    }
    if (r.status === 204) return null;
    return r.json();
  }

  async function submitIdea({ title, field, description, keywords }) {
    // Structured markdown body — no leading "#" so GitHub doesn't render
    // the whole content as an H1. Brief blockquote summary, then prose,
    // then a metadata bullet list, then a footer pointing back to the site.
    const summary = (description.split("\n", 1)[0] || "").slice(0, 200);
    const lines = [
      "> " + summary,
      "",
      "## Description",
      "",
      description,
      "",
      "## Metadata",
      "",
      "- **Field:** " + field,
    ];
    if (keywords) lines.push("- **Keywords:** " + keywords);
    lines.push("- **Stage:** brainstormed");
    lines.push("");
    lines.push("---");
    lines.push("*Submitted via the llmXive Dashboard. The Brainstorm and Flesh-Out agents will pick this up on the next pipeline cycle.*");
    const body = lines.join("\n");
    return ghFetch("/repos/" + OWNER + "/" + REPO + "/issues", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title, body, labels: ["idea", "brainstormed"] }),
    });
  }

  function _toBase64(s) { return btoa(unescape(encodeURIComponent(s))); }

  async function submitReview({ project_id, stage, verdict, summary, strengths, concerns }) {
    const date = new Date().toISOString().slice(0, 10);
    const u = user();
    const reviewer = (u && u.login) || "anonymous";
    const score = verdict === "accept" ? 1.0 : 0.0;
    const reviewKind = stage === "paper" ? "paper" : "research";
    const path = "projects/" + project_id + "/" +
      (reviewKind === "paper" ? "paper/reviews" : "reviews/research") +
      "/" + reviewer + "__" + date + "__M.md";
    const frontmatter = [
      "---",
      "reviewer_name: " + reviewer,
      "reviewer_kind: human",
      "artifact_path: projects/" + project_id + "/",
      "artifact_hash: 0000000000000000000000000000000000000000000000000000000000000000",
      "score: " + score,
      "verdict: " + verdict,
      "reviewed_at: " + new Date().toISOString(),
      "---",
      "",
      "## Summary",
      "",
      summary,
      "",
      strengths ? "## Strengths\n\n" + strengths + "\n" : "",
      concerns  ? "## Concerns\n\n" + concerns + "\n" : "",
    ].filter(Boolean).join("\n");
    return ghFetch("/repos/" + OWNER + "/" + REPO + "/contents/" + path, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: "Add human review for " + project_id + " (" + verdict + ")",
        content: _toBase64(frontmatter),
        branch: "main",
      }),
    });
  }

  window.LlmxiveAuth = {
    mount, handleCallback, startLogin, signOut, isSignedIn,
    user, token, submitIdea, submitReview,
  };
})();
