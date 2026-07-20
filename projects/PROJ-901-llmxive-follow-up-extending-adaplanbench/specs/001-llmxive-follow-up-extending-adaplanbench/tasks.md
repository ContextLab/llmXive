# Tasks: llmXive follow-up: extending "AdaPlanBench: Evaluating Adaptive Planning in Large Language Model Age"

**Input**: Design documents from `/specs/001-llmxive-follow-up-extending-adaplanbench/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

<!--
 ============================================================================
 IMPORTANT: The tasks below are SAMPLE TASKS for illustration purposes only.

 The /speckit-tasks command MUST replace these with actual tasks based on:
 - User stories from spec.md (with their priorities P1, P2, P3...)
 - Feature requirements from plan.md
 - Entities from data-model.md
 - Endpoints from contracts/

 Tasks MUST be organized by user story so each story can be:
 - Implemented independently
 - Tested independently
 - Delivered as an MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 [P] Create `data/raw/` directory
- [X] T002 [P] Create `data/processed/` directory
- [X] T003 [P] Create `code/` directory structure including `dataset/`, `agent/`, `analysis/`
- [X] T004 [P] Create `tests/unit/` and `tests/integration/` directories
- [X] T005 [P] Initialize Python project with `requirements.txt` (transformers, datasets, pandas, statsmodels, scikit-learn, pytest)
- [X] T006 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T007 Implement `code/config.py` with paths, random seeds, and resource limits (scaled vCPU, increased RAM)
- [X] T008 Implement `code/main.py` orchestration script with resource monitor wrapper (logs CPU/RAM per task, fails fast on limit)
- [X] T009 Create base `code/agent/base.py` abstract agent interface
- [X] T026a [P] [US3] Create `contracts/statistical-results.schema.yaml` defining the structure for GLMM output. Fields: `fixed_effects` (dict), `interaction_p_value` (float), `interaction_effect_size` (float), `convergence_status` (bool).
- [X] T026b [P] [US3] Create `contracts/power-report.schema.yaml` defining the structure for power analysis output. Fields: `calculated_power` (float), `effect_size` (float), `target_power` (float), `pass` (bool).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Dataset Preparation and Constraint Filtering (Priority: P1) 🎯 MVP

**Goal**: Isolate the specific subset of AdaPlanBench where constraints are revealed progressively (≥5) to establish the independent variable.

**Independent Test**: Load raw dataset, apply filter, verify output count and `constraint_count` field for a sample of tasks against metadata.

### Implementation for User Story 1

- [X] T010 [US1] Unit test for filter logic in `tests/unit/test_filter.py` (verifies exclusion of <5 constraints)
- [X] T012 [US1] Implement `code/dataset/loader.py` to fetch AdaPlanBench household tasks from `datasets.load_dataset('adaplanbench/adaplanbench')` (or the official URL). On fetch failure, raise a clear error and abort – no mock fallback.
- [X] T013 [US1] Implement filtering logic in `code/dataset/loader.py` to select tasks with ≥5 progressive constraint reveals
- [X] T014 [US1] Add `constraint_count` metadata column to filtered output in `data/processed/filtered_tasks.csv`. The column MUST be an integer derived from `len(progressive_constraints)` for each task, ensuring semantic alignment with US-1.
- [X] T011 [US1] Integration test `test_filtered_dataset_schema` in `tests/integration/test_dataset_content.py` (verifies `progressive_constraints` schema and `constraint_count` field presence; **Run AFTER T014**)
- [X] T015 [US1] Implement validation script `code/dataset/validate_subset.py` to sample a subset of tasks and verify constraint counts match original metadata

**Checkpoint**: Filtered dataset ready; independent variable established.

---

## Phase 4: User Story 2 - Dual-Track Agent Execution and Constraint Logging (Priority: P2)

**Goal**: Execute dual-track architecture (SLM generator + deterministic constraint store) and monolithic baseline, logging violations and corrections.

**Independent Test**: Run agent on a known task with a specific constraint violation; verify rule-based module intercepts, corrects, and logs the event.

### Tests for User Story 2

- [X] T016 [P] [US2] Unit test for `code/agent/resolver.py` in `tests/unit/test_resolver.py` (verifies string matching and negation patterns)
- [X] T017 [P] [US2] Contract test for execution log schema in `tests/contract/test_execution_log_schema.py`

### Implementation for User Story 2

- [X] T018 [US2] Implement `code/agent/monolithic.py` (direct SLM prompt) using a CPU‑tractable small model (e.g., Phi‑mini) in default precision
- [X] T019 [US2] Implement `code/agent/constraint_store.py` (deterministic key‑value store for active constraints)
- [X] T020 [US2] Implement `code/agent/resolver.py` with exact string matching, case‑insensitive substring matching, and explicit negation patterns (FR‑007)
- [X] T021 [US2] Implement `code/agent/dual_track.py` to orchestrate generator, store, and resolver; log "false_negative" if intent parsing fails (FR‑008)
- [X] T022 [US2] Implement logic to log "implicit_unverified" for constraints requiring common-sense reasoning. If the rule-based resolver fails to match a constraint via explicit patterns (FR-007), log the event as "implicit_unverified", flag it for human review, and exclude it from the primary violation rate calculation (FR-009). Do NOT hardcode specific keywords; implement a generic detector for non-explicit constraints.
- [X] T023a [US2] Implement `code/agent/monolithic_runner.py` with function `run_monolithic(dataset, model)` to execute the monolithic baseline on `data/processed/filtered_tasks.csv`. Output logs to `data/processed/monolithic_logs.json` conforming to `contracts/execution-log.schema.yaml`. **Run AFTER T014**.
- [X] T023b [US2] Implement `code/agent/dual_track_runner.py` with function `run_dual_track(dataset, generator, store, resolver)` to execute the dual-track agent on `data/processed/filtered_tasks.csv`. Output logs to `data/processed/dual_track_logs.json` conforming to `contracts/execution-log.schema.yaml`. **Run AFTER T014**.
- [X] T023c [US2] Implement `code/analysis/log_aggregator.py` with function `aggregate_logs(monolithic_path, dual_track_path)` to merge `monolithic_logs.json` and `dual_track_logs.json` into `data/processed/execution_traces.csv`. **Run AFTER T023a AND T023b**.
- [X] T024 [US2] Generate `data/processed/execution_traces.csv` containing architecture type, constraint count, violation boolean, and final score

**Checkpoint**: Dual‑track and monolithic agents executed; violation logs generated.

---

## Phase 5: User Story 3 - Statistical Analysis and Validation (Priority: P3)

**Goal**: Perform GLMM analysis and human annotation validation to determine if explicit constraint tracking mitigates performance degradation.

**Independent Test**: Run GLMM on logs; verify output includes fixed effect estimates, p‑values, and convergence diagnostics.

### Tests for User Story 3

- [X] T025 [P] [US3] Unit test for GLMM model fitting in `tests/unit/test_glmm.py` (sanity check on synthetic data)
- [X] T026 [P] [US3] Integration test for power analysis in `tests/integration/test_power_analysis.py`

### Implementation for User Story 3

- [X] T027 [US3] Implement `code/analysis/power.py` to perform power analysis on the filtered subset (target: detect medium effect size f² ≥ 0.15, power ≥ 0.80). Use `statsmodels.stats.power` or equivalent. Generate `data/processed/power_report.json` containing the calculated power value, the effect size, and a **pass/fail flag** (True if power ≥ 0.80, else False). Log the result regardless of pass/fail status; a 'fail' does not halt the pipeline. **Run AFTER T014**.
- [X] T028 [US3] Implement `code/analysis/glmm.py` to fit GLMM with binomial link function testing interaction between "number of constraints" and "architecture"
- [X] T029 [US3] Implement `code/hash_artifacts.py` to compute SHA‑256 hashes for existing files in `data/` (if any exist) and update state YAML (Constitution Principle V)
- [X] T030 [US3] Implement `code/dataset/annotator.py` CLI to randomly select a sample of **50 tasks** from `data/processed/filtered_tasks.csv`. Use `random.seed()` and stratified sampling by `constraint_count` (bins: 5, 6, 7, 8+) to ensure representativeness. Output `data/processed/annotation_sample.csv` with columns: `task_id`, `raw_prompt`, `constraint_list`. This sample is independent of the rule-based module (FR-010). **Run AFTER T014**.
- [X] T031 [US3] Implement comparison script that reads `data/processed/execution_traces.csv` and the human‑annotated ground truth (simulated from `data/processed/annotation_sample.csv` for pipeline validation), computes the agreement rate with confidence interval, and writes `data/processed/agreement_rate_report.json`. **Run AFTER T030**.
- [X] T032 [US3] Generate `data/processed/statistical-results.json` with GLMM p‑values, effect sizes, convergence status; structure matches `contracts/statistical-results.schema.yaml`. **Run AFTER T026a, T027, T028**.
- [X] T033 [US3] [P] Update `research.md` with a results section comparing dual‑track vs. monolithic violation rates across constraint counts. Explicitly report the **interaction effect** p-value and effect size as per SC-002. Link this output to the final paper generation to satisfy Constitution Principle IV.
- [X] T034 [US3] [P] Add unit tests for edge cases in `tests/unit/` including: implicit constraint handling (no violation logged), parsing failures (false_negative logged), and empty constraint lists

**Checkpoint**: Statistical significance established; hypothesis tested.

---

## Phase N: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T041 [P] Refactor `code/agent/resolver.py` to reduce cyclomatic complexity to <15 by extracting method `parse_intent` and `match_constraint` to separate modules
- [X] T007a [P] [US1] Generate `quickstart.md` with setup instructions, dependency installation, and execution steps to validate the project structure. (Reference plan.md Phase 1 documentation requirements). **Run AFTER all Phase 3, 4, 5 tasks are complete.**
- [X] T043 [P] Run `quickstart.md` validation and ensure all steps complete within 6 hours on CI

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Phase N**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for [endpoint] in tests/contract/test_[name].py"
Task: "Integration test for [user journey] in tests/integration/test_[name].py"

# Launch all models for User Story 1 together:
Task: "Create [Entity1] model in src/models/[entity1].py"
Task: "Create [Entity2] model in src/models/[entity2].py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1
   - Developer B: User Story 2
   - Developer C: User Story 3
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Scope Note**: Phase 6 (Turing-Adaptation) has been removed to align with the approved scope in `spec.md`.