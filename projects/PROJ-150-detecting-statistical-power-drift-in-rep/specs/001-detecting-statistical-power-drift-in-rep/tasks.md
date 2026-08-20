# Tasks: Detecting Statistical Power Drift in Replicated Studies

**Input**: Design documents from `/specs/001-detect-power-drift/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)
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

- [X] T001a [P] Create `projects/PROJ-150-detecting-statistical-power-drift-in-rep/` directory structure by running `mkdir -p data/raw data/derived code tests results state docs`
- [X] T001b [P] Initialize `.gitignore` for Python data projects (exclude data/raw, data/derived, __pycache__,.env)
- [X] T001c [P] Create `requirements.txt` with pinned versions: pandas, numpy, scipy, statsmodels, scikit-learn, matplotlib, seaborn, pyyaml, pytest, psutil

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 [P] Create `code/__init__.py` and establish package structure
- [X] T006 Implement `code/download.py` with real data fetch logic (no synthetic fallbacks) using `huggingface_hub` to fetch `osf/reproducibility_project` dataset, specifically the `data.csv` file. **Verification**: Include a step to verify the dataset metadata (title-token-overlap ≥ 0.7) matches the "OSF Reproducibility Project" source to ensure data integrity.
- [X] T007 Implement `code/validate_source.py` for URL reachability and title-token-overlap (≥ 0.7) validation
- [X] T008 [P] Create `code/update_state.py` to compute SHA-256 hashes and update project state file
- [X] T009 Setup `pytest` configuration and base test fixtures in `tests/conftest.py`
- [X] T036 [P] [US1] Implement `code/download.py` data loader. **Logic**: Attempt standard loading via `pandas.read_csv` or `datasets.load_dataset`. **Fallback**: If the file size exceeds a substantial threshold, automatically switch to `datasets.load_dataset(..., streaming=True)` to yield rows/chunks. **Verification**: Ensure the loader yields rows correctly and handles chunking if triggered. **Dependency**: T036 must complete before T011a. (FR-010, Plan Compute Constraints)
- [X] T037 [P] [US1] Implement `code/preprocess.py` to consume the loader from T036. **Logic**: Process rows to filter missing data and calculate power. **Dependency**: T037 depends on T036. (FR-010)

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Core Power Drift Analysis (Priority: P1) 🎯 MVP

**Goal**: Compute post-hoc power estimates and test for temporal decline using a Linear Mixed-Effects Model (LMM) with `power_residual` as the outcome, `year` as a fixed effect, and random intercepts for `field` AND `original_study_id`.

**Independent Test**: The system can be fully tested by running the power re-estimation and LMM scripts on a static subset of the OSF data, verifying that a slope coefficient and p-value is generated for the `year` predictor in the full model.

### Pre-Implementation Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Tasks marked [P] are file-level independent (can be written in parallel). However, per TDD practice, these tests MUST be written and verified to FAIL before the corresponding implementation tasks (T011a-T016) are implemented.

- [X] T010 [P] [US1] Unit test `tests/unit/test_power_calc.py::test_power_calc_handles_nan` for power calculation logic.
- [X] T011 [P] [US1] Integration test `tests/integration/test_lmm_pipeline.py::test_lmm_pipeline_full_run` for the full LMM pipeline.

### Implementation for User Story 1

- [X] T011a [US1] Implement `code/preprocess.py` to filter rows with missing `year`, `effect_size`, or `sample_size` (FR-008). **Logic**: If the data file is missing, raise a `DataFetchError`. If a row has missing values, skip the row and log a warning with the row index and reason. **Dependency**: T011a depends on T036 (data loader). **Verification**: Ensure `data/derived/cleaned_data.csv` exists and contains no NaN values in critical columns. Do NOT generate synthetic data.

- [X] T011b [US1] Implement `code/preprocess.py` to validate grouping variables (`field`, `original_study_id`) for variance and cardinality. **Logic**: Check that each grouping factor has > 1 unique level and non-zero variance in the target variable. If a factor has only 1 level (single study), flag it as "single_level" for logging purposes ONLY. **Handling**: This task DOES NOT influence model structure. The downstream model fitting (T012c) will handle zero-variance groups by fixing the random effect variance to a small epsilon (e.g., 1e-6) internally, regardless of this validation result. **Output**: Save `data/derived/grouping_validation.json` with status per factor (e.g., `{"field": "valid", "original_study_id": "single_level"}`). **Verification**: Ensure `data/derived/grouping_validation.json` exists, lists all factors with their validity status, and specifically marks factors with single studies as "single_level" for logging. (Edge Cases: Zero Variance) **Depends on T011a**.

- [X] T012a [US1] Implement `code/models.py` to fit a **Pilot OLS Model**: `power_est ~ effect_size + sample_size`. **Logic**: Use this pilot model to capture the deterministic relationship between power and its inputs. **Output**: Save the fitted pilot model object to `data/derived/pilot_ols_model.pkl`. **Verification**: Ensure `data/derived/pilot_ols_model.pkl` exists and is loadable. (Plan T011c Step 1 - Exploratory Only)

- [X] T012b [US1] Implement `code/models.py` to calculate `power_residual = power_est - predicted_power` from the Pilot OLS Model (T012a). **Logic**: This creates the residualized target variable for **visualization and exploratory checks only**. **Output**: Save `data/derived/residuals.csv` with columns `study_id`, `year`, `field`, `original_study_id`, `power_residual`. **Verification**: Ensure `data/derived/residuals.csv` exists and the mean of `power_residual` is approximately 0. (Plan T011c Step 2 - Visualization Prep) **Depends on T012a**.

- [X] T012c [US1] Implement `code/models.py` to execute the primary statistical workflow:
 1. **Primary Hypothesis Test**: Load `data/derived/residuals.csv`. Fit the **Full LMM**: `power_residual ~ year + (1|field) + (1|original_study_id)`.
 - **Constraint**: The model formula MUST include `(1|field) + (1|original_study_id)` unconditionally. **NO dynamic exclusion** of random effects is permitted. If T011b flags a "single_level" group, the model fitting MUST handle it by fixing the random effect variance (e.g., using `control` parameters with `start = 1e-6`) rather than excluding the term, to preserve the required model structure (Constitution Principle VII).
 2. **Extract Primary Metrics**: **The `slope_year` coefficient from the Full LMM is the primary drift metric.** Extract `slope_year`, `se_year`, `ci_lower`, `ci_upper` (Wald method) from the Full LMM's fixed effects.
 3. **Significance Validation**: Perform a Likelihood-Ratio Test (LRT) comparing the Full LMM against a Reduced LMM (`power_residual ~ (1|field) + (1|original_study_id)`). Extract `p_value_lrt`, `chi2_statistic`, `df_diff`. **Note**: The LRT validates the significance of the `year` term but is NOT the primary metric; the slope is.
 4. **Unified Output**: Save the full model summary, reduced model summary, LRT results, and the `year` slope/SE into a SINGLE file: `results/lmm_final_summary.json`. This file must contain keys: `slope_year`, `se_year`, `ci_lower`, `ci_upper`, `p_value_lrt`, `chi2_statistic`, `df_diff`.
 **Verification**:
 - Ensure `results/lmm_final_summary.json` contains valid floats for all keys, specifically `slope_year` derived from the **Full LMM on `power_residual`**.
 - Ensure the LRT p-value is correctly calculated and reported. (FR-002, FR-003, FR-009, Constitution Principle VII, SC-001) **Depends on T012b** (for residuals input).

- [X] T013 [US1] Implement `code/visualize.py` to generate a scatter plot of **residual power vs. year**.
 **Definition**: Residuals are `power_residual` from `data/derived/residuals.csv` (produced by T012b).
 **Input**: `data/derived/residuals.csv`.
 **Output**: Save plot to `results/power_drift_scatter.png`.
 **Verification**:
 - Ensure `results/power_drift_scatter.png` exists, has non-zero dimensions, and contains a regression line showing the drift trend. (FR-009) **Depends on T012c** (for model summary) and **T012b** (for residuals).

- [X] T014 [US1] Add error handling for missing data (skip row, log warning with row index and reason) and zero-variance fields (FR-008). Log format: `WARNING: Skipping row {index} due to {reason}`. Handle specific errors: `NaN` in `effect_size` or `sample_size`, and `ZeroDivisionError` in power calculation.

- [X] T015 [US1] Add logging for User Story 1 operations and data filtering steps.

**Checkpoint**: At this point, User Story 1 (Core Drift Analysis) should be fully functional and testable independently

---

## Phase 4: User Story 2 - Robustness via Permutation & Sensitivity (Priority: P2)
**Depends on T012c completion**

**Goal**: Validate the power drift results against non-parametric permutation tests and alpha threshold sensitivity analysis.

**Independent Test**: The system can be tested by running the permutation test (sufficient iterations to ensure convergence) and the sensitivity sweep on the the same dataset, verifying that the p-value distribution and trend stability are reported.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Unit test `tests/unit/test_permutation.py::test_permutation_logic_small_count` for permutation logic with small iteration count.
- [X] T019 [P] [US2] Integration test `tests/integration/test_sensitivity.py::test_sensitivity_analysis_sweep` for sensitivity analysis sweep.

### Implementation for User Story 2

- [X] T020 [US2] Implement `code/robustness.py` function for non-parametric permutation test: **shuffle `year` labels** (FR-004). **Target**: A large number of permutations. **Fallback**: If memory or time limits are exceeded, fallback to a minimum of **1,000** permutations. **Detection Mechanism**: Use `psutil` to monitor memory usage and `time` to track wall-clock duration. Trigger fallback if `time_elapsed > 300` seconds OR `psutil.Process().memory_info().rss > 6 * 1024**3` bytes. Terminate early if > 5 hours, flag as "approximate". **Input**: Drift coefficient (slope_year) from `results/lmm_final_summary.json` (produced by T012c) and `data/derived/cleaned_data.csv`. **Output**: Empirical p-value for the drift slope in `results/permutation_pvalue.json`. **Verification**: Ensure `results/permutation_pvalue.json` includes an `iterations_run` field (set to 10000 or 1000) and a `status` field (e.g., 'exact' or 'approximate'). **CRITICAL**: Verify that if `iterations_run` < 10000, the `status` field is explicitly set to "approximate". (FR-004) **Depends on T012c**.

- [X] T020b [US2] Implement `code/robustness.py` to load `results/lmm_final_summary.json` and `results/permutation_pvalue.json`, compare the parametric p-value with the empirical p-value, and generate `results/permutation_consistency.json`. **Verification**: Ensure `results/permutation_consistency.json` contains a `consistency_check` boolean and a `p_value_difference` float, confirming the results are consistent as required by SC-002. (SC-002, US-2 Acceptance Scenario 1) **Depends on T020**.

- [X] T021 [US2] Implement `code/robustness.py` function for sensitivity analysis sweeping alpha across a range of significance levels including conventional thresholds and report the resulting drift significance rates. **Input**: `results/lmm_final_summary.json` (produced by T012c). **Output**: `results/sensitivity_report.json`. **Verification**: Ensure `results/sensitivity_report.json` contains entries for a range of alpha values including and 0.1. Each entry must include `drift_significant` (boolean) and `p_value` (float). Additionally, ensure the report explicitly contains a `threshold_dependence_statement` string that concludes whether the drift is driven by a specific alpha choice or holds across the tested range (US-2 Acceptance Scenario 3). (FR-005, SC-003) **Depends on T012c**.

- [X] T022 [US2] Integrate permutation and sensitivity results into the final report generation in `code/main.py`

- [X] T023 [US2] Add logic to handle permutation convergence failures and flag results as "approximate" (Edge Case)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Cross-Field Aggregation & Drift Validation (Priority: P3)
**Depends on T012c completion**

**Goal**: Combine evidence across heterogeneous fields using adaptive weighting and validate drift via input permutation framework.

**Independent Test**: The system can be tested by executing the adaptively weighted statistic aggregation and the input permutation validation on the full dataset, verifying that a combined drift statistic is produced.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T024 [P] [US3] Unit test `tests/unit/test_meta_analysis.py::test_dersimonian_laird_weighting` for DerSimonian-Laird weighting logic.
- [X] T025 [P] [US3] Integration test `tests/integration/test_input_permutation.py::test_input_permutation_framework` for input permutation validation.

### Implementation for User Story 3

- [X] T026a [US3] Implement `code/robustness.py` to stratify the cleaned data by `field`, fit a separate LMM for each field using `power_residual ~ year + (1|field) + (1|original_study_id)` to extract the `year` slope and standard error. **Note**: This uses the residualized power calculated in T012b (`power_residual` from `data/derived/residuals.csv`) to ensure we are aggregating **residual power drift estimates** as required by FR-006. **Input**: `data/derived/residuals.csv`. **Output**: Save `data/derived/field_slopes.csv` with columns: `field`, `slope_year`, `se_slope`, `n_studies`. **Verification**: Ensure the file contains one row per field and that slopes are derived from `power_residual` (not raw power). (FR-006, US-3 Acceptance Scenario 1) **Depends on T012b**.

- [X] T026 [US3] Implement `code/robustness.py` function for inverse-variance weighting with heterogeneity adjustment (DerSimonian-Laird) to combine **residual power drift estimates** (adjusted slopes) across fields. **Algorithm**: Calculate heterogeneity (Q-statistic, tau-squared) and apply inverse-variance weighting to the `slope_year` and `se_slope` from `data/derived/field_slopes.csv` (produced by T026a). **Input**: `data/derived/field_slopes.csv`. **Output**: Aggregated drift estimate and confidence interval in `results/aggregated_drift.json`. **Comparison**: Generate `results/comparison_aggregated_vs_lmm.json` comparing the aggregated drift estimate against the primary mixed-model slope (from `results/lmm_final_summary.json` produced by T012c). **Verification**: Ensure the file contains both values and the consistency check (keys: `consistency_score` float, `method` string). (FR-006, US-3 Acceptance Scenario 3, SC-004) **Depends on T026a**.

- [X] T027 [US3] Implement `code/robustness.py` function for input permutation framework: **shuffle `effect_size` and `sample_size` while holding `year` constant** (FR-007). **Target**: A large number of permutations. **Fallback**: A sufficient number of permutations if resource limits are exceeded (use same detection mechanism as T020). **Algorithm**: For each iteration, randomly shuffle the `effect_size` and `sample_size` columns in `data/derived/cleaned_data.csv` while keeping the `year` column unchanged. Re-use the `fit_lmm` function from `code/models.py` to refit the model on the permuted data to generate a null distribution of slopes. **Output**:
 1. Generate `results/null_distribution_implied_power.csv` with columns: `simulated_drift`, `count`.
 2. **Generate `results/input_permutation_pvalue.json`**: This JSON must contain `observed_slope` (from T012c), `p_value` (empirical p-value derived from comparing observed slope to the null distribution), and `methodology` (string describing the permutation process).
 **Verification**: Ensure `results/input_permutation_pvalue.json` exists and contains the required keys. Ensure `results/null_distribution_implied_power.csv` contains a sufficient number of rows (with a fallback count) to support robust estimation. **CRITICAL**: Verify that the `year` column in the input data was held constant during the permutation process by including a metadata field `methodology: input_permutation_year_fixed` in the output JSON. (FR-007, US-3 Acceptance Scenario 2) **Depends on T012c** and **code/models.py::fit_lmm**.

- [X] T028 [US3] Update `code/visualize.py` to plot the null distribution of the input-permutation drift and compare observed slope (US-3)

- [X] T029 [US3] Integrate cross-field aggregation and input permutation results into the final report JSON (US-3)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Finalization, versioning, and pipeline orchestration

- [X] T030 [P] Implement `code/main.py` pipeline orchestrator to sequence download, validation, LMM fitting, robustness checks, and reporting

- [X] T031 Run `code/update_state.py` to compute SHA-256 hashes for all `data/derived/` and `results/` files (Phase 6)

- [X] T032 Verify that the `current_stage` is updated to `implemented` by checking `state/projects/PROJ-150-detecting-statistical-power-drift-in-rep/state.yaml` for `current_stage: implemented`. **Verification**: Run `update_state.py` manually in the test environment and confirm it successfully modifies the `current_stage` key in the state file. **Schema Requirement**: The `state.yaml` update MUST include an `artifact_hashes` map containing SHA-256 hashes for every file in `data/derived/` and `results/`. The keys must be the **relative file paths from the project root** (e.g., `data/derived/cleaned_data.csv`). (FR-010, Constitution Principle V)

- [ ] T033a [P] Update `README.md` in project root with pipeline overview and usage instructions.
- [X] T033b [P] Create `docs/methodology.md` documenting the LMM methodology, residualization process, and aggregation logic.
- [ ] T034 [P] Run full pipeline on a static subset to verify end-to-end execution within **6-hour** CPU limit (FR-010). **Verification**: Check for existence of `results/timing_report.json`.
- [ ] T034a [P] Implement `code/timing.py` to instrument pipeline execution and generate `results/timing_report.json` with start/end times and total duration.
- [X] T035a [P] Run linter (ruff/flake8) on `code/` and fix all warnings (Success: zero warnings)
- [X] T035b [P] Run formatter (black) on `code/` and verify no changes are needed (Success: no diff)
- [X] T038 [P] [US1] Implement `code/download.py` "No Synthetic Fallback" guard. **Logic**: Raise `DataFetchError` if the primary dataset source is unreachable (network error, 404). **Exception**: If the dataset fetches successfully but is missing specific columns (variables) required for analysis, log a warning and proceed with the available data (per Spec Assumptions). This does NOT apply to missing *rows* (handled by T011a). **Verification**: Ensure the pipeline fails only on source unreachability, not on partial column availability. (Constitution Principle III, Spec Assumptions)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Depends on T012c completion (slope extraction)
- **User Story 3 (P3)**: Depends on T012c completion (slope extraction) and T026a (field slopes)

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

### Specific Task Dependencies

- **T011a** must complete before **T011b** (cleaning before grouping validation).
- **T011b** must complete before **T012a** (grouping validation before model fitting).
- **T012a** must complete before **T012b** (Pilot OLS before residual calculation).
- **T012b** must complete before **T012c** (Residuals produced before LMM fitting).
- **T012c** must complete before **T013** (residual generation and model fitting before visualization).
- **T012c** must complete before **T020** (slope extraction before permutation validation).
- **T020** must complete before **T020b** (permutation result before consistency check).
- **T012b** must complete before **T026a** (Residuals produced before field-specific modeling).
- **T026a** must complete before **T026** (field slopes before aggregation).
- **T012c** must complete before **T027** (slope extraction before input permutation validation).
- **T036** must complete before **T011a** (Streaming generator before preprocessing).

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (T011a, T011b, T012a, T012b, T012c, T013)
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
- Avoid: vague tasks, cross-story dependencies that break independence
- **Data Integrity**: `code/download.py` MUST fail loudly on real data fetch failure; no synthetic fallbacks allowed. **Exception**: If the fetch succeeds but returns partial columns, proceed with available data (Spec Assumptions).
- **Methodology**: Tasks implement the Linear Mixed-Effects Model (LMM) as required by Spec FR-002, FR-003, and FR-009. The model includes random intercepts for `field` AND `original_study_id`, with **NO dynamic exclusion** of random effects. If variance is zero, the model must handle it via optimizer adjustments or fixed variance to preserve the required formula structure. The primary drift metric is the `slope_year` from the **Full Model** on `power_residual`.
- **Compute Feasibility**: All tasks are designed to run on CPU-only runners (multiple cores, 7GB RAM) within 6 hours. Permutation tests use vectorized `numpy` operations and chunked processing to fit memory constraints. Streaming logic (T036/T037) is implemented as a conditional fallback for large files, respecting the Spec's assumption that the dataset fits in RAM.
- **Revision Concern**: T033a, T033b, T034, and T034a added to ensure documentation of the LMM methodology is complete and the pipeline is verified end-to-end within the **6-hour** CPU limit as required by FR-010 and the Constitution.