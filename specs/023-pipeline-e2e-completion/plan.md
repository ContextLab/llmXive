# Implementation Plan: Pipeline End-to-End Completion

**Branch**: `023-pipeline-e2e-completion` | **Date**: 2026-06-10 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/023-pipeline-e2e-completion/spec.md`

## Summary

llmXive has never completed a project (issue #303). The root causes are
already empirically isolated (see [research.md](research.md)): the
advancement evaluator's review decisions are computed and then **discarded**
by the pipeline graph before persistence; the scheduler's exponential
stage weighting starves the idea-validation backlog (85% of projects) while
burning ~83% of runs on no-op re-reviews; CI persist steps omit `specs/`
(where revision work-specs live); de-escalation paths park projects for
humans on situations automation can handle; and the publication sign-off /
DOI mint path has never been exercised. The plan: (1) persist + consume
review decisions through the existing graph/advancement/implementer
machinery, (2) rebalance scheduling with queue-depth counterweighting and a
dedicated idea-validation lane plus intake throttling, (3) replace
human-escalation paths with bounded automation (archive + constrained
re-brainstorm; outage retry; auto-filed issues), (4) build the emoji-vote
publication sign-off gate on GitHub issues feeding the existing
Zenodo publisher, (5) add compile/audit failure reports + bounded repair
loop + honest site status, and (6) drive PROJ-552 (designated demo)
through every remaining phase to `posted` with a DOI, fixing every defect
encountered generally with regression tests.

## Technical Context

**Language/Version**: Python 3.11+ (existing `pyproject.toml` floor)
**Primary Dependencies**: existing `llmxive` package (no new runtime deps
expected); `requests` (Zenodo + GitHub REST, already used); PyYAML;
GitHub Actions cron lanes; Dartmouth Chat free models via the existing
backend router (paid path only via justification-gated `paid_opt_in`,
per Clarification 2026-06-10)
**Storage**: git-committed canonical state — `projects/<id>/` (project
state, reviews, paper), `state/` (run log, claims, revisions index),
`specs/auto-revisions/` (revision work-specs); no databases
**Testing**: pytest — offline suites `tests/unit tests/contract
tests/integration`; real-call suites `tests/real_call` gated by
`LLMXIVE_REAL_TESTS=1` + `DARTMOUTH_CHAT_API_KEY` (Constitution III);
`-m "not slow"` per-PR CI gate, nightly full
**Target Platform**: GitHub Actions (ubuntu) cron lanes + local macOS/Linux CLI
**Project Type**: single Python package (`src/llmxive/`) + CI workflows + static site (`web/` → `docs/`)
**Performance Goals**: scheduled lanes complete within existing CI budget;
no stage with eligible projects receives a near-zero pick share over a day
(FR-006); drain rate of fleshed-out queue exceeds intake (FR-007/008)
**Constraints**: free-first (Constitution IV); no hand-editing
pipeline-produced artifacts (FR-011); per-project locking must hold across
new lanes; publication idempotent (no double-minted DOIs); multi-day
wall-clock traversal monitored to completion
**Scale/Scope**: 696 existing projects (589 at flesh_out_complete, 92 at
paper review); ~150 agent runs/day; 94 papers on the public shelf

> Domain-specific empirical specifics (exact counts, dataset sizes, measured
> quantities) are deferred to the research/implementation phase. For any
> quantity stated here, cite its source/reference rather than asserting a
> measured value. (Counts above are from the issue-#303 audit of
> 2026-06-10; they are baselines, not targets.)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Evaluation | Status |
|-|-|-|
| I. Single Source of Truth | All fixes modify canonical modules in place (`pipeline/graph.py`, `pipeline/scheduler.py`, `agents/advancement.py`, `speckit/_publication_signoff.py`, `pipeline/zenodo.py`, `web_data.py`); the sign-off parser and repair loop reuse the existing revision/kickback machinery rather than adding parallel systems; no duplicated configs or prompts. | PASS |
| II. Verified Accuracy | Root causes verified empirically against the live repo (research.md cites file:line evidence and live run IDs); every external reference added during the traversal is fetch-verified; paper claims continue through the specs-016–020 claim stack. | PASS |
| III. Real-World Testing | Each fix lands with offline regression tests using injected-callable fakes (repo pattern, not mocks of our code) AND real-call/real-state demonstrations: a real project's review decision persisted and consumed, a real sign-off issue round-trip, a sandbox-DOI mint, the PROJ-552 traversal itself. | PASS |
| IV. Cost Effectiveness | Free models remain default everywhere; paid flips are justification-gated per agent within the daily credit budget (Clarification 2026-06-10) using the credit-managed guard from PR #302; Zenodo sandbox for test mints; GitHub free tiers for lanes/issues/site. | PASS |
| V. Fail Fast | Sign-off gate and publisher validate preconditions (maintainer list resolvable, token present, compiled PDF exists, audit green) before any mint; scheduler/lane changes validated by config tests; intake throttle is observable state, not silent. | PASS |
| VI. Convergent Review | No changes to the convergence protocol itself: the fix makes its verdicts *effective* (persisted, consumed, staleness-aware). Kickback caps and honest terminals are preserved; the sign-off gate sits after panel acceptance, as the sanctioned human decision. No point system is introduced. | PASS |

**Post-Phase-1 re-check (2026-06-10)**: design artifacts (data-model.md,
contracts/) introduce no new violations — entities map onto existing
records; the two new record types (sign-off record, paper status record)
each have exactly one canonical home. PASS.

## Project Structure

### Documentation (this feature)

```text
specs/023-pipeline-e2e-completion/
├── plan.md              # This file
├── spec.md              # Feature specification (committed b3bc8eb0)
├── research.md          # Phase 0: verified root-cause evidence + decisions
├── data-model.md        # Phase 1: entities and state transitions
├── quickstart.md        # Phase 1: how to run/verify each piece
├── contracts/           # Phase 1: record/interface contracts
│   ├── signoff-issue.md         # sign-off issue format + vote parsing rules
│   ├── paper-status-record.md   # per-paper compile/audit status schema
│   └── escalation-record.md     # exhaustion-evidence escalation schema
├── checklists/requirements.md   # spec quality checklist (all pass)
└── tasks.md             # Phase 2 (/speckit-tasks — not created by plan)
```

### Source Code (repository root)

```text
src/llmxive/
├── pipeline/
│   ├── graph.py            # FIX: persist advancement results (US1); dispatch gating
│   ├── scheduler.py        # FIX: queue-depth counterweight, lanes, throttle (US2)
│   ├── zenodo.py           # publication: idempotent DOI mint (US5)
│   └── pdf_pipeline/       # compile/restyle: failure reports (US6)
├── agents/
│   ├── advancement.py      # evaluator (works today); staleness handling (US1)
│   ├── implementer.py      # revision implementer; consumes work-spec (US1)
│   ├── publisher.py        # posted-state writer; idempotence (US5)
│   └── lifecycle.py        # flesh-out verdict → archive/re-brainstorm (US4)
├── speckit/
│   └── _publication_signoff.py  # sign-off gate: issue open/parse/remind (US5)
├── audit/                  # rendering audit → repair-work conversion (US6)
├── state/                  # escalation records, paper status records
└── web_data.py             # site status truthfulness (US6)

.github/workflows/          # persist `specs/`; idea-validation lane; signoff-poll lane
tests/
├── unit/  tests/contract/  tests/integration/   # offline regressions per fix
└── real_call/              # real-state / real-API demonstrations
```

**Structure Decision**: Single existing Python package; every change is an
in-place fix to the canonical module listed above (Constitution I). New
files are limited to: the sign-off vote parser additions inside
`speckit/_publication_signoff.py`'s module family, per-paper status records
under `state/`, contracts/tests, and one or two new CI lane workflow files.

## Complexity Tracking

> No Constitution Check violations — table not required.
