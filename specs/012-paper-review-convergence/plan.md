# Implementation Plan: Paper Review Convergence

**Branch**: `012-paper-review-convergence` | **Date**: 2026-05-17 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/012-paper-review-convergence/spec.md`

## Summary

Make the paper-review pipeline *converge* instead of oscillating forever between `paper_review` and `paper_minor_revision`. Three coordinated changes:

1. **Acceptance gate change**: advance to `paper_accepted` when every required specialist's *most-recent (non-stale)* verdict is `accept`. Drop the redundant point threshold.
2. **Structured action items + re-review protocol**: every review now emits a list of `ActionItem{id,text,severity}`. Re-reviewers (per-specialist, only if THAT specialist has prior reviews) ask only "(a) prior items addressed? (b) new issues?" — eliminating endless-nit oscillation.
3. **Three-way revision routing + auto-planned revision pipeline**: route by max severity (writing→`paper_minor_revision`, science→`paper_major_revision_science`, fatal→`brainstormed`). On a revision transition, auto-kick `speckit-{specify,clarify,plan,tasks,analyze}` for the revision spec, parking the project at a new `paper_revision_in_progress` stage (idempotent — scheduler skips). When all 5 stages clear, flip to `ready_for_implementation` flag for an implementer agent to pick up.

arXiv-intake guardrail: papers without a `paper/source/` we can mutate (third-party submissions) skip the writing-revision path entirely — they record an `upstream_feedback.yaml` annotation and resolve to `paper_accepted` (with caveats) or `brainstormed` (rejection).

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: pydantic 2.x (schema validation), pyyaml (frontmatter), Dartmouth Chat API (LLM backend via `llmxive.backends.dartmouth`), Hugging Face Inference (fallback backend)
**Storage**: Filesystem under `projects/<PROJ-ID>/` (per-project artifacts), `state/projects/<PROJ-ID>.yaml` (project state), `state/run-log/<YYYY-MM>/<run-id>.jsonl` (audit trail), `state/citations/<PROJ-ID>.yaml` (verified citations)
**Testing**: pytest 9.x; tests live under `tests/{unit,contract,real_call,integration}/`. Real-call tests gated on `LLMXIVE_REAL_TESTS=1` per Constitution III.
**Target Platform**: Linux server (GitHub Actions CI) + macOS dev (15.x); Python 3.11 on both.
**Project Type**: Multi-component CLI + cron-driven pipeline (no UI in scope for this feature; web dashboard reads regenerated state).
**Performance Goals**: A revision-spec auto-plan (5 speckit stages) MUST complete within one cron tick (16-hour budget; expected ≤30 minutes wall on Dartmouth at current token rates). Re-review of a paper with ≥1 prior round MUST complete in ≤ the time of a fresh review.
**Constraints**: NO breaking changes to existing `ReviewRecord` schema — `action_items` is additive (optional default `[]` for back-compat with older records). NO breaking changes to existing stage graph except additive: `paper_revision_in_progress` is new. Scheduler concurrency: at most one revision-spec auto-plan per project at a time (enforced by `paper_revision_in_progress` gate).
**Scale/Scope**: ~12 specialist reviewers per paper × ~30 active arxiv-intake papers + ~10 home-grown papers in flight at any time = ~500 review records/week. Action-item ID space is per-project, expected ≤200 distinct items per paper lifetime.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I — Single Source of Truth (NON-NEGOTIABLE)

- ✅ Stage definitions live in `src/llmxive/types.py` `Stage` enum. We add ONE new value (`PAPER_REVISION_IN_PROGRESS`) — no parallel state machine.
- ✅ Advancement logic lives in `src/llmxive/agents/advancement.py` — single decision point. We modify the existing function; do NOT create a parallel `advancement_v2.py`.
- ✅ Reviewer prompts live under `agents/prompts/` keyed by registry — we modify existing prompt files and add the re-review block as a shared snippet (single canonical location), not per-prompt copy-paste.
- ✅ `ReviewRecord` schema lives in `src/llmxive/types.py` — we add `action_items` field there once; everyone (writers + readers) consumes the same schema.

### Principle II — Verified Accuracy (NON-NEGOTIABLE)

- ✅ Action items are LLM output; the system records them verbatim as the LLM emitted them. No claim about *what* the LLM said is fabricated.
- ✅ Re-review protocol references prior action items by stable ID — the references resolve to actual prior records; we never invent prior items.
- ✅ The "consolidated action items" passed to the auto-planned revision pipeline is a deduplication of real prior records, not a synthesis.

### Principle III — Robustness & Reliability (Real-World Testing)

- ✅ The 5-stage auto-plan pipeline MUST be tested with REAL Dartmouth calls in `tests/real_call/test_paper_review_convergence_e2e.py` — drive a fixture project through one full review→revision→re-review cycle and assert convergence.
- ✅ The re-review protocol MUST be tested with a REAL LLM call (not mocked) to verify the two-question prompt actually elicits accept-or-list-unaddressed behavior.
- ✅ arXiv-intake guardrail MUST be tested on a real arxiv-intake fixture (we have PROJ-564/566/etc. on disk).
- Mock-based unit tests are added as a fast-feedback layer for pure-logic pieces (severity ordering, ID stability, classification routing) ONLY after the real-call test proves the wired-up behavior works.

### Principle IV — Cost Effectiveness (Free-First)

- ✅ Dartmouth Chat is free for this project (per memory note `dartmouth-api-free.md`). The new 5-stage auto-plan adds ~5 LLM calls per revision round — well within the free budget.
- ✅ Re-review protocol is *cheaper* than full critique (shorter prompt focused on diff-check) — net cost reduction.
- ✅ Convergence reduces total LLM spend by terminating ping-pong loops that today consume ~13 specialist calls × every cron tick × indefinitely.

### Principle V — Fail Fast

- ✅ Action-item validation happens at `handle_response` time (pydantic schema on `ReviewRecord`). A malformed `action_items` field fails the review with a clear error before the project state moves.
- ✅ The 5-stage auto-plan validates each stage's output before proceeding to the next (`plan.md` must exist before `tasks.md`; `tasks.md` must have ≥1 task before `analyze`; etc.) — fail fast at each boundary.
- ✅ `paper_revision_blocked` state is the explicit fail-fast outcome when the analyzer can't reach zero findings in 3 iterations — no silent advancement.
- ✅ arXiv-intake detection (presence of `paper/metadata.json` + absence of feature dir) MUST be evaluated before the revision pipeline is dispatched, not after.

**Verdict: PASS** — all five principles are satisfied without complexity-tracking justifications.

## Project Structure

### Documentation (this feature)

```text
specs/012-paper-review-convergence/
├── plan.md              # This file
├── research.md          # Phase 0: Auto-plan invocation strategy + ID-stability hash + recovery path
├── data-model.md        # Phase 1: ReviewRecord (extended), ActionItem, RevisionSpec, UpstreamFeedbackAnnotation
├── quickstart.md        # Phase 1: How to drive a paper through revision+re-review end-to-end
├── contracts/
│   ├── action_item.md           # ActionItem record shape + ID generation
│   ├── review_record_v2.md      # Extended ReviewRecord schema (action_items added)
│   ├── revision_spec.md         # Layout of an auto-planned revision spec dir
│   └── upstream_feedback.md     # arXiv-intake annotation file shape
├── checklists/
│   └── requirements.md  # (already created)
└── tasks.md             # Phase 2 output (created by /speckit-tasks)
```

### Source Code (repository root)

```text
src/llmxive/
├── agents/
│   ├── advancement.py            # MODIFY — three-way routing, most-recent-verdict gate
│   ├── paper_reviewer.py         # MODIFY — emit action_items; re-review prompt mode (per-specialist toggle)
│   ├── revision_planner.py       # NEW — auto-kicks speckit-{specify,clarify,plan,tasks,analyze}
│   └── upstream_feedback.py      # NEW — arxiv-intake annotation writer
├── lifecycle.py                  # MODIFY — add PAPER_REVISION_IN_PROGRESS, allowed transitions, scheduler skip rule
├── types.py                      # MODIFY — Stage enum + ReviewRecord (add action_items) + ActionItem class
└── state/
    └── reviews.py                # MODIFY — list_for must surface action_items; loader/writer pair extends to new field

