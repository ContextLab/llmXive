# Data Model: Phase 3 (Spec Kit Specify → Clarify) Validation

**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Date**: 2026-05-17

## Purpose

Concrete schema for every entity the spec produces or consumes, so the validation harness, the regression tests, the inspection records, and the carry-forward manifest can all reference the same definitions.

---

## E1. Reference Project

A real, committed `PROJ-NNN-<slug>` directory + its state YAML, used as the actual subject of Phase 3 validation.

**Identity**:
- `project_id` (string, regex `^PROJ-\d{3}-[a-z0-9-]{1,50}$`)
- The two Phase 3 reference projects: `PROJ-261-evaluating-the-impact-of-code-duplicatio`, `PROJ-262-predicting-molecular-dipole-moments-with`.

**Lifecycle entry conditions** (preflight asserts each):
- `state/projects/<project_id>.yaml` exists and `current_stage == "project_initialized"`.
- `projects/<project_id>/idea/<slug>.md` exists and is non-empty.
- `projects/<project_id>/.specify/scripts/bash/create-new-feature.sh` exists and is executable (Phase 2 contract).
- `state/projects/<project_id>.yaml::speckit_research_dir` is either `None` or points to a path the harness is about to delete (FR-015 reset).

**Lifecycle exit conditions** (success path):
- `state/projects/<project_id>.yaml::current_stage == "clarified"`.
- `projects/<project_id>/specs/<NNN>-<slug>/spec.md` exists and is non-empty.
- `state/projects/<project_id>.yaml::speckit_research_dir` points to that spec directory (relative to repo root).
- `spec.md` contains ≥4 `FR-NNN` bullets, ≥3 `SC-NNN` bullets, ≥2 user stories with explicit priority labels (machine-checked by SC-002 verification).
- `spec.md` contains zero `[NEEDS CLARIFICATION]` markers (machine-checked by SC-003).

**Relationships**:
- 1 reference project → 2 inspection records per validation run (one per agent).
- 1 reference project → 1 entry in the carry-forward manifest.

## E2. Inspection Record

A JSON file persisting verbatim per-agent I/O for one agent invocation on one reference project. Lives at `specs/011-…/inspections/<project_id>/<agent_name>.json`. See `contracts/inspection-record.md` for the formal schema.

**Identity**:
- `(project_id, agent_name)` pair. One file per pair; re-runs on the same project overwrite the prior record.

**Required fields**:
- `project_id` (string)
- `agent_name` (string ∈ {"specifier", "clarifier"})
- `agent_version` (string — copied from `agents/registry.yaml`)
- `model` (string — e.g., "anthropic.claude-haiku-4.5")
- `backend` (string — e.g., "dartmouth")
- `started_at` (ISO-8601 UTC timestamp)
- `ended_at` (ISO-8601 UTC timestamp)
- `duration_s` (float)
- `outcome` (string ∈ {"committed", "abstained", "failed", "held", "no-op"})
- `reset_artifacts` (array of strings — paths removed by FR-015 reset; empty list if nothing was wiped)
- `prompts` (object: `{system: string, user: string}` — verbatim text the agent sent to the LLM)
- `raw_response` (string — verbatim LLM response, untouched)
- `parsed_output` (object — the agent's parsed-and-structured interpretation, e.g., the clarifier's `{patches: [...], notes: "…"}`)
- `file_diffs` (array of `{path: string, before: string, after: string}` — one entry per file the agent wrote; before/after are full file contents, not unified-diff lines)
- `error` (string or null — non-null only when `outcome == "failed"`)

**Validation rules**:
- `started_at <= ended_at`.
- `duration_s` matches `(ended_at - started_at).total_seconds()` to within 0.1s.
- `outcome == "committed"` implies `error is None` AND `file_diffs` is non-empty.
- `outcome == "failed"` implies `error` is a non-empty string.

## E3. Carry-forward Manifest

A YAML file at `specs/011-…/carry-forward.yaml` that lists each reference project, its final stage, and a one-line justification, ready for Phase 4 to consume.

**Identity**:
- The single file `specs/011-…/carry-forward.yaml`. Phase 4's validation reads it at startup.

