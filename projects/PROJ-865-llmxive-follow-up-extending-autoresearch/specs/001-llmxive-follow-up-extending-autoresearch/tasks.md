# Tasks: llmXive follow-up: extending "AutoResearchClaw"

**Input**: Design documents from `/specs/001-llmxive-followup/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this user story belongs to (e.g., US1, US2, US3)
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

## Phase 0: Constitutional Gates

**Purpose**: Mandatory validation steps required by the Project Constitution before any development begins.

- [ ] T002 [Setup] **Reference-Validator Execution**: Implement and execute the `Reference-Validator Agent` as a blocking gate against `research.md`. **Action**: Run the validator script. **Gate**: If any citation is `unreachable` or `mismatch`, the pipeline MUST fail and block all subsequent tasks. **Output**: `data/artifacts/citation_validation_report.json` with status `PASS` or `FAIL`. **Dependency**: None (runs first).

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 [Setup] Initialize Project Structure: Create the full directory tree (`code/`, `data/`, `data/raw/`, `data/derived/`, `data/artifacts/`, `specs/001-llmxive-followup/contracts/`, `code/01_data_ingestion/`, `code/02_annotation_distillation/`, `code/03_execution/`, `code/04_analysis/`, `code/utils/`, `tests/`) and place a `.gitkeep` file in each to ensure they are committed and verifiable. **Note**: Uses `code/` at root per `plan.md` structure, not `src/`. **Dependency**: T002.

- [ ] T003 [Setup] Create `requirements.txt` at repository root with pinned versions (pandas, numpy, scikit-learn, statsmodels, pydantic, datasets, torch-cpu, transformers, psutil, scipy)

- [ ] T004 [P] [Setup] **Configure Linting and Formatting**: Create `pyproject.toml` at repository root with explicit `[tool.ruff]` and `[tool.black]` sections. **Action**: Write the following content to `pyproject.toml`:
```toml
[tool.ruff]
line-length = 88
target-version = "py310"
ignore = ["E501"]

