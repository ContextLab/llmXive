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

  function startLogin() {
    if (!CLIENT_ID) {
      console.warn("OAuth client id not configured");
      return;
    }
    const state = _randomState();
    sessionStorage.setItem(KEY_STATE, state);
    const params = new URLSearchParams({
      client_id: CLIENT_ID,
      redirect_uri: location.origin + location.pathname,
      scope: "public_repo",
      state,
    });
    location.href = "https://github.com/login/oauth/authorize?" + params.toString();
  }

  function signOut() {
    localStorage.removeItem(KEY_TOKEN);
    localStorage.removeItem(KEY_USER);
    renderSlot();
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
    const body = [
      "**Field:** " + field,
      "",
      description,
      "",
      keywords ? "**Keywords:** " + keywords : "",
      "",
      "---",
      "*Submitted via llmXive Dashboard.*",
    ].filter(Boolean).join("\n");
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