**Schema** (matches `specs/004-…/carry-forward.yaml` precedent):
- `spec` (string — this spec's directory name)
- `generated_at` (ISO-8601 UTC timestamp)
- `final_commit` (string — the git SHA at which the manifest was written, or `"HEAD"` if uncommitted)
- `projects` (list of objects, one per reference project)

Each `projects[].entry`:
- `project_id` (string)
- `final_state` (string ∈ {"clarified", "specified", "project_initialized", "human_input_needed", "blocked"})
- `final_commit` (string — git SHA of the commit that landed this project's final artifacts, or `"HEAD"`)
- `audited_iter_id` (string — for Phase 3 this equals `project_id` since FR-015 mandates in-place reset, not iter siblings)
- `agents_run` (list of `{name, iterations, final_outcome}`)
- `justification` (string ≤ 200 words — free-form prose explaining what passed / what's parked and why)

**Status keys** (top-level convention for Phase 4 consumption):
- A project with `final_state == "clarified"` is `passed` (Phase 4 can run on it).
- A project with `final_state ∈ {"project_initialized", "specified"}` is `held` (Phase 3 partially completed; Phase 4 skips it).
- A project with `final_state == "human_input_needed"` is `failed` (Phase 3 surfaced an unrecoverable error; the `justification` MUST cite the inspection record path).

## E4. Run-log Entry (read-only — existing concept)

Per-agent JSONL line at `state/run-log/<YYYY-MM>/<run-id>.jsonl`. Phase 3 validation READS these to confirm FR-010 (every invocation recorded with `started_at`, `ended_at`, `outcome`). The validation does NOT modify the format.

**Required fields read** (matches the format already written by `SlashCommandAgent` base class):
- `agent_name`
- `project_id`
- `started_at`
- `ended_at`
- `outcome`
- `error` (when present)

FR-010 cross-check: for each `(project_id, agent_name)` validated, exactly one matching run-log entry MUST be readable. A mismatch (zero or multiple) is a failure.

## E5. Regression Test Case

One pytest test function under `tests/integration/test_phase3_specify_clarify.py`. Phase 3 mandates three such tests (FR-012):

- `test_diff_leak_guard_rejects_unified_diff_response` — invokes the real `_diff_guard.refuse_if_diff` with a synthetic LLM response containing `--- a/spec.md\n+++ b/spec.md\n@@ ...` and asserts a `DiffLeakError` (or whatever exception type the guard raises) is raised.
- `test_template_guard_rejects_template_only_spec` — invokes the real `_real_only_guard.assert_real_or_raise` against a synthetic `spec.md` that's byte-equal (modulo whitespace) to `.specify/templates/spec-template.md` and asserts the appropriate template-refused exception is raised.
- `test_clarifier_rejects_echo_the_question_replacement` — invokes the real `clarify_cmd._parse_clarifier_response` + the subsequent quality gate against a synthetic Clarifier JSON whose `patches[N].replacement` text is identical to (or a sub-string of) the corresponding marker's question text, and asserts the patch is rejected (the marker remains in `spec.md` and the run outcome is `failed`).

**Test structure** (each test):
- Setup: build the minimal in-memory or temp-dir state needed to exercise the guard. No external LLM call.
- Exercise: invoke the real guard function. Mocks are limited to the LLM response object only; the guard logic itself is real.
- Assertion: the guard raises the expected exception (or returns the expected rejected status), and any side effects (file deletion, stage hold) are observable in the temp dir.

## E6. Validation Harness CLI

The single CLI driver `scripts/validate_phase3.py`. See `contracts/regression-tests.md` for the formal CLI contract.

**Invocation shape**:
- `python scripts/validate_phase3.py --project PROJ-261-evaluating-the-impact-of-code-duplicatio` — runs Phase 3 on one canonical.
- `python scripts/validate_phase3.py --all` — runs Phase 3 on both canonicals (sequential per D7).
- `python scripts/validate_phase3.py --emit-carry-forward` — writes `carry-forward.yaml` from the latest inspection records.

**Side effects**:
- Writes `specs/011-…/inspections/<project_id>/{specifier,clarifier}.json` per invocation.
- Mutates `state/projects/<project_id>.yaml` (stage transitions are real).
- Writes `projects/<project_id>/specs/<NNN>-<slug>/spec.md` per agent.
- May delete pre-existing `projects/<project_id>/specs/<NNN>-<slug>/` per FR-015 reset.
- Appends entries to `state/run-log/<YYYY-MM>/<run-id>.jsonl` (via the per-agent base class — harness doesn't write here directly).

**Exit codes**:
- `0` — all requested projects reached `clarified` and pass all post-conditions.
- `1` — at least one project failed validation (stage didn't advance OR a guard fired OR a post-condition check failed). The carry-forward manifest still gets written with the actual final states.
- `2` — preflight error (missing env var, missing project, etc.). No state changes attempted.
