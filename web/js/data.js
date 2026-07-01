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
    // external-paper intake triage (spec 024): ingested papers awaiting
    // code-vs-no-code reprocessing into the pipeline (drained each tick)
    "paper_ingested",
    // research lane — only REAL resting milestones (transient -ing states are
    // collapsed into their milestone via STAGE_DISPLAY_PHASE below)
    "brainstormed", "flesh_out_complete",
    "validator_revise", "validated", "project_initialized",
    "specified", "clarified",
    "planned", "tasked", "analyzed",
    "in_progress", "research_complete", "research_review",
    "research_full_revision", "research_accepted",
    // paper lane (paper_accepted is collapsed into awaiting sign-off)
    "paper_drafting_init", "paper_specified", "paper_clarified", "paper_planned",
    "paper_tasked", "paper_analyzed", "paper_in_progress", "paper_complete",
    "paper_review", "awaiting_publication_signoff",
    // needs-attention / terminal-but-not-published states (kept visible so no
    // project silently disappears; only render when non-empty)
    "validator_rejected", "research_rejected", "paper_fundamental_flaws",
    "publish_blocked", "human_input_needed", "blocked", "agent_blocked",
  ];

  // Some raw lifecycle stages are NOT real resting phases — they are the
  // transient "work-in-progress" of the milestone the project still sits at, or
  // a state that is immediately superseded. They MUST NOT get their own board
  // column; a project at one is DISPLAYED under its canonical milestone:
  //   * a plan being analyzed is still "tasked" (the user's example),
  //   * being clarified is still "specified", being fleshed out still "brainstormed",
  //   * an accepted paper is already "awaiting sign-off".
  // (`in_progress`/`paper_in_progress` are NOT here — those ARE real phases:
  // the research/paper implementation.)
  const STAGE_DISPLAY_PHASE = {
    flesh_out_in_progress: "brainstormed",
    clarify_in_progress: "specified",
    analyze_in_progress: "tasked",
    paper_accepted: "awaiting_publication_signoff",
  };
  const displayPhase = (stage) => STAGE_DISPLAY_PHASE[stage] || stage;

  // The forward research + paper pipeline stages (NOT the needs-attention /
  // terminal block above). The In-Progress board renders a column for EVERY one
  // of these always — even when momentarily empty — so the complete pipeline
  // skeleton, including the whole paper lane, is visible as a kanban at a glance
  // (previously empty stages rendered no column, so the mostly-empty paper lane
  // looked "missing"). Empty needs-attention/terminal stages stay hidden until
  // a project actually lands there. Revision states (validator_revise,
  // research_full_revision) are deliberately excluded — they show only when used.
  const PIPELINE_FLOW_STAGES = new Set([
    "brainstormed", "flesh_out_complete",
    "validated", "project_initialized",
    "specified", "clarified",
    "planned", "tasked", "analyzed",
    "in_progress", "research_complete", "research_review", "research_accepted",
    "paper_drafting_init", "paper_specified", "paper_clarified", "paper_planned",
    "paper_tasked", "paper_analyzed", "paper_in_progress", "paper_complete",
    "paper_review", "awaiting_publication_signoff",
  ]);

  // Stage → tab mapping (FR-005). Mirrors src/llmxive/web_data.py. TWO project
  // tabs: `papers` (Published = `posted` only) and `inProgress` (every other
  // lifecycle stage, DERIVED from IN_PROGRESS_STAGE_ORDER so tab membership and
  // the sectioned layout can never drift).
  const TAB_STAGE_SETS = {
    papers:     new Set(["posted"]),
    // Tab membership includes the collapsed raw stages too (they display under a
    // milestone column but a project there is still In-Progress, not hidden).
    inProgress: new Set([...IN_PROGRESS_STAGE_ORDER, ...Object.keys(STAGE_DISPLAY_PHASE)]),
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
    in_progress: "Implementation",
    research_complete: "Research complete",
    research_review: "Research review",
    research_accepted: "Research accepted",
    research_minor_revision: "Research minor revision",
    research_full_revision: "Research full revision",
    research_rejected: "Rejected",
    paper_ingested: "Paper intake",
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
    reviewed_preprint: "Reviewed preprint",
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
    // Reviewed Preprints are a DEDICATED, server-built collection (third-party
    // papers llmXive reviewed but never authored) — not filtered from `projects`.
    buckets.reviewedPreprints = (payload.reviewed_preprints || []).slice();
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
      // Bucket by DISPLAY phase: a project at a transient/collapsed raw stage
      // (e.g. analyze_in_progress) lands in its milestone column (tasked).
      const phase = displayPhase(p.current_stage);
      if (phase in byStage) byStage[phase].push(p);
    }
    const sections = [];
    for (const stage of IN_PROGRESS_STAGE_ORDER) {
      const items = byStage[stage];
      // Always emit the forward pipeline stages (so the paper lane is visible
      // even when empty); other (needs-attention/terminal) stages only when populated.
      if (!items.length && !PIPELINE_FLOW_STAGES.has(stage)) continue;
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
    EMPTY, TAB_STAGE_SETS, IN_PROGRESS_STAGE_ORDER, PIPELINE_FLOW_STAGES, STAGE_LABELS,
    STAGE_DISPLAY_PHASE, displayPhase,
    loadPayload, projectsByTab, inProgressByStage, authorNames, relativeTime,
  };
})();
