# Tasks: Phase 4 Pipeline Validation — Planner + Tasker (with Analyze loop)

**Input**: Design documents from `specs/014-phase4-plan-tasks-testing/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Test tasks ARE in scope — the spec explicitly requires regression tests (FR-016) and schema tests.

**Organization**: Grouped by the spec's four user stories. Phase 2 (Foundational) holds the Planner hardening + inspection instrumentation that US1/US2/US3 all depend on.

## Format: `[ID] [P?] [Story] Description with file path`

- **[P]**: parallelizable (different file, no dependency on an incomplete task)
- **[USx]**: the user story the task serves (story phases only)

---

## Phase 1: Setup

- [ ] T001 Preflight sanity: confirm `PROJ-261-evaluating-the-impact-of-code-duplicatio` and `PROJ-262-predicting-molecular-dipole-moments-with` are at `current_stage: clarified` (`grep current_stage state/projects/PROJ-26[12]-*.yaml`) and that `python -c "from llmxive.credentials import load_dartmouth_key; assert load_dartmouth_key()"` succeeds; record the baseline in a scratch note.
- [ ] T002 [P] Create the inspections output directory `specs/014-phase4-plan-tasks-testing/inspections/PROJ-261-evaluating-the-impact-of-code-duplicatio/` and `.../PROJ-262-predicting-molecular-dipole-moments-with/` (with `.gitkeep`).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The Planner gates (FR-006/FR-007) and per-round inspection capture (FR-004) that the real runs and quality-gate tests depend on. MUST complete before Phase 3.

- [X] T003 [P] Create `src/llmxive/speckit/_research_guard.py` (canonical, stdlib-only) defining `IncompleteArtifactSet(RuntimeError)`, `UnreachableReference(RuntimeError)`, `InconsistentDataModel(RuntimeError)`, `assert_artifact_set_complete(files: dict[str,str])` (FR-005: all 5 artifacts present + non-empty + ≥1 `contracts/*.yaml`; detect no-marker `{plan.md:…}` fallback as a failed split; raise `IncompleteArtifactSet`), `assert_urls_reachable(research_md_text, *, timeout=10)` (FR-006: extract `https?://`/`arXiv:`/`doi:` refs; HEAD→GET-range fallback; accept 200–399 only; raise on first non-2xx/3xx; NO retries), and `assert_data_model_contracts_consistent(files: dict[str,str])` (FR-007: entity↔schema name correspondence, normalized; raise on mismatch). Conform to `contracts/research-guard.md`.
- [X] T004 Wire the three gates into `PlannerAgent.write_artifacts` in `src/llmxive/speckit/plan_cmd.py`: call `assert_artifact_set_complete(files)` BEFORE the write loop; after the existing per-file `refuse_if_diff`+`guard_emit` loop, call `assert_data_model_contracts_consistent(files)` then `assert_urls_reachable(files.get("research.md",""))`; on any raise, unlink every artifact written this invocation before propagating (parity with `guard_emit`). (depends: T003)
- [X] T005 [P] Extend `capture()` in `src/llmxive/speckit/_inspection.py` to accept `rounds: list | None = None` and persist it under a new top-level `rounds` key (default `[]`), preserving every existing required key for back-compat with spec-011 records. Conform to `contracts/inspection-record.md`.
- [X] T006 Update `_maybe_write_inspection` in `src/llmxive/speckit/slash_command.py` to read `getattr(agent, "_inspection_rounds", [])` and pass it as `capture(rounds=...)`. (depends: T005)
- [X] T007 Instrument `TaskerAgent` in `src/llmxive/speckit/tasks_cmd.py` to accumulate one dict per analyze round (`round_index`, `analyze_report`, `mode_b_patch`, `verdict`, `files_rewritten`, `diffs`) into `self._inspection_rounds` inside the `range(TASKER_MAX_REVISION_ROUNDS)` loop — observability only, NO change to decision logic (FR-017). (depends: T006)

---

## Phase 3: User Story 1 — End-to-end Phase 4 run on a real project (Priority: P1)

**Goal**: A real project transits `clarified → planned → tasked → analyze_in_progress → analyzed` through the production path with `--max-tasks 2`.
**Independent test**: `python scripts/validate_phase4.py --project PROJ-261-…` ends with `current_stage: analyzed`, five plan artifacts + `tasks.md` present, `spec.md` preserved.

- [X] T008 [US1] Implement preflight in `scripts/validate_phase4.py` (Principle V, fail-fast <10s): `load_dartmouth_key()` non-empty; `python -m llmxive run --help` imports; target `state/projects/<id>.yaml` exists with `current_stage == clarified` (else FR-019 decline + report "already past this phase"); `projects/<id>/specs/001-*/spec.md` exists and `_real_only_guard.is_real`; inspections dir writable. Each failure names the precondition + fix.
- [X] T009 [US1] Add the FR-018 reset to `scripts/validate_phase4.py`: when stage is `clarified`, delete Phase-4 outputs (`plan.md`, `research.md`, `data-model.md`, `quickstart.md`, `contracts/`, `tasks.md`, and `.specify/memory/{tasker_rounds,human_input_needed}.yaml`) under `projects/<id>/specs/001-*/`, PRESERVING `spec.md`; collect removed paths for the inspection `reset_artifacts` field. (depends: T008)
- [X] T010 [US1] Add the run invocation to `scripts/validate_phase4.py`: export `LLMXIVE_INSPECTION_DIR=specs/014-…/inspections/<id>`, subprocess `python -m llmxive run --project <id> --max-tasks 2`, capture exit code + run-id. (depends: T009)
- [X] T011 [US1] Add post-run verification to `scripts/validate_phase4.py`: assert the stage chain reached `analyzed` (or `human_input_needed`/`held`) by reading `state/projects/<id>.yaml` + the run-log; assert the five plan artifacts + `tasks.md` exist, that `tasks.md` has ≥10 `^- \[ \] T###` lines (SC-004/FR-009), and that `spec.md` is unchanged (FR-018); run the FR-010 data-flow ordering check (download-before-use, dir-before-write) on the produced `tasks.md`; run the FR-012 constraint-non-deletion check (no `FR-NNN`/`SC-NNN` line count decrease across the Tasker's Mode-B `spec.md` rewrites, read from the inspection `rounds[]`); surface any mismatch as a finding. (depends: T010)
- [ ] T012 [US1] Run `python scripts/validate_phase4.py --project PROJ-261-evaluating-the-impact-of-code-duplicatio` (REAL Dartmouth call) and confirm it reaches `analyzed`; commit the produced artifacts. (depends: T004, T007, T011)
- [ ] T013 [US1] Run `python scripts/validate_phase4.py --project PROJ-262-predicting-molecular-dipole-moments-with` (REAL Dartmouth call) and confirm it reaches `analyzed`; commit the produced artifacts. (depends: T012)

