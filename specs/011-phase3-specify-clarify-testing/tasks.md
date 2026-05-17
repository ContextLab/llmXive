# Tasks: Phase 3 (Spec Kit Specify → Clarify) Validation

**Input**: Design documents from `specs/011-phase3-specify-clarify-testing/`
**Prerequisites**: spec.md, plan.md, research.md, data-model.md, contracts/inspection-record.md, contracts/carry-forward.md, contracts/regression-tests.md, contracts/diagnostic-report.md, quickstart.md

**Tests**: REQUIRED. FR-012 mandates 3 regression tests under `tests/integration/test_phase3_specify_clarify.py` (plus 1 gated real-call smoke test). The end-to-end validation against PROJ-261/PROJ-262 is itself the primary real-call test (per Constitution Principle III).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

Single project at repo root: `src/llmxive/`, `tests/integration/`, `scripts/`, `specs/011-phase3-specify-clarify-testing/`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm prerequisites, prepare directories, no functional code yet.

- [ ] T001 Confirm both reference projects are at `current_stage: project_initialized` by running `grep current_stage state/projects/PROJ-261-evaluating-the-impact-of-code-duplicatio.yaml state/projects/PROJ-262-predicting-molecular-dipole-moments-with.yaml` and asserting both YAMLs report `project_initialized`. Surface a stop-condition error if either is past that stage.
- [ ] T002 Create the inspections directory skeleton at `specs/011-phase3-specify-clarify-testing/inspections/` (initially empty; populated at validation-run time). Do NOT create per-project sub-directories — `_inspection.capture()` will create them at write time.
- [ ] T003 Confirm the Dartmouth API key resolves via the project's existing credential infrastructure by running `python -c "from llmxive.credentials import load_dartmouth_key; assert load_dartmouth_key(), 'no Dartmouth key in env or ~/.config/llmxive/credentials.toml'"`. The key may live in env (CI) OR in `~/.config/llmxive/credentials.toml` (local maintainer). Do NOT check `os.environ` directly — that misses the file fallback. Surface a stop-condition error only if `load_dartmouth_key()` returns None.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Build the single new helper that every later story depends on.

- [ ] T004 Create `src/llmxive/speckit/_inspection.py` implementing `capture(*, project_id, project_dir, agent_name, agent_version, model, backend, started_at, ended_at, outcome, prompts, raw_response, parsed_output, file_diffs, reset_artifacts, error, spec_root) -> Path` per the contract in `specs/011-phase3-specify-clarify-testing/contracts/inspection-record.md`. The function must (a) compute `duration_s = (ended_at - started_at).total_seconds()`, (b) apply the redaction deny-list (`DARTMOUTH_CHAT_API_KEY`, `GITHUB_TOKEN`, `ANTHROPIC_API_KEY`, `HF_TOKEN`, `OPENAI_API_KEY`) substituting `<redacted>` anywhere those secrets appear in `prompts.system`, `prompts.user`, `raw_response`, (c) serialize via `json.dumps(record, indent=2, sort_keys=True, ensure_ascii=False)` and write to `<spec_root>/inspections/<project_id>/<agent_name>.json` atomically via `.tmp` + `os.replace`, (d) return the final path. The function must also validate that every required schema key is present and that `outcome` is one of the documented values; raise `ValueError` with a clear message if not.
- [ ] T005 Add module-level helpers `_redact(text: str) -> str` and `_atomic_write(path: Path, data: str) -> None` to `src/llmxive/speckit/_inspection.py`. NOT parallel with T004 — same file. These are factored so the regression tests can exercise them in isolation. `_redact` reads the secret deny-list from a module constant `_SECRETS_ENV_VARS = ("DARTMOUTH_CHAT_API_KEY", "GITHUB_TOKEN", "ANTHROPIC_API_KEY", "HF_TOKEN", "OPENAI_API_KEY")`, looks each up via `os.environ.get`, and replaces the value with `<redacted>` (non-greedy, case-sensitive). `_atomic_write` writes to `<path>.tmp` then `os.replace`s into place; file mode `0o644`. T004's `capture()` calls these helpers internally — fold them out as a pure refactor of what T004 wrote, do not duplicate the logic.
- [ ] T006 [P] Verify `src/llmxive/speckit/_real_only_guard.py::assert_real_or_raise` and `TemplateRefused` exception class are exported (importable) without modification. Run `python -c "from llmxive.speckit._real_only_guard import assert_real_or_raise, TemplateRefused; print('ok')"` and confirm it prints `ok`. If the names are not importable, fix the missing exports (this is a real bug per the FR-013 "real bug" definition) — but do NOT change the guard semantics.
- [ ] T007 [P] Verify `src/llmxive/speckit/_diff_guard.py::refuse_if_diff` is exported. Run `python -c "from llmxive.speckit._diff_guard import refuse_if_diff; print('ok')"`. Same fix-only-if-broken rule as T006.

