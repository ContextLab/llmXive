# Issue #295 (audit Phase 3 follow-up) — session note (2026-06-10)

Branch: `022-audit-phase3-followup`. Spec: `specs/022-audit-phase3-followup/`.
Commits: `3a54a28a` (credits), `79c9af21` (MCP + pilot + observability).

## What landed (all three #295 scope items)

1. **Orchestration-harness pilot → DECISION: KEEP BESPOKE.** smolagents
   CodeAgent ran the implementer micro-lane through a RouterModel
   adapter (all calls inside `chat_with_fallback`). Run 1 failed
   (sandbox blocks execute-what-you-wrote; step cap); run 2 passed only
   after authorizing `subprocess` (sandbox forfeited). Net orchestration
   LOC would increase. Evidence:
   `specs/022-audit-phase3-followup/pilot/RESULTS.md`. smolagents NOT a
   dependency; unused `langgraph` dep removed (bootstrap-era, zero
   imports).
2. **MCP server** (`src/llmxive/mcp_server/`, extra `llmxive[mcp]`,
   `python -m llmxive.mcp_server`): 8 tools wrapping librarian
   (semantic scholar / arXiv / theoremsearch / resolve_reference) +
   claims (register_and_resolve, claim_status) + credit_balance.
   Unit (tool inventory) + real stdio-client tests green.
3. **Credit-managed paid path** (maintainer-directed): measured live —
   `GET /api/v1/credits/balance`; **1 credit = $0.001 list-price USD**
   (1000× ratio measured via a real haiku call); 2000 credits/day ≈
   $2.00/day; reset 03:45Z (11:45 PM ET); metering is ASYNC (seconds–
   tens of seconds lag). Implementation: `backends/credits.py`
   (LLMXIVE_PAID_OPT_IN master switch default OFF;
   LLMXIVE_PAID_BUDGET_FRACTION cap default 0.75; 30s TTL cache;
   FAIL-CLOSED), guard wired into `DartmouthBackend.chat` (replaces the
   v1 hard block), real cost estimates in run-log (cost invariant
   relaxed ONLY under the switch), `llmxive credits` CLI,
   `paid_opt_in` schema/types const-false → boolean default false
   (registry pin test = visible friction; flipping an agent needs a
   written justification — see
   `specs/022-audit-phase3-followup/paid-backend-justification.md`).
   17 unit + 3 real-call tests (tiny haiku e2e ≈ 0.03 credits).

## As-you-go fixes

- Observability (notes/spec-015 item 5): `<missing>` reviser padding now
  records WHY (zero-parse vs skip) in `what_changed` →
  `_reviser_response.build_concern_responses` + 2 contract tests.
- mypy.ini stale sections pruned; ruff/mypy clean.
- The audit note's "silent [] on missing extraction prompt" follow-up
  was ALREADY fixed on main (extract.py raises since spec 021).

## Pipeline goal status (per notes/spec-015-review-status.md)

- Offline gate at baseline: 2323/16/0; post-change gate re-run this
  session (see below for final numbers in the PR).
- PROJ-552 still `clarified` since 06-02 (crons work other projects).
  Dispatched a SCOPED run: `gh run` id **27306941191** (330-min budget,
  main). Check on resume: `git pull` + PROJ-552 `current_stage` +
  whether a plan trail / honest kickback persisted.

## Open / next

- Merge PR for `022-audit-phase3-followup` once CI green.
- After dispatch 27306941191: inspect plan-stage progress (notes item 4
  — persist-before-abort + reasoning-volume levers if it still stalls).
- Future policy decisions (each needs its own justification): flipping
  specific agents (e.g. deep paper review) to `paid_opt_in: true`.

## FINAL STATUS (end of session, 2026-06-10 ~22:45 UTC)

- **PR #302 MERGED** (`0b949813`); issue #295 auto-closed. Lint
  follow-up `0ab4fad8` (ruff autofix that missed the credits commit).
- **4th as-you-go bug, found LIVE from the first 552 dispatch:**
  all-transient model-chain exhaustion (qwen deadline-hang +
  gpt-oss/gemma 302→outage) raised plain BackendError → stage panel
  WRONGLY escalated PROJ-552 to human_input_needed. Fixed in
  `4daafe58` (exhaustion with any transient-class failure →
  BackendUnavailable → clean abort, state preserved; 6 regression
  tests). State remediated in `6b3e60f1` (552 reset to `clarified`,
  stale marker removed — bug-#8-style remediation).
- **PROJ-552 re-dispatched on fixed main: run 27311831772**
  (plan stage, ~3h expected). ON RESUME: `git pull`, check
  `state/projects/PROJ-552-*.yaml` current_stage — expect `planned`
  (advance), an honest `convergence_kickback.yaml` (content concerns:
  OEIS ~249 power-analysis + Knot-Atlas-vs-arXiv data source), or a
  clean transient abort still at `clarified` (retry). NEVER
  human_input_needed for an outage now.

## ADDENDUM — full-pipeline audit → issue #303 (same session)

Audited paper-pipeline + activity logs + funnel at the maintainer's
request. Headline: 696 projects, 0 ever completed. Root causes (all
verified, evidence in #303):
1. **Severed paper-revision loop**: `graph.py:726-728` keeps only
   `.current_stage` from `advancement_evaluate`, DISCARDING
   `revision_spec_path` — the exact field the revision implementer is
   gated on (`implementer.py:348`). Proven by running evaluate()
   directly on PROJ-565 (instantly produced round-1 spec). Also CI
   persist steps don't `git add specs/`. → 1,233 reviewer runs in June,
   0 paper_accepted ever, 92 papers stuck 20+ days.
2. **Starved research funnel**: scheduler 1.5^rank gives paper_review
   (rank 18, never exits) ~1,478x vs flesh_out_complete (rank 1);
   no cron targets flesh_out_complete → 589 ideas, ~0 advancement.
3. 18/94 papers silently fall back to raw arXiv PDF (no failure
   artifact); only 2/76 restyled PDFs pass the PDF audit.
4. Maintainer directives folded in: human escalation must be RARE
   (auto-rebrainstorm infeasible ideas; batch cap-escalations; engine
   failures → auto-filed issues) + DOI sign-off via emoji-vote GitHub
   issue at AWAITING_PUBLICATION_SIGNOFF.

NEXT SESSION: execute #303 in order (fix 1 first — small + unblocks
everything; write the run_one_step PAPER_REVIEW regression test).
