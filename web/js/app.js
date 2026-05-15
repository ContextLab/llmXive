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

  // Per-project recent-activity index: project_id → { comments: [{...}], all_simulators: [...] }.
  // Built once on boot from payload.recent_activity so card render is O(1).
  // Each `comments` entry preserves display_name + excerpt + review_path + ended_at,
  // sorted newest-first, so the card can show the most recent personality
  // comment directly (not just a count).
  let activityByProject = null;
  function _buildActivityByProject() {
    if (activityByProject || !payload) return;
    activityByProject = {};
    for (const a of (payload.recent_activity || [])) {
      const pid = a.project_id;
      if (!pid) continue;
      const e = activityByProject[pid] || { comments: [], all_simulators: [] };
      if (a.action === "comment" && a.display_name) {
        e.comments.push({
          display_name: a.display_name,
          slug: a.personality_slug || "",
          excerpt: a.excerpt || "",
          review_path: a.review_path || "",
          ended_at: a.ended_at || "",
        });
        if (!e.all_simulators.includes(a.display_name)) {
          e.all_simulators.push(a.display_name);
        }
      }
      activityByProject[pid] = e;
    }
    // Sort each project's comments newest-first.
    for (const e of Object.values(activityByProject)) {
      e.comments.sort((a, b) => (b.ended_at || "").localeCompare(a.ended_at || ""));
    }
  }

  function cardHTML(item, kind) {
    _buildActivityByProject();
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
    // Render the first 3 inline; everything beyond becomes a hidden tail that
    // the "+N more" pill reveals on click. The CSS sets the row to nowrap +
    // overflow-x:auto so the first 3 pills can stay on a single line; clicking
    // "+N more" adds the `.expanded` class which switches to flex-wrap and
    // injects the remaining pills.
    const headPills = authors.slice(0, 3).map(a =>
      '<span class="submitter">' + kindIcon(a.kind) + ' ' + escapeHtml(a.name) + '</span>'
    ).join(" ");
    const tailPills = authors.slice(3).map(a =>
      '<span class="submitter submitter-tail">' + kindIcon(a.kind) + ' ' + escapeHtml(a.name) + '</span>'
    ).join(" ");
    const more = authors.length > 3
      ? ` <button type="button" class="submitter-more" aria-expanded="false">+${authors.length - 3} more</button>`
      : "";
    const authorsRow = authors.length
      ? '<div class="submitter-row">authors ' + headPills + (tailPills ? ' <span class="submitter-tail-group" hidden>' + tailPills + '</span>' : "") + more + '</div>'
      : (item.submitter
          ? '<div class="submitter-row">submitted by <span class="submitter">'
            + kindIcon(kindOf(item.submitter))
            + ' ' + escapeHtml(item.submitter) + '</span></div>'
          : "");
    // Featured-artifact strip: shows the paper PDF prominently when one
    // exists. PDF link uses event.stopPropagation so it opens the PDF
    // directly in a new tab rather than the artifact dialog.
    const artifacts = item.artifact_links || {};
    const pdfPath = artifacts.paper_pdf;
    const supplementPath = artifacts.paper_supplement;
    const pdfBadge = pdfPath
      ? '<a class="feat-badge primary" href="' + escapeHtml(pdfPath) + '" target="_blank" rel="noopener" '
        + 'onclick="event.stopPropagation();">'
        + '<i class="fa-regular fa-file-pdf"></i> PDF'
        + '</a>'
      : "";
    const supplementBadge = supplementPath
      ? '<a class="feat-badge" href="' + escapeHtml(supplementPath) + '" target="_blank" rel="noopener" '
        + 'onclick="event.stopPropagation();">'
        + '<i class="fa-regular fa-file-pdf"></i> supplement'
        + '</a>'
      : "";
    const featuredRow = (pdfBadge || supplementBadge)
      ? '<div class="featured">' + pdfBadge + supplementBadge + '</div>'
      : "";

    // Personality-comments block: actual excerpts (not just count) shown
    // inline so users can see what was said. The most recent comment
    // appears in full; older ones collapse behind a "+N more" toggle.
    const activity = (activityByProject || {})[item.id];
    let commentsBlock = "";
    if (activity && activity.comments.length) {
      const renderOne = (c, hidden) => {
        const path = c.review_path
          ? ' <a class="comment-link" href="' + escapeHtml(c.review_path) + '" target="_blank" rel="noopener" '
            + 'onclick="event.stopPropagation();" title="open full review"><i class="fa-regular fa-arrow-up-right-from-square"></i></a>'
          : "";
        return '<div class="comment' + (hidden ? " comment-hidden" : "") + '">'
          + '<div class="comment-head">'
          + '<i class="fa-solid fa-quote-left"></i> '
          + '<span class="comment-name">' + escapeHtml(c.display_name) + '</span>'
          + path
          + '</div>'
          + '<div class="comment-text">' + escapeHtml(c.excerpt || "(no excerpt)") + '</div>'
          + '</div>';
      };
      const head = renderOne(activity.comments[0], false);
      const tail = activity.comments.slice(1).map(c => renderOne(c, true)).join("");
      const moreBtn = activity.comments.length > 1
        ? ' <button type="button" class="comments-more" '
          + 'onclick="event.stopPropagation();">'
          + '+' + (activity.comments.length - 1) + ' more'
          + '</button>'
        : "";
      commentsBlock = '<div class="comments-block" data-count="' + activity.comments.length + '">'
        + head + tail + moreBtn + '</div>';
    }
    return ''
      + '<article class="card" tabindex="0" data-pid="' + escapeHtml(item.id) + '">'
      + '<div class="kicker"><span class="dot"></span>' + kicker + '<span class="stage-pill ' + escapeHtml(stage) + '" style="margin-left:auto">' + escapeHtml(stageLabel) + '</span></div>'
      + '<h3>' + escapeHtml(item.title) + '</h3>'
      + '<p class="desc">' + escapeHtml(desc) + '</p>'
      + featuredRow
      + commentsBlock
      + '<div class="meta">'
      + '<div class="keys">' + keys + '</div>'
      + '<div class="right">' + points + '<span><i class="fa-regular fa-clock"></i> ' + escapeHtml(updated) + '</span></div>'
      + '</div>'
      + authorsRow
      + '</article>';
  }

  // Per-lane search state (one term per `data-search` input). Empty = no
  // filter. setupSearch() wires the inputs; matchesSearch() decides which
  // projects survive the filter for a given lane.
  const searchState = {};

  function matchesSearch(item, term) {
    if (!term) return true;
    const needle = term.trim().toLowerCase();
    if (!needle) return true;
    // Searchable haystack: title + description + field + keywords + author
    // names (so "kahneman" matches a paper authored by Daniel Kahneman, and
    // "biology" matches every biology project). Built once per card per
    // keystroke; the catalog is small (≤ ~600 projects) so this is fine.
    const parts = [
      item.title,
      item.description,
      item.field,
      ...(item.keywords || []),
      ...((item.authors || []).map(a => a.name)),
      item.submitter,
      item.id,
    ];
    const hay = parts.filter(Boolean).join("  ").toLowerCase();
    return hay.includes(needle);
  }

  function renderCards(kind) {
    const el = document.getElementById(kind + "-cards");
    if (!el) return;
    const allItems = (buckets && buckets[kind]) || [];
    const term = searchState[kind] || "";
    const items = allItems.filter(it => matchesSearch(it, term));
    if (!items.length) {
      el.replaceChildren();
      const empty = document.createElement("div");
      empty.style.cssText = "grid-column: 1/-1; text-align:center; padding:40px; color:var(--muted);";
      // Distinguish "empty lane" from "search has no matches" — the user
      // wants to know which one to act on.
      const msg = term
        ? `No matches for &ldquo;${escapeHtml(term)}&rdquo;.`
        : "No projects in this stage yet.";
      empty.insertAdjacentHTML("beforeend",
        '<i class="fa-regular fa-folder-open" style="font-size:32px; opacity:0.5"></i>' +
        '<p style="margin-top:12px;">' + msg + '</p>');
      el.appendChild(empty);
      return;
    }
    el.replaceChildren();
    el.insertAdjacentHTML("beforeend", items.map(it => cardHTML(it, kind)).join(""));
    el.querySelectorAll(".card").forEach(card => {
      card.addEventListener("click", e => {
        // Clicks on the "+N more" pill toggle the author tail; they should NOT
        // also open the project modal (the most surprising behaviour we could
        // ship would be "click to see more authors → modal pops over them").
        const moreBtn = e.target.closest(".submitter-more");
        if (moreBtn && card.contains(moreBtn)) {
          e.stopPropagation();
          const row = moreBtn.closest(".submitter-row");
          const tail = row && row.querySelector(".submitter-tail-group");
          const expanded = row && row.classList.toggle("expanded");
          if (tail) tail.hidden = !expanded;
          moreBtn.setAttribute("aria-expanded", String(!!expanded));
          moreBtn.textContent = expanded ? "show less" : `+${(tail ? tail.querySelectorAll(".submitter-tail").length : 0)} more`;
          return;
        }
        // Same dance for "+N more" inside .comments-block — toggles
        // the .comment-hidden siblings to reveal older personality comments.
        const cmtMore = e.target.closest(".comments-more");
        if (cmtMore && card.contains(cmtMore)) {
          e.stopPropagation();
          const block = cmtMore.closest(".comments-block");
          if (!block) return;
          const expanded = block.classList.toggle("expanded");
          const hidden = block.querySelectorAll(".comment-hidden");
          hidden.forEach(c => c.classList.toggle("comment-show", expanded));
          cmtMore.textContent = expanded
            ? "show less"
            : `+${hidden.length} more`;
          return;
        }
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
    // The Backlog tab has a single search input (`data-search="backlog"`)
    // that filters BOTH the research and the paper kanban columns. Apply
    // the same `matchesSearch` predicate per project before rendering.
    const term = searchState["backlog"] || "";
    const html = stages.map(stage => {
      const stageItems = lane[stage] || [];
      const items = stageItems.filter(p => matchesSearch(p, term));
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

  // Current contributor-area filter: "all" → show everyone; otherwise the
  // exact area string (e.g. "biology", "computer science"). Cleared by
  // clicking the "All areas" chip; toggled by clicking any other chip.
  let contributorAreaFilter = "all";

  // Contributors-tab UI state — preserved across re-renders.
  // `sortKey` ∈ rank / name / type / count / areas; `sortDir` ∈ asc / desc.
  // `page` is 1-based; PAGE_SIZE is the user-requested 50/page cap.
  let contribSortKey = "rank";
  let contribSortDir = "asc";
  let contribPage = 1;
  const CONTRIB_PAGE_SIZE = 50;

  function _contribCompare(a, b, key, dir) {
    const sign = dir === "asc" ? 1 : -1;
    let av, bv;
    switch (key) {
      case "rank":  av = a.rank;               bv = b.rank;               break;
      case "name":  av = (a.name || "").toLowerCase(); bv = (b.name || "").toLowerCase(); break;
      case "type":  av = a.kind || "";         bv = b.kind || "";         break;
      case "count": av = a.contribution_count; bv = b.contribution_count; break;
      case "areas": {
        // Sort by primary (first) area string; empty areas sort last regardless of dir.
        av = (a.areas && a.areas[0]) || "";
        bv = (b.areas && b.areas[0]) || "";
        if (av === "" && bv === "") return 0;
        if (av === "") return 1;
        if (bv === "") return -1;
        break;
      }
      default:      av = a.rank;               bv = b.rank;
    }
    if (av < bv) return -1 * sign;
    if (av > bv) return  1 * sign;
    return 0;
  }

  function renderContributors() {
    // The data is already sorted (real contributors by count desc, the single
    // "unattributed" bucket last); keep that order. Rank only real contributors.
    const everyone = (payload.contributors || []).slice();
    everyone.forEach((c, i) => c.rank = i + 1);

    // 1. Render the filter chips ONCE per renderContributors() call. The
    //    chip set is derived from the actual `areas` strings present in
    //    payload.contributors — so it's always in sync with the data and
    //    new fields show up automatically without an HTML edit (matches
    //    the personality-pool extensibility property).
    const bar = document.getElementById("contrib-filter-bar");
    if (bar) {
      // Collect every area, ranked by how many contributors touch it.
      const areaCounts = new Map();
      for (const c of everyone) {
        if (c.kind === "unattributed") continue;
        for (const a of (c.areas || [])) {
          areaCounts.set(a, (areaCounts.get(a) || 0) + 1);
        }
      }
      const orderedAreas = [...areaCounts.entries()]
        .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
        .map(([a]) => a);
      // Remove any pre-existing chip buttons (label survives) and rebuild.
      [...bar.querySelectorAll(".chip")].forEach(n => n.remove());
      const chipsHtml = ['<button class="chip' + (contributorAreaFilter === "all" ? " active" : "") + '" data-area-filter="all">All areas</button>']
        .concat(orderedAreas.map(a =>
          '<button class="chip' + (contributorAreaFilter === a ? " active" : "") +
          '" data-area-filter="' + escapeHtml(a) + '">' + escapeHtml(a) + '</button>'
        )).join("");
      bar.insertAdjacentHTML("beforeend", chipsHtml);
      // Re-bind handlers every time so the closure captures the freshest
      // renderContributors. Idempotent because we replaced the chip nodes.
      bar.querySelectorAll(".chip[data-area-filter]").forEach(chip => {
        chip.addEventListener("click", () => {
          contributorAreaFilter = chip.dataset.areaFilter;
          renderContributors();
        });
      });
    }

    // 2. Apply the filter. "all" → everyone; otherwise keep only
    //    contributors whose `areas` include the selected area. Unattributed
    //    bucket is always kept (it's the catch-all at the bottom).
    const matches = c => contributorAreaFilter === "all"
      || c.kind === "unattributed"
      || (c.areas || []).includes(contributorAreaFilter);
    const list = everyone.filter(matches);
    const ranked = list.filter(c => c.kind !== "unattributed");

    // 3. Re-rank within the filter so the podium reflects "top-3 in this
    //    area" rather than "top-3 overall, possibly absent here". The
    //    original rank (across all areas) is preserved in `c.rank` for
    //    the table column so users can see absolute standing too.
    ranked.forEach((c, i) => c.filteredRank = i + 1);

    const podium = document.getElementById("podium");
    podium.replaceChildren();
    if (!ranked.length) {
      const msg = contributorAreaFilter === "all"
        ? "No contributors yet."
        : `No contributors in &ldquo;${escapeHtml(contributorAreaFilter)}&rdquo;.`;
      podium.insertAdjacentHTML("beforeend",
        '<div style="grid-column: 1/-1; text-align:center; padding:40px; color:var(--muted);">' + msg + '</div>');
    } else {
      const top3 = ranked.slice(0, 3);
      const podiumOrder = [top3[1], top3[0], top3[2]];
      const html = podiumOrder.map((c) => {
        if (!c) return "";
        const isFirst = c.filteredRank === 1;
        const initials = c.name.split(/[-.]/).map(s => s[0]).join("").slice(0, 2).toUpperCase();
        return ''
          + '<div class="pod ' + (isFirst ? "first" : "") + '">'
          + '<div class="rank">' + c.filteredRank + '</div>'
          + '<div class="avatar">' + escapeHtml(initials || "?") + '</div>'
          + '<div class="name">' + escapeHtml(c.name) + '</div>'
          + '<div class="type">' + escapeHtml(kindLabel(c.kind)) + '</div>'
          + '<div class="n">' + c.contribution_count + '<small>contributions</small></div>'
          + '</div>';
      }).join("");
      podium.insertAdjacentHTML("beforeend", html);
    }

    const table = document.getElementById("contrib-table");
    // Reflect current sort key/direction in the header indicators so the
    // user can see what's active. Each .sortable header gets a class for
    // styling and a unicode arrow in .sort-ind.
    table.querySelectorAll(".tr.head .sortable").forEach(h => {
      const key = h.getAttribute("data-sort");
      const ind = h.querySelector(".sort-ind");
      h.classList.toggle("active-sort", key === contribSortKey);
      if (ind) {
        ind.textContent = key === contribSortKey
          ? (contribSortDir === "asc" ? " ▲" : " ▼")
          : "";
      }
    });

    // Sort + paginate. The "unattributed" bucket is always pinned to the
    // very last page (or end of the only page) — it's a catch-all summary,
    // not a real contributor to rank against.
    const real = list.filter(c => c.kind !== "unattributed");
    const unattr = list.filter(c => c.kind === "unattributed");
    real.sort((a, b) => _contribCompare(a, b, contribSortKey, contribSortDir));

    // Clamp the page to the new valid range — important after sort/filter
    // changes that may shrink the list.
    const totalPages = Math.max(1, Math.ceil(real.length / CONTRIB_PAGE_SIZE));
    if (contribPage > totalPages) contribPage = totalPages;
    if (contribPage < 1) contribPage = 1;

    const start = (contribPage - 1) * CONTRIB_PAGE_SIZE;
    const pageReal = real.slice(start, start + CONTRIB_PAGE_SIZE);

    // The unattributed-bucket row appears only on the LAST page.
    const pageRows = (contribPage === totalPages)
      ? pageReal.concat(unattr)
      : pageReal;

    [...table.querySelectorAll(".tr:not(.head)")].forEach(n => n.remove());
    const rowsHtml = pageRows.map(c => ''
      + '<div class="tr' + (c.kind === "unattributed" ? " unattributed" : "") + '">'
      + '<div>' + (c.kind === "unattributed" ? "—" : c.rank) + '</div>'
      + '<div>' + escapeHtml(c.kind === "unattributed" ? "Unattributed contributions" : c.name) + '</div>'
      + '<div class="ttype"><i class="' + kindTableIcon(c.kind) + '"></i> ' + escapeHtml(kindLabel(c.kind)) + '</div>'
      + '<div>' + c.contribution_count + '</div>'
      + '<div class="areas">' + (c.areas || []).map(a => '<span>' + escapeHtml(a) + '</span>').join("") + '</div>'
      + '</div>').join("");
    table.insertAdjacentHTML("beforeend", rowsHtml);

    // Pager: hidden when everything fits on one page. Info string is
    // "1–50 of 132" style so the user knows where they are in the list.
    const pager = document.getElementById("contrib-pager");
    if (pager) {
      const showPager = real.length > CONTRIB_PAGE_SIZE;
      pager.hidden = !showPager;
      if (showPager) {
        const end = Math.min(start + CONTRIB_PAGE_SIZE, real.length);
        const info = pager.querySelector("[data-page-info]");
        if (info) {
          info.textContent = `${start + 1}–${end} of ${real.length}`
            + ` · page ${contribPage} / ${totalPages}`;
        }
        const prev = pager.querySelector("[data-page-prev]");
        const next = pager.querySelector("[data-page-next]");
        if (prev) prev.disabled = contribPage <= 1;
        if (next) next.disabled = contribPage >= totalPages;
      }
    }
  }

  function setupContributorsControls() {
    // Header click → sort by that column (toggle direction if already active).
    // Bind once on boot; renderContributors is called many times but the
    // listeners are attached to the header divs (which are NEVER replaced —
    // only the data rows are recreated), so we don't re-bind.
    const table = document.getElementById("contrib-table");
    if (table) {
      table.querySelectorAll(".tr.head .sortable").forEach(h => {
        h.addEventListener("click", () => {
          const key = h.getAttribute("data-sort");
          if (key === contribSortKey) {
            contribSortDir = (contribSortDir === "asc" ? "desc" : "asc");
          } else {
            contribSortKey = key;
            // Default: count + rank go desc (most interesting first); text
            // columns go asc (alphabetical).
            contribSortDir = (key === "count") ? "desc" : "asc";
          }
          contribPage = 1;
          renderContributors();
        });
      });
    }
    // Pager prev / next.
    const pager = document.getElementById("contrib-pager");
    if (pager) {
      const prev = pager.querySelector("[data-page-prev]");
      const next = pager.querySelector("[data-page-next]");
      if (prev) prev.addEventListener("click", () => {
        if (contribPage > 1) { contribPage--; renderContributors(); }
      });
      if (next) next.addEventListener("click", () => {
        // The clamp inside renderContributors caps overshoots.
        contribPage++; renderContributors();
      });
    }
  }

  // ── Activity tab — cross-project recent-run feed ─────────────────────
  //
  // Data: payload.recent_activity (emitted by web_data.py _recent_activity).
  // Filter chips: "all" / "personality" / "pipeline" / "reviews".
  //   - personality → agent_name == "personality"
  //   - pipeline    → agent_name is one of the pipeline drivers
  //                   (brainstorm, flesh_out, specifier, clarifier, planner,
  //                   tasker, implementer, plus paper-stage equivalents)
  //   - reviews     → agent_name starts with "research_reviewer" or
  //                   "paper_reviewer"
  //   - all         → no agent filter
  // Plus a free-text search over project_id / agent / display_name.
  let activityFilter = "all";
  let activitySearch = "";
  let activityStage = "";          // "" = all; otherwise current_stage string
  let activityContributor = "";    // "" = all; otherwise agent or display_name
  let activityStatus = "";         // "" = all; otherwise outcome string
  let activitySort = "desc";       // "desc" = newest first; "asc" = oldest first
  let activityPage = 1;
  const ACTIVITY_PER_PAGE = 50;

  const _ACTIVITY_PIPELINE_AGENTS = new Set([
    "brainstorm", "flesh_out", "research_question_validator", "idea_selector",
    "project_initializer", "librarian", "specifier", "clarifier", "planner",
    "tasker", "implementer", "advancement",
    "paper_initializer", "paper_specifier", "paper_clarifier",
    "paper_planner", "paper_tasker", "paper_implementer",
    "latex_build", "latex_fix", "reference_validator",
    "submission_intake", "status_reporter", "repository_hygiene",
  ]);

  function _activityCategory(entry) {
    const a = entry.agent || "";
    if (a === "personality") return "personality";
    if (a.startsWith("research_reviewer") || a.startsWith("paper_reviewer")) return "reviews";
    if (_ACTIVITY_PIPELINE_AGENTS.has(a)) return "pipeline";
    return "other";
  }

  function _relTime(iso) {
    if (!iso) return "—";
    try {
      const dt = new Date(iso);
      const ms = Date.now() - dt.getTime();
      const s = Math.round(ms / 1000);
      if (s < 60) return s + "s ago";
      const m = Math.round(s / 60);
      if (m < 60) return m + "m ago";
      const h = Math.round(m / 60);
      if (h < 48) return h + "h ago";
      const d = Math.round(h / 24);
      return d + "d ago";
    } catch (e) { return "—"; }
  }

  function _outcomeBadge(outcome) {
    // success/committed → ok; abstained → muted; failures → bad.
    const bad = ["rate_limited", "model_error", "malformed_response",
                 "target_missing", "librarian_held", "timeout", "failure", "failed"];
    let cls = "ok";
    if (bad.includes(outcome)) cls = "bad";
    if (outcome === "abstained") cls = "muted";
    return '<span class="outcome ' + cls + '">' + escapeHtml(outcome || "—") + '</span>';
  }

  function _activityContributorKey(r) {
    // Personalities get their display_name (e.g. "Daniel Kahneman (simulated)");
    // generic agents fall back to the agent name.
    return r.display_name || r.agent || "";
  }

  function _filteredActivity() {
    let rows = (payload.recent_activity || []).slice();
    if (activityFilter !== "all") {
      rows = rows.filter(r => _activityCategory(r) === activityFilter);
    }
    if (activityStage) {
      rows = rows.filter(r => (r.project_stage || "") === activityStage);
    }
    if (activityContributor) {
      rows = rows.filter(r => _activityContributorKey(r) === activityContributor);
    }
    if (activityStatus) {
      rows = rows.filter(r => (r.outcome || "") === activityStatus);
    }
    if (activitySearch) {
      const needle = activitySearch.toLowerCase();
      rows = rows.filter(r => {
        const hay = [r.project_id, r.agent, r.display_name, r.personality_slug,
                     r.action, r.outcome, r.model, r.project_stage]
          .filter(Boolean).join(" ").toLowerCase();
        return hay.includes(needle);
      });
    }
    rows.sort((a, b) => {
      const ta = a.ended_at || a.started_at || "";
      const tb = b.ended_at || b.started_at || "";
      return activitySort === "asc" ? ta.localeCompare(tb) : tb.localeCompare(ta);
    });
    return rows;
  }

  function _populateActivityDropdowns() {
    // Build option lists from the full activity payload (not the filtered
    // view) so users can reach every value. Preserve selections.
    const all = payload.recent_activity || [];
    const stages = Array.from(new Set(all.map(r => r.project_stage || "").filter(Boolean))).sort();
    const contributors = Array.from(new Set(all.map(_activityContributorKey).filter(Boolean))).sort();
    const statuses = Array.from(new Set(all.map(r => r.outcome || "").filter(Boolean))).sort();

    function fill(sel, label, items, current) {
      if (!sel) return;
      // Rebuild via DOM to keep escaping safe (no innerHTML).
      sel.replaceChildren();
      const blank = document.createElement("option");
      blank.value = ""; blank.textContent = label;
      sel.appendChild(blank);
      for (const v of items) {
        const opt = document.createElement("option");
        opt.value = v; opt.textContent = v;
        if (v === current) opt.selected = true;
        sel.appendChild(opt);
      }
    }
    fill(document.querySelector("[data-activity-stage]"), "All stages", stages, activityStage);
    fill(document.querySelector("[data-activity-contributor]"), "All contributors", contributors, activityContributor);
    fill(document.querySelector("[data-activity-status]"), "All statuses", statuses, activityStatus);
  }

  function renderActivity() {
    const root = document.getElementById("activity-list");
    if (!root) return;
    _populateActivityDropdowns();

    const rows = _filteredActivity();
    const total = rows.length;
    const totalPages = Math.max(1, Math.ceil(total / ACTIVITY_PER_PAGE));
    if (activityPage > totalPages) activityPage = totalPages;
    if (activityPage < 1) activityPage = 1;
    const start = (activityPage - 1) * ACTIVITY_PER_PAGE;
    const slice = rows.slice(start, start + ACTIVITY_PER_PAGE);

    const countEl = document.getElementById("activity-count");
    if (countEl) {
      const lo = total === 0 ? 0 : start + 1;
      const hi = Math.min(start + ACTIVITY_PER_PAGE, total);
      countEl.textContent = total === 0 ? "0 results"
        : (total + " result" + (total === 1 ? "" : "s")
            + " · showing " + lo + "–" + hi);
    }

    root.replaceChildren();
    if (!slice.length) {
      root.insertAdjacentHTML("beforeend",
        '<div class="activity-empty">No activity matching the current filters.</div>');
      _renderActivityPager(0, 1);
      return;
    }
    const html = slice.map(r => {
      // Display the persona's "(simulated)" display_name when present,
      // else the agent name — same FR-010 invariant the contributor list
      // honors.
      const who = r.display_name || r.agent || "—";
      const actor = '<span class="actor">' + escapeHtml(who) + '</span>';
      const project = r.project_id
        ? '<span class="project" data-pid="' + escapeHtml(r.project_id) + '">'
            + escapeHtml(r.project_id) + '</span>'
        : '<span class="project muted">(no project)</span>';
      const actionTag = r.action
        ? '<span class="atag">' + escapeHtml(r.action) + '</span>'
        : '';
      const dur = r.duration_s
        ? '<span class="dur">' + (r.duration_s).toFixed(1) + 's</span>'
        : '';
      return '<div class="activity-row" data-cat="' + _activityCategory(r) + '">'
        + '<span class="when" title="' + escapeHtml(r.ended_at || r.started_at || "") + '">'
        + escapeHtml(_relTime(r.ended_at || r.started_at)) + '</span>'
        + actor + actionTag + project + _outcomeBadge(r.outcome) + dur
        + '</div>';
    }).join("");
    root.insertAdjacentHTML("beforeend", html);
    // Clicking a project pill opens that project's modal.
    root.querySelectorAll(".project[data-pid]").forEach(el => {
      el.addEventListener("click", () => {
        const pid = el.dataset.pid;
        const proj = (payload.projects || []).find(p => p.id === pid);
        if (proj) Dialog.open(proj);
      });
    });
    _renderActivityPager(total, totalPages);
  }

  function _renderActivityPager(total, totalPages) {
    const root = document.getElementById("activity-pager");
    if (!root) return;
    root.replaceChildren();
    if (total <= ACTIVITY_PER_PAGE) return;

    const mkBtn = (label, page, opts = {}) => {
      const b = document.createElement("button");
      b.className = "chip" + (opts.active ? " active" : "");
      if (opts.disabled) b.disabled = true;
      b.textContent = label;
      b.addEventListener("click", () => {
        activityPage = page;
        renderActivity();
        const panel = document.querySelector("[data-panel='activity']");
        if (panel) panel.scrollIntoView({ behavior: "smooth", block: "start" });
      });
      return b;
    };

    root.appendChild(mkBtn("← Prev", Math.max(1, activityPage - 1),
      { disabled: activityPage === 1 }));

    // Window: show current ± 2, with first/last anchors and ellipses.
    const window_ = new Set([1, totalPages, activityPage,
      activityPage - 1, activityPage - 2,
      activityPage + 1, activityPage + 2]);
    const pages = Array.from(window_).filter(p => p >= 1 && p <= totalPages).sort((a, b) => a - b);
    let last = 0;
    for (const p of pages) {
      if (p - last > 1) {
        const sep = document.createElement("span");
        sep.className = "pager-ellipsis";
        sep.textContent = "…";
        root.appendChild(sep);
      }
      root.appendChild(mkBtn(String(p), p, { active: p === activityPage }));
      last = p;
    }

    root.appendChild(mkBtn("Next →", Math.min(totalPages, activityPage + 1),
      { disabled: activityPage === totalPages }));
  }

  function setupActivity() {
    // Action chips (legacy filter)
    document.querySelectorAll("[data-activity-filter]").forEach(chip => {
      chip.addEventListener("click", () => {
        activityFilter = chip.dataset.activityFilter;
        document.querySelectorAll("[data-activity-filter]").forEach(c =>
          c.classList.toggle("active", c.dataset.activityFilter === activityFilter));
        activityPage = 1;
        renderActivity();
      });
    });
    // Stage / Contributor / Status selects
    const stageSel = document.querySelector("[data-activity-stage]");
    if (stageSel) stageSel.addEventListener("change", () => {
      activityStage = stageSel.value;
      activityPage = 1;
      renderActivity();
    });
    const contribSel = document.querySelector("[data-activity-contributor]");
    if (contribSel) contribSel.addEventListener("change", () => {
      activityContributor = contribSel.value;
      activityPage = 1;
      renderActivity();
    });
    const statusSel = document.querySelector("[data-activity-status]");
    if (statusSel) statusSel.addEventListener("change", () => {
      activityStatus = statusSel.value;
      activityPage = 1;
      renderActivity();
    });
    // Sort chips
    document.querySelectorAll("[data-activity-sort]").forEach(chip => {
      chip.addEventListener("click", () => {
        activitySort = chip.dataset.activitySort;
        document.querySelectorAll("[data-activity-sort]").forEach(c =>
          c.classList.toggle("active", c.dataset.activitySort === activitySort));
        activityPage = 1;
        renderActivity();
      });
    });
    // Search input
    const searchInput = document.querySelector("[data-activity-search]");
    if (searchInput) {
      let timer = null;
      searchInput.addEventListener("input", () => {
        clearTimeout(timer);
        timer = setTimeout(() => {
          activitySearch = (searchInput.value || "").trim();
          activityPage = 1;
          renderActivity();
        }, 100);
      });
      searchInput.addEventListener("keydown", e => {
        if (e.key === "Escape" && searchInput.value) {
          searchInput.value = "";
          activitySearch = "";
          activityPage = 1;
          renderActivity();
        }
      });
    }
  }

  function setupSearch() {
    // Wire every `<input data-search="LANE">` in index.html to filter that
    // lane's cards (or kanban columns for backlog) by the typed term.
    // The `searchState` map and `matchesSearch` predicate above are the
    // canonical filter — every render-lane call already honors them.
    //
    // Inputs (per index.html):
    //   data-search="papers"     → renderCards("papers")
    //   data-search="paper"      → renderCards("paper")
    //   data-search="inProgress" → renderCards("inProgress")
    //   data-search="backlog"    → renderBacklog()
    //
    // Debounce keystrokes lightly (100ms) so we don't re-render on every
    // single character for users typing quickly. The render path is fast
    // (≤ ~600 projects, plain DOM strings), but the debounce keeps the
    // UI feeling smooth.
    document.querySelectorAll("[data-search]").forEach(input => {
      const lane = input.dataset.search;
      if (!lane) return;
      let timer = null;
      input.addEventListener("input", () => {
        clearTimeout(timer);
        timer = setTimeout(() => {
          searchState[lane] = input.value || "";
          if (lane === "backlog") {
            renderBacklog();
          } else {
            // The other four (papers / paper / inProgress / plans / designs)
            // each have their own `<div id="${lane}-cards">` rendered by
            // renderCards.
            renderCards(lane);
          }
        }, 100);
      });
      // Esc clears the input + re-renders.
      input.addEventListener("keydown", e => {
        if (e.key === "Escape" && input.value) {
          input.value = "";
          searchState[lane] = "";
          if (lane === "backlog") renderBacklog();
          else renderCards(lane);
        }
      });
    });
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

    // FR-013b: on a successful artifact submission show, IN THE MODAL, a
    // confirmation with a clickable link to the created issue + that the
    // contribution will be processed within the next hour. On failure: an
    // inline error, input preserved for retry.
    function setMsg(id, kind, html) {
      const el = document.getElementById(id);
      if (!el) return;
      el.className = "modal-msg " + (kind || "");
      el.innerHTML = html;
    }
    function confirmHtml(issue, what) {
      return (what || "Submitted") + ' as <a href="' + escapeHtml(issue.html_url) + '" target="_blank" rel="noopener">issue #' + issue.number +
        '</a>. A maintenance agent will process it within the next hour.';
    }

    document.getElementById("submit-idea-btn").addEventListener("click", async () => {
      const title = document.querySelector("[data-submit='title']").value.trim();
      const field = document.querySelector("[data-submit='field']").value.trim();
      const desc  = document.querySelector("[data-submit='description']").value.trim();
      const kw    = document.querySelector("[data-submit='keywords']").value.trim();
      setMsg("submit-msg", "", "");
      if (!title || !field || !desc) { setMsg("submit-msg", "err", "Title, field, and description are required."); return; }
      if (!Auth.isSignedIn()) { setMsg("submit-msg", "err", "Please sign in with GitHub to submit an idea."); Auth.startLogin(); return; }
      const btn = document.getElementById("submit-idea-btn"); btn.disabled = true;
      try {
        const issue = await Auth.submitIdea({ title, field, description: desc, keywords: kw });
        setMsg("submit-msg", "ok", confirmHtml(issue, "Idea submitted"));
        ["title", "field", "description", "keywords"].forEach(k => { const f = document.querySelector("[data-submit='" + k + "']"); if (f) f.value = ""; });
      } catch (err) {
        setMsg("submit-msg", "err", "Could not submit idea: " + escapeHtml(String(err.message || err)));
      } finally { btn.disabled = false; }
    });

    document.getElementById("submit-review-btn").addEventListener("click", async () => {
      const pid = document.getElementById("review-project-id").value;
      const stage = document.querySelector("[data-review='stage']").value;
      const verdict = document.querySelector("[data-review='verdict']").value;
      const summary = document.querySelector("[data-review='summary']").value.trim();
      const strengths = document.querySelector("[data-review='strengths']").value.trim();
      const concerns = document.querySelector("[data-review='concerns']").value.trim();
      setMsg("review-msg", "", "");
      if (!pid || !summary) { setMsg("review-msg", "err", "Pick a project and provide a summary."); return; }
      if (!Auth.isSignedIn()) { setMsg("review-msg", "err", "Sign in with GitHub to submit a review."); Auth.startLogin(); return; }
      const btn = document.getElementById("submit-review-btn"); btn.disabled = true;
      try {
        const res = await Auth.submitReview({ project_id: pid, stage, verdict, summary, strengths, concerns });
        // submitReview returns the Contents-API response (the commit), not an
        // issue — link to the created review file + still say "within the hour"
        // (the advancement evaluator picks it up on the next cycle).
        const url = (res && res.content && res.content.html_url) || ("https://github.com/ContextLab/llmXive/tree/main/projects/" + pid + "/reviews");
        setMsg("review-msg", "ok", 'Review submitted for ' + escapeHtml(pid) + ' — <a href="' + escapeHtml(url) + '" target="_blank" rel="noopener">view it on GitHub</a>. It will be counted on the next pipeline cycle (within the hour).');
      } catch (err) {
        setMsg("review-msg", "err", "Could not submit review: " + escapeHtml(String(err.message || err)));
      } finally { btn.disabled = false; }
    });

    const paperBtn = document.getElementById("submit-paper-btn");
    if (paperBtn) paperBtn.addEventListener("click", async () => {
      const url = (document.querySelector("[data-paper='url']").value || "").trim();
      const fileInput = document.querySelector("[data-paper='file']");
      const pdfFile = fileInput && fileInput.files && fileInput.files[0];
      setMsg("paper-msg", "", "");
      if (!url && !pdfFile) { setMsg("paper-msg", "err", "Enter a paper URL or choose a PDF."); return; }
      if (!Auth.isSignedIn()) { setMsg("paper-msg", "err", "Sign in with GitHub to submit a paper."); Auth.startLogin(); return; }
      paperBtn.disabled = true; setMsg("paper-msg", "", pdfFile ? "Uploading PDF…" : "Submitting…");
      try {
        const issue = await Auth.submitPaper(pdfFile ? { pdfFile } : { url });
        setMsg("paper-msg", "ok", confirmHtml(issue, "Paper submitted"));
        document.querySelector("[data-paper='url']").value = "";
        if (fileInput) fileInput.value = "";
      } catch (err) {
        setMsg("paper-msg", "err", "Could not submit paper: " + escapeHtml(String(err.message || err)));
      } finally { paperBtn.disabled = false; }
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
      // Use the `*Into` helper so Prism runs over the live nodes after the
      // sanitized HTML is inserted — that's how fenced code blocks
      // (Python tools, bash hooks, YAML config) get syntax-highlighted.
      M.fetchAndRenderMarkdownInto(promptEl, a.prompt_raw_url)
        .catch(err => {
          if (promptEl) {
            promptEl.replaceChildren();
            promptEl.insertAdjacentHTML("beforeend",
              '<p class="muted">Could not load the prompt (' + escapeHtml(String(err.message || err)) + ').</p>');
          }
        });
    } else if (promptEl) {
      promptEl.replaceChildren();
      promptEl.insertAdjacentHTML("beforeend", '<p class="muted">No prompt available.</p>');
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

  // ── Personality Registry modal (spec 008 / US6 / FR-022 / FR-023) ──
  //
  // Mirrors openAgentRegistry's behaviour: same `.about-modal` shell, same
  // `.am-agent-list` / `.am-agent-row` / `.am-prompt` / `.md-body` styling,
  // same `fetchAndRenderMarkdownInto` markdown-with-Prism path. The
  // "(simulated)" suffix is appended at display time; the bare
  // `display_name` from `payload.personalities` is NEVER shown to a user
  // without it (FR-010).
  function _personalityBySlug(slug) {
    return (payload.personalities || []).find(p => p.slug === slug) || null;
  }

  function _personalityDetailHtml(p) {
    const displayWithSuffix = escapeHtml(p.display_name) + " (simulated)";
    const sources = (p.sources || []).length
      ? '<ul>' + p.sources.map(s => '<li>' + escapeHtml(s) + '</li>').join("") + '</ul>'
      : '<p class="muted">—</p>';
    return '' +
      '<div class="am-section am-agent-meta">' +
        '<p><strong>' + displayWithSuffix + '</strong> — ' + escapeHtml(p.summary || "") + '</p>' +
        '<p class="muted am-hint">This is a SIMULATED AI persona shaped from the public-record writings of ' +
          escapeHtml(p.display_name) + '. It is not the real person.</p>' +
        '<div class="am-links">' +
          (p.prompt_github_url ? '<a class="btn" href="' + escapeHtml(p.prompt_github_url) + '" target="_blank" rel="noopener"><i class="fa-brands fa-github"></i> View prompt on GitHub</a>' : '') +
          '<button class="btn" data-personalities-back><i class="fa-solid fa-arrow-left"></i> All personalities</button>' +
        '</div>' +
      '</div>' +
      '<div class="am-section"><h3>Grounded on</h3>' + sources + '</div>' +
      '<div class="am-section"><h3>Prompt</h3><div class="am-prompt md-body"><div class="ad-art-loading">Loading prompt…</div></div></div>';
  }

  function openPersonalityDetail(slug) {
    const p = _personalityBySlug(slug);
    if (!p) return;
    const title = "Personality · " + p.display_name + " (simulated)";
    const body = _openAboutModal(title, _personalityDetailHtml(p));
    body.querySelector("[data-personalities-back]")?.addEventListener("click", openPersonalityRegistry);
    const promptEl = body.querySelector(".am-prompt");
    const M = window.LlmxiveMarkdown;
    if (p.prompt_raw_url && M) {
      // Use the same `*Into` helper as the Agent Registry — Prism applies
      // to fenced code blocks (Markdown syntax samples inside the
      // grounding-card body for some personas).
      M.fetchAndRenderMarkdownInto(promptEl, p.prompt_raw_url)
        .catch(err => {
          if (promptEl) {
            promptEl.replaceChildren();
            promptEl.insertAdjacentHTML("beforeend",
              '<p class="muted">Could not load the prompt (' + escapeHtml(String(err.message || err)) + ').</p>');
          }
        });
    } else if (promptEl) {
      promptEl.replaceChildren();
      promptEl.insertAdjacentHTML("beforeend", '<p class="muted">No prompt available.</p>');
    }
  }

  function openPersonalityRegistry() {
    const personalities = (payload.personalities || []).slice().sort((x, y) => x.slug.localeCompare(y.slug));
    const intro = '<div class="am-section"><p>' + personalities.length +
      ' simulated personalities take turns commenting on artifacts, contributing edits, and proposing new arXiv papers — one persona per 30-minute cron tick, in deterministic rotation. ' +
      'Each persona&apos;s voice is shaped from the public-record writings of the real figure. ' +
      'Every output is tagged <code>&lt;Name&gt; (simulated)</code> and disclaims its AI origin; the rotation pool lives in <code>agents/prompts/personalities/</code> — adding a new prompt file adds a new personality on the next tick.</p>' +
      '<a class="btn" href="https://github.com/ContextLab/llmXive/tree/main/agents/prompts/personalities" target="_blank" rel="noopener"><i class="fa-brands fa-github"></i> View personalities on GitHub</a></div>';
    const rows = personalities.map(p =>
      '<button class="am-agent-row" data-personality="' + escapeHtml(p.slug) + '">' +
        '<span class="ar-name">' + escapeHtml(p.display_name) + ' (simulated)</span>' +
        '<span class="ar-purpose">' + escapeHtml(p.summary || "") + '</span>' +
        '<span class="ar-go"><i class="fa-solid fa-chevron-right"></i></span>' +
      '</button>').join("");
    _openAboutModal("Personality registry", intro + '<div class="am-agent-list">' + rows + '</div>');
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
    // "Personality registry" triggers (spec 008 / US6).
    document.querySelectorAll('[data-open-modal="personalities"]').forEach(b => {
      b.addEventListener("click", openPersonalityRegistry);
    });
    // Delegated: any [data-agent] (an agent chip in a step modal, or a row in
    // the registry list) opens that agent's detail view.
    document.addEventListener("click", e => {
      const t = e.target.closest("[data-agent]");
      if (t && !t.hasAttribute("disabled")) openAgentDetail(t.dataset.agent);
    });
    // Delegated: any [data-personality] (a row in the Personality
    // Registry modal) opens that personality's detail view.
    document.addEventListener("click", e => {
      const t = e.target.closest("[data-personality]");
      if (t && !t.hasAttribute("disabled")) openPersonalityDetail(t.dataset.personality);
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
    renderActivity();

    setupTabs();
    setupSearch();
    setupActivity();
    setupContributorsControls();
    setupModals();
    setupAboutModals();

    window._llmxive = { payload, buckets, lanes };
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else { boot(); }
})();
