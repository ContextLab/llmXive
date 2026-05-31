# Phase 0 Research — Pipeline Convergence Protocol

Resolves the technical unknowns in `plan.md` Technical Context. Each item: **Decision / Rationale / Alternatives**. All grounded in the 2026-05-27 code audit (design doc SSoT) and the Phase-0 codebase map.

## R1 — Token-budget measurement for the summarizer

**Decision**: Add a single budget helper in `tools/summarize.py`: `estimate_tokens(text) -> int` using a char/4 heuristic (consistent with the existing `paper_reviewer.py:56` "180KB ≈ 45K tokens"), and a model→budget map (`qwen.qwen3.5-122b` → 32_768, matching `router.py:78-87`) with a configurable completion-headroom reserve (default ~25% of budget). `summarize(..., token_budget=None)` resolves the budget from the model when not given.
**Rationale**: There is no token counter today (no `tiktoken`); the codebase already sizes by chars. A heuristic is honest, dependency-free, and conservative (round up). Const. IV (no extra paid/heavy deps) and Const. V (cheap up-front check).
**Alternatives**: `tiktoken` (rejected — built for OpenAI BPE, not qwen; adds a dep for marginal accuracy); a live "count via the backend" call (rejected — wastes a call, the budget only needs to be approximate with headroom).

## R2 — Inode-table pointer format (`summarize`/`desummarize`)

