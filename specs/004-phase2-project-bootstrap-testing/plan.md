# Implementation Plan: Phase 2 (Project Bootstrap) End-to-End Testing & Diagnostics

**Branch**: `008-phase2-project-bootstrap-testing` | **Date**: 2026-05-05 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/004-phase2-project-bootstrap-testing/spec.md`

## Summary

Drive the single Phase 2 agent (`project_initializer`) through the production code path against the Dartmouth Chat backend on **iter2 siblings** of the spec-003 carry-forward projects (PROJ-261 + PROJ-262). The agent renders `.specify/memory/constitution.md` from `agents/templates/research_project_constitution.md` (LLM-driven domain adaptation) and mechanically scaffolds `.specify/{scripts,templates}/` via `init_speckit_in`. For each iter2 sibling, audit the rendered constitution against the explicit output contract in `agents/prompts/project_initializer.md`, verify full idempotency under a second invocation, and induce all three deliberate failure modes (backend-unreachable / idea-missing / template-missing) on dedicated iter siblings to prove failure paths are loud. Record every artifact verbatim in a single diagnostic report; emit a `carry-forward.yaml` manifest naming the substrate for spec 005 (Phase 3 testing).

Technical approach: reuse the spec-003 sibling spawner (`tests/phase1/sibling_project.py`) with one extension (add `validated` to `ALLOWED_START_STAGES`); apply one in-PR fix to make `project_initializer` idempotent on the constitution write (skip-if-exists, per Q3 clarification); lean on the existing `python -m llmxive run` orchestrator for every agent invocation; verify the existing backend-router retry policy at `src/llmxive/backends/router.py` already satisfies the Q4 retry budget (3 attempts × primary model + 1 attempt × 2 peer models per backend = sufficient transient-error tolerance). Use git history as the canonical iteration trail. The diagnostic itself is a manual procedure driven by the maintainer with the orchestrator CLI; no production code changes are required for the testing infrastructure beyond the two tightly-scoped fixes (spawner allowlist + agent idempotency).

## Technical Context

**Language/Version**: Python 3.11 (matches `pyproject.toml`)
**Primary Dependencies**: existing `llmxive` package (orchestrator, agents, backends, speckit), `pyyaml` (already available), spec-003's `tests/phase1/sibling_project.py` (extended)
**Storage**: filesystem — `projects/<id>/.specify/{memory,scripts,templates}/**`, `projects/<id>/idea/<slug>.md`, `state/projects/<id>.yaml`, `state/run-log/<YYYY-MM>/*.jsonl`, all committed to git
**Testing**: pytest for the `project_initializer` idempotency fix unit test (real filesystem temp dir); the diagnostic itself is a manual procedure driven by the maintainer with the orchestrator CLI; spec-003's `tests/phase1/test_citation_resolver.py` continues to run in CI as a regression check on the substrate
**Target Platform**: macOS / Linux (developer workstation), Dartmouth Chat backend reachable; eventually GHA cron per the project's broader vision (out of scope for this spec)
**Project Type**: research-pipeline diagnostic — single-project (no separate frontend/backend split)
**Performance Goals**: per-agent wall-clock budget already encoded in `agents/registry.yaml` (project_initializer 300s); idempotency check must add no more than 60s of overhead per sibling (sha256 over <30 files); each induced-failure run must hard-fail within 60s (faster than wall_clock_budget) so the cumulative cost of all failure inductions stays bounded
**Constraints**: every agent invocation MUST go through `python -m llmxive run --project <sibling-id> --max-tasks 1` (no direct agent-class instantiation, except in the idempotency-check Python harness for US3 acceptance scenario 2 where re-running from `validated` is impossible via the CLI); iterations are sibling projects per spec-003 FR-004 (never state surgery); transient backend errors retry per the existing router policy (3 attempts on primary model + 1 on each peer in `MODEL_FALLBACKS`, then fall through to next backend in `fallback_backends`); FR-005 5-cycle iteration cap inherited from spec 003
**Scale/Scope**: 2 happy-path iter2 siblings (1 per canonical, per Q1) + up to 5 iter3+ siblings (if defects surface, per FR-005 cap × ≤2 canonicals) + 3 dedicated induced-failure iter siblings (one per Q2 scenario). Worst case ≤10 committed `projects/PROJ-NNN-…-iterN/` directories. Each sibling produces a constitution (~100 lines), a scaffold tree (~12 files, all bytewise copies of repo-root templates), one state YAML (~20 lines), and one run-log JSONL line. Total artifacts: bounded under 200 files; well under 1MB total.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

The constitution at `.specify/memory/constitution.md` v1.0.0 names five non-negotiable principles. Each is evaluated below.

### I. Single Source of Truth (NON-NEGOTIABLE)

- **Compliance**: PASS. The plan creates no duplicate prompts, helpers, or schemas. New artifacts (`notes/2026-05-05-phase2-diagnostic.md`, `specs/004-phase2-project-bootstrap-testing/carry-forward.yaml`, the four `contracts/*.md` files in this spec dir) are unique additions with single canonical locations. The two in-PR fixes (extend `ALLOWED_START_STAGES`; skip-if-exists in `project_initializer.py`) modify single canonical locations rather than forking. The sibling-spawner from spec 003 is extended in place — not duplicated. Constitution-template path (`agents/templates/research_project_constitution.md`) and prompt path (`agents/prompts/project_initializer.md`) remain canonical.

### II. Verified Accuracy (NON-NEGOTIABLE)

- **Compliance**: PASS. The diagnostic is itself a verified-accuracy mechanism: every artifact is quoted verbatim, every constitution line is audited against the explicit output contract in `agents/prompts/project_initializer.md` (a 6-item check per US2), and any token-substitution leak (`{{project_id}}`, etc.) is a CRITICAL defect (SC-010). The constitution may not introduce external citations (SC-011) — a stricter requirement than the parent constitution's verified-accuracy mandate, since governance documents shouldn't depend on external sources at all. The audit also explicitly checks that the produced constitution does not contradict any parent-constitution principle, preventing weakening of the meta-system's accuracy guarantees.

### III. Robustness & Reliability (Real-World Testing)

- **Compliance**: PASS. The diagnostic explicitly forbids mocks and stubs (FR-002, US1-US4 acceptance scenarios). Every agent invocation runs against the real Dartmouth Chat backend; `init_speckit_in` writes real files to the real filesystem; the sibling spawner produces real committed projects. The induced-failure-mode requirement (FR-012, all three modes per Q2) confirms failure paths produce loud, recorded outcomes rather than silent advancement — including the worst case (backend dies mid-stream and the spec verifies no partial constitution is left behind). The idempotency check (US3) computes real sha256 hashes against real files on real disk, not against a checksummed-by-policy contract.

### IV. Cost Effectiveness (Free-First)

- **Compliance**: PASS. Dartmouth Chat is free per `agents/registry.yaml` (`is_paid: false`). The diagnostic introduces no paid dependencies. Worst-case backend usage is bounded: 2 happy-path runs × 300s budget + ≤5 iteration runs × 300s + 3 induced-failure runs × 60s (early hard-fail) = ~36 minutes of backend wall-clock at the absolute upper bound, well within the daily quota estimate of 100 calls/day for one maintainer.

### V. Fail Fast

- **Compliance**: PASS. Preflight checks before any agent run: (a) `DARTMOUTH_CHAT_API_KEY` non-empty (verified via `llmxive auth check` or direct credential file read at `~/.config/llmxive/credentials.toml`); (b) `python -m llmxive run --help` succeeds; (c) `git status` clean before starting an iter2 batch; (d) `tests/phase1/sibling_project.py --help` succeeds (proves spawner is on the import path); (e) the `validated` start-stage extension landed in the same commit as FR-003a's prerequisite work. The Backend-unreachable edge case in spec.md mandates immediate halt rather than retry-forever (router walks the fallback chain once each then surfaces the original `TransientBackendError`). The induced-failure-mode test (FR-012 × 3) explicitly exercises fail-fast on all three precondition violations Phase 2 depends on.

**Verdict**: All five principles satisfied. No Complexity Tracking entries needed.

## Project Structure

### Documentation (this feature)

```text
specs/004-phase2-project-bootstrap-testing/
├── plan.md              # This file
├── spec.md              # Feature specification (already created, /speckit-clarify resolved)
├── research.md          # Phase 0 output (this file's Phase 0)
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── diagnostic-report.md       # Markdown structural contract for the report
│   ├── carry-forward.md           # YAML schema contract for the manifest
│   ├── idempotency-check.md       # CLI/IO contract for the sha256 verification harness
│   └── induced-failure-runs.md    # Procedural contract for each of the three induced-failure scenarios
├── checklists/
│   └── requirements.md   # Spec-quality checklist (already created)
├── carry-forward.yaml    # Output of US6 — produced during /speckit-implement
└── tasks.md              # Phase 2 output (/speckit-tasks; not produced by /speckit-plan)
```

### Source Code (repository root)

```text
# Production code (touched by the two tightly-scoped fixes only)
src/llmxive/
├── __main__.py            # existing — orchestrator entry point
├── cli.py                 # existing — `run` subcommand
├── pipeline/              # existing — graph + state machine
├── agents/
│   └── project_initializer.py  # FIX P2-D01 — skip-if-exists on constitution write (Q3)
├── backends/              # existing — router policy already satisfies Q4 (no edit)
├── speckit/
│   └── runner.py          # existing — `init_speckit_in` already idempotent on dirs (no edit)
└── ...

agents/
├── registry.yaml          # existing — project_initializer entry (no edit unless prompt iterates)
├── prompts/
│   └── project_initializer.md  # iteration target if constitution audit (US2) surfaces defects
└── templates/
    └── research_project_constitution.md  # iteration target if domain adaptation underperforms

# Diagnostic-only code (extension of spec 003's tests/phase1/)
tests/phase1/
├── sibling_project.py     # FIX P2-D02 — extend ALLOWED_START_STAGES to include 'validated' (FR-003a)
└── test_idempotency.py    # NEW — pytest harness for US3 sha256-tree idempotency check

# Diagnostic outputs (NEW, this spec)
notes/2026-05-05-phase2-diagnostic.md    # FR-013 — the report itself

# Real project artifacts (produced by agents during /speckit-implement)
projects/PROJ-261-evaluating-the-impact-of-code-duplicatio-iter2/
projects/PROJ-262-predicting-molecular-dipole-moments-with-iter2/
projects/PROJ-261-…-iterN/   # zero or more iter3+ if defects surface (≤5 per FR-005)
projects/PROJ-262-…-iterN/   # zero or more iter3+ if defects surface (≤5 per FR-005)
projects/PROJ-261-…-iterFAIL-{backend,idea,template}/   # induced-failure siblings (one per Q2 scenario)
state/projects/PROJ-…-iterN.yaml
state/run-log/2026-05/<run-id>.jsonl
```

**Structure Decision**: Single-project layout (Option 1). The diagnostic introduces only one new pytest module (`tests/phase1/test_idempotency.py`) and one new markdown report. Two production-code edits land as in-PR fixes (one ALLOWED_START_STAGES extension, one constitution-write skip-if-exists guard). All other behavior flows through existing pipeline code paths. Real-project artifacts under `projects/` and `state/` are produced by the agents themselves via the orchestrator CLI — no new directory contracts are introduced.

## Complexity Tracking

> No Constitution-Check violations to justify. Table omitted.
