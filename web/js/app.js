// llmXive — main app. Wires data + UI + auth + dialog.
// All interpolated values are passed through escapeHtml() before insertion.

(function () {
  const D = window.LlmxiveData;
  const Auth = window.LlmxiveAuth;
  const Dialog = window.LlmxiveDialog;

  let payload = null;
  let buckets = null;
  let lanes = null;

  function banner(kind, msg) {
    const root = document.getElementById("banners");
    if (!root) return;
    const div = document.createElement("div");
    div.className = "shell banner " + (kind || "");
    const html =
      '<i class="fa-solid fa-circle-info"></i> ' + msg + ' ' +
      '<span class="x" title="dismiss"><i class="fa-solid fa-xmark"></i></span>';
    div.insertAdjacentHTML("beforeend", html);
    div.querySelector(".x").addEventListener("click", () => div.remove());
    root.appendChild(div);
  }

  function renderAggregates(p) {
    const agg = (p && p.aggregates) || {};
    document.querySelectorAll("[data-agg]").forEach(el => {
      const k = el.getAttribute("data-agg");
      const v = agg[k];
      el.textContent = (v === undefined || v === null) ? "—" : String(v);
    });
  }

  function escapeHtml(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
  }

  // Authoritative model-vs-human-vs-unattributed icon, by `kind` from the data
  // (NEVER regex-guessed from the name — FR-007). For a bare submitter string
  // with no `kind`, look it up in the contributors list.
  function kindOf(name) {
    if (!name || !payload) return null;
    const c = (payload.contributors || []).find(c => c.name === name);
    return c ? c.kind : null;
  }
  function kindIcon(kind) {
    if (kind === "human") return '<i class="fa-regular fa-user"></i>';
    if (kind === "llm") return '<i class="fa-solid fa-robot"></i>';
    return '<i class="fa-regular fa-circle-question" title="contributor not attributed"></i>';
  }

  function cardHTML(item, kind) {
    const kicker = ({
      papers:    "Published",
      paper:     "Paper pipeline",
      inProgress:"Research in progress",
      plans:     "Research plan",
      designs:   "Research spec",
    })[kind] || "";
    const stage = item.current_stage || "";
    const stageLabel = (D.STAGE_LABELS[stage] || stage).toLowerCase();
    const updated = D.relativeTime(item.updated_at);
    const points =
      kind === "papers" || kind === "paper"
        ? '<span><i class="fa-solid fa-star-half-stroke"></i> ' + (item.points_paper_total || 0).toFixed(1) + ' pts</span>'
        : '<span><i class="fa-solid fa-star-half-stroke"></i> ' + (item.points_research_total || 0).toFixed(1) + ' pts</span>';
    const keys = (item.keywords || []).slice(0, 4)
      .map(k => '<span>' + escapeHtml(k) + '</span>').join("");
    const desc = item.description || item.field || "";
    const authors = item.authors || [];
    const authorPills = authors.slice(0, 3).map(a =>
      '<span class="submitter">' + kindIcon(a.kind) + ' ' + escapeHtml(a.name) + '</span>'
    ).join(" ");
    const more = authors.length > 3 ? ` <span class="submitter-more">+${authors.length - 3} more</span>` : "";
    const authorsRow = authors.length
      ? '<div class="submitter-row">authors ' + authorPills + more + '</div>'
      : (item.submitter
          ? '<div class="submitter-row">submitted by <span class="submitter">'
            + kindIcon(kindOf(item.submitter))
            + ' ' + escapeHtml(item.submitter) + '</span></div>'
          : "");
    return ''
      + '<article class="card" tabindex="0" data-pid="' + escapeHtml(item.id) + '">'
      + '<div class="kicker"><span class="dot"></span>' + kicker + '<span class="stage-pill ' + escapeHtml(stage) + '" style="margin-left:auto">' + escapeHtml(stageLabel) + '</span></div>'
      + '<h3>' + escapeHtml(item.title) + '</h3>'
      + '<p class="desc">' + escapeHtml(desc) + '</p>'
      + '<div class="meta">'
      + '<div class="keys">' + keys + '</div>'
      + '<div class="right">' + points + '<span><i class="fa-regular fa-clock"></i> ' + escapeHtml(updated) + '</span></div>'
      + '</div>'
      + authorsRow
      + '</article>';
  }

  function renderCards(kind) {
    const el = document.getElementById(kind + "-cards");
    if (!el) return;
    const items = (buckets && buckets[kind]) || [];
    if (!items.length) {
      el.replaceChildren();
      const empty = document.createElement("div");
      empty.style.cssText = "grid-column: 1/-1; text-align:center; padding:40px; color:var(--muted);";
      empty.insertAdjacentHTML("beforeend",
        '<i class="fa-regular fa-folder-open" style="font-size:32px; opacity:0.5"></i>' +
        '<p style="margin-top:12px;">No projects in this stage yet.</p>');
      el.appendChild(empty);
      return;
    }
    el.replaceChildren();
    el.insertAdjacentHTML("beforeend", items.map(it => cardHTML(it, kind)).join(""));
    el.querySelectorAll(".card").forEach(card => {
      card.addEventListener("click", () => {
        const pid = card.getAttribute("data-pid");
        const proj = (payload.projects || []).find(p => p.id === pid);
        if (proj) Dialog.open(proj);
      });
      card.addEventListener("keydown", e => {
        if (e.key === "Enter" || e.key === " ") { e.preventDefault(); card.click(); }
      });
    });
  }

  function renderTabCounts() {
    Object.entries(buckets).forEach(([k, items]) => {
      const el = document.querySelector('[data-count="' + k + '"]');
      if (el) el.textContent = items.length;
    });
  }

  function renderBacklogLane(rootEl, lane, stages) {
    const html = stages.map(stage => {
      const items = lane[stage] || [];
      const label = D.STAGE_LABELS[stage] || stage;
      const issues = items.map(p => {
        const desc = (p.description || "").slice(0, 140) + ((p.description || "").length > 140 ? "…" : "");
        return ''
          + '<div class="issue" data-pid="' + escapeHtml(p.id) + '">'
          + '<div class="title">' + escapeHtml(p.title) + '</div>'
          + (desc ? '<div class="issue-desc">' + escapeHtml(desc) + '</div>' : "")
          + '<div class="row"><span>' + escapeHtml(p.field || "") + '</span>'
          + '<span class="upv"><i class="fa-solid fa-arrow-up"></i> ' + (p.points_research_total || 0).toFixed(1) + '</span></div>'
          + '</div>';
      }).join("");
      return ''
        + '<div class="col" data-stage="' + escapeHtml(stage) + '">'
        + '<div class="col-head"><span class="name"><span class="dot"></span>' + escapeHtml(label) + '</span>'
        + '<span class="count">' + items.length + '</span></div>'
        + '<div class="col-body">' + issues + '</div></div>';
    }).join("");
    rootEl.replaceChildren();
    rootEl.insertAdjacentHTML("beforeend", html);
    rootEl.querySelectorAll(".issue").forEach(iss => {
      iss.addEventListener("click", () => {
        const pid = iss.getAttribute("data-pid");
        const proj = (payload.projects || []).find(p => p.id === pid);
        if (proj) Dialog.open(proj);
      });
    });
  }

  function renderBacklog() {
    renderBacklogLane(document.getElementById("backlog-research"), lanes.research, D.RESEARCH_LANE_STAGES);
    renderBacklogLane(document.getElementById("backlog-paper"), lanes.paper, D.PAPER_LANE_STAGES);
  }

  // Authoritative kind → display label / table icon-class (FR-007).
  function kindLabel(kind) {
    if (kind === "human") return "Human";
    if (kind === "llm") return "AI model";
    return "Unattributed";
  }
  function kindTableIcon(kind) {
    if (kind === "human") return "fa-regular fa-user";
    if (kind === "llm") return "fa-solid fa-robot";
    return "fa-regular fa-circle-question";
  }

  function renderContributors() {
    // The data is already sorted (real contributors by count desc, the single
    // "unattributed" bucket last); keep that order. Rank only real contributors.
    const list = (payload.contributors || []).slice();
    list.forEach((c, i) => c.rank = i + 1);
    const ranked = list.filter(c => c.kind !== "unattributed");

    const podium = document.getElementById("podium");
    podium.replaceChildren();
    if (!ranked.length) {
      podium.insertAdjacentHTML("beforeend",
        '<div style="grid-column: 1/-1; text-align:center; padding:40px; color:var(--muted);">No contributors yet.</div>');
    } else {
      const top3 = ranked.slice(0, 3);
      const podiumOrder = [top3[1], top3[0], top3[2]];
      const html = podiumOrder.map((c) => {
        if (!c) return "";
        const isFirst = c.rank === 1;
        const initials = c.name.split(/[-.]/).map(s => s[0]).join("").slice(0, 2).toUpperCase();
        return ''
          + '<div class="pod ' + (isFirst ? "first" : "") + '">'
          + '<div class="rank">' + c.rank + '</div>'
          + '<div class="avatar">' + escapeHtml(initials || "?") + '</div>'
          + '<div class="name">' + escapeHtml(c.name) + '</div>'
          + '<div class="type">' + escapeHtml(kindLabel(c.kind)) + '</div>'
          + '<div class="n">' + c.contribution_count + '<small>contributions</small></div>'
          + '</div>';
      }).join("");
      podium.insertAdjacentHTML("beforeend", html);
    }

    const table = document.getElementById("contrib-table");
    [...table.querySelectorAll(".tr:not(.head)")].forEach(n => n.remove());
    const rowsHtml = list.map(c => ''
      + '<div class="tr' + (c.kind === "unattributed" ? " unattributed" : "") + '">'
      + '<div>' + (c.kind === "unattributed" ? "—" : c.rank) + '</div>'
      + '<div>' + escapeHtml(c.kind === "unattributed" ? "Unattributed contributions" : c.name) + '</div>'
      + '<div class="ttype"><i class="' + kindTableIcon(c.kind) + '"></i> ' + escapeHtml(kindLabel(c.kind)) + '</div>'
      + '<div>' + c.contribution_count + '</div>'
      + '<div class="areas">' + (c.areas || []).map(a => '<span>' + escapeHtml(a) + '</span>').join("") + '</div>'
      + '</div>').join("");
    table.insertAdjacentHTML("beforeend", rowsHtml);
  }

  function setupTabs() {
    const tabs = [...document.querySelectorAll(".tab")];
    const underline = document.getElementById("underline");
    const tabsRow = underline ? underline.parentElement : null;

    // FR-002: position the underline from getBoundingClientRect() of the active
    // tab *relative to its container* — correct even when .tabs-row has scrolled
    // horizontally (mobile), and recomputed on resize / rotate / web-font load
    // (all of which shift tab widths). The old offsetLeft approach assumed the
    // underline's containing block was .tabs-row, but .tabs (position:sticky)
    // was the actual containing block, so it drifted.
    function positionUnderline() {
      if (!underline || !tabsRow) return;
      const active = tabs.find(t => t.classList.contains("active"));
      if (!active) return;
      const rowRect = tabsRow.getBoundingClientRect();
      const tabRect = active.getBoundingClientRect();
      // Add the row's own scrollLeft back: getBoundingClientRect is viewport-
      // relative, so (tabRect.left - rowRect.left) is the visible offset; the
      // underline lives in the scrollable content, so add scrollLeft.
      underline.style.left = (tabRect.left - rowRect.left + tabsRow.scrollLeft) + "px";
      underline.style.width = tabRect.width + "px";
    }

    function activate(name, tab) {
      tabs.forEach(t => t.classList.toggle("active", t === tab));
      document.querySelectorAll(".panel").forEach(p => {
        p.classList.toggle("active", p.dataset.panel === name);
      });
      positionUnderline();
      history.replaceState(null, "", "#" + name);
    }
    tabs.forEach(t => t.addEventListener("click", () => activate(t.dataset.tab, t)));

    function init() {
      const initial = (location.hash || "#papers").slice(1);
      const tab = tabs.find(t => t.dataset.tab === initial) || tabs[0];
      activate(tab.dataset.tab, tab);
    }
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(init); else init();
    // Recompute on font load (widths change once the web font swaps in).
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(positionUnderline);

    // rAF-debounced resize + orientationchange.
    let rafPending = false;
    function scheduleReposition() {
      if (rafPending) return;
      rafPending = true;
      requestAnimationFrame(() => { rafPending = false; positionUnderline(); });
    }
    window.addEventListener("resize", scheduleReposition);
    window.addEventListener("orientationchange", scheduleReposition);
    // The tabs row scrolls horizontally on mobile — keep the underline aligned.
    if (tabsRow) tabsRow.addEventListener("scroll", scheduleReposition, { passive: true });

    document.querySelectorAll(".bar").forEach(bar => {
      bar.addEventListener("click", e => {
        const chip = e.target.closest(".chip");
        if (!chip) return;
        bar.querySelectorAll(".chip").forEach(c => c.classList.remove("active"));
        chip.classList.add("active");
      });
    });

    document.addEventListener("keydown", e => {
      if (!["ArrowLeft", "ArrowRight"].includes(e.key)) return;
      if (document.activeElement.tagName === "INPUT" || document.activeElement.tagName === "TEXTAREA") return;
      const idx = tabs.findIndex(t => t.classList.contains("active"));
      const next = e.key === "ArrowRight" ? (idx + 1) % tabs.length : (idx - 1 + tabs.length) % tabs.length;
      tabs[next].click();
      tabs[next].focus();
    });
  }

  function setupModals() {
    document.querySelectorAll("[data-open-modal]").forEach(b => {
      b.addEventListener("click", () => {
        const id = "modal-" + b.dataset.openModal;
        document.getElementById(id)?.classList.add("open");
      });
    });
    document.querySelectorAll(".modal-backdrop").forEach(bd => {
      bd.addEventListener("click", e => {
        if (e.target === bd || e.target.closest("[data-close-modal]")) {
          bd.classList.remove("open");
        }
      });
    });
    document.addEventListener("keydown", e => {
      if (e.key === "Escape") document.querySelectorAll(".modal-backdrop.open").forEach(m => m.classList.remove("open"));
    });

    document.getElementById("submit-idea-btn").addEventListener("click", async () => {
      const title = document.querySelector("[data-submit='title']").value.trim();
      const field = document.querySelector("[data-submit='field']").value.trim();
      const desc  = document.querySelector("[data-submit='description']").value.trim();
      const kw    = document.querySelector("[data-submit='keywords']").value.trim();
      if (!title || !field || !desc) {
        banner("warn", "Title, field, and description are required.");
        return;
      }
      if (!Auth.isSignedIn()) {
        banner("warn", "Please sign in with GitHub to submit an idea.");
        Auth.startLogin();
        return;
      }
      try {
        const issue = await Auth.submitIdea({ title, field, description: desc, keywords: kw });
        document.getElementById("modal-submit").classList.remove("open");
        const safeUrl = escapeHtml(issue.html_url);
        banner("info", 'Idea submitted as <a href="' + safeUrl + '" target="_blank" rel="noopener">issue #' + issue.number + '</a>.');
      } catch (err) {
        banner("error", "Could not submit idea: " + escapeHtml(String(err.message || err)));
      }
    });

    document.getElementById("submit-review-btn").addEventListener("click", async () => {
      const pid = document.getElementById("review-project-id").value;
      const stage = document.querySelector("[data-review='stage']").value;
      const verdict = document.querySelector("[data-review='verdict']").value;
      const summary = document.querySelector("[data-review='summary']").value.trim();
      const strengths = document.querySelector("[data-review='strengths']").value.trim();
      const concerns = document.querySelector("[data-review='concerns']").value.trim();
      if (!pid || !summary) {
        banner("warn", "Pick a project and provide a summary.");
        return;
      }
      if (!Auth.isSignedIn()) { Auth.startLogin(); return; }
      try {
        await Auth.submitReview({ project_id: pid, stage, verdict, summary, strengths, concerns });
        document.getElementById("modal-review").classList.remove("open");
        banner("info", "Review submitted for " + escapeHtml(pid) + ".");
      } catch (err) {
        banner("error", "Could not submit review: " + escapeHtml(String(err.message || err)));
      }
    });
  }

  // ── About-page modals: pipeline-step (FR-003) + agent-registry (FR-004) ──
  //
  // A single generic modal element (#about-modal) that we fill with either a
  // pipeline-step's details or the agent registry / one agent's prompt. Content
  // comes from web/data/projects.json's pipeline_steps[] and agents[] blocks
  // (built from agents/registry.yaml + the stage definitions — Constitution I).
  function _ensureAboutModal() {
    let bd = document.getElementById("about-modal");
    if (bd) return bd;
    bd = document.createElement("div");
    bd.id = "about-modal";
    bd.className = "modal-backdrop about-modal-backdrop";
    bd.innerHTML =
      '<div class="modal about-modal" role="dialog" aria-modal="true">' +
      '<div class="am-head"><h2 class="am-title">—</h2>' +
      '<button class="am-close" data-close-modal aria-label="close"><i class="fa-solid fa-xmark"></i> Close</button></div>' +
      '<div class="am-body"></div></div>';
    document.body.appendChild(bd);
    bd.addEventListener("click", e => {
      if (e.target === bd || e.target.closest("[data-close-modal]")) bd.classList.remove("open");
    });
    document.addEventListener("keydown", e => {
      if (e.key === "Escape" && bd.classList.contains("open")) bd.classList.remove("open");
    });
    return bd;
  }

  function _openAboutModal(title, bodyHtml) {
    const bd = _ensureAboutModal();
    bd.querySelector(".am-title").textContent = title;
    const body = bd.querySelector(".am-body");
    body.innerHTML = bodyHtml;
    bd.classList.add("open");
    body.scrollTop = 0;
    return body;
  }

  function _agentByName(name) {
    return (payload.agents || []).find(a => a.name === name) || null;
  }

  function _renderMd(raw) {
    const M = window.LlmxiveMarkdown;
    return M ? M.renderMarkdown(raw) : escapeHtml(String(raw == null ? "" : raw));
  }

  function _pipelineStepHtml(step) {
    const list = arr => (arr && arr.length)
      ? '<ul>' + arr.map(x => '<li>' + _renderMd(x) + '</li>').join("") + '</ul>'
      : '<p class="muted">—</p>';
    const agentItems = (step.agents || []).map(name => {
      const a = _agentByName(name);
      return '<button class="am-agent-chip" data-agent="' + escapeHtml(name) + '"' + (a ? "" : " disabled") + '>' +
        '<i class="fa-solid fa-robot"></i> ' + escapeHtml(name) + '</button>';
    }).join(" ");
    const examples = (step.example_artifacts || []).length
      ? '<ul class="am-examples">' + step.example_artifacts.map(ex =>
          '<li><a href="' + escapeHtml(ex.github_url) + '" target="_blank" rel="noopener">' +
          escapeHtml(ex.title || ex.project_id) + '</a> <span class="muted">(' + escapeHtml(ex.project_id) + ')</span></li>'
        ).join("") + '</ul>'
      : '<p class="muted">No example artifacts yet.</p>';
    return '' +
      '<div class="am-section"><div class="am-desc md-body">' + _renderMd(step.description) + '</div></div>' +
      '<div class="am-cols">' +
        '<div class="am-section"><h3>Inputs</h3>' + list(step.inputs) + '</div>' +
        '<div class="am-section"><h3>Outputs</h3>' + list(step.outputs) + '</div>' +
      '</div>' +
      '<div class="am-section"><h3>Agents this step uses</h3>' +
        '<div class="am-agents">' + (agentItems || '<span class="muted">—</span>') + '</div>' +
        '<p class="muted am-hint">Click an agent to see its prompt &amp; tools.</p></div>' +
      '<div class="am-section"><h3>Recent example artifacts</h3>' + examples + '</div>';
  }

  function _agentDetailHtml(a) {
    const tools = (a.tools || []).length
      ? a.tools.map(t => '<span class="am-tool">' + escapeHtml(t) + '</span>').join(" ")
      : '<span class="muted">no extra tools</span>';
    return '' +
      '<div class="am-section am-agent-meta">' +
        '<p>' + escapeHtml(a.purpose || "") + '</p>' +
        '<div class="am-kv"><span>tools</span><div>' + tools + '</div></div>' +
        '<div class="am-kv"><span>backend</span><div>' + escapeHtml(a.default_backend || "—") + '</div></div>' +
        '<div class="am-kv"><span>model</span><div>' + escapeHtml(a.default_model || "—") + '</div></div>' +
        '<div class="am-links">' +
          (a.prompt_github_url ? '<a class="btn" href="' + escapeHtml(a.prompt_github_url) + '" target="_blank" rel="noopener"><i class="fa-brands fa-github"></i> View prompt on GitHub</a>' : '') +
          '<a class="btn" href="https://github.com/ContextLab/llmXive/blob/main/agents/registry.yaml" target="_blank" rel="noopener"><i class="fa-solid fa-list"></i> registry.yaml</a>' +
          '<button class="btn" data-agents-back><i class="fa-solid fa-arrow-left"></i> All agents</button>' +
        '</div></div>' +
      '<div class="am-section"><h3>Prompt</h3><div class="am-prompt md-body"><div class="ad-art-loading">Loading prompt…</div></div></div>';
  }

  function openAgentDetail(name) {
    const a = _agentByName(name);
    if (!a) return;
    const body = _openAboutModal("Agent · " + name, _agentDetailHtml(a));
    body.querySelector("[data-agents-back]")?.addEventListener("click", openAgentRegistry);
    const promptEl = body.querySelector(".am-prompt");
    const M = window.LlmxiveMarkdown;
    if (a.prompt_raw_url && M) {
      M.fetchAndRenderMarkdown(a.prompt_raw_url).then(html => { if (promptEl) promptEl.innerHTML = html; })
        .catch(err => { if (promptEl) promptEl.innerHTML = '<p class="muted">Could not load the prompt (' + escapeHtml(String(err.message || err)) + ').</p>'; });
    } else if (promptEl) {
      promptEl.innerHTML = '<p class="muted">No prompt available.</p>';
    }
  }

  function openAgentRegistry() {
    const agents = (payload.agents || []).slice().sort((x, y) => x.name.localeCompare(y.name));
    const intro = '<div class="am-section"><p>' + agents.length + ' agents drive the two Spec-Kit pipelines. Click one for its prompt and tools.</p>' +
      '<a class="btn" href="https://github.com/ContextLab/llmXive/blob/main/agents/registry.yaml" target="_blank" rel="noopener"><i class="fa-brands fa-github"></i> View agents/registry.yaml on GitHub</a></div>';
    const rows = agents.map(a =>
      '<button class="am-agent-row" data-agent="' + escapeHtml(a.name) + '">' +
        '<span class="ar-name">' + escapeHtml(a.name) + '</span>' +
        '<span class="ar-purpose">' + escapeHtml(a.purpose || "") + '</span>' +
        '<span class="ar-go"><i class="fa-solid fa-chevron-right"></i></span>' +
      '</button>').join("");
    _openAboutModal("Agent registry", intro + '<div class="am-agent-list">' + rows + '</div>');
  }

  function setupAboutModals() {
    // Pipeline-diagram circles → step modal.
    document.querySelectorAll(".pipeline .stage[data-step]").forEach(el => {
      el.addEventListener("click", () => {
        const key = el.dataset.step;
        const step = (payload.pipeline_steps || []).find(s => s.key === key);
        if (!step) return;
        _openAboutModal(step.name, _pipelineStepHtml(step));
      });
    });
    // "Agent registry" triggers (footer button + the About-page button).
    document.querySelectorAll('[data-open-modal="agents"]').forEach(b => {
      b.addEventListener("click", openAgentRegistry);
    });
    // Delegated: any [data-agent] (an agent chip in a step modal, or a row in
    // the registry list) opens that agent's detail view.
    document.addEventListener("click", e => {
      const t = e.target.closest("[data-agent]");
      if (t && !t.hasAttribute("disabled")) openAgentDetail(t.dataset.agent);
    });
  }

  async function boot() {
    Auth.mount(document.getElementById("auth-slot"));
    await Auth.handleCallback();

    payload = await D.loadPayload();
    if (payload._loadError) {
      banner("warn", "Pipeline state not yet generated. The site will be empty until the pipeline writes <code>web/data/projects.json</code>.");
    }
    buckets = D.projectsByTab(payload);
    lanes = D.projectsByLaneStage(payload);

    renderAggregates(payload);
    renderTabCounts();
    ["papers", "paper", "inProgress", "plans", "designs"].forEach(renderCards);
    renderBacklog();
    renderContributors();

    setupTabs();
    setupModals();
    setupAboutModals();

    window._llmxive = { payload, buckets, lanes };
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else { boot(); }
})();
