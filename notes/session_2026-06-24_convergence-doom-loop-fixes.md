# Session 2026-06-24 — research-review convergence unblocked

**Goal:** drive ≥1 project brainstorm→complete-paper via the fully automated
pipeline, fixing only the platform/agents (general fixes, no per-project tweaks).

## Starting state
- Population (777): 488 validated, 173 flesh_out_in_progress, 110 paper_review,
  2 in_progress, 2 specified, 1 clarified, **1 research_review (PROJ-552)**.
  Middle of the pipeline empty → nothing flowing through.
- PROJ-552 (the ONLY brainstorm-grown project past in_progress → the goal
  vehicle) frozen 6 days in an `agent_blocked` doom loop.

## Root cause (general) of the research-review freeze + fixes shipped
1. **Noisy revision tasks** — `advancement._consolidate_action_items` trusted
   stored `action_items` (older reviewers stored section headers / positive
   observations / "(non-blocking)" recs). Now re-derives from the reviewer's
   curated "Required Changes" body section; filters stored items. → `3363455bd`
2. **Track-blind failsafe** — the zero-success failsafe hardcoded
   `last_command="lualatex"` + a `paper/source/main.tex` kickback for RESEARCH
   projects (no manuscript) → file-not-found → AGENT_BLOCKED. Made track-aware. → `3363455bd`
3. **delete_file crash** — `after_hashes[f]=""` violated the Sha256Field pattern
   → ValidationError crashed the run → reviewer-requested deletion = 0-success
   round. Deleted file now carries no after-hash. → `3363455bd`
4. **lualatex** — paper compile crashed when TeX absent (61 failures); now
   gracefully defers; pipeline-review.yml installs TeX. → `3363455bd`
5. **compute-and-fill value sourcing** — `_computation_context` only saw the few
   `execution_status.artifacts`, missing the computed report files (vif_report.csv
   etc.). Now scans `data/` (8 MB cap skips the 190 MB raw dump), surfaces small
   report CSV/JSON VALUES + whitelists them. → `e9ffb1570`
6. **compute-and-fill mapping prompt** — implementer skipped fillable placeholders
   on name mismatch; prompt now maps placeholder→value explicitly, prefers
   filling, keeps the anti-fabrication guard. → `10a4104f3`

All fixes general; full unit suite green (2325 passed). Memory notes:
`review-convergence-doom-loop`, `load-balanced-scheduler`.

## PROJ-552 result
Frozen→actively converging. 6/7 gating reviewers ACCEPT. Across rounds the
implementer filled REAL traceable values (VIF 1.078, excluded-count, checksums,
artifact-hash, data_quality_report counts). Operational recovery done (cleared
buggy revision_history [1,2,3], agent_blocked marker, zero-round counter).

## Remaining blocker (the honest crux — NOT a platform bug)
`data_quality` still blocks on `docs/reproducibility/invariant_coverage.md`:
`PLACEHOLDER_TOTAL` / `PLACEHOLDER_COVERAGE`. These are emitted by 552's OWN
generator `code/analysis/invariant_coverage.py`; the hyperbolic-volume coverage %
is a DERIVED value the analysis never computed, so the anti-fabrication guard
(correctly) won't let the implementer invent it. Fix must come from 552's
analysis CODE computing the value — the convergence loop's job over cycles.

## Identified NEXT general improvement
When a research reviewer blocks on a placeholder/uncomputed value in a GENERATED
artifact (doc names its generator, or maps to a `code/analysis/*.py` writer), the
revision should fix the GENERATOR (compute the value + re-run) rather than
hand-edit the doc (which regenerates). Substantial; flagged for design input.

## Pipeline health
Doom loops removed; kickback path is capped (IDEA_RETRY_CAP → human escalation),
so non-converging projects escalate gracefully (no infinite loop). Load-balanced
scheduler + unfiltered lanes now actively drain the 488/173/110 backlog.