**Checkpoint**: Both canonicals at `analyzed` with real plan artifacts + `tasks.md` on disk.

---

## Phase 4: User Story 2 — Inspect inputs + outputs at every step (Priority: P1)

**Goal**: Every agent invocation (and every Tasker analyze round) leaves a reconstructable inspection record.
**Independent test**: open the four records; each has verbatim prompts + raw response + diffs; the Tasker records nest one entry per round.

- [ ] T014 [US2] In `scripts/validate_phase4.py`, after each run assert `inspections/<id>/planner.json` and `tasker.json` exist with every required key incl. `rounds` (FR-003/FR-004/SC-005), and that the Tasker record has one `rounds[]` entry per analyze round actually run (cross-check against `tasker_rounds.yaml`). (depends: T012, T013)
- [ ] T015 [US2] Add an SC-009 reconstruction assertion to `scripts/validate_phase4.py` and `tests/integration/test_phase4_plan_tasks.py`: from a record alone, `prompts.system`, `prompts.user`, `raw_response`, and each round's `analyze_report`+`mode_b_patch` are present and non-empty. (depends: T014)

**Checkpoint**: 4 inspection records on disk, schema-valid, reconstructable.

---

## Phase 5: User Story 3 — Quality gates catch silent shortcuts (Priority: P1)

**Goal**: Template/invented/evasive output is rejected by real guard code.
**Independent test**: `pytest tests/integration/test_phase4_plan_tasks.py -v` — all gate tests pass against the real guards.

- [X] T016 [US3] Write the FR-016(a) FILE-marker split test AND the FR-005 completeness test AND the FR-008 template-rejection test in `tests/integration/test_phase4_plan_tasks.py`: a valid 5-file block splits to 5 keys; a no-marker / 4-file / empty-artifact response raises `IncompleteArtifactSet` and `write_artifacts` unlinks (FR-005); a template-equal `plan.md` triggers `_real_only_guard.guard_emit`'s `TemplateRefused` (FR-008).
- [X] T017 [US3] Write the FR-016(b) URL-reachability test in `tests/integration/test_phase4_plan_tasks.py` using a real local `http.server` fixture: 200 passes; 404, 500, and a connect-timeout each raise `UnreachableReference`; assert `PlannerAgent.write_artifacts` unlinks artifacts + raises. (depends: T003)
- [X] T018 [US3] Write the FR-007 consistency test in `tests/integration/test_phase4_plan_tasks.py`: `assert_data_model_contracts_consistent` raises `InconsistentDataModel` on an entity-without-schema and a schema-without-entity; passes when aligned. (depends: T003)
- [X] T019 [US3] Write the FR-016(c) prose-stub `tasks.md` test in `tests/integration/test_phase4_plan_tasks.py` against the real `tasks_cmd` Mode-A validator (`<5` `T###` lines raises; stage holds at `planned`).
- [X] T020 [US3] Write the FR-016(d) Mode-B diff-leak test, FR-016(e) Mode-B header-preservation test, AND the FR-012 constraint-non-deletion test in `tests/integration/test_phase4_plan_tasks.py` against the real `tasks_cmd` Mode-B path (`_diff_guard.looks_like_diff`; the `<1 header` skip) and the `validate_phase4` FR/SC-count check (a Mode-B `spec.md` rewrite that drops an `FR-NNN` line is flagged; a non-reducing rewrite passes).
- [X] T021 [US3] Write the FR-016(f) analyze-loop cap test in `tests/integration/test_phase4_plan_tasks.py`: drive a never-clean analyze so the loop hits `TASKER_MAX_REVISION_ROUNDS`; assert `human_input_needed.yaml` is written, the stage holds at `analyze_in_progress`, and the run-log/outcome is `escalated`. (depends: T007)

