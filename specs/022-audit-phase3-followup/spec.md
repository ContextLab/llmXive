# Spec 022 — Audit #294 Phase 3 follow-up (issue #295)

**Status:** in progress (2026-06-10)
**Issue:** #295 — orchestration-harness pilot + MCP exposure of librarian/claim
tools + paid `paid_opt_in` backend policy.
**Branch:** `022-audit-phase3-followup`

Issue #295 tracks the deliberately-deferred optional phase of audit #294
(Phases 0–2 landed via spec 021). Three scope items, each with its own
acceptance bar:

## Scope item 1 — One-lane orchestration-harness pilot

Evaluate replacing parts of the bespoke `src/llmxive/pipeline/` loop
(checkpointing, retries, context offload) with a harness (`smolagents`
preferred for the implementer/code-execution lane; LangGraph noted for
planning lanes).

**Adoption threshold (verbatim intent from the audit):** adopt only if a
one-lane pilot reduces orchestration LOC and passes the same
eval/real-call gates; otherwise keep the bespoke pipeline.

**Constraints:**
- Constitution I: the pilot must not fork the lifecycle state machine —
  the harness runs the loop, llmXive owns the semantics (stage dicts,
  convergence protocol, claim layer, git-as-database stay in-house).
- The pilot must keep ALL model calls inside llmXive's router
  (`backends/router.py` chat_with_fallback: free-model guard, per-model
  circuit breakers, peer-model fallback) — a harness that bypasses the
  router is disqualified outright.

**Method:** the pilot lives in `specs/022-audit-phase3-followup/pilot/`
(NOT in `src/`) until/unless the adoption threshold is met — wiring a
permanent flag into production for a rejected harness would itself add
the orchestration LOC the threshold exists to reduce. The pilot runs the
representative implementer micro-lane (pick task → LLM implements →
write file → validate → check off) twice on the same fixture with the
same free Dartmouth model: once through the bespoke seam, once through a
smolagents `CodeAgent` whose model adapter delegates to
`chat_with_fallback`. Measured: orchestration LOC delta; gate parity
(does the harness lane complete the task the bespoke lane completes).
Result + decision recorded in `pilot/RESULTS.md`.

**Lane mapping (from the code survey):**
- Bespoke implementer orchestration: ~222 LOC
  (`speckit/implement_cmd.py` task picker :52-76, verdict handling
  :212-456, checkbox checkpointing :412-420; dispatched from
  `pipeline/graph.py:439`).
- Stage-level orchestration that stays in-house regardless: ~580 LOC
  (`graph.py` run_one_step + _decide_next_stage, `_kickback.py`,
  `scheduler.py`, `lock.py`).
- Semantics that stay in-house regardless: ~515 LOC (stage dicts,
  convergence gates, escalation markers, kickback persistence).

## Scope item 2 — MCP servers for librarian + claim-verifier tools

Expose the Semantic Scholar / arXiv / TheoremSearch search-and-verify
tools and the claims register→resolve→cache layer once via MCP
(`src/llmxive/mcp_server/`, optional dependency extra `mcp`), so they
are reusable across whichever harness (or none) is chosen, decoupled
from the bespoke router.

**Acceptance:** `python -m llmxive.mcp_server` serves stdio MCP; tools
wrap the existing librarian/claims functions (no reimplementation);
offline unit test asserts the tool inventory; real-call test drives the
server over stdio with a real arXiv query + live credit balance.

## Scope item 3 — Credit-managed `paid_opt_in` backend

Maintainer decision (issue #295 comment, 2026-06-10): the Dartmouth
Chat daily credit allocation may be used for paid models and still
satisfies free-first, provided credits are (a) managed carefully and
(b) never exceeded. The exploration the maintainer requested was
performed live on 2026-06-10 — findings in
`paid-backend-justification.md` (1 credit = $0.001 list-price
equivalent; 2000 credits/day ≈ $2.00/day; balance endpoint
`GET /api/v1/credits/balance`; reset 03:45Z = 11:45 PM ET).

**Acceptance (landed in commit 3a54a28a):**
- `backends/credits.py`: live balance fetch + FAIL-CLOSED guard;
  master switch `LLMXIVE_PAID_OPT_IN` (default OFF); budget cap
  `LLMXIVE_PAID_BUDGET_FRACTION` (default 75% of max_budget).
- `DartmouthBackend.chat`: paid models pass through the guard instead
  of the unconditional v1 hard block; opted-in calls log REAL cost
  estimates.
- Run-log cost invariant relaxed ONLY under the same switch.
- Registry schema/types: `paid_opt_in` const-false → boolean default
  false; the all-false registry pin test remains as visible friction.
- `llmxive credits` CLI; 17 offline + 3 real-call tests (incl. a tiny
  opted-in haiku e2e measuring server-side metering).

**Out of scope (future, needs separate justification per agent):**
actually flipping any registry agent to `paid_opt_in: true` (e.g. deep
paper review). The machinery is ready; each flip is its own reviewed
decision.
