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
    return ''
      + '<article class="card" tabindex="0" data-pid="' + escapeHtml(item.id) + '">'
      + '<div class="kicker"><span class="dot"></span>' + kicker + '<span class="stage-pill ' + escapeHtml(stage) + '" style="margin-left:auto">' + escapeHtml(stageLabel) + '</span></div>'
      + '<h3>' + escapeHtml(item.title) + '</h3>'
      + '<p class="desc">' + escapeHtml(item.field || "") + '</p>'
      + '<div class="meta">'
      + '<div class="keys">' + keys + '</div>'
      + '<div class="right">' + points + '<span><i class="fa-regular fa-clock"></i> ' + escapeHtml(updated) + '</span></div>'
      + '</div></article>';
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
      const issues = items.map(p => ''
        + '<div class="issue" data-pid="' + escapeHtml(p.id) + '">'
        + '<div class="title">' + escapeHtml(p.title) + '</div>'
        + '<div class="row"><span>' + escapeHtml(p.field || "") + '</span>'
        + '<span class="upv"><i class="fa-solid fa-arrow-up"></i> ' + (p.points_research_total || 0).toFixed(1) + '</span></div>'
        + '</div>').join("");
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

  function renderContributors() {
    const list = (payload.contributors || []).slice();
    list.sort((a, b) => b.contribution_count - a.contribution_count);
    list.forEach((c, i) => c.rank = i + 1);

    const podium = document.getElementById("podium");
    podium.replaceChildren();
    if (!list.length) {
      podium.insertAdjacentHTML("beforeend",
        '<div style="grid-column: 1/-1; text-align:center; padding:40px; color:var(--muted);">No contributors yet.</div>');
    } else {
      const top3 = list.slice(0, 3);
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
          + '<div class="type">' + escapeHtml(c.kind === "human" ? "Human" : "AI") + '</div>'
          + '<div class="n">' + c.contribution_count + '<small>contributions</small></div>'
          + '</div>';
      }).join("");
      podium.insertAdjacentHTML("beforeend", html);
    }

    const table = document.getElementById("contrib-table");
    [...table.querySelectorAll(".tr:not(.head)")].forEach(n => n.remove());
    const rowsHtml = list.map(c => ''
      + '<div class="tr">'
      + '<div>' + c.rank + '</div>'
      + '<div>' + escapeHtml(c.name) + '</div>'
      + '<div class="ttype"><i class="fa-' + (c.kind === "human" ? "regular fa-user" : "solid fa-robot") + '"></i> ' + escapeHtml(c.kind === "human" ? "Human" : "AI") + '</div>'
      + '<div>' + c.contribution_count + '</div>'
      + '<div class="areas">' + (c.areas || []).map(a => '<span>' + escapeHtml(a) + '</span>').join("") + '</div>'
      + '</div>').join("");
    table.insertAdjacentHTML("beforeend", rowsHtml);
  }

  function setupTabs() {
    const tabs = [...document.querySelectorAll(".tab")];
    const underline = document.getElementById("underline");

    function moveUnderline(tab) {
      const r = tab.getBoundingClientRect();
      const parentR = tab.parentElement.getBoundingClientRect();
      underline.style.left = (r.left - parentR.left) + "px";
      underline.style.width = r.width + "px";
    }
    function activate(name, tab) {
      tabs.forEach(t => t.classList.toggle("active", t === tab));
      document.querySelectorAll(".panel").forEach(p => {
        p.classList.toggle("active", p.dataset.panel === name);
      });
      moveUnderline(tab);
      history.replaceState(null, "", "#" + name);
    }
    tabs.forEach(t => t.addEventListener("click", () => activate(t.dataset.tab, t)));

    function init() {
      const initial = (location.hash || "#papers").slice(1);
      const tab = tabs.find(t => t.dataset.tab === initial) || tabs[0];
      activate(tab.dataset.tab, tab);
    }
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(init); else init();
    window.addEventListener("resize", () => {
      const active = tabs.find(t => t.classList.contains("active"));
      if (active) moveUnderline(active);
    });

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

    window._llmxive = { payload, buckets, lanes };
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else { boot(); }
})();
