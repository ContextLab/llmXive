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

  const ARTIFACT_ROWS = [
    ["idea",            "fa-lightbulb",        "Idea"],
    ["spec",            "fa-file-lines",       "Research spec"],
    ["plan",            "fa-rectangle-list",   "Research plan"],
    ["tasks",           "fa-list-check",       "Research tasks"],
    ["code",            "fa-code",             "Code"],
    ["data",            "fa-database",         "Data"],
    ["paper_spec",      "fa-newspaper",        "Paper spec"],
    ["paper_plan",      "fa-rectangle-list",   "Paper plan"],
    ["paper_tasks",     "fa-list-check",       "Paper tasks"],
    ["paper_source",    "fa-file-code",        "LaTeX source"],
    ["paper_figures",   "fa-image",            "Figures"],
    ["paper_pdf",       "fa-file-pdf",         "Paper PDF"],
    ["reviews_research","fa-magnifying-glass", "Research reviews"],
    ["reviews_paper",   "fa-magnifying-glass-plus", "Paper reviews"],
    ["citations",       "fa-quote-left",       "Citations"],
  ];

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
      + '<button class="ad-close" aria-label="close"><i class="fa-solid fa-xmark"></i> Close</button>'
      + '</div>'
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

  function _renderListColumn(project) {
    const links = project.artifact_links || {};
    const artifacts = ARTIFACT_ROWS
      .map(([key, icon, label]) => _artifactRow(label, icon, links[key]))
      .filter(Boolean).join("");
    return '' +
      '<h4>Artifacts</h4>' +
      (artifacts || '<div style="color:var(--muted); font-size:11px;">No artifacts produced yet.</div>') +
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

  // FR-009 / FR-009b: render whatever artifact best represents the project's
  // current state into the left pane — a published PDF, else the current-stage
  // text artifact (Markdown rendered, LaTeX/JSON/YAML shown as formatted
  // source), else a clear placeholder. NEVER an <embed> pointing at a PDF that
  // doesn't exist.
  function _renderArtifactPane(pdfEl, project) {
    pdfEl.replaceChildren();
    const ca = project.current_artifact || { type: "none" };
    const M = window.LlmxiveMarkdown;

    // Helper: a "view on GitHub" footer link.
    const ghLink = (url, label) => url
      ? '<div class="ad-art-foot"><a class="btn" href="' + escapeHtml(url) + '" target="_blank" rel="noopener">' +
        '<i class="fa-brands fa-github"></i> ' + (label || "View on GitHub") + '</a></div>'
      : "";

    if (ca.type === "pdf") {
      // Prefer the explicit current_artifact.raw_url; fall back to the legacy
      // artifact_links.paper_pdf for older payloads.
      const pdfUrl = ca.raw_url || raw((project.artifact_links || {}).paper_pdf);
      pdfEl.insertAdjacentHTML("beforeend", '<embed type="application/pdf" src="' + escapeHtml(pdfUrl) + '" />');
      setTimeout(() => {
        const embed = pdfEl.querySelector("embed");
        if (embed && !embed.clientHeight) {
          pdfEl.replaceChildren();
          pdfEl.insertAdjacentHTML("beforeend",
            '<div class="ad-pdf-empty"><div>PDF preview unavailable in this browser.<br/>' +
            '<a class="btn primary" style="margin-top:12px;" href="' + escapeHtml(pdfUrl) + '" target="_blank" rel="noopener">' +
            '<i class="fa-solid fa-download"></i> Download PDF</a></div></div>');
        }
      }, 1500);
      return;
    }

    if (ca.type === "markdown" && ca.raw_url && M) {
      pdfEl.insertAdjacentHTML("beforeend",
        '<div class="ad-art-body md-body"><div class="ad-art-loading">Loading ' + escapeHtml(ca.repo_path || "artifact") + '…</div></div>'
        + ghLink(ca.github_url));
      M.fetchAndRenderMarkdown(ca.raw_url).then(html => {
        const body = pdfEl.querySelector(".ad-art-body");
        if (body) body.innerHTML = html;
      }).catch(err => {
        const body = pdfEl.querySelector(".ad-art-body");
        if (body) body.innerHTML = '<div class="ad-pdf-empty">Could not load this artifact (' + escapeHtml(String(err.message || err)) + ').</div>';
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

  function open(project) {
    const bd = _ensureMount();
    bd.querySelector(".ad-title").textContent = project.title || project.id;
    bd.querySelector(".ad-stage-badge").textContent = (D.STAGE_LABELS[project.current_stage] || project.current_stage || "");
    const list = bd.querySelector(".ad-list");
    list.replaceChildren();
    list.insertAdjacentHTML("beforeend", _renderListColumn(project));

    _renderArtifactPane(bd.querySelector(".ad-pdf"), project);

    bd.classList.add("open");
  }

  window.LlmxiveDialog = { open, close };
})();