[tool.black]
line-length = 88
target-version = ['py310']
```
**Artifact**: `pyproject.toml`. **Dependency**: T002.

- [ ] T005 [P] [Setup] **Create .gitignore**: Create or update the root `.gitignore` file to explicitly include rules for `data/raw/`, `data/derived/`, and `data/artifacts/`. **Action**: Append the following lines to `.gitignore`:
```text
data/raw/*
!data/raw/.gitkeep
data/derived/*
!data/derived/.gitkeep
data/artifacts/*
!data/artifacts/.gitkeep
```
**Artifact**: `.gitignore`. **Dependency**: T002.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T006a [Setup] **Create Schema**: Create `specs/001-llmxive-followup/contracts/failure_case.schema.yaml` with explicit JSON schema definition: keys `task_id` (string), `raw_error_log` (string), `ground_truth_resolution` (string), `annotated_structural_feature` (enum: "Syntactic Error", "Logical Loop", "Semantic Ambiguity", "Missing Context", "Unstructured").

- [ ] T006b [Setup] **Create Schema**: Create `specs/001-llmxive-followup/contracts/distilled_rule.schema.yaml` with explicit JSON schema definition: keys `rule_id` (string), `condition_pattern` (string), `pivot_action` (string), `confidence` (float).

- [ ] T006c [Setup] **Create Schema**: Create `specs/001-llmxive-followup/contracts/pivot_attempt.schema.yaml` with explicit JSON schema definition: keys `task_id` (string), `method` (string), `time_to_pivot` (float), `success` (boolean), `failure_type` (string).

- [ ] T007 [Setup] Implement `code/utils/config.py` with environment variables, random seeds, and explicit resource limits: `MAX_CPU_CORES=2`, `MAX_MEMORY_GB=7`, `TIMEOUT_SECONDS=3600`.

- [ ] T007c [Setup] Implement `code/utils/resource_watchdog.py` to actively monitor CPU and RAM usage at runtime. **IPC Mechanism**: If RAM > 7GB, the watchdog MUST raise a `ResourceLimitExceeded` exception and exit with code 1 (failure). **Constraint**: The distillation script (T013) and rule engine (T017) must be invoked via a wrapper that catches this exception and fails the task; NO fallback to regex or other methods is permitted. **Dependency**: T007.

- [ ] T008 [Setup] Implement `code/utils/logging.py` for structured logging of pipeline stages

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Failure Mode Annotation & Rule Distillation Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest ARC-Bench failure transcripts, annotate structural features, and generate a deterministic rule library using a CPU-tractable small model.

**Independent Test**: Run the pipeline on a small held-out subset of cases and verify `rules_library.json` contains valid "If-Condition-Then-Action" structures.

### Implementation for User Story 1

- [ ] T009 [US1] Implement `code/01_data_ingestion/download_arc_bench.py` to fetch the ARC-Bench topic subset via HuggingFace `datasets`.

- [ ] T010 [US1] Implement `code/01_data_ingestion/parse_reasoning_traces.py` to extract raw error logs and ground-truth resolutions from traces

- [ ] T011b [US1] [FR-001] **Artifact Generation**: Implement `code/02_annotation_distillation/annotate_failures.py` to read `data/derived/parsed_traces.json` (from T010), annotate each case with exactly one structural feature, and write the labeled dataset to `data/derived/failure_cases.json`. **Schema**: The JSON MUST be an array of objects with keys: `task_id` (string), `raw_error_log` (string), `ground_truth_resolution` (string), `annotated_structural_feature` (enum: "Syntactic Error", "Logical Loop", "Semantic Ambiguity", "Missing Context", "Unstructured"). **Data Splitting**: Implement logic within this script to split `failure_cases.json` into `failure_cases_train.json`, `failure_cases_val.json`, AND `failure_cases_test.json` using the fixed random seed from `config.py`. **Schema Validation**: Validate output against `specs/001-llmxive-followup/contracts/failure_case.schema.yaml` (T006a) before writing; if validation fails, raise an explicit error and stop. **Output**: Save all three files to `data/derived/`. **Dependency**: T006a, T010.

- [ ] T013 [US1] [FR-002] Implement `code/02_annotation_distillation/distill_rules.py` using a CPU-tractable small model. **Model Selection**: Attempt to load models in the following order, stopping at the first one that fits within 7GB RAM: `Llama-3-8B-INT4`, `TinyLlama-1.1B`, `Phi-3-mini-4k-instruct`. **Resource Handling**: Use `psutil` to monitor RAM. If the current model exceeds 7GB RAM, the script MUST immediately attempt the next smaller model. If no model fits, the script MUST FAIL with exit code 1. **Coverage Logic**: The script MUST achieve ≥90% coverage on `data/derived/failure_cases_val.json` using the LLM. If coverage < 90%, the script MUST FAIL with exit code 1 (NO fallback to regex). **Execution**: This task must be executed wrapped by the ResourceWatchdog from T007c. **Output**: Write `data/derived/rules_library.json` containing the generated rules. **Dependency**: T011b, T006b, T007c.

- [ ] T014 [US1] [FR-002] **Coverage Measurement**: Run the validation logic to calculate rule coverage against `data/derived/failure_cases_val.json` defined in T011c. Output `data/derived/coverage_report.json` with the final coverage percentage. **Logic**: If coverage < 90%, the task MUST FAIL with exit code 1. **Note**: This task measures the final coverage after T013's logic. **Dependency**: T013.

- [ ] T015b [US1] Add schema validation in `distill_rules.py` to ensure output matches `specs/001-llmxive-followup/contracts/distilled_rule.schema.yaml`. **Dependency**: T006b.

- [ ] T016 [US1] Add logging to track annotation counts and rule generation metrics: Extend `annotate_failures.py` to write structured logs to `data/artifacts/annotation.log`. **Metrics**: Log `total_cases`, `syntactic_count`, `semantic_count`, `logical_count`, `missing_count`, `unstructured_count`. **Dependency**: T011b.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Rule Engine Execution & Baseline Comparison (Priority: P2)

**Goal**: Execute the distilled rule engine on a held-out test set and compare performance against the full baseline agent.

**Independent Test**: Run on 10 unseen tasks, log "Time-to-Pivot" and "Success", and verify metrics match expected format.

**⚠️ DEPENDENCY**: This phase MUST wait for Phase 3 (US1) completion to access `rules_library.json` and `failure_cases.json`.

### Implementation for User Story 2

- [ ] T017 [US2] Implement `code/03_execution/rule_engine.py` to parse error logs and execute pivot actions without LLM invocation. **This task must be executed wrapped by the ResourceWatchdog from T007c.**

- [ ] T018 [US2] Implement logic in `rule_engine.py` to handle "Unstructured" cases: If no rule matches, default to a probabilistic retrieval action using `code/01_data_ingestion/download_arc_bench.py` with `fallback_mode=True` and log the action as `Unstructured`. **Dependency**: T017.

- [ ] T019a [US2] **CRITICAL**: Implement `code/03_execution/generate_manifest.py` to create `data/derived/experiment_manifest.csv`. **Depends on T011b completion.**
 - **Source**: `data/derived/failure_cases_test.json` (from T011b).
 - **Logic**: Select **exactly 100** task IDs using a stratified random sample based on the `annotated_structural_feature` column (mapped to `failure_type`).
 - **Validation**: Verify the output CSV contains a sufficient number of rows before writing. If any stratum has fewer than the required sample size, the task MUST fail with an error message.
 - **Reproducibility**: Use the fixed random seed defined in `code/utils/config.py`.
 - **Output**: CSV with columns `task_id`, `failure_type`.
 - **Dependency**: T011b.

- [ ] T019 [US2] Implement `code/03_execution/run_experiments.py` to run the rule engine on the tasks listed in `data/derived/experiment_manifest.csv`.

- [ ] T020 [US2] Ensure `run_experiments.py` records "Time-to-Pivot" (seconds), "Success Rate of First Pivot" (binary), and `failure_type` for every task, appending rows to `data/derived/results_rule_engine.csv` with columns: task_id, method, time_to_pivot, success, failure_type. **Stratification**: Metrics MUST be recorded and tagged by `failure_type`. **Dependency**: T006c.

- [ ] T021c [US2] **Instrument Baseline Resource Metrics (Local Mode Only)**: Implement `code/03_execution/instrument_baseline.py` to wrap the baseline agent execution and capture resource metrics. **Logic**: 
 1. Accept `data/derived/experiment_manifest.csv` as input.
 2. **Local Mode Only**: Monitor process `CPU` and `RAM` via `psutil` and log to `data/derived/baseline_resource_metrics.json`.
 3. **Output**: `data/derived/baseline_resource_metrics.json` with schema `{ task_id, peak_memory_mb, cpu_time_seconds }`. **Dependency**: T019a.

- [ ] T021 [US2] Implement `code/03_execution/run_baseline_external.py` to orchestrate baseline agent execution and retrieval. **Logic**:
 1. Accept `data/derived/experiment_manifest.csv` as input.
 2. **Invoke T021c**: Run `instrument_baseline.py` as a wrapper to ensure resource metrics are generated.
 3. Trigger the baseline agent execution (e.g., via CLI or external job submission).
 4. **Polling Loop**: Poll for `data/derived/baseline_results.json` and `data/derived/baseline_resource_metrics.json` with exponential backoff. **Constraint**: Do NOT enforce an arbitrary timeout that blocks data collection; the process must wait for the external job to complete or fail permanently.
 5. **Timeout Handling**: If the job fails permanently (e.g., external error), log an error and exit with code 1. Implement a SIGINT signal handler to allow explicit cancellation.
 6. **Output**: `data/derived/baseline_results.json` with the exact same task IDs as the manifest. **Format**: JSON object with keys `task_id`, `time_to_pivot`, `success`. **Dependency**: T021c, T019a.

- [ ] T022 [US2] [FR-004] **Data Merging**: Implement `code/03_execution/merge_results.py` to merge CI rule-engine logs (`data/derived/results_rule_engine.csv`) with external baseline logs (`data/derived/baseline_results.json`) into a single `data/derived/results.csv`, ensuring strict ID matching for paired comparison using the manifest from T019a. **Validation**: Verify that `baseline_results.json` contains all task IDs from the manifest. If a task is missing due to external failure, mark it as 'failed' in `results.csv`. **Dependency**: T021, T019a.

- [ ] T029b [US3] [SC-002] Implement `code/04_analysis/calculate_stratified_rates.py` to calculate "Success Rate of First Pivot" stratified by failure type. **Output**: `data/derived/stratified_success_rates.csv` with columns for each failure type (e.g., `syntactic_rate`, `semantic_rate`). **Dependency**: T022.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Analysis & Error Taxonomy (Priority: P3)

**Goal**: Perform mixed-effects logistic regression and categorize failed pivots to determine the interaction between failure type and method.

**Independent Test**: Run analysis script and verify output includes regression coefficients for the interaction term.

**⚠️ DEPENDENCY**: This phase MUST wait for Phase 4 (US2) completion to access `data/derived/results.csv`.

### Implementation for User Story 3

- [ ] T025 [US3] Implement `code/04_analysis/statistical_model.py` to fit mixed-effects logistic regression (Success ~ FailureType * Method + (1|TaskID))

- [ ] T026a [US3] **Model Fitting**: Ensure `statistical_model.py` outputs p-values for the interaction term to `data/derived/regression_results.json`. **Dependency**: T022.

- [ ] T026b [US3] [SC-003] **Significance Determination**: Implement logic in `statistical_model.py` (or a wrapper) to compare the p-value from T026a against alpha=0.05. **Output**: Update `data/derived/regression_results.json` with key `interaction_significant` (boolean) and `narrative_conclusion` (string: "The interaction term is significant (p < 0.05)" or "The interaction term is not significant (p >= 0.05)"). **Dependency**: T026a.

- [ ] T029a [US3] [SC-001] Implement `code/04_analysis/time_diff_test.py` to perform paired t-test or Wilcoxon signed-rank test on "Time-to-Pivot" differences using `scipy.stats`. **Filtering**: **CRITICAL**: Include ALL rows from `data/derived/results.csv`. For rows where the baseline failed (timeout/error), impute `time_to_pivot` with the fixed timeout value defined in `config.py` to ensure the statistical population reflects the true cost of failure. **Output schema**: `data/derived/time_diff_results.json` containing keys: `p_value`, `ci_lower`, `ci_upper`, `statistic`. **Dependency**: T022.

- [ ] T027 [US3] [FR-007] Implement `code/04_analysis/error_taxonomy.py` to categorize failed pivots. **Inputs**: `data/derived/results.csv` and `data/derived/failure_cases.json` (from T011b). **Logic**: If no rule matches -> "Coverage Gap"; If rule matches but action != `ground_truth_resolution` (from T011b) -> "Distillation Error". **Dependency**: T022, T011b.

- [ ] T027b [US3] **Execute & Populate**: Run `error_taxonomy.py` against `data/derived/results.csv` and `data/derived/failure_cases.json` to generate `data/derived/error_taxonomy_results.json`. **Output Schema**: `{ "coverage_gap_count": <int>, "distillation_error_count": <int>, "total_failures": <int>, "breakdown_by_type": { "<type>": { "coverage_gap": <int>, "distillation_error": <int> } } }`. **Depends on T022, T011b**.

- [ ] T028 [US3] **Ground Truth Arbitration**: Ensure `error_taxonomy.py` uses `ground_truth_resolution` from `failure_cases.json` to arbitrate the categorization of failures (Coverage Gap vs Distillation Error). **Dependency**: T011b.

- [ ] T029d [US3] [SC-002] **Execute Stratified Rates**: Run `calculate_stratified_rates.py` to generate `data/derived/stratified_success_rates.csv`. **Dependency**: T029b.

- [ ] T029c [US3] [SC-001] **Execute Time Diff**: Run `time_diff_test.py` to generate `data/derived/time_diff_results.json`. **Dependency**: T029a.

- [ ] T030a [US3] [SC-005] **Resource Logging (Local)**: Implement `code/04_analysis/aggregate_local_resources.py` to collect local resource logs (from T013, T017) and output `data/derived/local_resource_log.json`. **Output Schema**: `{ "task_id": <string>, "peak_memory_mb": <float>, "cpu_time_seconds": <float> }`. **Dependency**: T013, T017.

- [ ] T030b [US3] [SC-005] **Resource Logging (Local Aggregate Only)**: Implement `code/04_analysis/aggregate_external_resources.py` to collect local resource logs (from T013, T017) and produce `data/derived/resource_summary.json` containing total compute time and peak memory for the **CI-constrained tasks only**. **Constraint**: This task explicitly EXCLUDES external baseline metrics (T021c) to ensure the metric reflects "deployment feasibility on consumer hardware" (SC-005) without conflating environments. **Dependency**: T013, T017. **Output Schema**: `{ "total_compute_time_seconds": <float>, "peak_memory_mb": <float> }`.

- [ ] T029e [US3] [SC-003] [SC-004] [SC-005] **Create Report Template**: Implement `code/04_analysis/templates/report_template.md.j2`. **Template Path**: `code/04_analysis/templates/report_template.md.j2`. **Variables**: `regression_results`, `time_diff_results`, `stratified_success_rates`, `error_taxonomy_results`, `resource_summary`. **Structure**: Executive Summary, Methodology, Time-to-Pivot Analysis (SC-001), Success Rate Analysis (SC-002), Error Taxonomy (SC-004), Statistical Significance (SC-003 - MUST include `narrative_conclusion` from T026b), and Conclusion. **Dependency**: None (creates artifact).

- [ ] T029f [US3] [Report] **Generate Final Report**: Execute `code/04_analysis/generate_report.py` with the template from T029e and data from T026b, T029c, T029d, T027b, T030b to produce `data/derived/final_report.md`. **Dependency**: T029e, T026b, T029c, T029d, T027b, T030b.

- [ ] T031 [P] Write `code/tests/test_rule_engine.py` to validate rule matching logic. **Test Cases**: `test_syntactic_error_match` (verify regex match), `test_unstructured_fallback` (verify default behavior), `test_edge_case_empty_log` (verify handling of empty logs). **Input Data**: Use sample logs from `data/derived/failure_cases.json`.

- [ ] T032 [P] Write `code/tests/test_pipeline.py` for integration tests of the full data flow

- [ ] T033 [P] Update `quickstart.md` with instructions for running the pipeline and external baseline: Add a section "Running the External Baseline" with steps: 1. Ensure baseline agent is installed on target machine. 2. Run `python code/03_execution/run_baseline_external.py --manifest data/derived/experiment_manifest.csv`. 3. Wait for `data/derived/baseline_results.json`. **Dependency**: T021.

- [ ] T034 [P] Run `code/utils/update_state.py` to finalize `state.yaml` with all artifact hashes: Verify `state.yaml` contains updated hashes for all `data/derived/` artifacts and the `updated_at` timestamp is current. **Dependency**: T029f.

- [ ] T035a [P] Run `ruff --check` on `code/` and verify exit code 0 (linting pass): If check fails, generate `lint_report.txt` with the error output and exit with code 1.

- [ ] T035b [P] Run `black --check` on `code/` and verify exit code 0 (formatting pass): If check fails, generate `lint_report.txt` with the error output and exit with code 1.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T007 [P] **Update State**: Create `code/utils/update_state.py` to calculate SHA-256 hashes of all artifacts in `data/derived/` and `results/`. **File Filter**: Recursively traverse directories, filtering for files with extensions `.json`, `.csv`, `.yaml`. **Hash Calculation**: Include the full relative path in the hash calculation to ensure reproducibility. **Execution**: Run this task after each major phase (US1, US2, US3) and in this final phase. Update `state/projects/PROJ-865-llmxive-follow-up-extending-autoresearch.yaml` with the new hashes and `updated_at` timestamp.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 0 (Constitutional Gates)**: No dependencies - starts immediately. Blocks Phase 1.
- **Setup (Phase 1)**: Depends on Phase 0 completion.
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

1. Complete Phase 0: Constitutional Gates
2. Complete Phase 1: Setup
3. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
4. Complete Phase 3: User Story 1
5. **STOP and VALIDATE**: Test User Story 1 independently
6. Deploy/demo if ready

### Incremental Delivery

1. Complete Phase 0 + Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Phase 0 + Setup + Foundational together
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