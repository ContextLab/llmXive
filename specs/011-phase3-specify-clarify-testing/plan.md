# Implementation Plan: Phase 3 (Spec Kit Specify → Clarify) End-to-End Testing & Diagnostics

**Branch**: `main` (validation work; spec dir `011-phase3-specify-clarify-testing`) | **Date**: 2026-05-16 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/011-phase3-specify-clarify-testing/spec.md`

## Summary

Drive the two Phase 3 agents (`specifier`, `clarifier`) through the production code path against the Dartmouth Chat backend on the two carry-forward canonicals from spec 004 — `PROJ-261-evaluating-the-impact-of-code-duplicatio` (Computer Science) and `PROJ-262-predicting-molecular-dipole-moments-with` (Chemistry), both currently parked at `project_initialized`. For each canonical, capture verbatim per-agent I/O (system prompt + user prompt + raw LLM response + parsed output + before/after file diffs) to `specs/011-…/inspections/<project_id>/<agent>.json` so the run is reviewable without re-invoking the LLM. Enforce the three historical failure-mode guards (template-only spec rejection per `_real_only_guard`, diff-leak rejection per `_diff_guard`, echo-the-question clarifier rejection per `clarify_cmd` quality gate) with targeted regression tests under `tests/integration/test_phase3_specify_clarify.py`. Emit a `carry-forward.yaml` manifest naming both canonicals at `clarified` as the substrate for spec 012 (Phase 4 testing).

Technical approach: extend the spec-010 `_real_only_guard.assert_real_or_raise` + `_diff_guard.refuse_if_diff` already wired into `specify_cmd.write_artifacts` and `clarify_cmd.write_artifacts` with **no new production-code changes** (per FR-013); add a single inspection-capture helper (`src/llmxive/speckit/_inspection.py`) that wraps the existing `slash_command.SlashCommandAgent.handle_response` write path so every Phase 3 invocation persists a `<spec_dir>/inspections/<proj>/<agent>.json` record. Wire FR-015's reset semantic (wipe pre-existing `specs/<n>-<slug>/` before invoking Specifier) into the validation harness — NOT into the agents themselves, since FR-013 forbids modifying agent code without justification. Use the existing `python -m llmxive run --project <id> --max-tasks 2` orchestrator; the orchestrator already routes to the Specifier when stage is `project_initialized` and to the Clarifier when stage is `specified`. Each agent invocation already writes to `state/run-log/<YYYY-MM>/<run-id>.jsonl` via the per-agent base class — Phase 3 validation reads those run-log lines (does not modify the format). Reference projects are mutated in place; iteration trail visible in git history per the iteration convention change documented at `notes/2026-05-06-iteration-convention-change.md`.

## Technical Context

**Language/Version**: Python 3.11 (matches `pyproject.toml`)
**Primary Dependencies**: existing `llmxive` package (orchestrator, `speckit/{specify_cmd,clarify_cmd,slash_command,_real_only_guard,_diff_guard,_comments_context}.py`, `backends/router.py`), `pyyaml` (for state YAML round-trip in the validation harness), `pytest` (for the three regression tests under FR-012)
**Storage**: filesystem — `projects/<id>/specs/<n>-<slug>/spec.md` (the artifact under test, written + edited by the two agents); `state/projects/<id>.yaml` (stage transitions: `project_initialized` → `specified` → `clarified`); `state/run-log/<YYYY-MM>/<run-id>.jsonl` (per-agent invocation records, read-only); `specs/011-…/inspections/<project_id>/<agent>.json` (new — verbatim I/O capture, FR-003/FR-004); `specs/011-…/carry-forward.yaml` (final manifest, FR-011)
**Testing**: pytest. Three regression integration tests under `tests/integration/test_phase3_specify_clarify.py` (FR-012: diff-leak guard, template-rejection guard, echo-question clarifier guard) — all use the real `_real_only_guard` / `_diff_guard` / `clarify_cmd._parse_clarifier_response` code paths (no mocks for those), but mock the LLM response since we're testing the guards, not the LLM. The end-to-end validation against PROJ-261/PROJ-262 is itself a real-call test driven by `python -m llmxive run`.
**Target Platform**: macOS / Linux (developer workstation); Dartmouth Chat backend reachable (the only required external dependency); eventual GHA cron schedule is OUT OF SCOPE for this spec.
**Project Type**: research-pipeline diagnostic — single-project (no separate frontend/backend split). All changes land under `src/llmxive/speckit/_inspection.py` (one new helper), `tests/integration/test_phase3_specify_clarify.py` (one new test file), and `specs/011-…/` (the validation artifacts).
**Performance Goals**: per-agent wall-clock budget already encoded in `agents/registry.yaml` (specifier 600s, clarifier 600s — FR-014). Each canonical's full Phase 3 run = 1 Specifier call + 1 Clarifier call = ≤ 1200s end-to-end. Inspection-capture overhead MUST be <500ms per invocation (single JSON write — measured on a representative reference project; a regression test asserts the bound).
**Constraints**: every Phase 3 agent invocation MUST go through `python -m llmxive run --project <id> --max-tasks 2` (no direct agent-class instantiation, except in the three pytest regression tests where we deliberately invoke `write_artifacts` with synthetic input to test the guards in isolation). FR-013 forbids modifying `SpecifierAgent` or `ClarifierAgent` source unless a real bug is found — and any bug-fix commit MUST cite a failing inspection record by path. FR-015 ("reset cleanly") implemented in the validation harness, not in the agents (out-of-band cleanup). The 60-second arXiv circuit-breaker from PR #183 may incidentally fire if the LLM cites uncommon arXiv IDs — that's expected behavior; the spec doesn't require zero arXiv calls.
**Scale/Scope**: 2 canonicals × 2 agents = 4 inspection records. Phase 3 produces 1 `spec.md` per canonical (≤200 lines typical), 4 inspection JSON records (≤50KB each, dominated by the LLM response body), 1 `carry-forward.yaml`, 3 regression test cases. Total new artifacts <500KB. Lifetime: inspection records committed permanently (FR-004's "commit-safe" requirement — no secrets to redact; per Q1 the `reset_artifacts` key documents what was wiped).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

The constitution at `.specify/memory/constitution.md` v1.0.0 names five non-negotiable principles. Each is evaluated below.

### I. Single Source of Truth (NON-NEGOTIABLE)

- **Compliance**: PASS. The plan creates exactly one new file under `src/`: `src/llmxive/speckit/_inspection.py` (the inspection-capture helper, called by the validation harness — NOT by the agents). The three guards already invoked by the agents (`_real_only_guard`, `_diff_guard`, `clarify_cmd._parse_clarifier_response`) are reused as-is — not duplicated. The four contracts files under `specs/011-…/contracts/` describe the inspection-record JSON schema, the carry-forward manifest schema, the diagnostic-report markdown structure, and the three regression-test interfaces — they describe contracts the validation observes, not new runtime code. The validation harness lives in `tests/integration/test_phase3_specify_clarify.py` and a single CLI driver `scripts/validate_phase3.py` (the canonical orchestrator for the end-to-end run); both reuse `python -m llmxive run` rather than re-implementing orchestration.

### II. Verified Accuracy (NON-NEGOTIABLE)

- **Compliance**: PASS. The diagnostic IS itself a verified-accuracy mechanism: every agent invocation's full I/O is persisted verbatim under `specs/011-…/inspections/`, so any later auditor can reconstruct exactly what was sent and what came back. The Specifier and Clarifier outputs are classified by the existing `_real_only_guard` (which checks for template literals, placeholder phrases, and obvious filler) — and a TEMPLATE classification mandates artifact deletion + `failed` outcome (FR-008). The Clarifier's per-marker replacement is rejected if it echoes the question text (FR-009), which is the historical "fake resolution" pattern. The inspection records themselves carry the actual model ID, the truncated request ID, the resolved-arxiv-id list (if any citations were made), and the file diff — every claim about the run can be checked against a real on-disk artifact.

### III. Robustness & Reliability (Real-World Testing)

- **Compliance**: PASS. The end-to-end validation IS a real-call test: `python -m llmxive run --project PROJ-261-… --max-tasks 2` against the real Dartmouth Chat backend, producing a real `spec.md` on disk for a real research project. The three pytest regression tests (FR-012) exercise the real guard implementations — `_real_only_guard.assert_real_or_raise` is called against a synthetic spec.md content (no mock); `_diff_guard.refuse_if_diff` is called against a synthetic LLM response (no mock); `clarify_cmd._parse_clarifier_response` is called against a synthetic echo-the-question JSON (no mock). The LLM call itself is mocked only in the three guard-regression tests, because those tests are validating the guards' behavior on a known-bad LLM output — calling a real LLM would make the test non-deterministic. The end-to-end validation against the two canonicals uses the real LLM. Inspection records are real JSON files on real disk; the harness writes and reads them through the real `_inspection.py` helper.

### IV. Cost Effectiveness (Free-First)

- **Compliance**: PASS. Dartmouth Chat is free per `agents/registry.yaml` (`is_paid: false`). The diagnostic introduces no paid dependencies. Worst-case backend usage is bounded: 2 canonicals × 2 agents × 600s budget = ≤ 40 minutes of backend wall-clock at the absolute upper bound (in practice each agent call resolves in 20-60s). The three regression tests are deterministic and use mocked LLM responses; they cost zero backend time. If FR-008 (template rejection) triggers on a canonical, the harness will retry once with a fresh seed before failing — bounding the retry budget at 2× per agent per canonical = ≤ 80 minutes worst case. Well within the maintainer's daily quota.

### V. Fail Fast

- **Compliance**: PASS. Preflight checks before any agent run (built into the validation harness, before invoking `python -m llmxive run`):
  - (a) `DARTMOUTH_CHAT_API_KEY` non-empty in env;
  - (b) `python -m llmxive run --help` succeeds (proves the package is importable);
  - (c) The target reference project's state YAML exists at `state/projects/PROJ-261-….yaml` (or PROJ-262) and `current_stage == project_initialized`;
  - (d) The target reference project's idea body exists at `projects/<id>/idea/<slug>.md` and is non-empty;
  - (e) FR-015 reset: if `projects/<id>/specs/<n>-<slug>/` exists, delete it and record the paths in the upcoming inspection record's `reset_artifacts` key;
  - (f) `git status` clean for any staged path under the target project (refuse to overwrite uncommitted maintainer work);
  - (g) The inspection directory `specs/011-…/inspections/<id>/` is writable.
  Failures surface in <10s with an actionable message naming the failed precondition and the fix. The 600s wall-clock budget is enforced by the existing agent base class; a timeout produces `outcome: failed` (FR-014), never `committed`.

**Verdict**: All five principles satisfied. No Complexity Tracking entries needed.

## Project Structure

### Documentation (this feature)

```text
specs/011-phase3-specify-clarify-testing/
├── plan.md                       # this file (/speckit-plan output)
├── spec.md                       # already exists (/speckit-specify output)
├── checklists/
│   └── requirements.md           # already exists (/speckit-specify output)
├── research.md                   # Phase 0 output (/speckit-plan)
├── data-model.md                 # Phase 1 output (/speckit-plan)
├── contracts/                    # Phase 1 output (/speckit-plan)
│   ├── inspection-record.md
│   ├── carry-forward.md
│   ├── diagnostic-report.md
│   └── regression-tests.md
├── quickstart.md                 # Phase 1 output (/speckit-plan)
├── tasks.md                      # Phase 2 output (/speckit-tasks — NOT created here)
├── inspections/                  # populated at validation-run time
│   ├── PROJ-261-…/{specifier.json, clarifier.json}
│   └── PROJ-262-…/{specifier.json, clarifier.json}
└── carry-forward.yaml            # populated at validation-end (FR-011)
```

### Source Code (repository root)

```text
src/llmxive/speckit/
├── _inspection.py                # NEW — single helper: capture(prompts, response, parsed, diff, path)
├── specify_cmd.py                # UNCHANGED (FR-013 — no agent edits unless real bug found)
├── clarify_cmd.py                # UNCHANGED (FR-013)
├── _real_only_guard.py           # UNCHANGED (reused as-is)
├── _diff_guard.py                # UNCHANGED (reused as-is)
└── _comments_context.py          # UNCHANGED (reused as-is — already integrated with both cmds)

