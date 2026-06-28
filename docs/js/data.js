// llmXive — data layer. Fetches web/data/projects.json and exposes a typed model.
// Falls back to an empty payload if the file is missing or malformed.

(function () {
  const EMPTY = {
    schema_version: "2.0.0",
    generated_at: null,
    aggregates: {
      total_contributions: 0, active_projects: 0, papers_posted: 0,
      total_contributors: 0, human_contributors: 0, ai_contributors: 0,
      total_collaborations: 0,
    },
    projects: [],
    contributors: [],
  };

  // SINGLE ordered list of every non-published lifecycle stage, top-to-bottom
  // in pipeline progression order (research lane → paper lane → needs-attention
  // states). This is the SSoT: the In-Progress TAB membership is DERIVED from
  // it (see TAB_STAGE_SETS below) and the In-Progress tab renders one section
  // per stage in this order — so a project can never be in the tab without a
  // section (or vice-versa), and no drift check is needed. Mirrors the live
  // Stage enum in src/llmxive/types.py: every value EXCEPT `posted` (which is
  // the Published tab). Keeping the needs-attention states here means no
  // project is ever hidden — empty stages simply render no section.
  const IN_PROGRESS_STAGE_ORDER = [
    // research lane
    "brainstormed", "flesh_out_in_progress", "flesh_out_complete",
    "validator_revise", "validated", "project_initialized",
    "specified", "clarify_in_progress", "clarified",
    "planned", "tasked", "analyze_in_progress", "analyzed",
    "in_progress", "research_complete", "research_review",
    "research_full_revision", "research_accepted",
    // paper lane
    "paper_drafting_init", "paper_specified", "paper_clarified", "paper_planned",
    "paper_tasked", "paper_analyzed", "paper_in_progress", "paper_complete",
    "paper_review", "paper_accepted", "awaiting_publication_signoff",
    // needs-attention / terminal-but-not-published states (kept visible so no
    // project silently disappears; only render when non-empty)
    "validator_rejected", "research_rejected", "paper_fundamental_flaws",
    "publish_blocked", "human_input_needed", "blocked", "agent_blocked",
  ];

  // Stage → tab mapping (FR-005). Mirrors src/llmxive/web_data.py. TWO project
  // tabs: `papers` (Published = `posted` only) and `inProgress` (every other
  // lifecycle stage, DERIVED from IN_PROGRESS_STAGE_ORDER so tab membership and
  // the sectioned layout can never drift).
  const TAB_STAGE_SETS = {
    papers:     new Set(["posted"]),
    inProgress: new Set(IN_PROGRESS_STAGE_ORDER),
  };

  const STAGE_LABELS = {
    brainstormed: "Brainstormed",
    flesh_out_in_progress: "Fleshing out",
    flesh_out_complete: "Fleshed out",
    validated: "Validated",
    project_initialized: "Initialized",
    specified: "Specified",
    clarify_in_progress: "Clarifying",
    clarified: "Clarified",
    planned: "Planned",
    tasked: "Tasked",
    analyze_in_progress: "Analyzing",
    analyzed: "Analyzed",
    in_progress: "In progress",
    research_complete: "Research complete",
    research_review: "Research review",
    research_accepted: "Research accepted",
    research_minor_revision: "Research minor revision",
    research_full_revision: "Research full revision",
    research_rejected: "Rejected",
    paper_drafting_init: "Paper init",
    paper_specified: "Paper spec",
    paper_clarified: "Paper clarified",
    paper_planned: "Paper plan",
    paper_tasked: "Paper tasks",
    paper_analyzed: "Paper analyzed",
    paper_in_progress: "Paper drafting",
    paper_complete: "Paper complete",
    paper_review: "Paper review",
    paper_accepted: "Paper accepted",
    paper_minor_revision: "Paper minor revision",
    paper_major_revision_writing: "Paper revision (writing)",
    paper_major_revision_science: "Paper revision (science)",
    paper_fundamental_flaws: "Fundamental flaws",
    posted: "Posted",
    // Spec 012/013 convergence + publication stages
    ready_for_implementation: "Ready for implementer",
    paper_revision_in_progress: "Revision planning",
    paper_revision_blocked: "Revision blocked",
    publish_blocked: "Publish blocked",
    human_input_needed: "Human input needed",
    blocked: "Blocked",
    validator_revise: "Validation revising",
    validator_rejected: "Rejected (validation)",
    awaiting_publication_signoff: "Awaiting sign-off",
    agent_blocked: "Agent blocked",
  };

  async function loadPayload() {
    const url = new URL("data/projects.json", document.baseURI).href;
    try {
      const r = await fetch(url, { cache: "no-cache" });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const j = await r.json();
      // Migrate v1→v2 if needed.
      if (!j.aggregates) {
        return { ...EMPTY, projects: (j.projects || []).map(migrateV1Project) };
      }
      return j;
    } catch (err) {
      console.warn("[llmXive] could not load projects.json:", err);
      return { ...EMPTY, _loadError: String(err) };
    }
  }

  function migrateV1Project(p) {
    return {
      id: p.id, title: p.title, field: p.field,
      current_stage: p.stage || "brainstormed",
      phase_group: "idea",
      points_research_total: 0, points_paper_total: 0,
      created_at: p.last_updated || new Date().toISOString(),
      updated_at: p.last_updated || new Date().toISOString(),
      keywords: [], speckit_research_dir: null, speckit_paper_dir: null,
      artifact_links: {}, citation_summary: { verified: 0, mismatch: 0, unreachable: 0, pending: 0 },
      last_run_log: [],
    };
  }

  function projectsByTab(payload) {
    // One empty array per tab in TAB_STAGE_SETS (papers + inProgress).
    const buckets = Object.fromEntries(Object.keys(TAB_STAGE_SETS).map(t => [t, []]));
    for (const proj of payload.projects || []) {
      for (const [tab, stages] of Object.entries(TAB_STAGE_SETS)) {
        if (stages.has(proj.current_stage)) buckets[tab].push(proj);
      }
    }
    // Sort each bucket by updated_at desc by default.
    for (const k of Object.keys(buckets)) {
      buckets[k].sort((a, b) => (b.updated_at || "").localeCompare(a.updated_at || ""));
    }
    return buckets;
  }

  // Bucket the In-Progress projects by their current stage, in
  // IN_PROGRESS_STAGE_ORDER. Returns an ordered array of
  // { stage, label, items } sections — one per stage that HAS at least one
  // project (empty stages are omitted by the caller / here). Items are sorted
  // recently-updated first, matching the default card sort. Pass an optional
  // `projects` array (e.g. a search-filtered subset); defaults to the whole
  // payload. A project whose stage isn't in IN_PROGRESS_STAGE_ORDER is not an
  // In-Progress project and is skipped.
  function inProgressByStage(payload, projects) {
    const list = projects || (payload && payload.projects) || [];
    const byStage = Object.fromEntries(IN_PROGRESS_STAGE_ORDER.map(s => [s, []]));
    for (const p of list) {
      if (p.current_stage in byStage) byStage[p.current_stage].push(p);
    }
    const sections = [];
    for (const stage of IN_PROGRESS_STAGE_ORDER) {
      const items = byStage[stage];
      if (!items.length) continue;               // skip empty stages
      items.sort((a, b) => (b.updated_at || "").localeCompare(a.updated_at || ""));
      sections.push({ stage, label: STAGE_LABELS[stage] || stage, items });
    }
    return sections;
  }

  // Normalize a project's `authors` into a plain array of display-name
  // strings. Author entries arrive in two shapes across the dataset: bare
  // strings ("Ada Lovelace") OR objects ({name, kind, ...}). Everything that
  // needs author names (search haystack, the author facet, card pills) routes
  // through here so the two shapes are handled in exactly one place (SSoT).
  function authorNames(item) {
    const out = [];
    for (const a of (item && item.authors) || []) {
      const name = typeof a === "string" ? a : (a && a.name);
      if (name) out.push(name);
    }
    return out;
  }

  function relativeTime(iso) {
    if (!iso) return "—";
    const t = Date.parse(iso);
    if (isNaN(t)) return "—";
    const dsec = (Date.now() - t) / 1000;
    if (dsec < 60) return "just now";
    if (dsec < 3600) return `${Math.floor(dsec / 60)} min ago`;
    if (dsec < 86400) return `${Math.floor(dsec / 3600)} h ago`;
    const d = Math.floor(dsec / 86400);
    if (d < 7) return `${d} day${d === 1 ? "" : "s"} ago`;
    if (d < 30) return `${Math.floor(d / 7)} week${d < 14 ? "" : "s"} ago`;
    return new Date(t).toISOString().slice(0, 10);
  }

  window.LlmxiveData = {
    EMPTY, TAB_STAGE_SETS, IN_PROGRESS_STAGE_ORDER, STAGE_LABELS,
    loadPayload, projectsByTab, inProgressByStage, authorNames, relativeTime,
  };
})();
