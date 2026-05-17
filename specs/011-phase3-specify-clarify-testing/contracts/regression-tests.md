# Contract: Regression Tests + CLI Driver

**Files**: `tests/integration/test_phase3_specify_clarify.py`, `scripts/validate_phase3.py`
**Producer**: This spec (FR-012 for tests; FR-001 + FR-003 for the CLI driver)
**Consumer**: CI pipeline (tests); maintainers + Phase 4 prerequisites (CLI)

---

## A. Regression test contract (`tests/integration/test_phase3_specify_clarify.py`)

### Test 1 — `test_diff_leak_guard_rejects_unified_diff_response`

**Purpose**: Catch regressions in `_diff_guard.refuse_if_diff` (spec 010 bug — 8 production files were corrupted before the guard landed).

**Setup**:
- Construct a synthetic LLM response string starting with:
  ```
  --- a/spec.md
  +++ b/spec.md
  @@ -1,3 +1,3 @@
  ```
- No actual filesystem I/O, no actual LLM call.

**Exercise**:
- Call `from llmxive.speckit._diff_guard import refuse_if_diff` with the synthetic response and `artifact_kind="spec.md"`.

**Assert**:
- The function raises the documented exception (whatever `_diff_guard` raises — typically `RuntimeError` or a custom `DiffLeakError`).
- The exception message contains "diff" (substring match, case-insensitive) so a maintainer reading a stacktrace can identify the cause.

**Failure interpretation**: If this test fails, `_diff_guard` has regressed — fix the guard before merging, do NOT weaken the test.

---

### Test 2 — `test_template_guard_rejects_template_only_spec`

**Purpose**: Catch regressions in `_real_only_guard.assert_real_or_raise` (spec 009 FR-009 — template-only artifacts must be deleted).

**Setup**:
- Create a temp directory.
- Write a `spec.md` whose content is byte-equal (modulo trailing whitespace) to the file `.specify/templates/spec-template.md`. The test reads that real template at test time — not a copy — so the test stays in sync if the template changes.
- No actual LLM call.

**Exercise**:
- Call `from llmxive.speckit._real_only_guard import assert_real_or_raise` with the temp spec.md path and the real repo root.

**Assert**:
- The function raises `TemplateRefused` (the documented exception class).
- The exception message identifies the failed classification ("template" substring).

**Failure interpretation**: If this test fails, `_real_only_guard` has regressed. Fix the guard, not the test.

---

### Test 3 — `test_clarifier_rejects_echo_the_question_replacement`

**Purpose**: Catch regressions in the Clarifier's quality gate (the historical "fake resolution" pattern where the LLM replaces a `[NEEDS CLARIFICATION: foo?]` marker with literal text `Resolved: foo?` or similar).

**Setup**:
- Construct a synthetic Clarifier JSON response with:
  ```json
  {
    "patches": [
      {"marker_index": 0, "replacement": "What is the auth method?"}
    ],
    "notes": ""
  }
  ```
- Construct a synthetic markers list whose `markers[0]["question"]` is `"What is the auth method?"` — i.e., the replacement is identical to the question (the canonical fake-resolution shape).
- Construct a temp `spec.md` with one `[NEEDS CLARIFICATION: What is the auth method?]` marker.

**Exercise**:
- Call the real `ClarifierAgent.write_artifacts` path with a `ChatResponse` whose `text` is the synthetic JSON. Use `monkeypatch` only to swap out `chat_with_fallback` — not the guards or parsing logic.

**Assert**:
- The marker REMAINS in the on-disk `spec.md` (verifying the "echo-the-question" patch was rejected).
- The agent's outcome (as visible via raised exception or returned status) classifies as `failed`.

**Failure interpretation**: If this test fails, the Clarifier's quality gate has regressed. Fix `clarify_cmd.write_artifacts`, not the test.

---

### Test 4 (smoke, gated) — `test_phase3_end_to_end_on_proj_261`

**Purpose**: Real-call end-to-end smoke against PROJ-261.

**Skip condition**: `@pytest.mark.skipif(not os.environ.get("DARTMOUTH_CHAT_API_KEY"), reason="real-call test — requires backend key")`

**Setup**:
- Preflight all 7 checks documented in plan.md Constitution Check / Section V.