**Decision**: When content fits the budget, `summarize` returns it verbatim. When it overflows, `summarize` writes an on-disk hierarchy under `<cache_dir>/<sha256[:16]>/` containing: (a) `manifest.json` — ordered list of entries `{element_id, kind, file, critical (verbatim list), summary}`; (b) one content file per chunk; (c) for deep overflow, a chunk's entry may itself be a pointer to a nested `manifest.json` (recursion). `summarize` *returns a compact pointer block* (a short, model-readable text naming the manifest path + the verbatim critical elements that fit) — never a lossy prose blob. `desummarize(text, *, want=None, max_depth=…)` recursively resolves pointer blocks → underlying content (optionally only the entries matching `want`, e.g. a specific URL/FR-id). Deterministic **extraction** (regex/parse, no LLM) collects URLs/DOIs/arXiv-ids/citation-keys/FR-SC-task-ids; goal-targeted LLM summarization (reusing the `paper_reviewer` per-chunk call) handles prose. Critical elements are copied into every level's `critical` list (no recursion loss). Reuses `_cached_summarize`'s sha256 disk-memoization.
**Rationale**: Directly implements the user's clarified "inode-table" decision — content is never silently dropped; it lives on disk and is paged in recursively. JSON manifest + content files = inspectable, testable, SSoT. Generalizes (not forks) the existing chunk+cache machinery.
**Alternatives**: A flat single-level summary (rejected — the design's superseded "truncate-with-notice", loses elements); an embedded vector store (rejected — overkill, adds deps, opaque, violates verbatim-preservation requirement).

## R3 — Convergence engine model (generalizing the panels)

**Decision**: `convergence/engine.py` is backend-agnostic and operates on **callables**: a `ReviewSpec` supplies `reviewers: list[Reviewer]` (each a callable `(artifacts, prior_concerns, advisory_inputs, constitution) -> list[Concern]|list[Verdict]`) and a `reviser` callable `(artifacts, concerns) -> ConcernResponse`. Existing agents (`ResearchReviewerAgent`, `PaperReviewerAgent`, speckit revisers) are wrapped as adapters; the new early-step panels are thin prompt-driven reviewers. R3 reuses `agents/prompts/_shared/rereview_block.md` (already a diff-against-prior-action-items mechanism). `Concern` maps onto the existing `ActionItem` (id, text, severity); `severity` is widened to the design's `{trivial, code, methodology, requirement, fatal, writing, science}` set via a mapping table (back-compat with the current `writing|science|fatal`).
**Rationale**: Callable parameterization is the SSoT way to make one engine serve every step (Const. I). Reusing `rereview_block` and `ActionItem` avoids forking. The engine owns the loop/cap/budget/inspection so no step re-implements it.
**Alternatives**: Subclass-per-step engine (rejected — duplication); leaving the tasker loop separate (rejected — it's the bespoke non-converging loop we're replacing).

## R4 — Adaptive kickback routing

**Decision**: `convergence/kickback.py` maps the **worst unresolved concern severity** → a prior `Stage` via a per-unit table (design §6): idea→`BRAINSTORMED`; spec→`PROJECT_INITIALIZED` (or `FLESH_OUT_IN_PROGRESS` if root-cause is the idea); plan→`CLARIFIED`; tasks→`PLANNED`; research-unit→ idea/plan/tasks/in-loop by severity; paper twins→ `PAPER_DRAFTING_INIT`/`PAPER_CLARIFIED`/`PAPER_PLANNED` (and to the research side if the science is the root cause). Emits a `KickbackRecord` (unresolved concerns + artifact/review links + plain-language reason). Reuses the existing revision `Stage` values; the legacy graph transient stages and `advancement.py` spec-012 routing are **deleted** in favor of this single table.
**Rationale**: Collapses the two parallel schemes (#51 / discrepancy #6) into one SSoT router. Adaptive-by-severity is the design decision.
**Alternatives**: Always-kick-to-immediately-prior-stage (rejected — loses the root-cause adaptivity); keep both schemes (rejected — the bug we're fixing).

## R5 — No global kickback cap; honest convergence

**Decision**: The engine keeps the **per-step 3-round** `[R2→R3]` cap (→ kickback). There is **no global cap** on kickbacks; a `ConvergenceResult.converged` flag always reflects reality (never `passed` when unresolved). A `ProgressRecord` per kickback records the unresolved-concern set so a non-improving cycle (identical unresolved set recurring) is inspectable, but the engine never abandons a convergable project. Genuine agent/tool/backend failures route to `human_input_needed`/`*_blocked` (fail-fast).
**Rationale**: Clarified user decision (FR-017). Reconciled with Const. V in the Constitution Check.
**Alternatives**: Hard total cap (rejected by the user — would dead-end good work).

## R6 — Point removal + advancement/graph collapse

**Decision**: Delete `advancement.py:_award_review_points` and the `RESEARCH_ACCEPT_THRESHOLD`/`PAPER_ACCEPT_THRESHOLD` comparisons; remove the thresholds from `config.py`. `advancement.py` becomes a thin function that reads a `ConvergenceResult` (and runs the kickback router). `graph._decide_next_stage` delegates all reviewable-stage transitions to the engine outcome; the hardcoded transient-stage routing block is removed. `ReviewRecord.score` (the 0.0/0.5/1.0 field) is retained in the schema for back-compat of stored records but is **no longer read** by any gate.
**Rationale**: FR-019/020/034; one SSoT gate. Keeping `score` as a dead-but-present field avoids a destructive schema migration of 1257 existing project YAMLs while guaranteeing no gate reads it (verified by grep).
**Alternatives**: Hard schema migration removing `score` (rejected — risky, unnecessary; grep-verified non-use is sufficient).

## R7 — Manual DOI sign-off (FR-054)

**Decision**: Add a publication-gate stage. When a project reaches `paper_accepted`, the wired publisher first assembles the final PDF + a `pending_publication.yaml` (DOI metadata, file manifest, content hash) and **halts at a new `awaiting_publication_signoff` state**, writing a clear run-log entry. The maintainer approves by an explicit recorded action — a CLI command `llmxive publish-approve <PROJ-ID>` (writes `publication_signoff.yaml` with `approved_by`, `approved_at`, `content_hash`). Only with a matching, current signoff does the publisher mint the real Zenodo DOI, close the issue, post to the site, and write `publication.yaml`. The same gate applies to living-document version DOIs.
**Rationale**: Implements the clarified human checkpoint while keeping real public publication. A stage + signoff file is inspectable, idempotent, and content-hash-bound (a changed PDF invalidates a stale signoff). Const. V (precondition) + II (verified before publish).
**Alternatives**: Interactive blocking prompt inside the cron (rejected — cron is non-interactive); auto-publish with post-hoc review (rejected — DOIs are irreversible).

## R8 — Review-intake triage + personality cron

**Decision**: `convergence/triage.py` exposes `triage(review, *, stage_context) -> TriageRecord`: (1) a quality filter (an LLM judgment + deterministic checks: non-empty, on-topic to the project, evidence-bearing, family-friendly/safe) → ignore if it fails; (2) stage-aware aspect-mapping (the current stage's lenses) → the matched reviewer(s) receive the review text as an extra advisory input in their R1/R3 prompt. Quality+safe+on-topic reviews are copied into the project's preserved review log; failures are excluded. The personality cron (`agents/personality.py:tick`) keeps writing review `.md` files but they now flow through `triage` (advisory), never point-scoring. Human GitHub comments flow through the same `triage`.
**Rationale**: FR-021/022/023; unifies human + personality into one advisory flow. Reuses the existing review-file ingestion + personality producer.
**Alternatives**: Separate human and personality flows (rejected — two code paths, violates SSoT).

## R9 — arXiv / theoremsearch resilience

**Decision**: Wrap the arXiv/theoremsearch HTTP calls in a small retry-with-backoff that, on transient 429/503/timeout, returns a graceful "source temporarily unavailable" result (empty enrichment + a recorded notice) instead of raising — because theoremsearch is an *optional enrichment*, not a precondition. Hard failures (4xx other than 429, malformed responses) still raise.
**Rationale**: Folded-in standalone fix (spec FR-040). This is the one place "best-effort continuation" is acceptable under Const. V because the operation is non-critical enrichment, not a gating precondition; the distinction is documented.
**Alternatives**: Hard-fail on any non-200 (rejected — transient arXiv 429s would needlessly block math-theory projects); silent swallow of all errors (rejected — hides real outages; we record a notice).

## R10 — Calibration harness (differential clean-vs-injected)

**Decision**: `calibration/injectors.py` deterministically injects one known flaw into a good artifact (per the 6 flaw kinds) tagged with the lens that must catch it. `calibration/differential.py` runs a panel on the clean and injected forms, asserts the injected flaw appears in the injected verdicts (correct lens) and not in the clean ones, and writes any **extra** findings to a markdown adjudication report for the maintainer (Claude pre-evaluates true-vs-false-positive; maintainer spot-checks). `calibration/domains.py` registers ≥1 real peer-reviewed anchor paper per `LIBRARIAN_DEFAULT_FIELDS` (9 fields) + the HF-daily and backlog samples, with a held-out field flag. No fixed numeric over-flag ceiling; sensitivity is tuned adaptively from the reports.
**Rationale**: Implements the clarified calibration method exactly; anti-circular (real papers as ground truth); manual adjudication is the QC. Const. II + III.
**Alternatives**: Fixed % over-flag threshold (rejected by the user); LLM-judges-LLM auto-scoring (rejected — circular).
