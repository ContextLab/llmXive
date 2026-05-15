// llmXive — artifact-log dialog (US2).
// All interpolated values pass through escapeHtml() before insertion.

(function () {
  const D = window.LlmxiveData;

  const REPO_BASE = "https://github.com/ContextLab/llmXive";
  const RAW_BASE  = "https://raw.githubusercontent.com/ContextLab/llmXive/main";

  function escapeHtml(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
  }

  function blob(rel) { return rel ? REPO_BASE + "/blob/main/" + rel : null; }
  function raw(rel)  { return rel ? RAW_BASE + "/" + rel : null; }

  // Map `projects/<PID>/paper/pdf/<file>.pdf` to the same-origin mirror at
  // `<site-base>/papers/<PID>/<file>.pdf`. The deploy workflow (pages.yml)
  // copies every project's PDFs into that location so we can <embed> them
  // inline — raw.githubusercontent.com forces a download instead.
  // Returns null if `repoPath` doesn't match the expected layout (e.g. a
  // non-paper PDF or a malformed path).
  function _toSameOriginPdf(repoPath) {
    if (!repoPath) return null;
    const m = String(repoPath).match(/^projects\/([^/]+)\/paper\/pdf\/(.+\.pdf)$/i);
    if (!m) return null;
    // Compute the site base from the current location so this works both at
    // https://context-lab.com/llmXive/ and at GitHub Pages preview URLs.
    // pathname is e.g. "/llmXive/" — keep that prefix when constructing
    // mirror URLs.
    const base = window.location.pathname.replace(/\/[^/]*$/, "/");
    return base + "papers/" + m[1] + "/" + m[2];
  }

  const ARTIFACT_ROWS = [
    ["idea",                    "fa-lightbulb",            "Idea"],
    ["spec",                    "fa-file-lines",           "Research spec"],
    ["plan",                    "fa-rectangle-list",       "Research plan"],
    ["tasks",                   "fa-list-check",           "Research tasks"],
    ["code",                    "fa-code",                 "Code"],
    ["data",                    "fa-database",             "Data"],
    ["paper_spec",              "fa-newspaper",            "Paper spec"],
    ["paper_plan",              "fa-rectangle-list",       "Paper plan"],
    ["paper_tasks",             "fa-list-check",           "Paper tasks"],
    ["paper_source",            "fa-file-code",            "LaTeX source (main)"],
    ["paper_supplement_source", "fa-file-code",            "LaTeX source (supplement)"],
    ["paper_figures",           "fa-image",                "Figures"],
    ["paper_pdf",               "fa-file-pdf",             "Paper PDF"],
    ["paper_supplement",        "fa-file-pdf",             "Supplement PDF"],
    ["reviews_research",        "fa-magnifying-glass",     "Research reviews"],
    ["reviews_paper",           "fa-magnifying-glass-plus", "Paper reviews"],
    ["citations",               "fa-quote-left",           "Citations"],
  ];

  let _currentProject = null;
  let _feedbackArtifactKind = null;

  function _ensureMount() {
    let bd = document.getElementById("ad-backdrop");
    if (bd) return bd;
    bd = document.createElement("div");
    bd.id = "ad-backdrop";
    bd.className = "modal-backdrop";
    const html = ''
      + '<div class="modal artifact-dialog" role="dialog" aria-modal="true">'
      + '<div class="ad-head">'
      + '<div><h2 class="ad-title">—</h2><span class="ad-stage-badge"></span></div>'
      + '<div class="ad-head-actions">'
      + '<button class="ad-feedback-btn" type="button"><i class="fa-regular fa-comment-dots"></i> Send feedback</button>'
      + '<button class="ad-close" aria-label="close"><i class="fa-solid fa-xmark"></i> Close</button>'
      + '</div>'
      + '</div>'
      + '<div class="ad-feedback" hidden>'
      + '<div class="ad-fb-inner">'
      + '<label class="field"><span class="l">Your feedback on this artifact</span>'
      + '<textarea class="ad-fb-text" placeholder="What\'s missing, wrong, or could be improved? A maintenance agent will triage this to the right pipeline step within the hour."></textarea></label>'
      + '<div class="ad-fb-actions">'
      + '<span class="ad-fb-msg"></span>'
      + '<button class="btn ghost ad-fb-cancel" type="button">Cancel</button>'
      + '<button class="btn primary ad-fb-submit" type="button"><i class="fa-solid fa-paper-plane"></i> Submit feedback</button>'
      + '</div></div></div>'
      + '<div class="ad-body">'
      + '<div class="ad-pdf"><div class="ad-pdf-empty">No PDF available yet.</div></div>'
      + '<div class="ad-list"></div>'
      + '</div></div>';
    bd.insertAdjacentHTML("beforeend", html);
    document.body.appendChild(bd);

    bd.addEventListener("click", e => {
      if (e.target === bd || e.target.closest(".ad-close")) close();
    });
    document.addEventListener("keydown", e => {
      if (e.key === "Escape" && bd.classList.contains("open")) close();
    });

    // Feedback panel wiring.
    const fbPanel = bd.querySelector(".ad-feedback");
    const fbText = bd.querySelector(".ad-fb-text");
    const fbMsg = bd.querySelector(".ad-fb-msg");
    bd.querySelector(".ad-feedback-btn").addEventListener("click", () => {
      fbPanel.hidden = !fbPanel.hidden;
      if (!fbPanel.hidden) { fbMsg.innerHTML = ""; fbMsg.className = "ad-fb-msg"; fbText.focus(); }
    });
    bd.querySelector(".ad-fb-cancel").addEventListener("click", () => { fbPanel.hidden = true; });
    bd.querySelector(".ad-fb-submit").addEventListener("click", async () => {
      const Auth = window.LlmxiveAuth;
      const text = (fbText.value || "").trim();
      if (!text) { fbMsg.textContent = "Please enter some feedback."; fbMsg.className = "ad-fb-msg err"; return; }
      if (!Auth || !Auth.isSignedIn()) {
        fbMsg.textContent = "Sign in with GitHub to submit feedback.";
        fbMsg.className = "ad-fb-msg err";
        if (Auth) Auth.startLogin();
        return;
      }
      const btn = bd.querySelector(".ad-fb-submit");
      btn.disabled = true; fbMsg.textContent = "Submitting…"; fbMsg.className = "ad-fb-msg";
      try {
        const issue = await Auth.submitFeedback({
          target_id: _currentProject ? _currentProject.id : null,
          target_kind: _feedbackArtifactKind,
          target_stage: _currentProject ? _currentProject.current_stage : null,
          content: text,
        });
        // FR-013b: confirmation with a clickable issue link + "within the hour".
        fbMsg.innerHTML = 'Thanks — created <a href="' + escapeHtml(issue.html_url) + '" target="_blank" rel="noopener">issue #' + issue.number + '</a>. ' +
          'A maintenance agent will process it within the next hour.';
        fbMsg.className = "ad-fb-msg ok";
        fbText.value = "";
      } catch (err) {
        fbMsg.textContent = "Could not submit: " + (err && err.message ? err.message : String(err));
        fbMsg.className = "ad-fb-msg err";
      } finally {
        btn.disabled = false;
      }
    });
    return bd;
  }

  function close() {
    const bd = document.getElementById("ad-backdrop");
    if (bd) bd.classList.remove("open");
  }

  function _citationHTML(summary) {
    if (!summary) return "";
    const total = (summary.verified || 0) + (summary.mismatch || 0)
                + (summary.unreachable || 0) + (summary.pending || 0);
    if (!total) return '<div class="ad-citation"><span>No citations recorded.</span></div>';
    return ["verified", "mismatch", "unreachable", "pending"]
      .filter(s => summary[s])
      .map(s => '<div class="ad-citation"><span class="pill ' + s + '">' + s + '</span><span>' + summary[s] + '</span></div>')
      .join("");
  }

  function _runlogHTML(rows) {
    if (!rows || !rows.length) return '<div style="color:var(--muted); font-size:11px;">No run-log entries for this project yet.</div>';
    return '<div class="ad-runlog">' +
      rows.map(r => {
        const dur = (r.duration_s != null) ? r.duration_s.toFixed(1) + "s" : "—";
        const who = r.model || r.agent || "";
        const subAgent = (r.model && r.agent) ? r.agent : "";
        return '<div class="row">' +
          '<span class="ts">' + escapeHtml((r.ended_at || "").slice(0, 10)) + '</span>' +
          '<span class="agent">' + escapeHtml(who) +
          (subAgent ? ' <span class="role" style="color:var(--muted); font-size:10px;">(' + escapeHtml(subAgent) + ')</span>' : "") +
          '</span>' +
          '<span class="outcome ' + escapeHtml(r.outcome || "") + '">' + escapeHtml(r.outcome || "") + '</span>' +
          '<span class="dur" style="margin-left:auto;">' + escapeHtml(dur) + '</span>' +
          '</div>';
      }).join("") +
      '</div>';
  }

  function _artifactRow(label, icon, rel) {
    if (!rel) return "";
    return '<a class="ad-row" href="' + escapeHtml(blob(rel)) + '" target="_blank" rel="noopener">' +
      '<span class="ad-row-icon"><i class="fa-solid ' + icon + '"></i></span>' +
      '<span class="ad-row-label">' + escapeHtml(label) + '</span>' +
      '<span class="ad-row-meta">' + escapeHtml(rel) + '</span>' +
      '</a>';
  }

  function _authorsHTML(authors) {
    if (!authors || !authors.length) {
      return '<div style="color:var(--muted); font-size:11px;">No contributors recorded yet.</div>';
    }
    return authors.map(a => {
      const icon = a.kind === "human"
        ? '<i class="fa-regular fa-user"></i>'
        : (a.kind === "unattributed"
            ? '<i class="fa-regular fa-circle-question"></i>'
            : '<i class="fa-solid fa-robot"></i>');
      const roles = (a.roles || []).slice(0, 4).map(escapeHtml).join(", ");
      const moreRoles = (a.roles || []).length > 4 ? `, +${a.roles.length - 4} more` : "";
      return '<div class="ad-row" style="cursor:default;">' +
        '<span class="ad-row-icon">' + icon + '</span>' +
        '<span class="ad-row-label">' + escapeHtml(a.name) + ` <span style="color:var(--muted); font-size:10px;">(${a.contributions} contributions)</span></span>` +
        '<span class="ad-row-meta">' + roles + moreRoles + '</span>' +
        '</div>';
    }).join("");
  }

  // Spec-010 follow-up: render the per-project personality-review excerpts
  // that used to live inline on the card. Each `comments` entry has
  // `display_name`, `excerpt`, `review_path`, `ended_at` (see
  // _buildActivityByProject in app.js for the canonical shape).
  function _personalityReviewsHTML(comments) {
    if (!comments || !comments.length) {
      return '<div style="color:var(--muted); font-size:11px;">No personality reviews yet.</div>';
    }
    return comments.map(c => {
      const link = c.review_path
        ? ' <a class="comment-link" href="' + escapeHtml(c.review_path) +
          '" target="_blank" rel="noopener" title="open full review">' +
          '<i class="fa-regular fa-arrow-up-right-from-square"></i></a>'
        : "";
      return '<div class="comment">' +
        '<div class="comment-head">' +
        '<i class="fa-solid fa-quote-left"></i> ' +
        '<span class="comment-name">' + escapeHtml(c.display_name || "") + '</span>' +
        link +
        '</div>' +
        '<div class="comment-text">' + escapeHtml(c.excerpt || "(no excerpt)") + '</div>' +
        '</div>';
    }).join("");
  }

  function _renderListColumn(project, comments) {
    const links = project.artifact_links || {};
    const artifacts = ARTIFACT_ROWS
      .map(([key, icon, label]) => _artifactRow(label, icon, links[key]))
      .filter(Boolean).join("");
    return '' +
      '<h4>Artifacts</h4>' +
      (artifacts || '<div style="color:var(--muted); font-size:11px;">No artifacts produced yet.</div>') +
      '<h4>Personality reviews</h4>' +
      _personalityReviewsHTML(comments) +
      '<h4>Authors</h4>' +
      _authorsHTML(project.authors) +
      '<h4>Citations</h4>' +
      _citationHTML(project.citation_summary) +
      '<h4>Recent run-log</h4>' +
      _runlogHTML(project.last_run_log) +
      '<h4>Project state</h4>' +
      '<a class="ad-row" href="' + REPO_BASE + '/blob/main/state/projects/' + escapeHtml(project.id) + '.yaml" target="_blank" rel="noopener">' +
      '<span class="ad-row-icon"><i class="fa-solid fa-folder"></i></span>' +
      '<span class="ad-row-label">Project YAML</span>' +
      '<span class="ad-row-meta">state/projects/' + escapeHtml(project.id) + '.yaml</span>' +
      '</a>';
  }

  function _stageLabel(project) {
    return D.STAGE_LABELS[project.current_stage] || project.current_stage || "this stage";
  }

  // The "farthest along the pipeline" artifact to feature. Prefer the explicit
  // current_artifact block from web_data.py (E3); if the payload predates it
  // (e.g. a not-yet-redeployed projects.json), derive it from artifact_links
  // the same way web_data.py does — published PDF → LaTeX source → paper
  // tasks/plan/spec → research tasks/plan/spec → citations → idea — so the
  // modal still shows a real artifact instead of "none".
  const _MD_KEYS = ["paper_tasks", "paper_plan", "paper_spec", "tasks", "plan", "spec", "idea"];
  function _resolveArtifact(project) {
    const ca = project.current_artifact;
    if (ca && ca.type && ca.type !== "none") return ca;
    const links = project.artifact_links || {};
    const mk = (type, rel) => rel
      ? { type, repo_path: rel, github_url: blob(rel), raw_url: raw(rel) }
      : null;
    if (links.paper_pdf) return mk("pdf", links.paper_pdf);
    if (links.paper_source) return mk("latex", links.paper_source);
    for (const k of _MD_KEYS) { if (links[k]) return mk("markdown", links[k]); }
    if (links.citations) return mk("yaml", links.citations);
    return { type: "none", repo_path: null, github_url: null, raw_url: null };
  }

  // FR-009 / FR-009b: render whatever artifact best represents the project's
  // current state into the left pane — a published PDF, else the current-stage
  // text artifact (Markdown rendered, LaTeX/JSON/YAML shown as formatted
  // source), else a clear placeholder. NEVER an <embed> pointing at a PDF that
  // doesn't exist.
  function _renderArtifactPane(pdfEl, project) {
    pdfEl.replaceChildren();
    const ca = _resolveArtifact(project);
    const M = window.LlmxiveMarkdown;

    // Helper: a "view on GitHub" footer link.
    const ghLink = (url, label) => url
      ? '<div class="ad-art-foot"><a class="btn" href="' + escapeHtml(url) + '" target="_blank" rel="noopener">' +
        '<i class="fa-brands fa-github"></i> ' + (label || "View on GitHub") + '</a></div>'
      : "";

    if (ca.type === "pdf") {
      // raw.githubusercontent.com serves PDFs with Content-Disposition:
      // attachment + X-Frame-Options: deny, which forces a download and blocks
      // iframe embedding. The deploy workflow mirrors every project's PDFs
      // under <site>/papers/<project_id>/<name>.pdf where they're served from
      // the same origin with proper Content-Type: application/pdf — those can
      // be embedded inline.
      const repoPath = ca.repo_path
        || (project.artifact_links || {}).paper_pdf
        || "";
      const sameOriginUrl = _toSameOriginPdf(repoPath);
      const rawUrl = ca.raw_url || raw((project.artifact_links || {}).paper_pdf);
      // Prefer the same-origin mirror; fall back to the raw URL (link only,
      // no embed) when no mirror exists (older payload that predates the
      // pages.yml workflow change).
      const embedUrl = sameOriginUrl || rawUrl;
      pdfEl.insertAdjacentHTML("beforeend", '<embed type="application/pdf" src="' + escapeHtml(embedUrl) + '" />');
      setTimeout(() => {
        const embed = pdfEl.querySelector("embed");
        if (embed && !embed.clientHeight) {
          pdfEl.replaceChildren();
          pdfEl.insertAdjacentHTML("beforeend",
            '<div class="ad-pdf-empty"><div>PDF preview unavailable in this browser.<br/>' +
            '<a class="btn primary" style="margin-top:12px;" href="' + escapeHtml(rawUrl || embedUrl) + '" target="_blank" rel="noopener">' +
            '<i class="fa-solid fa-download"></i> Download PDF</a></div></div>');
        }
      }, 1500);
      return;
    }

    if (ca.type === "markdown" && ca.raw_url && M) {
      pdfEl.insertAdjacentHTML("beforeend",
        '<div class="ad-art-body md-body"><div class="ad-art-loading">Loading ' + escapeHtml(ca.repo_path || "artifact") + '…</div></div>'
        + ghLink(ca.github_url));
      // Use the `*Into` helper so Prism highlights fenced code blocks
      // (matches the agent-registry modal behaviour).
      const body = pdfEl.querySelector(".ad-art-body");
      M.fetchAndRenderMarkdownInto(body, ca.raw_url).catch(err => {
        if (body) {
          body.replaceChildren();
          body.insertAdjacentHTML("beforeend",
            '<div class="ad-pdf-empty">Could not load this artifact (' + escapeHtml(String(err.message || err)) + ').</div>');
        }
      });
      return;
    }

    if ((ca.type === "latex" || ca.type === "json" || ca.type === "yaml") && ca.raw_url) {
      pdfEl.insertAdjacentHTML("beforeend",
        '<div class="ad-art-body src-body"><pre class="ad-art-loading">Loading ' + escapeHtml(ca.repo_path || "source") + '…</pre></div>'
        + ghLink(ca.github_url));
      fetch(ca.raw_url, { cache: "no-cache" }).then(r => {
        if (!r.ok) throw new Error("HTTP " + r.status);
        return r.text();
      }).then(text => {
        const body = pdfEl.querySelector(".ad-art-body");
        if (body) {
          const pre = document.createElement("pre");
          pre.className = "ad-art-src";
          pre.textContent = text;          // textContent — no HTML injection
          body.replaceChildren(pre);
        }
      }).catch(err => {
        const body = pdfEl.querySelector(".ad-art-body");
        if (body) body.innerHTML = '<div class="ad-pdf-empty">Could not load this source (' + escapeHtml(String(err.message || err)) + ').</div>';
      });
      return;
    }

    // type === "none" (or markdown with no renderer / no raw_url): placeholder
    // that uses the space — what stage we're at, what's coming, and a GitHub link.
    pdfEl.insertAdjacentHTML("beforeend",
      '<div class="ad-pdf-empty"><div>' +
      '<i class="fa-regular fa-file" style="font-size:32px;opacity:.4;display:block;margin-bottom:12px;"></i>' +
      'No artifact to preview yet — this project is at the <strong>' + escapeHtml(_stageLabel(project)) + '</strong> stage.<br/>' +
      'The next artifact will appear here. Meanwhile, the artifact list on the right links to everything produced so far.' +
      '<div style="margin-top:14px;"><a class="btn" href="https://github.com/ContextLab/llmXive/tree/main/projects/' + escapeHtml(project.id) + '" target="_blank" rel="noopener">' +
      '<i class="fa-brands fa-github"></i> Browse this project on GitHub</a></div>' +
      '</div></div>');
  }

  function open(project, opts) {
    const bd = _ensureMount();
    _currentProject = project;
    const ca = _resolveArtifact(project);
    _feedbackArtifactKind = ca.type === "none" ? "project" : ca.type;
    bd.querySelector(".ad-title").textContent = project.title || project.id;
    bd.querySelector(".ad-stage-badge").textContent = (D.STAGE_LABELS[project.current_stage] || project.current_stage || "");
    // Reset the feedback panel for the new project.
    const fbPanel = bd.querySelector(".ad-feedback");
    if (fbPanel) {
      fbPanel.hidden = true;
      const fbText = bd.querySelector(".ad-fb-text"); if (fbText) fbText.value = "";
      const fbMsg = bd.querySelector(".ad-fb-msg"); if (fbMsg) { fbMsg.textContent = ""; fbMsg.className = "ad-fb-msg"; }
    }
    const list = bd.querySelector(".ad-list");
    list.replaceChildren();
    // Spec-010 follow-up: caller passes the per-project personality-review
    // comments derived from payload.recent_activity. dialog.js itself does
    // not own the payload, so the comments arrive via opts.comments.
    const comments = (opts && opts.comments) || [];
    list.insertAdjacentHTML("beforeend", _renderListColumn(project, comments));

    _renderArtifactPane(bd.querySelector(".ad-pdf"), project);

    bd.classList.add("open");
  }

  window.LlmxiveDialog = { open, close };
})();