scripts/
└── validate_phase3.py            # NEW — CLI driver for the end-to-end run on PROJ-261/262

tests/
└── integration/
    └── test_phase3_specify_clarify.py    # NEW — 3 regression tests + 1 end-to-end smoke (skipped if no backend key)
```

**Structure Decision**: Single-project layout (Option 1 from the template). All source code lives in the existing `src/llmxive/` tree; tests live in the existing `tests/integration/` tree; validation artifacts live under the spec directory. No new top-level directories. The `scripts/validate_phase3.py` driver follows the same convention as the existing `scripts/compile_paper.py` and `scripts/extract_paper_content.py` — pure orchestrator, no business logic, callable from CI or a maintainer's shell.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations. No entries needed. The plan introduces:
- 1 new helper module (`_inspection.py`, ~80 LOC, single responsibility).
- 1 new CLI driver (`scripts/validate_phase3.py`, ~120 LOC, pure orchestrator).
- 1 new test file (`tests/integration/test_phase3_specify_clarify.py`, ~200 LOC, 3 regression tests + 1 e2e smoke).
- 4 new contract markdown files under `specs/011-…/contracts/`.
- Zero changes to the Specifier or Clarifier agent code (per FR-013).

Per Principle I, every new file is checked for prior equivalents:
- `_inspection.py` — no existing capture helper for speckit invocations; the closest analog is the per-agent run-log writer in `personality.py::_write_run_log_entry`, which captures outcome metadata but not verbatim prompts/responses. Phase 3 validation needs verbatim I/O capture, which is a strictly new capability.
- `validate_phase3.py` — no existing phase-validation CLI driver; spec 004's diagnostic was a manual procedure, not a scripted one. This is the canonical Phase 3 driver going forward (Phase 4+ may reuse the same pattern).
- The four contract files are spec-local and have no equivalents elsewhere.
