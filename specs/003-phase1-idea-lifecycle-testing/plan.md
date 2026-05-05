# Implementation Plan: Phase 1 (Idea Lifecycle) End-to-End Testing & Diagnostics

**Branch**: `003-phase1-idea-lifecycle-testing` | **Date**: 2026-05-04 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/003-phase1-idea-lifecycle-testing/spec.md`

## Summary

Drive the three Phase-1 agents (`brainstorm`, `flesh_out`, `idea_selector`) through the production code path against the Dartmouth Chat backend on real, committed `projects/PROJ-NNN-*` directories. Iterate prompt/code/registry until at least 2-3 projects survive all three agents' quality bars; record every artifact, run-log entry, state YAML, and iteration `git diff` verbatim in a single diagnostic report; emit a `carry-forward.yaml` manifest naming the substrate for the next-phase spec. Each iteration spawns a sibling project (`PROJ-NNN-<slug>-iter2`) — no state surgery on prior iterations.

Technical approach: write a small standalone citation resolver (`tests/phase1/citation_resolver.py`) plus a sibling-spawner helper, lean on the existing `python -m llmxive run` orchestrator for every agent invocation, and use git history as the canonical iteration trail. No production-pipeline code changes are required for the testing infrastructure itself; the only `src/` edits will be the prompt patches discovered during iteration (which land naturally as part of the iteration loop, FR-005).

**Architecture update (2026-05-04, mid-spec, per D10)**: A new `research_question_validator` agent is added to Phase 1 between `flesh_out` and `idea_selector`. The lifecycle becomes `brainstormed → flesh_out_complete → validated → project_initialized` (with `validator_revise` rolling back to `flesh_out_in_progress` and `validator_rejected` rolling back to `brainstormed`). This catches two failure modes that slipped through citation verification: implementation-method narrowing (PROJ-262) and circular construction (PROJ-268). Architecture lands in commit `aea01ec`: `Stage.VALIDATED` / `Stage.VALIDATOR_REVISE` / `Stage.VALIDATOR_REJECTED` enum values, `ResearchQuestionValidatorAgent` class, registry entry, prompt at `agents/prompts/research_question_validator.md`, `STAGE_TO_AGENT` + `STAGE_AFTER_AGENT` rewiring, and sentinel-file routing in `_decide_next_stage`. See spec.md US3.5 + FR-020 through FR-023.

## Technical Context

**Language/Version**: Python 3.11 (matches `pyproject.toml`)
**Primary Dependencies**: existing `llmxive` package (orchestrator, agents, backends, speckit), `requests` (for citation HTTP HEAD checks), standard library `json`/`yaml` (already available)
**Storage**: filesystem — `projects/<id>/idea/*.md`, `state/projects/<id>.yaml`, `state/run-log/<YYYY-MM>/*.jsonl`, all committed to git
**Testing**: pytest for the citation_resolver helper unit tests (real HTTP HEAD against known-good and known-bad URLs); the diagnostic itself is a manual procedure driven by the maintainer with the orchestrator CLI
**Target Platform**: macOS / Linux (developer workstation), Dartmouth Chat backend reachable
**Project Type**: research-pipeline diagnostic — single-project (no separate frontend/backend split)
**Performance Goals**: per-agent wall-clock budgets are already encoded in `agents/registry.yaml` (brainstorm 300s, flesh_out 600s, idea_selector 300s). Citation resolver: ≤5s per HTTP HEAD, ≤30s per arXiv API call, hard timeout 60s per citation.
**Constraints**: every agent invocation MUST go through `python -m llmxive run [--project <id>] --max-tasks 1` (no direct agent-class instantiation); citation resolution is two-stage (script → agent verifier) per FR-010; iterations are sibling projects per FR-004 (never state surgery)
**Scale/Scope**: brainstorm cohorts of 8 seeds; up to 5 cohorts → ≤40 brainstormed projects; up to 3 carry-forward candidates × up to 5 flesh_out iterations × up to 5 idea_selector iterations → ≤45 sibling projects max. Worst-case ~85 committed `projects/PROJ-NNN-*` directories, each with small idea artifacts (under 100 lines/file)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

The constitution at `.specify/memory/constitution.md` v1.0.0 names five non-negotiable principles. Each is evaluated below.

### I. Single Source of Truth (NON-NEGOTIABLE)

- **Compliance**: PASS. The plan does not create duplicate prompts, helpers, or schemas. The new files (`tests/phase1/citation_resolver.py`, `tests/phase1/sibling_project.py`, `notes/2026-05-04-phase1-diagnostic.md`, `specs/003-phase1-idea-lifecycle-testing/carry-forward.yaml`) are unique additions with single canonical locations; the orchestrator CLI and agent registry remain the canonical entry points; FR-003a tightens `agents/prompts/brainstorm.md` in place rather than forking it.

### II. Verified Accuracy (NON-NEGOTIABLE)

- **Compliance**: PASS. The diagnostic is *itself* a verified-accuracy mechanism: every artifact is quoted verbatim, every citation is resolved against primary sources via a two-stage pipeline (script + agent verifier) at 100% threshold (FR-010, SC-005), every prompt patch is committed with rationale tied to a specific defect in the report. The 100% citation-verification bar is stricter than the constitutional minimum, not weaker.

### III. Robustness & Reliability (Real-World Testing)

- **Compliance**: PASS. The diagnostic explicitly forbids mocks and stubs (FR-002, US1-US4 acceptance scenarios). Every agent runs against the real Dartmouth Chat backend; the citation resolver issues real HTTP HEADs / DOI lookups / arXiv queries; the sibling-project spawner writes real files to the real filesystem and commits them. The induced-failure-mode requirement (FR-015) confirms failure paths produce loud, recorded outcomes rather than silent advancement.

### IV. Cost Effectiveness (Free-First)

- **Compliance**: PASS. Dartmouth Chat is free per `agents/registry.yaml` (`is_paid: false`). The diagnostic introduces no paid dependencies. The citation resolver uses public APIs (arxiv.org, doi.org, generic HTTPS) that are free. Worst-case backend usage is bounded: 8 seeds × ≤5 cohorts (40 brainstorm calls @ 300s each) + ≤15 flesh_out calls (@ 600s each) + ≤15 idea_selector calls (@ 300s each) = ~7h backend wall-clock at the absolute upper bound, well within the daily quota estimate of 100 calls/day.

### V. Fail Fast

- **Compliance**: PASS. The plan's preflight checks before any agent run: (a) DARTMOUTH_CHAT_API_KEY non-empty (b) `python -m llmxive run --help` succeeds (c) `git status` clean before starting a cohort (d) `tests/phase1/citation_resolver.py --self-test` passes a known-good and known-bad citation. The Backend-unreachable edge case in spec.md mandates immediate halt rather than retry-forever. The induced-failure-mode test (FR-015) also exercises fail-fast on intentional misconfiguration.

**Verdict**: All five principles satisfied. No Complexity Tracking entries needed.

## Project Structure

### Documentation (this feature)

```text
specs/003-phase1-idea-lifecycle-testing/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── citation-resolver.md      # CLI/IO contract for the resolver
│   ├── sibling-project.md        # CLI/IO contract for the spawner
│   ├── diagnostic-report.md      # Markdown structural contract
│   └── carry-forward.md          # YAML schema contract
├── checklists/
│   └── requirements.md  # Spec-quality checklist (already created)
├── carry-forward.yaml   # Output of US5 — produced during /speckit-implement
└── tasks.md             # Phase 2 output (/speckit-tasks)
```

### Source Code (repository root)

```text
# Production code (touched only by iteration loop, per FR-004/FR-005)
src/llmxive/
├── __main__.py            # existing — orchestrator entry point
├── cli.py                 # existing — `run` subcommand
├── pipeline/              # existing — graph + state machine
├── agents/                # existing — agent classes
├── backends/              # existing — Dartmouth Chat etc.
├── speckit/               # existing — Spec Kit driver
└── ...

agents/
├── registry.yaml          # existing — agent definitions; iteration may tweak
└── prompts/
    ├── brainstorm.md      # existing — iteration target for FR-003a (scope content)
    ├── flesh_out.md       # existing — iteration target if citations fabricated
    └── idea_selector.md   # existing — iteration target if rationales boilerplate

# Diagnostic-only code (NEW, this spec)
tests/phase1/
├── __init__.py
├── citation_resolver.py    # FR-010 stage 1: HTTP HEAD / DOI / arXiv resolver script
├── sibling_project.py      # FR-004 helper: spawn PROJ-NNN-<slug>-iterN sibling
└── test_citation_resolver.py  # pytest unit tests w/ real HTTP

# Diagnostic outputs (NEW, this spec)
notes/2026-05-04-phase1-diagnostic.md    # FR-012 — the report itself

# Real project artifacts (produced by agents, NEW, this spec)
projects/PROJ-NNN-<slug>/
projects/PROJ-NNN-<slug>-iter2/
...
state/projects/PROJ-NNN-<slug>.yaml
state/projects/PROJ-NNN-<slug>-iter2.yaml
state/run-log/2026-05/<run-id>.jsonl
```

**Structure Decision**: Single-project layout (Option 1). The diagnostic introduces only a new `tests/phase1/` directory for the resolver+spawner helpers and a single `notes/` markdown report; everything else flows through existing pipeline code paths. Real-project artifacts under `projects/` and `state/` are produced by the agents themselves via the orchestrator CLI — no new directory contracts are introduced.

## Phase 0: Outline & Research

The Technical Context above has zero `NEEDS CLARIFICATION` markers — every unknown was resolved during `/speckit-clarify`. Phase 0 research therefore consolidates the **mechanism choices** that the clarifications committed to, plus a small amount of repo-introspection needed to confirm the orchestrator's actual invocation signature and state-machine entry conditions.

Research output lives in [research.md](./research.md) and covers:

1. **Orchestrator CLI signature**: confirm exact `python -m llmxive run` flags by reading `src/llmxive/cli.py` (specifically: does `--project <id>` work pre-creation or is the project auto-created on first run?).
2. **State YAML schema**: enumerate fields in `state/projects/<id>.yaml` (current_stage, last_run_id, history pointer) by reading 2-3 existing real-project YAMLs in the repo.
3. **Run-log JSONL schema**: enumerate fields in `state/run-log/<YYYY-MM>/<run-id>.jsonl` from existing entries.
4. **Sibling-spawn mechanics**: determine the minimum filesystem operations to produce a `PROJ-NNN-<slug>-iter2` project from a canonical iter1 project (copy `idea/seed.md`, write fresh `state/projects/<id>-iter2.yaml`, do NOT reuse run-log id).
5. **Citation-resolver coverage**: enumerate the citation formats `flesh_out` actually produces (arXiv IDs, DOIs, raw HTTPS URLs, BibTeX-style entries?) by reading 2-3 existing `idea.md` files under `projects/`.
6. **Failure-mode induction**: identify the cleanest mis-routing technique to deliberately cause a backend failure for the FR-015 induced-failure run (mis-set `DARTMOUTH_CHAT_API_KEY` env var, point at non-resolving host, or use a deliberately-mangled model name in the registry).

## Phase 1: Design & Contracts

Phase 1 produces three artifacts (data-model, contracts/, quickstart) plus an agent-context update.

### Data Model — see [data-model.md](./data-model.md)

Captures the entities the spec already names (real project, brainstorm pool, sibling iteration project, diagnostic report, carry-forward manifest, run-log entry, project state, idea artifact, iteration diff) with concrete field-level shape, validation rules, and state transitions. Pulls schema details from Phase 0 research (state YAML / run-log JSONL).

### Contracts — see [contracts/](./contracts/)

Four small contracts, since this feature has internal interfaces rather than HTTP APIs:

1. **`citation-resolver.md`** — CLI/IO contract for `tests/phase1/citation_resolver.py`. Inputs: path to `idea.md`, optional `--timeout`. Outputs: stdout JSON `[{citation, kind, status, evidence_url, ...}]`. Exit codes: 0 if all citations resolved or stage 1 finished cleanly (with per-citation results), non-zero only on script-level errors (network broken, file missing).
2. **`sibling-project.md`** — CLI/IO contract for `tests/phase1/sibling_project.py`. Inputs: canonical project ID + iteration number. Side effects: creates the sibling project directory, copies `idea/seed.md`, writes a fresh `state/projects/<id>-iterN.yaml` at the same `current_stage` as the canonical's relevant entry stage. Refuses to clobber an existing sibling.
3. **`diagnostic-report.md`** — Markdown structural contract for `notes/2026-05-04-phase1-diagnostic.md`: required sections (Executive summary, Per-agent runs with verbatim quotes, Citation resolution audit, Iteration diffs, Defects categorized by severity, After-fix sections, Carry-forward summary). Reviewer must be able to read top-to-bottom and confirm every spec acceptance criterion is addressed.
4. **`carry-forward.md`** — YAML schema contract for `specs/003-phase1-idea-lifecycle-testing/carry-forward.yaml`: list of 2-3 entries each with `project_id`, `final_state`, `final_commit`, `agents_run` (list of `{name, iterations}`), `justification`. Schema is parseable by `yq` so spec 004 can `yq '.projects[].project_id' carry-forward.yaml`.

### Quickstart — see [quickstart.md](./quickstart.md)

A maintainer-facing runbook of the diagnostic, in execution order: preflight → first brainstorm cohort → cohort review → iterate brainstorm prompt → repeat until 2-3 carry-forward candidates → flesh_out per project → citation-resolver per `idea.md` → iterate flesh_out → idea_selector per project → iterate idea_selector → finalize report → write `carry-forward.yaml`. Every step names the exact command and expected outcome.

### Agent context update

Update the plan reference between the `<!-- SPECKIT START -->` and `<!-- SPECKIT END -->` markers in `CLAUDE.md` to point at this plan file (`specs/003-phase1-idea-lifecycle-testing/plan.md`).

## Re-Check: Constitution Check (post-design)

After Phase 1 design (citation-resolver contract, sibling-project contract, diagnostic-report contract, carry-forward schema):

- **I. Single Source of Truth**: PASS — each contract has a single canonical file under `contracts/`; helpers are single files under `tests/phase1/`; the report is a single file under `notes/`.
- **II. Verified Accuracy**: PASS — design strengthens the verification bar (100% citation resolution, two-stage pipeline) over the spec's draft (90%, single-stage).
- **III. Robustness & Reliability**: PASS — citation resolver has its own pytest suite that issues real HTTP HEADs against known-good (e.g., `https://arxiv.org/abs/1706.03762`) and known-bad (`https://example.invalid/this-does-not-exist`) URLs.
- **IV. Cost Effectiveness**: PASS — design adds zero paid dependencies.
- **V. Fail Fast**: PASS — citation resolver `--self-test` runs first; sibling-project spawner refuses to clobber; backend-unreachable check happens before any LLM call.

No new violations introduced by Phase 1. No Complexity Tracking entries needed.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations. Table empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-|-|-|
| _(none)_ | _(n/a)_ | _(n/a)_ |
