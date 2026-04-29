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
        return '<div class="row">' +
          '<span class="ts">' + escapeHtml((r.ended_at || "").slice(0, 10)) + '</span>' +
          '<span class="agent">' + escapeHtml(r.agent || "") + '</span>' +
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

  function _renderListColumn(project) {
    const links = project.artifact_links || {};
    const artifacts = ARTIFACT_ROWS
      .map(([key, icon, label]) => _artifactRow(label, icon, links[key]))
      .filter(Boolean).join("");
    return '' +
      '<h4>Artifacts</h4>' +
      (artifacts || '<div style="color:var(--muted); font-size:11px;">No artifacts produced yet.</div>') +
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

  function open(project) {
    const bd = _ensureMount();
    bd.querySelector(".ad-title").textContent = project.title || project.id;
    bd.querySelector(".ad-stage-badge").textContent = (D.STAGE_LABELS[project.current_stage] || project.current_stage || "");
    const list = bd.querySelector(".ad-list");
    list.replaceChildren();
    list.insertAdjacentHTML("beforeend", _renderListColumn(project));

    const pdfEl = bd.querySelector(".ad-pdf");
    pdfEl.replaceChildren();
    const pdfRel = (project.artifact_links || {}).paper_pdf;
    if (pdfRel) {
      const pdfUrl = raw(pdfRel);
      pdfEl.insertAdjacentHTML("beforeend", '<embed type="application/pdf" src="' + escapeHtml(pdfUrl) + '" />');
      setTimeout(() => {
        const embed = pdfEl.querySelector("embed");
        if (embed && !embed.clientHeight) {
          pdfEl.replaceChildren();
          const fallback = '<div class="ad-pdf-empty"><div>' +
            'PDF preview unavailable in this browser.<br/>' +
            '<a class="btn primary" style="margin-top:12px;" href="' + escapeHtml(pdfUrl) + '" target="_blank" rel="noopener">' +
            '<i class="fa-solid fa-download"></i> Download PDF</a>' +
            '</div></div>';
          pdfEl.insertAdjacentHTML("beforeend", fallback);
        }
      }, 1500);
    } else {
      pdfEl.insertAdjacentHTML("beforeend", '<div class="ad-pdf-empty">No PDF compiled yet for this project.</div>');
    }

    bd.classList.add("open");
  }

  window.LlmxiveDialog = { open, close };
})();