**Checkpoint**: All six FR-016 tests + the FR-007 test green against real code.

---

## Phase 6: User Story 4 — Carry-forward + Phase 5 handoff (Priority: P2)

**Goal**: A machine-readable manifest hands both canonicals to Phase 5.
**Independent test**: open `carry-forward.yaml`; both projects appear with `final_state: analyzed` and `status: passed` (or accurate failure/hold).

- [X] T022 [US4] Implement `carry-forward.yaml` generation in `scripts/validate_phase4.py` per `contracts/carry-forward.md` (per-project `final_state`, `status`, `agents_run` incl. `analyze_rounds`, justification citing inspection path on failure). (depends: T011)
- [X] T023 [US4] Implement `phase-report.md` generation in `scripts/validate_phase4.py` per `contracts/phase-report.md` (summary, FR→evidence table, quality-gate findings naming inspection paths, Mode-B coverage statement per project — SC-010/SC-011). (depends: T014, T022)
- [ ] T024 [US4] Generate `carry-forward.yaml` + `phase-report.md` from the real PROJ-261/262 runs; assert SC-008 (recorded `final_state` matches each on-disk `state/projects/<id>.yaml` `current_stage`) and SC-002/FR-020 (each produced `plan.md` contains a Constitution Check section addressing every numbered principle, verified by automated scan). (depends: T013, T022, T023)

**Checkpoint**: `carry-forward.yaml` + `phase-report.md` written; both projects `passed` at `analyzed`.

---

## Phase 7: Polish & Cross-Cutting

- [X] T025 [P] Write the FR-010 ordering-check unit test, the inspection-record-schema test (incl. `rounds` + `_redact` no-secrets), and the carry-forward-schema test in `tests/integration/test_phase4_plan_tasks.py`.
- [X] T026 Run the full verification suite: `pytest tests/integration/test_phase4_plan_tasks.py -v` and a broader `pytest tests/ -q` to catch regressions from the `plan_cmd`/`tasks_cmd`/`_inspection`/`slash_command` edits. Fix the CODE (never weaken a test) until green; re-run the ENTIRE suite after any fix (CLAUDE.md).
- [X] T027 [P] Commit-safety: assert the produced inspection records contain no secret-shaped strings (`_inspection._redact`); confirm no key/token committed; update `requirements.txt`/`pyproject.toml` only if a dependency was added (expected: none — stdlib only).
- [X] T028 [P] Documentation parity: confirm `specs/014-…/quickstart.md` flags/paths match the implemented `scripts/validate_phase4.py`; update either to match (Principle: documentation parity).

---

## Dependencies & ordering

- Setup (T001–T002) → Foundational (T003–T007) → US1 (T008–T013) → US2 (T014–T015) → US3 (T016–T021) → US4 (T022–T024) → Polish (T025–T028).
- Hard edges: T004←T003; T006←T005; T007←T006; T009←T008←(none); T010←T009; T011←T010; T012←T004,T007,T011; T013←T012; T014←T012,T013; T015←T014; T017←T003; T018←T003; T021←T007; T022←T011; T023←T014,T022; T024←T013,T022,T023.
- US3 tests (T016–T021) depend only on Foundational code (T003/T007), so they can be written in parallel with the US1 real runs once Foundational is done.

## Parallel execution examples

- After T002: run T003 and T005 in parallel (different files: `_research_guard.py` vs `_inspection.py`).
- After Foundational: write the US3 guard tests (T016–T021, distinct test functions) alongside executing the US1 real runs (T012–T013).
- Polish: T025/T027/T028 touch independent concerns and can run in parallel.

## Implementation strategy

MVP = Foundational + US1 (a real project reaches `analyzed` through the hardened production path with inspection capture). US2 adds reviewability, US3 proves the gates, US4 hands off to Phase 5. Ship incrementally; commit after each phase checkpoint (CLAUDE.md: frequent commits).
