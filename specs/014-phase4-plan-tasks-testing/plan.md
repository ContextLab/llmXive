# Implementation Plan: Phase 4 (Spec Kit Plan → Tasks, with Analyze loop) End-to-End Validation & Hardening

**Branch**: `014-phase4-plan-tasks-testing` | **Date**: 2026-05-21 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/014-phase4-plan-tasks-testing/spec.md`

## Summary

Drive the two Phase 4 agents — `planner` (`clarified → planned`) and `tasker` (`planned → tasked → analyze_in_progress → analyzed | human_input_needed`) — through the **production** code path against the Dartmouth Chat backend on the two carry-forward canonicals handed forward by spec 011: `PROJ-261-evaluating-the-impact-of-code-duplicatio` (Computer Science) and `PROJ-262-predicting-molecular-dipole-moments-with` (Chemistry), both currently parked at `current_stage: clarified`. For each canonical, capture verbatim per-agent I/O (system + user prompt, raw LLM response, parsed output, before/after file diffs) to `specs/014-…/inspections/<project_id>/<agent>.json` — and for the Tasker, one sub-record per analyze round — so the run is reviewable without re-invoking the LLM.

Per the 2026-05-21 clarification (plus the analyze remediation of F2), this feature **hardens the Planner agent** with three gates it lacks today: FR-005 (the artifact set must be complete — all five files present and the FILE-marker split must have succeeded; hard-fail otherwise), FR-006 (every `research.md` URL must return 2xx/3xx, hard-fail otherwise — no transient-retry leniency), and FR-007 (every `data-model.md` entity must correspond to a `contracts/` schema and vice-versa, hard-fail on mismatch). All three land in a single new canonical guard module `src/llmxive/speckit/_research_guard.py`, wired into `PlannerAgent.write_artifacts` alongside the existing `refuse_if_diff` + `guard_emit` calls. The Tasker's existing guards (task-ID≥5, Mode-B header/diff/prose-stub rejection, `TASKER_MAX_REVISION_ROUNDS` cap → `human_input_needed.yaml`) are reused as-is and exercised by regression tests; no Tasker decision logic changes (FR-017), only per-round inspection instrumentation is added.

Technical approach: (1) add `_research_guard.py` and wire it into `plan_cmd.py`; (2) extend the spec-011 inspection hook so the Tasker record nests a `rounds[]` array (analyze report + Mode-B patch + verdict + diffs per round) — observability only; (3) add a single end-to-end driver `scripts/validate_phase4.py` that runs preflight checks (Principle V), applies the FR-018 reset (delete Phase-4 outputs, PRESERVE `spec.md`), sets `LLMXIVE_INSPECTION_DIR`, invokes `python -m llmxive run --project <id> --max-tasks 2`, verifies the stage chain `clarified → … → analyzed`, runs the FR-010 data-flow ordering check on the produced `tasks.md`, and emits `carry-forward.yaml` + a phase report; (4) add `tests/integration/test_phase4_plan_tasks.py` with the six FR-016 regression tests plus inspection-schema and carry-forward-schema tests. The Tasker drives its full Mode-A→Mode-B analyze loop **inside one invocation** (`for round_idx in range(TASKER_MAX_REVISION_ROUNDS)` at `tasks_cmd.py:188`), so `--max-tasks 2` (one Planner step + one Tasker step) drives the whole phase. Reference projects are mutated in place; the iteration trail is visible in git history.

## Technical Context

**Language/Version**: Python 3.11 (matches `pyproject.toml`)
**Primary Dependencies**: existing `llmxive` package (orchestrator `cli.py`; `speckit/{plan_cmd,tasks_cmd,analyze_cmd,slash_command,_real_only_guard,_diff_guard,_inspection,_comments_context}.py`; `backends/router.py`; `agents/registry.py` + `agents/prompts/{planner,tasker}.md`); `pyyaml` (state YAML + carry-forward round-trip); `pytest` (regression tests); the Python stdlib `urllib`/`http` for FR-006 URL reachability (no new third-party dependency — Free-First, Principle IV).
**Storage**: filesystem —
- `projects/<id>/specs/001-<slug>/` — the artifacts under test: `spec.md` (input, PRESERVED), and Planner/Tasker outputs `plan.md`, `research.md`, `data-model.md`, `quickstart.md`, `contracts/*.yaml`, `tasks.md`;
- `projects/<id>/.specify/memory/{tasker_rounds.yaml,human_input_needed.yaml}` — Tasker loop state;
- `state/projects/<id>.yaml` — stage transitions (`clarified → planned → tasked → analyze_in_progress → analyzed`);
- `state/run-log/<YYYY-MM>/<run-id>.jsonl` — per-agent invocation records (read-only for validation);
- `specs/014-…/inspections/<project_id>/{planner,tasker}.json` — new verbatim I/O capture (FR-003/FR-004);
- `specs/014-…/carry-forward.yaml` + `specs/014-…/phase-report.md` — final manifests (FR-015/SC-008, FR-022/SC-011).

**Testing**: pytest. `tests/integration/test_phase4_plan_tasks.py` holds the six FR-016 regression tests — (a) FILE-marker split, (b) invented/unreachable URL rejection, (c) prose-stub `tasks.md` rejection, (d) Mode-B diff-leak, (e) Mode-B header preservation, (f) analyze-loop cap → `human_input_needed` — plus inspection-record-schema, carry-forward-schema, and FR-010 ordering-check tests. Per Constitution III, every regression test exercises the **real** guard implementation (`_research_guard`, `_diff_guard.refuse_if_diff`, `_real_only_guard.guard_emit`, the real `tasks_cmd` validators); the LLM response is synthesized only where the test's purpose is the guard's behavior on a known-bad output (not the LLM). FR-006's URL-reachability regression test uses a local `http.server` fixture (real HTTP, real sockets — no mock) returning controlled 200/404/500 so it is deterministic without depending on the public internet. The end-to-end PROJ-261/262 run is itself a real-call test (`scripts/validate_phase4.py`).
**Target Platform**: macOS / Linux developer workstation; Dartmouth Chat backend reachable (the only required external service). GHA cron scheduling is OUT OF SCOPE.
**Project Type**: research-pipeline diagnostic + minimal agent hardening — single project (no frontend/backend split). New code: `src/llmxive/speckit/_research_guard.py` (one module), edits to `plan_cmd.py` (wire two guards) and `_inspection.py`/`tasks_cmd.py` (per-round capture), `scripts/validate_phase4.py` (one driver), `tests/integration/test_phase4_plan_tasks.py` (one test file), and the `specs/014-…/` validation artifacts.
**Performance Goals**: per-agent wall-clock budget is the registry value `wall_clock_budget_seconds: 900` (FR-021); for the Tasker it applies PER analyze round. Worst case per canonical = 1 Planner call (≤900s) + 1 Tasker call running ≤5 analyze rounds (≤900s/round). FR-006 URL checks add network latency at plan time; each HEAD/GET uses a short timeout (≤10s) and the Planner fails fast on the first unreachable URL. Inspection capture overhead < 500ms per record (single JSON write); a test asserts the bound.
**Constraints**: every Phase 4 agent invocation MUST go through `python -m llmxive run --project <id> --max-tasks 2` (no direct agent instantiation, except the pytest regression tests that deliberately invoke `write_artifacts`/Mode-B parsing with synthetic input to exercise the guards in isolation). FR-017 permits exactly three Planner additions (the FR-005 completeness + FR-006 URL-reachability + FR-007 consistency gates), shipping together as the `_research_guard` module; beyond those, agent logic changes only on a real bug, citing the failing inspection record. FR-012's constraint-non-deletion check lives in the validation layer (`scripts/validate_phase4.py`), not the agent. FR-018 reset (delete Phase-4 outputs, PRESERVE `spec.md`) is implemented in the validation driver, not the agents. FR-006 hard-fails on any non-2xx/3xx with no transient-retry leniency (accepted determinism/flakiness tradeoff, per clarification).
**Scale/Scope**: 2 canonicals × 2 agents = 4 inspection records (the Tasker record nests its per-round array). Phase 4 produces, per canonical: 5 plan artifacts + `tasks.md` (≤300 lines typical), 1 planner.json + 1 tasker.json inspection record (≤200KB each, dominated by the LLM bodies + round diffs). Plus 1 `carry-forward.yaml`, 1 `phase-report.md`, and ~9 regression/schema test cases. Total new artifacts < 1MB. Inspection records committed permanently (FR-004 commit-safe — `_inspection._redact` strips secrets; only model id + truncated request id retained).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

The constitution at `.specify/memory/constitution.md` v1.0.0 names five non-negotiable principles. Each is evaluated below.

### I. Single Source of Truth (NON-NEGOTIABLE)

PASS. New runtime code is exactly one module: `src/llmxive/speckit/_research_guard.py`, holding both FR-006 (URL reachability) and FR-007 (consistency) gates as the canonical implementation, imported by `plan_cmd.py` (the only caller) and by the regression tests. The existing guards (`_real_only_guard.guard_emit`, `_diff_guard.refuse_if_diff`, the `tasks_cmd` task-ID/header/escalate validators) are reused, not duplicated. The inspection per-round capture extends the existing `_inspection.capture` rather than forking it. The end-to-end driver `scripts/validate_phase4.py` reuses `python -m llmxive run` rather than re-implementing orchestration. The five contract docs under `contracts/` describe observed contracts, not new runtime code.

### II. Verified Accuracy (NON-NEGOTIABLE)

PASS — and this feature *strengthens* the principle at the source. FR-006 makes the Planner itself verify that every `research.md` citation URL resolves (HEAD/GET → 2xx/3xx) at plan time, hard-failing on invented/unreachable references — exactly the "plausible-sounding citations are not citations" rule, enforced in code. Every agent invocation's full I/O is persisted verbatim under `inspections/`, so any later auditor can reconstruct what was sent and returned. FR-007 ties `data-model.md` entities to `contracts/` schemas so the design can't claim entities it never specifies. The phase report cites inspection-record paths for every finding (SC-010).

### III. Robustness & Reliability (Real-World Testing)

PASS. The end-to-end validation IS a real-call test: `python -m llmxive run --project PROJ-261-… --max-tasks 2` against the real Dartmouth backend, producing real plan artifacts + `tasks.md` on disk. The six regression tests exercise the real guard code paths (no mocks for the guards). FR-006's URL test stands up a real local `http.server` (real sockets, controlled status codes) instead of mocking `urllib`, so it tests the actual network path deterministically. The Mode-B regression tests feed the real `tasks_cmd` Mode-B parser/validators synthetic analyze patches (the known-bad outputs) — the guard logic is real; only the LLM is synthesized, because the test's subject is the guard, not the model. FR-022/SC-011: Mode-B is covered on real content when a canonical naturally triggers a finding, and guaranteed by the synthetic regression tests regardless; the phase report records which path provided coverage.

### IV. Cost Effectiveness (Free-First)

PASS. Dartmouth Chat is free (`agents/registry.yaml`: `paid_opt_in: false`). No paid dependency is introduced; FR-006 uses stdlib `urllib`/`http`. Backend usage is bounded: 2 canonicals × (1 Planner + 1 Tasker with ≤5 rounds) within the 900s/call budget. The regression tests are deterministic and make zero backend calls (synthetic LLM bodies + a local HTTP fixture). If a guard hard-fails a canonical (template/URL/consistency), the driver records the failure and stops for that canonical rather than retrying indefinitely (Principle V).

### V. Fail Fast

PASS. `scripts/validate_phase4.py` runs preflight checks before any agent call: (a) `load_dartmouth_key()` returns a non-empty key (per the credential-resolution rule — never read `os.environ` directly); (b) `python -m llmxive run --help` imports cleanly; (c) the target `state/projects/<id>.yaml` exists with `current_stage == clarified`; (d) the input `projects/<id>/specs/001-<slug>/spec.md` exists and is non-template (`_real_only_guard.is_real`); (e) FR-018 reset deletes any pre-existing Phase-4 outputs (PRESERVING `spec.md`) and records `reset_artifacts`; (f) the inspection dir is writable. Failures surface in <10s with an actionable message. The FR-006 URL gate itself fails fast on the first unreachable citation. The 900s budget is enforced by the agent base class; a timeout yields `outcome: failed`, never `committed` (FR-021).

**Verdict**: All five principles satisfied. The three Planner gates (FR-005/006/007) are pre-authorized agent changes under FR-017 (clarification of 2026-05-21 + analyze F2), shipping together as the canonical `_research_guard` module. No Complexity Tracking entries needed.

## Project Structure

### Documentation (this feature)

```text
specs/014-phase4-plan-tasks-testing/
├── plan.md                 # this file (/speckit-plan output)
├── spec.md                 # exists (/speckit-specify + /speckit-clarify output)
├── research.md             # Phase 0 output (/speckit-plan)
├── data-model.md           # Phase 1 output (/speckit-plan)
├── quickstart.md           # Phase 1 output (/speckit-plan)
├── contracts/              # Phase 1 output (/speckit-plan)
│   ├── research-guard.md         # FR-006/FR-007 Planner guard contract
│   ├── inspection-record.md      # planner.json + tasker.json (with rounds[]) schema
│   ├── carry-forward.md          # carry-forward.yaml schema
│   ├── phase-report.md           # phase-report.md structure
│   └── regression-tests.md       # the six FR-016 tests + schema tests
├── checklists/
│   └── requirements.md     # exists (/speckit-specify output)
├── inspections/            # produced by the end-to-end run (FR-003/FR-004)
│   ├── PROJ-261-…/{planner.json,tasker.json}
│   └── PROJ-262-…/{planner.json,tasker.json}
├── carry-forward.yaml      # produced by the driver (FR-015)
├── phase-report.md         # produced by the driver (SC-010/SC-011)
└── tasks.md                # Phase 2 output (/speckit-tasks — NOT created here)
```

### Source code (repository root)

```text
src/llmxive/speckit/
├── _research_guard.py      # NEW — FR-005 artifact-set completeness + FR-006 URL reachability + FR-007 data-model↔contracts consistency
├── plan_cmd.py             # EDIT — wire _research_guard into PlannerAgent.write_artifacts
├── _inspection.py          # EDIT — support nested rounds[] in the Tasker record
├── tasks_cmd.py            # EDIT — emit per-round detail for inspection capture (observability only)
├── slash_command.py        # (reuse) LLMXIVE_INSPECTION_DIR hook already present
├── _real_only_guard.py     # (reuse) template guard
└── _diff_guard.py          # (reuse) diff-leak guard

scripts/
└── validate_phase4.py      # NEW — end-to-end driver: preflight + reset + run + verify + carry-forward + phase report

tests/integration/
└── test_phase4_plan_tasks.py   # NEW — six FR-016 regression tests + inspection/carry-forward schema + FR-010 ordering
```

**Structure Decision**: Single-project research-pipeline diagnostic. Production hardening is confined to `src/llmxive/speckit/` (one new module + three minimal edits); all validation logic is in `scripts/validate_phase4.py` and `tests/integration/test_phase4_plan_tasks.py`; all artifacts under `specs/014-…/`. This mirrors spec 011's structure exactly, extended for the Planner gates and the Tasker's per-round capture.

## Complexity Tracking

> No Constitution Check violations. Table intentionally empty.

## Phase 0 — Research

See [research.md](./research.md). Resolves: the URL-extraction + reachability strategy for FR-006; the data-model↔contracts entity-matching strategy for FR-007; how to capture per-round Tasker detail without changing decision logic; and confirmation that `--max-tasks 2` drives the full phase (Tasker loops internally).

## Phase 1 — Design & Contracts

See [data-model.md](./data-model.md), [contracts/](./contracts/), and [quickstart.md](./quickstart.md). Defines the inspection-record (with `rounds[]`), carry-forward, and phase-report schemas; the Planner guard contract; and the six regression-test interfaces.
