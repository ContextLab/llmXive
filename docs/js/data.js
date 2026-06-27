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

  // Stage → tab mapping (FR-005). Mirrors src/llmxive/web_data.py.
  //
  // The dashboard now exposes just TWO project tabs: `papers` (Published) and
  // a single consolidated `inProgress` (In Progress) tab. The In-Progress tab
  // is the UNION of every non-published, non-archived project stage — what
  // used to be the separate "paper pipeline", "in progress", "research plans",
  // "research specs", and "backlog" tabs. Any project that is not yet
  // published (and is not a terminal/archived state) shows up under In
  // Progress, so a project never silently falls off the board between stages.
  const TAB_STAGE_SETS = {
    // Published papers (FR-029): only `posted` qualifies as published.
    // Spec 013 made `paper_accepted` a transient pre-publication state —
    // the `paper_publisher` agent picks those up and transitions them
    // to `posted` once Zenodo confirms the DOI. So `paper_accepted` no
    // longer belongs on the published tab.
    papers:     new Set(["posted"]),
    // In Progress — the union of the former backlog + research-specs +
    // research-plans + in-progress + paper-pipeline buckets.
    inProgress: new Set([
      // — former "backlog" (idea + validation lane) —
      "brainstormed", "flesh_out_in_progress", "flesh_out_complete",
      "validated", "project_initialized",
      // — former "research specs" —
      "specified", "clarify_in_progress", "clarified",
      // — former "research plans" —
      "planned", "tasked", "analyze_in_progress", "analyzed",
      // — former "in progress" (research execution + research review) —
      "in_progress", "research_complete", "research_review",
      "research_minor_revision", "research_full_revision", "research_accepted",
      // — former "paper pipeline" —
      "paper_drafting_init", "paper_specified", "paper_clarified", "paper_planned",
      "paper_tasked", "paper_analyzed", "paper_in_progress", "paper_complete",
      "paper_review", "paper_minor_revision", "paper_major_revision_writing",
      "paper_major_revision_science", "paper_fundamental_flaws",
      // Spec 012/013 convergence-pipeline stages (in-flight; NOT on the
      // published papers tab):
      "paper_revision_in_progress", "ready_for_implementation",
      "paper_revision_blocked",
      // Spec 013: paper_accepted is transient (waiting for publisher);
      // publish_blocked is operator-action-needed.
      "paper_accepted", "publish_blocked",
    ]),
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
    EMPTY, TAB_STAGE_SETS, STAGE_LABELS,
    loadPayload, projectsByTab, relativeTime,
  };
})();
