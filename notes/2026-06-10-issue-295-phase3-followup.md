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
