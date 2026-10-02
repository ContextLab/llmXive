# Tasks: Embodied Curriculum Learning: Physical Simulation for Abstract Concept Teaching

**Input**: Design documents from `/specs/[###-feature]/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this story belongs to (e., US1, US2, US3)
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

- [X] T001a [P] Create code directories: `code/src/`, `code/tests/` at repository root (Constitution Principle III, FR-001)
- [X] T001b [P] Create data directories: `data/raw/`, `data/processed/`, `data/synthetic/`, `data/derivation_logs/` (Constitution Principle III, FR-001)
- [X] T001c [P] Create state directories: `state/projects/PROJ-560-embodied-curriculum-learning-physical-si/` (Constitution Principle III, FR-001)
- [X] T002a [P] Create `code/requirements.in` listing `pandas`, `scipy`, `statsmodels`, `numpy`, `pyyaml`, `pytest`, `black`, `ruff` as dependencies, one per line, no comments.
- [X] T002b [P] Resolve and pin exact versions for dependencies in `code/requirements.txt` using `pip-compile requirements.in` (or manual lookup) ensuring reproducibility.
- [X] T003 [P] Configure linting (`ruff`) and formatting (`black`) tools in `code/` (create `ruff.toml` and `pyproject.toml` configurations).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Create `code/src/config.py` and define the constant `INFERENTIAL_FRAMING_STRING = "Findings are associational; no causal inference is drawn due to observational nature of data."` (FR-003, SC-002).
- [X] T005 [P] Implement `code/src/__init__.py` and basic logging configuration in `code/src/logging_config.py`
- [X] T006 [P] Create `DatasetRecord` dataclass in `code/src/models.py` with `pre_test_score`, `post_test_score`, `instruction_type`, `covariates` (static data structure only)
- [X] T007 [P] Create `AnalysisResult` and `SensitivitySweep` dataclasses in `code/src/models.py`
- [X] T008 [P] Implement CLI argument parser in `code/src/cli.py` supporting `--mode`, `--input`, `--sweep_thresholds`, `--seed`, `--n` (for synthetic data size), `--mean_diff_embodied`, and `--mean_diff_static`. **Do NOT** include `--concept_definition` as it is out of scope per Spec and Plan; ground truths are configured via `--mean_diff` flags instead, and the synthetic generator maps these to abstract concepts internally. **Dependency**: None. <!-- FAILED: unspecified -->
- [X] T009 [P] Setup deterministic random seed management in `code/src/utils.py` for reproducibility (numpy, python)
- [X] T014a [P] Implement parameter parsing in `code/src/synthetic_gen.py` to accept `n`, `seed`, `mean_diff_embodied`, `mean_diff_static` via CLI or config. **Dependency**: T008 (CLI Args).
- [X] T014b [US1] Implement `SyntheticDataGenerator` class in `code/src/synthetic_gen.py` to generate datasets with configurable mean differences, sample sizes, and ground truths for statistical validation (FR-009). **Must include**:
 1. Generate a CSV file at `data/synthetic/generated_data.csv` with columns `pre_test_score`, `post_test_score`, `instruction_type`.
 2. Ensure generation is deterministic based on `seed`.
 3. **MUST generate `mapping_log.json` for ALL synthetic data generation runs**, regardless of whether physics parameters are explicitly provided by the user. If physics parameters are not provided, the generator MUST use default/placeholder physics parameters to populate the log, ensuring Constitution Principle VI (Simulation-Pedagogy Alignment) is satisfied even in fallback scenarios. This log maps the synthetic physics parameters to the abstract concept variables. **Do NOT** generate `mapping_log` for `--mode=secondary_analysis`.
 4. The `mapping_log` must contain the derivation log linking physical variables to abstract concept variables as required by the Constitution for synthetic mode.
 **Dependency**: T006 (Base Schema), T014a (Parameter Parsing). **Note**: This task is NOT parallel with T006; T006 must be complete before T014b starts.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Processing and Synthetic Data Generation (Priority: P1) 🎯 MVP

**Goal**: Provide a deterministic, CPU-tractable environment that loads public data or generates synthetic data for validation.

**Independent Test**: The system can be tested by either (a) loading a sample of the OpenML math reasoning dataset and outputting a processed CSV, or (b) invoking the synthetic data generator to create a labeled dataset, all without requiring external network calls or GPU resources.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Unit test for `DatasetRecord` validation in `code/tests/test_models.py`
- [X] T011 [P] [US1] Unit test for `SyntheticDataGenerator` output schema in `code/tests/test_synthetic_gen.py` <!-- FAILED: unspecified -->
- [X] T041 [US1] Unit test for `handle_fallback_logic` error path in `code/tests/test_data_loader.py`. **Must verify**:
 1. When `instruction_type` is missing and synthetic generation fails, The system exits with a non-zero error code.
 2. The error message printed to stderr is exactly: `Primary research question cannot be answered: missing instruction_type and synthetic generation failed`.
 3. The error is logged to `data/derivation_logs/skipped_records.log` in JSONL format with `reason: "synthetic_gen_failed"`.
 4. **Schema Verification**: The test MUST verify that the log entry contains the exact keys `timestamp`, `reason`, and `dataset_source` in JSONL format. The log entry must be a single line of JSON.
 5. **Integration Requirement**: The test MUST mock `SyntheticDataGenerator.generate` to simulate a failure (raise an `Exception`) and verify that `data_loader.handle_fallback_logic` correctly propagates this failure to the CLI exit code 1 and logs the error as specified.
 **Dependency**: T012c (Implementation of fallback logic). **Note**: This test is listed here to follow the "Test First" methodology, meaning it should be written and failing before T012c is implemented.

### Implementation for User Story 1

- [X] T012a [US1] Implement `load_public_dataset` in `code/src/data_loader.py` to read CSV/JSON, validate required columns (`pre_test_score`, `post_test_score`, `instruction_type`). **Logic**:
 1. Read input file.
 2. Validate presence of required columns.
 3. Return dataset if valid.
 **Output**: Dataset object.
 **Dependency**: T006 (DatasetRecord), T008 (CLI Args).
- [X] T012c [US1] Implement `handle_fallback_logic` in `code/src/data_loader.py` to:
 1. If `instruction_type` column is missing in public data, **load and validate** the file produced by T014b (`data/synthetic/generated_data.csv`) before proceeding.
 2. **MUST verify** that the loaded synthetic data actually contains the `instruction_type` column before proceeding to the gain score calculation. If the column is missing, the system MUST exit with code 1 and log a clear error message.
 3. If generation fails, **MUST** exit with code 1 and **MUST** print to stderr: `Primary research question cannot be answered: missing instruction_type and synthetic generation failed`.
 4. Log error to `data/derivation_logs/skipped_records.log` in JSONL format with exact schema: `{"timestamp": "<ISO8601>", "reason": "synthetic_gen_failed", "dataset_source": "<url_or_path>"}` (FR-008).
 **Output**: `data/processed/validated_fallback.csv` (if successful) or exit code 1.
 **Dependency**: T014b (Phase 2) must be implemented and complete before T012c starts. **Logic Branch**: Conditional on T012a validation failure (missing `instruction_type`). **Note**: T012c explicitly consumes the output artifact of T014b.
- [X] T013 [US1] Implement `calculate_gain_scores` in `code/src/data_loader.py` to compute `post - pre`, excluding rows with missing values and logging them to `data/derivation_logs/skipped_records.log` (FR-001).
- [X] T015 [US1] Implement CLI entry point logic in `code/src/cli.py` to switch between `--mode=secondary_analysis` and `--mode=synthetic` and write output to `data/processed/` or `data/synthetic/` (depends on T008, T014, T012a, T012c). **Dependency**: Phase 2 (Foundational) completion.
- [X] T017a [P] [US1] Configure logging handler in `code/src/logging_config.py` to write specifically to `data/derivation_logs/skipped_records.log` in JSONL format. **Dependency**: T005 (logging configuration).
- [X] T017b [P] [US1] Add log statements in `code/src/data_loader.py` for data loading events and missing pre-test scores, ensuring they write to the configured handler from T017a. **Dependency**: T017a.

---

## Phase 4: User Story 2 - Statistical Comparison and Inference (Priority: P2)

**Goal**: Perform independent samples t-tests as the primary analysis method (per Spec FR-002) and ANCOVA as a secondary descriptive method (per Plan Complexity Tracking), framing results as associational.

**Independent Test**: The system can be tested by running the analysis script on a synthetic dataset where the "embodied" group has a known mean gain and the "static" group has a known mean gain., verifying that the output reports a t-statistic and p-value consistent with these inputs.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Unit test for Welch's t-test logic in `code/tests/test_stats_engine.py`
- [X] T019 [P] [US2] Unit test for Bonferroni correction logic in `code/tests/test_stats_engine.py`

### Implementation for User Story 2

- [X] T020a [US2] Implement `run_t_test` in `code/src/stats_engine.py` to perform Student's or Welch's t-test on gain scores based on Levene's test result (FR-002). **This is the PRIMARY analysis method** per Spec FR-002. **Note**: ANCOVA is the secondary descriptive method (see T020b).
- [X] T020b [US2] [OPTIONAL] Implement `run_ancova` in `code/src/stats_engine.py` to perform Analysis of Covariance (ANCOVA) adjusting for pre-test scores. **This is the SECONDARY descriptive method** per Plan Complexity Tracking to address regression to the mean in observational data. Output must include adjusted means, F-statistic, p-value, and effect size. **NOTE**: This is NOT a required success criterion for FR-002; FR-002 mandates only t-tests. ANCOVA is provided for robustness in observational data but is optional.
- [X] T021a [US2] Implement `calculate_effect_size` (Cohen's d) and `confidence_interval` in `code/src/stats_engine.py` (FR-002).
- [X] T021b [US2] Implement `detect_multiple_concepts` in `code/src/stats_engine.py` to scan the input dataset for columns representing distinct mathematical concepts (e.g., columns containing 'concept' or 'topic' in name, or distinct groups). **Logic**:
 1. Identify columns that represent distinct concepts to be tested.
 2. Count the number of concepts (N_concepts).
 3. Return a dictionary: `{'n_concepts': int, 'concept_ids': list[str]}`.
 **Output**: Dictionary with `n_concepts` (int) and `concept_ids` (list of strings).
 **Dependency**: T012a (Data Loading). **Purpose**: Enables Bonferroni correction for multiple comparisons.
- [X] T022 [US2] Implement `apply_bonferroni_correction` in `code/src/stats_engine.py` to adjust alpha based on N_concepts (from T021b). **Logic**: α_adj = 0.05 / N_concepts. **Dependency**: T021b.
- [X] T023 [US2] Implement `frame_inference` in `code/src/stats_engine.py` to explicitly label all findings as "associational" and include methodological caveats (FR-003). **MUST retrieve the exact string from `code/src/config.py` constant `INFERENTIAL_FRAMING_STRING`** to ensure consistency. **Dependency**: T004 (Config Creation), T020a (Primary Test).
- [X] T024 [US2] Implement `check_collinearity` in `code/src/stats_engine.py` to detect |r| > 0.8 between predictors and report diagnostics (FR-006). **Output Schema**: `{'high_correlation_pairs': list[dict], 'warning': str}`.
- [X] T025 [US2] Implement `calculate_power` in `code/src/stats_engine.py` to compute achieved power and flag "underpowered" results if < 0.80 (FR-007). **Output Schema**: `{'achieved_power': float, 'is_underpowered': bool}`.
- [X] T026a [US2] Implement `aggregate_stats_results` in `code/src/stats_engine.py` to combine t-test (primary), ANCOVA (secondary), effect sizes, power, and collinearity diagnostics into a single dictionary structure. **Output**: Dictionary. **Dependency**: T020a, T020b, T021a, T022, T023, T024, T025.
- [ ] T026b [US2] Implement `write_partial_results` in `code/src/stats_engine.py` to write the aggregated dictionary from T026a to `data/processed/results_us2.json`. **Schema Keys** (in order):
 - `t_statistic` (PRIMARY: from T020a)
 - `p_value` (PRIMARY: from T020a)
 - `corrected_p_value` (Bonferroni-adjusted, required when N_concepts > 1)
 - `effect_size_cohen_d`
 - `confidence_interval`
 - `inference_framing` (Must contain the exact string from FR-003: "Findings are associational; no causal inference is drawn due to observational nature of data." - **MUST retrieve this exact string from `code/src/config.py` constant `INFERENTIAL_FRAMING_STRING`**).
 - `ancova_results` (SECONDARY: F-statistic, p-value, adjusted_means)
 - `power_analysis` (**MANDATORY**: MUST include the full object produced by T025. Schema: `{'achieved_power': float, 'is_underpowered': bool}`). This field is required by FR-007 and must be written to `results_us2.json`.
 - `collinearity_diagnostics` (**MANDATORY**: MUST include the full object produced by T024. Schema: `{'high_correlation_pairs': list[dict], 'warning': str}`). This field is required by FR-006 and must be written to `results_us2.json`.
 **Dependency**: T023, T024, T025, T026a, T021b, T022, T004. **Purpose**: Enables independent testing of US2 without requiring US3. **Note**: This task MUST implement the file writing logic and create `results_us2.json`, ensuring `t_statistic` and `p_value` are listed first to reflect the methodological hierarchy mandated by FR-002.
 **Note**: This task MUST explicitly mandate writing `power_analysis` and `collinearity_diagnostics` objects to the JSON file. The implementer must ensure that the dictionaries returned by `calculate_power` (T025) and `check_collinearity` (T024) are directly assigned to these keys in the output JSON.
 **Note**: This task MUST explicitly mandate writing `power_analysis` and `collinearity_diagnostics` objects to the JSON file.

---

## Phase 5: User Story 3 - Sensitivity Analysis for Thresholds (Priority: P3)

**Goal**: Execute a sensitivity analysis sweeping inclusion thresholds to demonstrate robustness of the headline effect size.

**Independent Test**: The system can be tested by running the analysis with the `--sweep` flag on a dataset with N ≥ 30 and verifying that the output contains a table of effect sizes corresponding to each threshold value.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T027 [P] [US3] Unit test for sensitivity sweep logic in `code/tests/test_sensitivity.py`

### Implementation for User Story 3

- [X] T028 [US3] Implement `run_sensitivity_sweep` in `code/src/sensitivity.py` to: (1) check total N; (2) if N < 30, return early with `insufficient_data: true` flag and the exact string 'insufficient data for robustness check' in the results; (3) if N >= 30, read thresholds from the `--sweep_thresholds` CLI argument (defined in T008), **defaulting strictly to the hardcoded set {0.01, 0.05, 0.10}** if the argument is not provided (per FR-005), calculate effect sizes, aggregate results into `SensitivitySweep` objects, and append to the main JSON report (FR-005). **Output Schema**: Each entry MUST include `threshold_value`, `n_participants_retained`, `effect_size_cohen_d`, and `robustness_flag`. **Dependency**: T008 (CLI Args), T028 must complete before T030.
- [ ] T030 [US3] Implement `check_robustness_warning` in `code/src/sensitivity.py` to flag `robustness_warning: true` in the output if the effect size drops below a meaningful threshold (per SC-003) at any point in the sweep. **MUST pass the calculated `robustness_warning` flag to the final aggregator (T026c) and include it in the `results.json` schema**. **Dependency**: Must consume `SensitivitySweep` objects produced by T028. **Note**: This task explicitly mandates passing the `robustness_warning` flag to T026c.
- [X] T026c [US3] **MOVED TO PHASE 6**: See Phase 6 for implementation details. This task is now the final integration step.

---

## Phase 6: Integration (Cross-Phase Dependency)

**Purpose**: Final integration of US2 and US3 results.

- [ ] T026c [Integration] Implement `finalize_results` in `code/src/stats_engine.py` to merge `results_us2.json` (T026b) with sensitivity analysis results (T028, T030) into the final `data/processed/results.json`. **Schema Keys**:
 - `t_statistic` (PRIMARY)
 - `p_value` (PRIMARY)
 - `corrected_p_value` (Bonferroni-adjusted)
 - `effect_size_cohen_d`
 - `confidence_interval`
 - `inference_framing` (Must contain exact string "associational" from T023, plus full explanatory statement)
 - `ancova_results` (SECONDARY)
 - `sensitivity_analysis` (Array of objects: `{"threshold_value": float, "n_participants_retained": int, "effect_size_cohen_d": float, "robustness_flag": bool}`)
 - `robustness_warning` (boolean, MUST be populated from T030)
 **Dependency**: T023, T026a, T026b, T028, T030. **Note**: This task is the integration step and MUST wait for T026b (US2) and T028/T030 (US3) to be complete. It cannot run in parallel with them. **Note**: This task MUST implement the file writing logic and create `results.json`.
 **Dependency**: T030 is explicitly listed as a dependency to ensure data flow.

---

## Phase 7: Scope Boundary & Documentation

**Purpose**: Address scope limitations and constitutional requirements without modifying core statistical logic.

**Note on Scope**: This phase addresses documentation and cleanup. Philosophical framing (training vs. teaching, abstract concept definitions) is **explicitly out of scope** for this MVP as per Spec Assumptions and Risks.

### Implementation for Scope Clarification

- [X] T037a [P] Update `code/../quickstart.md` to include an example of running with synthetic data (the fallback scenario) and the "Data Sources" section to explain the `instruction_type` requirement and fallback behavior. The documentation must clarify that if public data lacks `instruction_type`, synthetic data is used for pipeline validation only.
- [X] T037b [P] Update `docs/` (e.g., `docs/limitations.md`) to explain the `instruction_type` requirement and fallback behavior, referencing Spec Assumptions and Risks.
- [X] T038 [P] Code cleanup and refactoring to ensure type hinting and docstrings are complete. Run `ruff check --select=ANN code/src/` and ensure all files pass (exit code 0). Generate a report at `code/tests/ruff_report.txt` if any warnings exist, or record success. **Dependency**: T003 (ruff config).
- [X] T039 [P] Performance verification: Run `python -m timeit -n 1 -s 'import sys; sys.path.insert(0, "code/src")' 'from cli import main; main()'` with `--mode=synthetic --n=10000` on a **GitHub Actions free-tier runner (2-core, 7GB RAM)**. **Constraint Enforcement**: The CI step MUST verify the runner has a sufficient number of CPU cores (e.g., by checking `nproc` output) **ensuring >= 2 cores** before executing the benchmark. **Verify**: Exit time < 600s (10 minutes) **wall-clock time** (SC-001).
 **Pass/Fail Criteria**:
 - Task **PASSES** if duration <= 600s AND `data/processed/perf_log.json` is written.
 - Task **FAILS** if duration > 600s OR `perf_log.json` is missing. If duration > 600s, write a warning to the log and mark task as FAILED in the CI step.
 Write the timing result to `data/processed/perf_log.json` with exact schema: `{ "timestamp": "<ISO8601>", "n_records": int, "duration_seconds": float, "command_executed": "<string>" }`.
 **Note**: The `--n=10000` parameter is mandatory for this benchmark to match the Plan's Performance Goals. The test MUST be run on a multi-core CPU environment. to satisfy SC-001.
- [ ] T040a [P] Add unit test `test_t_test_underpowered` in `code/tests/test_stats_engine.py` for N < 30 case.
- [X] T040b [P] Add unit test `test_load_missing_columns` in `code/tests/test_data_loader.py` for missing column handling.
- [ ] T040c [P] Add unit test `test_collinearity_detection` in `code/tests/test_stats_engine.py` for |r| > 0.8 case.
- [X] T042 [P] Run `quickstart.md` validation to ensure end-to-end flow works. The test MUST pass using either a valid public dataset OR the synthetic data generator (if public data lacks `instruction_type`), as per the spec's Risk section. Execute: `pytest code/tests/test_e2e.py::test_quickstart_flow`.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Sensitivity Analysis (Phase 5)**: Depends on Phase 4 (US2) completion to aggregate stats.
- **Documentation (Phase 6)**: Can run in parallel with user story implementation as they are documentation focused, but T037b may depend on T023 completion for accurate framing.
- **Integration (Phase 6)**: Depends on Phase 4 (US2) and Phase 5 (Phase 5) completion.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories (T014 is now in Phase 2)
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 for data input
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1/US2 for data and base stats

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2, except T014b which depends on T006/T014a)
- Once Foundational phase completes, all user stories can start in parallel (if staffed)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members
- Phase 7 (Documentation) tasks can run in parallel with user story implementation as they are documentation focused.
- **Note**: T026c (Phase 6) is NOT parallel; it is a blocking dependency for US3 completion. This phase serves as the finalization step for the entire pipeline.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for DatasetRecord validation in code/tests/test_models.py"
Task: "Unit test for SyntheticDataGenerator output schema in code/tests/test_synthetic_gen.py"
Task: "Unit test for handle_fallback_logic error path in code/tests/test_data_loader.py"

# Launch all models for User Story 1 together:
Task: "Implement load_public_dataset in code/src/data_loader.py" (Note: T014 must be done first, but T014 is in Phase 2)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories, includes T014)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Add Phase 7 Documentation → Address philosophical boundaries without altering core logic
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Data/Synthetic)
 - Developer B: User Story 2 (Stats/Inference)
 - Developer C: User Story 3 (Sensitivity)
 - Developer D: Documentation (Phase 7)
3. Stories complete and integrate independently.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical Constraint**: All statistical tasks must run on CPU-only CI with a minimal core count and constrained memory allocation. No GPU, no 8-bit quantization, no large model training.
- **Data Integrity**: Never fabricate input data. Use real public datasets or synthetic data *only* for pipeline validation as per FR-009.
- **Constitution Principle VI**: The `mapping_log` is **REQUIRED** for synthetic mode to satisfy Simulation-Pedagogy Alignment. It is **NOT REQUIRED** for secondary analysis mode. T014b now correctly mandates `mapping_log` for synthetic mode only, using defaults if physics parameters are not provided.
- **FR-008 Compliance**: If `instruction_type` is missing in public data, the system MUST automatically invoke the Synthetic Data Generator. If generation fails, the system MUST exit with code 1 and log a clear error message: "Primary research question cannot be answered: missing instruction_type and synthetic generation failed".
- **Associational Framing**: All statistical findings MUST be framed as "associational" (FR-003). No causal claims (e.g., "teaching" vs "training") are permitted in the output without explicit qualification.
- **Scope Boundary**: Philosophical/pedagogical framing (training vs. teaching, abstract concept definitions) is **explicitly out of scope** for the statistical engine's core logic and output report, but MUST be documented in `docs/` as per Phase 7 (T037b) if needed, but not as a primary deliverable.
- **Plan Mismatch**: The plan.md Complexity Tracking table mentions ANCOVA. The Spec mandates t-tests. **This tasks.md satisfies BOTH**: t-tests are PRIMARY (per Spec FR-002) and ANCOVA is SECONDARY/OPTIONAL (per Plan Complexity Tracking).
- **Synthetic Mode Validity**: The `--mode=synthetic` is valid for pipeline validation. The system does not reject `pedagogical_mode` values; it generates data as requested. Documentation must reflect that the tool is a statistical validator, not a pedagogical simulator.
- **Removed Tasks**: Phase 8 (T050-T054) and associated tasks have been **removed** as they address philosophical framing explicitly marked as 'out of scope' in the Spec's Assumptions and Risks.
- **Rejected Tasks**: Tasks T002a, T016, T026 (old), and T038 (old) marked as "REJECTED" in input have been removed or updated (T026 split into T026a/T026b/T026c; T002a re-enabled; T037 split into T037a/T037b).
- **Schema Conformance**: T026b and T026c now use exact keys from Spec `SensitivitySweep` entity and US-3 acceptance criteria: `threshold_value`, `n_participants_retained`.
- **Performance Benchmark**: T039 explicitly mandates `--n=10000` to align with Plan Performance Goals. T039 also explicitly mandates a >=2-core CPU environment with verification.
- **US2 Independent Test**: T026b allows US2 to be tested independently by writing a partial report. T026c merges US3 results for the final report.
- **T046 Moved/Removed**: T046 (code metadata update) has been **removed** as it was part of the scope violation (mandating `mapping_log` with causal mechanism). The `mapping_log` requirement in T014b is strictly for synthetic mode alignment, not causal claims.
- **T014 Split**: T014 has been split into T014a (Parameter Parsing) and T014b (Generation) to improve executability.
- **T012c Dependency**: T012c is now a conditional branch of T012a, not a sequential dependency.
- **T026c Integration**: T026c is explicitly marked as the integration step that must wait for US2 and US3 completion. **Moved to Phase 6**.
- **T041 Added**: T041 has been added to verify the error handling path in T012c.
- **T028 CLI Fix**: T028 now reads thresholds from `--sweep_thresholds` CLI argument, **defaulting strictly to the hardcoded set {0.01, 0.05, 0.10}** to ensure compliance with FR-005.
- **T039 2-Core Fix**: T039 explicitly mandates a >=2-core CPU environment and verification step.
- **T014b Mapping Log Fix**: T014b now requires `mapping_log.json` for synthetic mode only, using defaults if physics parameters are not provided.
- **T026a-setup Removed**: T026a-setup has been merged into T026b (now T026a).
- **T026b Dependencies**: T026b now explicitly includes T024 and T025 as dependencies.
- **T026c Dependencies**: T026c now explicitly includes T030 as a dependency.
- **T026b Schema Order**: T026b now lists `t_statistic` and `p_value` first to reflect the methodological hierarchy mandated by FR-002.
- **T026b Diagnostics**: T026b now explicitly includes `power_analysis` and `collinearity_diagnostics` in the schema.
- **T026b Framing**: T026b now explicitly mandates the exact FR-003 compliant string for `inference_framing`, retrieved from `config.py` (T004).
- **T030 Robustness**: T030 now explicitly mandates passing the `robustness_warning` flag to T026c.
- **T028 Insufficient Data**: T028 now explicitly mandates the output of the `insufficient_data` flag and the exact string 'insufficient data for robustness check' when N < 30.
- **Phase 8 Removed**: Phase 8 (T050-T054) has been removed as these tasks address philosophical framing explicitly marked as 'out of scope' in the Spec's Assumptions and Risks.
- **T026a-setup Removed**: T026a-setup has been merged into T026b.
- **T026b Dependencies**: T026b now explicitly includes T024 and T025 as dependencies.
- **T026c Dependencies**: T026c now explicitly includes T030 as a dependency.
- **T026b Schema Order**: T026b now lists `t_statistic` and `p_value` first to reflect the methodological hierarchy mandated by FR-002.
- **T026b Diagnostics**: T026b now explicitly includes `power_analysis` and `collinearity_diagnostics` in the schema.
- **T026b Framing**: T026b now explicitly mandates the exact FR-003 compliant string for `inference_framing`, retrieved from `config.py` (T004).
- **T030 Robustness**: T030 now explicitly mandates passing the `robustness_warning` flag to T026c.
- **T028 Insufficient Data**: T028 now explicitly mandates the output of the `insufficient_data` flag and the exact string 'insufficient data for robustness check' when N < 30.
- **T004 Added**: T004 has been added to create `config.py` and define `INFERENTIAL_FRAMING_STRING` to resolve missing dependency for T023.