**Exercise**:
- Run `python scripts/validate_phase3.py --project PROJ-261-evaluating-the-impact-of-code-duplicatio` via `subprocess.run`.

**Assert**:
- Exit code == 0.
- `state/projects/PROJ-261-….yaml::current_stage == "clarified"`.
- `specs/011-…/inspections/PROJ-261-…/specifier.json` exists and parses as the inspection-record contract.
- `specs/011-…/inspections/PROJ-261-…/clarifier.json` exists and parses as the inspection-record contract.

**Cleanup**: Resets PROJ-261 back to `project_initialized` so subsequent test runs are deterministic. Cleanup is in a `finally` so a test failure doesn't leave the project in a half state.

---

## B. CLI driver contract (`scripts/validate_phase3.py`)

### Synopsis

```
python scripts/validate_phase3.py [--project <PROJ-ID>] [--all] [--emit-carry-forward] [--no-reset]
```

### Flags

| Flag | Description |
|-|-|
| `--project <PROJ-ID>` | Run Phase 3 on a single canonical. Mutually exclusive with `--all`. |
| `--all` | Run Phase 3 on both canonicals (PROJ-261 + PROJ-262), sequentially. |
| `--emit-carry-forward` | After all selected projects finish, write `carry-forward.yaml`. Implicit when `--all` is set. |
| `--no-reset` | Skip the FR-015 reset step (i.e., DON'T wipe pre-existing `specs/<n>-<slug>/`). For diagnostic re-runs where the maintainer wants to preserve a partial spec.md. Mutually exclusive with normal validation. |

### Preflight checks (executed before any agent invocation)

In order:

1. `DARTMOUTH_CHAT_API_KEY` env var is set and non-empty (Constitution Principle V).
2. `python -m llmxive run --help` exits 0 (proves the package is importable).
3. For each target project:
   - `state/projects/<id>.yaml` exists and `current_stage == "project_initialized"`.
   - `projects/<id>/idea/<slug>.md` exists and is non-empty.
   - `projects/<id>/.specify/scripts/bash/create-new-feature.sh` exists and is executable.
4. `git status` reports no staged changes under any target project path (refuse to overwrite uncommitted maintainer work; bypass with `--force` if explicitly requested — not in scope for v1).

A preflight failure exits 2 with a clear message naming the failed check.

### Per-project execution

For each target project (sequential):

1. **Reset** (FR-015, unless `--no-reset`): delete `projects/<id>/specs/<n>-<slug>/` if it exists. Record removed paths in a list to thread into the Specifier's eventual inspection record.
2. **Specifier**: invoke `python -m llmxive run --project <id> --max-tasks 1` (this routes to the Specifier since stage is `project_initialized`). The harness monkey-patches `chat_with_fallback` for the duration to capture the system + user prompts + raw response; reads the produced `spec.md` to compute `file_diffs`. On completion, write `specs/011-…/inspections/<id>/specifier.json`.
3. **Clarifier**: same pattern (now stage is `specified`). The harness re-snapshots `spec.md` before + after to compute `file_diffs`. On completion, write `specs/011-…/inspections/<id>/clarifier.json`. If the Specifier produced zero markers, the Clarifier's outcome is `no-op` and `raw_response` is empty (no LLM call made).
4. **Post-conditions check**:
   - `state/projects/<id>.yaml::current_stage == "clarified"` (else project final_state is whatever it ended at).
   - `spec.md` exists at the expected path.
   - SC-002: ≥4 `FR-NNN`, ≥3 `SC-NNN`, ≥2 user stories. Failure → project marked `failed` in the carry-forward manifest with the specific count in `justification`.
   - SC-003: zero `[NEEDS CLARIFICATION]` markers in the final `spec.md`. Failure → project marked `failed`.
   - FR-010 cross-check: a matching run-log entry exists for each agent call. Missing entry → project marked `failed`.

### Emit carry-forward

When the run completes (all projects processed), write `specs/011-…/carry-forward.yaml` per the carry-forward contract.

### Exit codes

| Code | Meaning |
|-|-|
| 0 | All projects reached `clarified` and passed all post-conditions |
| 1 | At least one project failed validation (manifest still written) |
| 2 | Preflight failed (no state changes made) |

### Logging

- All progress output to stderr (so stdout can be redirected to a JSON summary if needed).
- The final exit message is a one-line summary: `validated N project(s): X passed, Y failed`.
