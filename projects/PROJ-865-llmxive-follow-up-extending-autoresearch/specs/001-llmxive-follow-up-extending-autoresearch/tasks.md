# Tasks: llmXive follow-up: extending "AutoResearchClaw"

**Input**: Design documents from `/specs/001-llmxive-followup/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

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

- [ ] T001a [Setup] Create directory `code/` at repository root
- [ ] T001b [Setup] Create directory `data/` at repository root
- [ ] T001c [Setup] Create directory `data/raw/` at repository root
- [ ] T001d [Setup] Create directory `data/derived/` at repository root
- [ ] T001e [Setup] Create directory `data/artifacts/` at repository root
- [ ] T001f [Setup] Create directory `specs/001-llmxive-followup/contracts/`
- [ ] T001g [Setup] Create directory `code/01_data_ingestion/`
- [ ] T001h [Setup] Create directory `code/02_annotation_distillation/`
- [ ] T001i [Setup] Create directory `code/03_execution/`
- [ ] T001j [Setup] Create directory `code/04_analysis/`
- [ ] T001k [Setup] Create directory `code/utils/`
- [ ] T001l [Setup] Create directory `code/tests/`

- [X] T002 [Setup] Create `requirements.txt` at repository root with pinned versions (pandas, numpy, scikit-learn, statsmodels, pydantic, datasets, torch-cpu, transformers, psutil, scipy)
- [ ] T003 [P] [Setup] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [Setup] Create schema contracts in `specs/001-llmxive-followup/contracts/` (`failure_case.schema.yaml`, `distilled_rule.schema.yaml`, `pivot_attempt.schema.yaml`)
- [X] T005 [Setup] Implement `code/utils/config.py` with environment variables, random seeds, and explicit resource limits: `MAX_CPU_CORES=2`, `MAX_MEMORY_GB=7`
- [X] T005c [Setup] Implement `code/utils/resource_watchdog.py` to actively monitor CPU and RAM usage at runtime; if limits (2 cores, 7GB) are exceeded, the watchdog MUST kill the process immediately. This file must be importable and usable by execution tasks.
- [X] T006 [Setup] Implement `code/utils/logging.py` for structured logging of pipeline stages
- [ ] T007 [Setup] Create `code/utils/update_state.py` to calculate SHA-256 hashes of artifacts and update `state.yaml`
- [ ] T008 [Setup] Create `.gitignore` rules for `data/raw/`, `data/derived/`, and `data/artifacts/`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Failure Mode Annotation & Rule Distillation Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest ARC-Bench failure transcripts, annotate structural features, and generate a deterministic rule library using a CPU-tractable small model.

**Independent Test**: Run the pipeline on a small held-out subset of cases. and verify `rules_library.json` contains valid "If-Condition-Then-Action" structures.

### Implementation for User Story 1

- [X] T009 [US1] Implement `code/01_data_ingestion/download_arc_bench.py` to fetch the ARC-Bench 25-topic subset via HuggingFace `datasets`.
- [X] T010 [US1] Implement `code/01_data_ingestion/parse_reasoning_traces.py` to extract raw error logs and ground-truth resolutions from traces
- [X] T011 [US1] Implement `code/02_annotation_distillation/annotate_failures.py` to label failures as Syntactic, Logical, Semantic, Missing Context, or Unstructured
- [ ] T012 [US1] Add schema validation in `annotate_failures.py` to ensure output matches `specs/001-llmxive-followup/contracts/failure_case.schema.yaml` before writing to `data/derived/`
- [X] T013 [US1] Implement `code/02_annotation_distillation/distill_rules.py` using a CPU-tractable small model (e.g., TinyLlama-1.1B); use `psutil` to monitor RAM; if RAM > 6GB, switch to a regex-based heuristic extraction fallback (using frequent error substrings). **This task must be executed wrapped by the ResourceWatchdog from T005c.**
- [ ] T013b [US1] If T013 triggers the regex fallback, document this deviation as a scope change in `data/derived/scope_changes.md` to preserve FR-002 intent.
- [X] T014 [US1] Implement validation logic to calculate coverage against the validation split and assert >= 0.90; **This task acts as the gatekeeper:** if coverage < 90%, the build fails unless T013d retry succeeds. Output `data/derived/coverage_report.json`.
- [ ] T013d [US1] **Retry Loop**: IF T014 fails (coverage < 90%) AND T013b triggered (regex fallback), explicitly re-run `distill_rules.py` with a smaller model (e.g., TinyLlama-1.1B quantized or a simpler regex set) and re-validate coverage. Do not proceed until coverage >= 90% or all fallback options exhausted.
- [ ] T015 [US1] Add schema validation in `distill_rules.py` to ensure output matches `specs/001-llmxive-followup/contracts/distilled_rule.schema.yaml`
- [ ] T016 [US1] Add logging to track annotation counts and rule generation metrics

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Rule Engine Execution & Baseline Comparison (Priority: P2)

**Goal**: Execute the distilled rule engine on a held-out test set and compare performance against the full baseline agent.

**Independent Test**: Run on 10 unseen tasks, log "Time-to-Pivot" and "Success", and verify metrics match expected format.

**⚠️ DEPENDENCY**: This phase MUST wait for Phase 3 (US1) completion to access `rules_library.json`.

### Implementation for User Story 2

- [X] T017 [US2] Implement `code/03_execution/rule_engine.py` to parse error logs and execute pivot actions without LLM invocation. **This task must be executed wrapped by the ResourceWatchdog from T005c.**
- [~] T018 [US2] Implement logic in `rule_engine.py` to handle "Unstructured" cases by defaulting to baseline retrieval method
- [~] T019a [US2] **CRITICAL**: Implement `code/03_execution/generate_manifest.py` to create `data/derived/experiment_manifest.csv` containing exactly 100 stratified task IDs (balanced by failure type). This file is the SINGLE SOURCE OF TRUTH for both rule engine and baseline tasks.
- [~] T019 [US2] Implement `code/03_execution/run_experiments.py` to run the rule engine on the tasks listed in `data/derived/experiment_manifest.csv`.
- [~] T020 [US2] Ensure `run_experiments.py` records "Time-to-Pivot" (seconds), "Success Rate of First Pivot" (binary), and `failure_type` for every task, appending rows to `data/derived/results.csv` with columns: task_id, method, time_to_pivot, success, failure_type
- [X] T021 [US2] Implement `code/03_execution/run_baseline_external.py` to orchestrate baseline agent execution on external resources. The script MUST:
 1. Accept `data/derived/experiment_manifest.csv` (from T019a) as input to ensure strict task ID alignment.
 2. Invoke the baseline agent via CLI: `python code/03_execution/run_baseline.py --manifest <path> --output data/derived/baseline_results.json`.
 3. Output `data/derived/baseline_results.json` with the exact same task IDs as the manifest.
- [ ] T022 [US2] Implement logic in `run_experiments.py` to merge CI rule-engine logs with external baseline logs from `data/derived/baseline_results.json` (generated by T021) into a single `data/derived/results.csv`, ensuring strict ID matching for paired comparison using the manifest from T019a.
- [~] T023 [US2] Add stratification logic to ensure metrics are recorded separately for each failure type (Syntactic, Semantic, etc.)
- [ ] T024 [US2] Add validation to ensure `data/derived/results.csv` schema matches `specs/001-llmxive-followup/contracts/pivot_attempt.schema.yaml`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Analysis & Error Taxonomy (Priority: P3)

**Goal**: Perform mixed-effects logistic regression and categorize failed pivots to determine the interaction between failure type and method.

**Independent Test**: Run analysis script and verify output includes regression coefficients for the interaction term.

**⚠️ DEPENDENCY**: This phase MUST wait for Phase 4 (US2) completion to access `data/derived/results.csv`.

### Implementation for User Story 3

- [X] T025 [US3] Implement `code/04_analysis/statistical_model.py` to fit mixed-effects logistic regression (Success ~ FailureType * Method + (1|TaskID))
- [ ] T026 [US3] Ensure `statistical_model.py` outputs p-values for the interaction term and determines significance (p < 0.05); write results to `data/derived/regression_results.json` including key `interaction_p_value`
- [~] T029a [US3] Implement `code/04_analysis/time_diff_test.py` to perform paired t-test or Wilcoxon signed-rank test on "Time-to-Pivot" differences using `scipy.stats`. **Output schema must be a JSON file `data/derived/time_diff_results.json` containing keys: `p_value`, `ci_lower`, `ci_upper`, `statistic`.**
- [~] T027 [US3] Implement `code/04_analysis/error_taxonomy.py` to categorize failed pivots. **Inputs**: `data/derived/results.csv` and `data/derived/failure_cases.json`. **Logic**: If no rule matches -> "Coverage Gap"; If rule matches but action != ground_truth -> "Distillation Error".
- [ ] T027b [US3] **Execute & Populate**: Run `error_taxonomy.py` against `data/derived/results.csv` and `data/derived/failure_cases.json` to generate `data/derived/error_taxonomy_results.json`. **This task must complete before T029c.**
- [~] T028 [US3] Ensure `error_taxonomy.py` uses ground-truth resolution to arbitrate the categorization of failures
- [ ] T029b [US3] Implement `code/04_analysis/calculate_stratified_rates.py` to calculate "Success Rate of First Pivot" stratified by failure type. **Output**: `data/derived/stratified_success_rates.csv` with columns for each failure type (e.g., `syntactic_rate`, `semantic_rate`).
- [ ] T029c [US3] Generate `data/derived/final_report.md` aggregating Time-to-Pivot t-test results (from T029a), **Stratified Success Rates from T029b**, Error Taxonomy Results (from T027b), and regression coefficients (SC-003).
- [ ] T030 [US3] Add checks to ensure total compute time and memory usage are logged and compared against CI limits (h, memory threshold).

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T031 [P] Write `code/tests/test_rule_engine.py` to validate rule matching logic and edge cases
- [ ] T032 [P] Write `code/tests/test_pipeline.py` for integration tests of the full data flow
- [ ] T033 Update `quickstart.md` with instructions for running the pipeline and external baseline
- [ ] T034 Run `code/utils/update_state.py` to finalize `state.yaml` with all artifact hashes
- [ ] T035a [P] Run `ruff --check` on `code/` and verify exit code 0 (linting pass)
- [ ] T035b [P] Run `black --check` on `code/` and verify exit code 0 (formatting pass)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**:
 - **User Story 1 (Phase 3)**: Can start after Foundational (Phase 2) - No dependencies on other stories
 - **User Story 2 (Phase 4)**: MUST wait for User Story 1 (Phase 3) completion to access `rules_library.json` and T019a manifest
 - **User Story 3 (Phase 5)**: MUST wait for User Story 2 (Phase 4) completion to access `results.csv`
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- **ONLY User Story 1** can start after Foundational phase completion.
- User Story 2 and User Story 3 are **strictly sequential** and cannot start in parallel with previous stories due to data-flow dependencies.
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members ONLY if the sequential dependency constraints (US1 -> US2 -> US3) are respected.

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
 - Developer B: User Story 2 (MUST wait for US1 artifacts)
 - Developer C: User Story 3 (MUST wait for US2 artifacts)
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