agents/prompts/
├── paper_reviewer.md             # MODIFY — instruct emit of action_items YAML block
├── paper_reviewer_*.md           # MODIFY (12 files) — same action_items block, severity guidance per specialty
└── _shared/
    └── rereview_block.md         # NEW — shared "two-question protocol" snippet, included by all paper_reviewer prompts when prior reviews exist

tests/
├── unit/
│   ├── test_action_item_schema.py             # NEW
│   ├── test_advancement_three_way_routing.py  # NEW — pure logic: max-severity wins, all-accept gate, arxiv-intake guardrail
│   ├── test_paper_reviewer_action_items.py    # NEW — frontmatter parse + emit
│   ├── test_rereview_per_specialist_toggle.py # NEW — toggle activation logic
│   └── test_revision_planner_unit.py          # NEW — 5-stage state machine on fakes
├── real_call/
│   └── test_paper_review_convergence_e2e.py   # NEW — full cycle on a fixture project
└── integration/
    └── test_revision_in_progress_idempotency.py  # NEW — scheduler skips locked projects
```

**Structure Decision**: Single-project Python module (DEFAULT). All new modules live under `src/llmxive/agents/`. The constitution's "single source of truth" requires modifications happen in the canonical files, not parallel copies. The 12 specialist prompts already exist; we modify them in place to emit action_items + include the shared re-review snippet via a small template helper. No new package, no new directory tree at the top level.

## Complexity Tracking

(No constitution violations to justify.)