**Checkpoint**: After T004–T007, the inspection helper is callable and the two guards are confirmed accessible. No agent code has been touched.

---

## Phase 3: User Story 1 — Run full Phase 3 pipeline on a single fresh real project (Priority: P1)

**Story goal**: A maintainer can run `python scripts/validate_phase3.py --project PROJ-261-…` and get a clarified project back, with state, spec.md, and run-log entries all consistent.

**Independent test criteria** (per spec US1): `python -m llmxive run --project PROJ-261-evaluating-the-impact-of-code-duplicatio --max-tasks 2` (or the equivalent via the new CLI) transitions PROJ-261 from `project_initialized` → `clarified` with zero `[NEEDS CLARIFICATION]` markers in the final `spec.md`.

- [ ] T008 [US1] Create `scripts/validate_phase3.py` skeleton with argparse for `--project <PROJ-ID>`, `--all`, `--emit-carry-forward`, `--no-reset` per the CLI contract in `specs/011-phase3-specify-clarify-testing/contracts/regression-tests.md` Section B. Mutual exclusion: `--project` and `--all` are mutually exclusive; `--no-reset` and `--emit-carry-forward` are independent. Exit 2 with a clear stderr message on argparse errors. Stub the per-project handler `def _run_one_project(project_id: str, *, reset: bool) -> dict[str, Any]` that returns `{"project_id": project_id, "final_state": "stub", "agents_run": []}`.
- [ ] T009 [US1] Implement preflight checks in `scripts/validate_phase3.py::_preflight()` per plan.md Constitution Section V: (a) Dartmouth key resolvable via `llmxive.credentials.load_dartmouth_key()` (env OR `~/.config/llmxive/credentials.toml`; if the key is in the file, also call `llmxive.backends.dartmouth._ensure_api_key_env()` to populate `os.environ` so the subprocess launched in T013 inherits it), (b) `python -m llmxive run --help` exits 0, (c) for each target project: state YAML exists + `current_stage == "project_initialized"`, (d) idea body exists + non-empty, (e) `create-new-feature.sh` exists + executable, (f) `git status --porcelain projects/<id>/` is empty (no uncommitted maintainer work), (g) `specs/011-phase3-specify-clarify-testing/inspections/` is writable (mkdir + touch + rm test file). Exit 2 with named-precondition error on any failure. Return a `dict[project_id, dict]` of preflight metadata (snapshots of pre-run state) for the harness to thread through.
- [ ] T010 [US1] Implement FR-015 reset in `scripts/validate_phase3.py::_reset_project_specs(project_id: str) -> list[str]`. Lists `projects/<project_id>/specs/<n>-<slug>/` directories (via `Path.glob("specs/*/")`); if any exist, `shutil.rmtree` each and return the project-relative paths as a list. Also: load the project state YAML; if `speckit_research_dir` points at any removed path, set it to `None` and re-save via `llmxive.state.project.save`. Return `[]` if nothing was removed.
- [ ] T011 [US1] Repurposed (originally an in-process chat-capture wrapper; obsolete given the subprocess-based T013 design that reads records from T012's env-hook). Replacement: add a fast unit test at `tests/unit/test_speckit_inspection_hook.py::test_hook_writes_when_env_set` (and `test_hook_no_op_when_env_unset`) that constructs a minimal `SlashCommandContext`, mocks `chat_with_fallback`, and asserts (a) with `LLMXIVE_INSPECTION_DIR` set, a record is written to that dir; (b) with the env var unset, no record is written. No external LLM call.
- [ ] T012 [US1] Add a SAFE, OPT-IN side-channel for inspection capture: in `src/llmxive/speckit/slash_command.py::SlashCommandAgent.handle_response`, IF the environment variable `LLMXIVE_INSPECTION_DIR` is set, after the agent commits its artifacts, additionally call `_inspection.capture(...)` to write a per-agent record under that directory. The env var is only set by the validation harness — production cron jobs never set it. This is the ONE permitted edit to agent infrastructure (justification: the harness CANNOT capture verbatim in-process prompts/responses without either modifying the agents or duplicating the orchestrator; the env-gated hook satisfies FR-003 with minimal blast radius). The `slash_command.py` edit must be ≤15 LOC and gated entirely behind `if os.environ.get("LLMXIVE_INSPECTION_DIR"):`. Document the env var contract at the top of `slash_command.py` with a brief docstring block. MUST land before T013 — T013 depends on this agent-side hook existing.
- [ ] T013 [US1] Implement `scripts/validate_phase3.py::_run_one_agent(project_id: str, agent_label: str, reset_artifacts: list[str], spec_root: Path) -> dict` that orchestrates a single agent invocation through the production CLI and reads back the inspection record written by T012's agent-side hook: (a) snapshots `projects/<id>/specs/*/spec.md` content (if any) for the before-diff, (b) records `started_at`, (c) sets `LLMXIVE_INSPECTION_DIR=<spec_root>/inspections/<project_id>` in the subprocess env so T012's hook fires, (d) invokes `python -m llmxive run --project <id> --max-tasks 1` via `subprocess.run` (NOT in-process — must go through production CLI per plan.md constraint), (e) snapshots the after-state of spec.md, (f) records `ended_at`, (g) reads the project state YAML to compute `outcome` based on whether the stage advanced, (h) reads back the inspection record T012's hook just wrote and augments it with the host-side `file_diffs` (before/after spec.md content) and `reset_artifacts`, (i) returns a dict summarizing the run (outcome, duration, inspection path). Depends on T012.
- [ ] T014 [US1] Wire `_run_one_project(project_id, reset)` in `scripts/validate_phase3.py` to: preflight → reset (if `reset=True`) → set `LLMXIVE_INSPECTION_DIR` → run Specifier (`_run_one_agent` with `agent_label="specifier"`) → check stage advanced to `specified` → run Clarifier (`_run_one_agent` with `agent_label="clarifier"`) → check stage advanced to `clarified` → unset `LLMXIVE_INSPECTION_DIR` → return per-project result dict. On any stage-advance failure, return a result dict with `final_state` reflecting where the project stopped.
- [ ] T015 [US1] Implement the post-conditions checker in `scripts/validate_phase3.py::_check_postconditions(project_id, run_result) -> tuple[bool, list[str], list[str]]` per plan.md US1 acceptance scenarios: (a) `current_stage == "clarified"`, (b) `spec.md` exists at the expected path, (c) SC-002 counts: ≥4 `FR-NNN`, ≥3 `SC-NNN`, ≥2 user stories (regex-counted from `spec.md`), (d) SC-003: zero `[NEEDS CLARIFICATION]` markers in the final spec.md, (e) FR-010: exactly one matching run-log entry per agent under `state/run-log/<YYYY-MM>/*.jsonl`, (f) FR-006 cap-flag: read the Specifier inspection record's `file_diffs[].after` for spec.md (i.e., the spec.md content immediately after the Specifier wrote it, before the Clarifier resolved anything) and count `[NEEDS CLARIFICATION` markers — if >3, emit a WARNING (not a failure) into the returned warnings list so the diagnostic report can surface it. Returns `(passed: bool, failures: list[str], warnings: list[str])` — `failures` is empty on pass; `warnings` carries non-blocking issues like the FR-006 cap excess.

**Checkpoint**: After T015, the full single-project happy path works for PROJ-261. The end-to-end smoke test (T021 below) exercises this.

---

## Phase 4: User Story 2 — Inspect inputs + outputs at every Phase 3 step (Priority: P1)

**Story goal**: A maintainer can open any of the 4 inspection records and reconstruct exactly what each agent received and produced.

**Independent test criteria**: 4 inspection records exist on disk after a `--all` run, each parsing as valid JSON, each satisfying the schema in `contracts/inspection-record.md`.

- [ ] T016 [US2] Add a JSON-schema-validation test at `tests/integration/test_phase3_specify_clarify.py::test_inspection_record_schema_validates_all_fields`. The test loads a fixture inspection record (committed at `tests/fixtures/phase3/sample_specifier_inspection.json` — T017) and asserts every required key from `contracts/inspection-record.md` is present with the correct type. Also asserts the `outcome ∈ {"committed", "abstained", "failed", "held", "no-op"}` enum. **SC-006 reconstruction check**: when `outcome == "committed"`, assert `prompts.system`, `prompts.user`, and `raw_response` are all non-empty strings (≥10 chars each) — this verifies a maintainer can reconstruct what the agent did from this one file alone, without consulting any other artifact.
- [ ] T017 [P] [US2] Create a hand-written fixture file `tests/fixtures/phase3/sample_specifier_inspection.json` containing a realistic-shape inspection record (matching the example in `contracts/inspection-record.md`). This fixture is used by T016 and by future regression tests; the values are illustrative (not pulled from a real run).
- [ ] T018 [US2] Add `tests/integration/test_phase3_specify_clarify.py::test_inspection_record_redacts_secrets`. The test calls `_inspection._redact(text)` with text containing an API key value (set via `monkeypatch.setenv("DARTMOUTH_CHAT_API_KEY", "sk-fake-1234567890abcdef")` and a sample text including that string) and asserts the returned string has `<redacted>` instead of the key value. Also asserts `_redact` leaves other text untouched (no over-redaction).
- [ ] T019 [US2] Add `tests/integration/test_phase3_specify_clarify.py::test_inspection_record_atomic_write` using `tmp_path`. The test calls `_inspection.capture(...)` with a synthetic record into `tmp_path`, then asserts (a) the final file exists, (b) no `.tmp` file remains, (c) re-reading the file with `json.load` yields a dict equal (up to key ordering) to the input. Calls `capture` twice with the same `(project_id, agent_name)` and asserts the second call overwrites the first cleanly.

---

## Phase 5: User Story 3 — Quality gates that catch silent shortcuts (Priority: P1)

**Story goal**: The three historical failure-mode guards (diff-leak, template-only, echo-the-question) are exercised by regression tests that prevent silent regressions.

**Independent test criteria**: All three regression tests pass against the current guard implementations; injecting a synthetic regression (e.g., commenting out the guard) makes the corresponding test fail.

- [ ] T020 [P] [US3] Add `tests/integration/test_phase3_specify_clarify.py::test_diff_leak_guard_rejects_unified_diff_response` per `contracts/regression-tests.md` Test 1. Construct a synthetic LLM response starting with `--- a/spec.md\n+++ b/spec.md\n@@ -1,3 +1,3 @@\n …` and assert that `_diff_guard.refuse_if_diff(synthetic, artifact_kind="spec.md")` raises an exception whose message contains the substring "diff" (case-insensitive). No actual filesystem I/O; no actual LLM call.
- [ ] T021 [P] [US3] Add `tests/integration/test_phase3_specify_clarify.py::test_template_guard_rejects_template_only_spec` per `contracts/regression-tests.md` Test 2. Uses `tmp_path` to write a `spec.md` whose content is byte-equal (modulo trailing whitespace) to the real `.specify/templates/spec-template.md` (read fresh at test time, so the test stays in sync with template changes). Calls `_real_only_guard.assert_real_or_raise(spec_path, repo_root=Path("."))` and asserts `TemplateRefused` is raised with a message containing "template" substring.
- [ ] T022 [P] [US3] Add `tests/integration/test_phase3_specify_clarify.py::test_clarifier_rejects_echo_the_question_replacement` per `contracts/regression-tests.md` Test 3. Constructs a synthetic spec.md in `tmp_path` with one `[NEEDS CLARIFICATION: What is the auth method?]` marker; constructs a synthetic `ChatResponse` whose `.text` is `{"patches":[{"marker_index":0,"replacement":"What is the auth method?"}],"notes":""}` (the canonical echo-the-question shape — replacement identical to question); invokes the real `ClarifierAgent.write_artifacts` path with that synthetic response via `monkeypatch` of `chat_with_fallback`; asserts the marker REMAINS in the on-disk spec.md AND the agent classifies the run as `failed` (via raised exception or returned outcome).

---

## Phase 6: User Story 4 — Carry-forward manifest for downstream phases (Priority: P2)

**Story goal**: After `--all` completes, a `carry-forward.yaml` exists listing both canonicals at `clarified` (or accurately reporting failures).

**Independent test criteria**: Open `specs/011-…/carry-forward.yaml`; both `PROJ-261` and `PROJ-262` appear under `projects[]` with `final_state: clarified` (on a clean run) or the actual final stage on failure.

- [ ] T023 [US4] Implement `scripts/validate_phase3.py::_emit_carry_forward(results: list[dict], spec_root: Path) -> Path` per `contracts/carry-forward.md`. Takes a list of per-project result dicts from `_run_one_project`, constructs the manifest dict (with `spec`, `generated_at`, `final_commit`, `projects[]`), serializes via `yaml.safe_dump(manifest, sort_keys=False, default_flow_style=False, allow_unicode=True)`, writes atomically (`.tmp` + `os.replace`) to `<spec_root>/carry-forward.yaml`. `final_commit` is resolved by running `git rev-parse HEAD`; if the repo has uncommitted changes affecting the spec/projects/state, log a warning and use `"HEAD"` as a sentinel.
- [ ] T024 [US4] Wire `_emit_carry_forward` into the main flow of `scripts/validate_phase3.py`: emit the manifest at the END of a `--all` run, OR when `--emit-carry-forward` is set. A `--project <id>` single-run does NOT emit the manifest (per quickstart.md "Carry-forward manifest missing" troubleshooting note) — that would clobber a 2-project manifest with 1-project data.
- [ ] T025 [P] [US4] Add `tests/integration/test_phase3_specify_clarify.py::test_carry_forward_manifest_schema` that constructs a synthetic 2-project results list, calls `_emit_carry_forward(results, tmp_path)`, then loads the written YAML and asserts every required key from `contracts/carry-forward.md` is present with correct types. Asserts the `projects[]` list has the expected count + ordering.

---

## Phase 7: Polish & Cross-Cutting

**Purpose**: Final wiring, documentation, and the gated real-call e2e test.

- [ ] T026 Add gated end-to-end real-call test `tests/integration/test_phase3_specify_clarify.py::test_phase3_end_to_end_on_proj_261` per `contracts/regression-tests.md` Test 4. Decorated with `@pytest.mark.skipif(not os.environ.get("DARTMOUTH_CHAT_API_KEY"), reason="real-call test — requires backend key")`. Invokes `subprocess.run(["python", "scripts/validate_phase3.py", "--project", "PROJ-261-evaluating-the-impact-of-code-duplicatio"])`, asserts exit code 0 and `state/projects/PROJ-261-….yaml::current_stage == "clarified"` and both inspection records exist. Cleans up in `finally` by rolling PROJ-261 back to `project_initialized` and removing the produced specs/ directory so subsequent runs are deterministic.
- [ ] T027 Run the full Phase 3 validation manually: `python scripts/validate_phase3.py --all` against the real Dartmouth backend on PROJ-261 + PROJ-262. Verify both reach `clarified`. Open all 4 inspection records and confirm prompts/responses look sane. Verify `carry-forward.yaml` is well-formed with both canonicals at `final_state: clarified`. Verify SC-001..SC-008 are all met against the actual artifacts on disk.
- [ ] T028 [P] Run the fast regression test subset: `python -m pytest tests/integration/test_phase3_specify_clarify.py -v -k "not end_to_end"`. Expect all 3 guard tests + 4 inspection-record-schema/redact/atomic/carry-forward tests to pass in <2s total. The `end_to_end` substring matches `test_phase3_end_to_end_on_proj_261` (T026) which is gated by `@pytest.mark.skipif` on `DARTMOUTH_CHAT_API_KEY` — the `-k` filter is belt-and-suspenders so a CI run without the secret doesn't spend time loading the gated test.
- [ ] T029 [P] Update `notes/2026-05-17-spec-011-phase3-diagnostic.md` (create new file) following `contracts/diagnostic-report.md` structure. Fill in TL;DR, per-project summary, guards-fired table, recommendations, and sign-off section based on the actual T027 run output.
- [ ] T030 Final commit + PR: stage `src/llmxive/speckit/_inspection.py`, `src/llmxive/speckit/slash_command.py`, `scripts/validate_phase3.py`, `tests/integration/test_phase3_specify_clarify.py`, `tests/fixtures/phase3/sample_specifier_inspection.json`, the updated `projects/PROJ-26[12]-*/` artifacts, the updated `state/projects/PROJ-26[12]-*.yaml`, the new run-log entries, `specs/011-…/inspections/`, `specs/011-…/carry-forward.yaml`, `notes/2026-05-17-spec-011-phase3-diagnostic.md`. Commit message: `spec(011): Phase 3 validation complete — PROJ-261 + PROJ-262 reach clarified`. Open PR, request merge.

---

## Dependencies

- **Phase 1** (T001–T003): No dependencies — runs first.
- **Phase 2** (T004–T007): Depends on Phase 1. T004 → (T005, T006, T007) can run in parallel.
- **US1** (T008–T015): Depends on Phase 2. Tasks T008→T009→T010 are sequential (all in `scripts/validate_phase3.py`); T011 [P] can run alongside; T012→T013→T014→T015 are sequential.
- **US2** (T016–T019): Depends on Phase 2. T017 [P] can run before T016; T018 and T019 [P] can run alongside each other.
- **US3** (T020–T022): Depends on Phase 2 (specifically T006, T007). All three are [P] — independent files-of-test logic.
- **US4** (T023–T025): Depends on US1 (`_run_one_project` returns the result dict that `_emit_carry_forward` consumes). T023 → T024 sequential. T025 [P] can run alongside.
- **Polish** (T026–T030): Depends on US1, US2, US3, US4. T028, T029 [P] can run alongside each other; T027 must run before T029; T030 is final.

## Parallel execution examples

- After T004 (Phase 2 helper exists), run T005 + T006 + T007 in parallel.
- After T015 (US1 complete), run all of US3 (T020 + T021 + T022) in parallel.
- After T027 (real-call run), run T028 + T029 in parallel.

## Implementation strategy

MVP scope = Phase 1 + Phase 2 + US1 = a maintainer can validate one project end-to-end with full inspection records. This is the demo-able increment. US2, US3, US4 then bolt on additional verification + downstream-phase handoff. Polish wraps with the diagnostic report + final commit.

## Format-validation footer

All 30 tasks above follow the strict checklist format: `- [ ] T### [P?] [Story?] Description with file path`. No tasks are missing the checkbox, ID, or file path. User-story tasks (T008–T025) all carry a [USn] label; Setup/Foundational/Polish tasks (T001–T007, T026–T030) carry no story label per the convention.
