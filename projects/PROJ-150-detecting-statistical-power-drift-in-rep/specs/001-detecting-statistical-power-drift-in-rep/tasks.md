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
- [X] T006 Implement `code/download.py` with real data fetch logic (no synthetic fallbacks) using `huggingface_hub` to fetch the `osf/reproducibility_project` dataset, specifically the `data.csv` file. **Logic**:
 1. Attempt to fetch using `datasets.load_dataset("osf/reproducibility_project", split="train", streaming=True)` if file size > 100MB, else `read_csv`.
 2. Verify dataset metadata by calculating **title-token-overlap** (cosine similarity of tokenized titles) between the fetched dataset title and "OSF Reproducibility Project"; require overlap ≥ 0.7.
 3. **CRITICAL**: If the dataset fetch fails (network error, 404), raise `DataFetchError`. Do NOT fall back to synthetic data.
 4. **Verification**: Ensure the loader yields rows correctly and handles chunking if triggered. **Output**: A reusable data loader function in `code/download.py`. **Dependency**: T006 must complete before T011a. (FR-010, Plan Compute Constraints, Constitution Principle II)
- [X] T007 Implement `code/validate_source.py` for URL reachability and title-token-overlap (≥ 0.7) validation
- [X] T008 [P] Create `code/update_state.py` to compute SHA-256 hashes and update project state file
- [X] T009 Setup `pytest` configuration and base test fixtures in `tests/conftest.py`

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

- [ ] T011a [US1] **Implement Preprocessing & Power Calculation**.
  - **CRITICAL BLOCKER**: This task MUST be implemented to generate `data/derived/cleaned_data.csv`. All downstream tasks (T011b, T011c, T013, T020, T025, T027) depend on this artifact.
  - **Logic**:
    1. Load raw data from `data/raw/data.csv` (produced by T006).
    2. **Missing File**: If `data/raw/data.csv` is missing, raise `DataFetchError`.
    3. **Missing Rows (FR-008)**: Filter out rows where `year`, `effect_size`, or `sample_size` are missing/NaN. **DO NOT** generate synthetic data. Log a warning for each skipped row: `WARNING: Skipping row {index} due to missing {column}`.
    4. **Power Calculation (FR-001)**: Calculate `power_estimate` for remaining rows using Cohen's *d*, sample size, and α=0.05.
    5. **Output**: Save `data/derived/cleaned_data.csv` with columns: `study_id`, `year`, `field`, `original_study_id`, `effect_size`, `sample_size`, `power_estimate`.
  - **Verification**: Ensure `data/derived/cleaned_data.csv` exists, contains no NaN in critical columns, and has fewer rows than the raw input (if any missing data existed). (FR-001, FR-008) **Depends on T006**.

- [ ] T011b [US1] Implement `code/preprocess.py` to validate grouping variables (`field`, `original_study_id`) for variance and cardinality. **Logic**: Check that each grouping factor has > 1 unique level and non-zero variance in the target variable.
 - **Handling**: If a factor has only 1 level (single study), flag it as "single_level" for **exclusion from the dataset** in downstream modeling (to avoid convergence errors).
 - **Alternative Path**: If a field has zero variance but > 1 level, attempt to **collapse** the field by merging it with the nearest neighbor field or excluding it from the random effect structure if the model fails to converge.
 - **Output**: Save `data/derived/grouping_validation.json` with status per factor.
 - **Schema Requirement**: The JSON MUST contain keys: `{"field": {"status": "valid"|"single_level"|"zero_variance", "count": <int>}, "original_study_id": {"status": "valid"|"single_level"|"zero_variance", "count": <int>}}`.
 - **Verification**: Ensure `data/derived/grouping_validation.json` exists, lists all factors with their validity status, and specifically marks factors with single studies or zero variance as "single_level" or "zero_variance" with the correct count. (Edge Cases: Zero Variance) **Depends on T011a**.

- [ ] T011c [US1] Implement `code/models.py` to execute the primary statistical workflow:
 1. **Pilot OLS Model**: Fit `power_est ~ effect_size + sample_size` to capture the deterministic relationship. Save model to `data/derived/pilot_ols_model.pkl`. **Note**: This step explicitly removes `effect_size` and `sample_size` (covariates) to satisfy FR-002's requirement to "control for input drift" before modeling the residual trend.
 2. **Residualization**: Calculate `power_residual = power_est - predicted_power`. Save `data/derived/residuals.csv` with columns `study_id`, `year`, `field`, `original_study_id`, `power_residual`.
 3. **Field Composition Check**: Read `data/derived/grouping_validation.json`. Identify groups flagged as "single_level" or "zero_variance".
 4. **Primary Hypothesis Test**: Load `data/derived/residuals.csv`. Fit the **Full LMM**: `power_residual ~ year + (1|field) + (1|original_study_id)`.
 - **Constraint Handling**: **Dynamically construct the random effects formula** to exclude groups flagged as "single_level" or "zero_variance" by T011b. If a group has only 1 study, do NOT include it as a random effect (to avoid convergence errors). This satisfies the spec's Edge Cases requirement for graceful handling.
 - **Note**: Do NOT introduce a "field_proportion" covariate or any heuristic threshold (e.g., 10%). The spec requires exclusion/collapse, not covariate adjustment.
 5. **Execute Likelihood-Ratio Test (LRT)**:
 - Fit the **Reduced LMM**: `power_residual ~ (1|field) + (1|original_study_id)` (no `year` fixed effect).
 - Perform the LRT comparing the Full LMM against the Reduced LMM.
 - Extract `p_value_lrt`, `chi2_statistic`, `df_diff`.
 6. **Extract Primary Metrics**: Extract `slope_year`, `se_year`, `ci_lower`, `ci_upper` (Wald method) from the Full LMM's fixed effects.
 7. **Unified Output**: Save the full model summary, reduced model summary, LRT results, and the `year` slope/SE into a SINGLE file: `results/lmm_final_summary.json`. This file must contain keys: `slope_year`, `se_year`, `ci_lower`, `ci_upper`, `p_value_lrt`, `chi2_statistic`, `df_diff`.
 **Verification**:
 - Ensure `results/lmm_final_summary.json` contains valid floats for all keys, specifically `slope_year` derived from the **Full LMM on `power_residual`** and `p_value_lrt` from the explicit LRT step.
 - Ensure the LRT p-value is correctly calculated and reported. (FR-002, FR-003, FR-009, Constitution Principle VII, SC-001, Plan T011c Conditional Step) **Depends on T011b** (for residuals input and validation).

- [ ] T012 [US1] Implement `code/models.py` to verify convergence of the LMM fitted in T011c.
 **Logic**: Check convergence status flags from the LMM solver. If convergence failed, log a warning and attempt to refit with adjusted optimizer controls.
 **Schema Validation**: Validate `results/lmm_final_summary.json` against `contracts/drift_model_output.schema.yaml`.
 **Output**: Ensure the JSON passes schema validation.
 **Verification**: Ensure the task fails if the schema validation fails. (Plan T012) **Depends on T011c**.

- [ ] T013 [US1] Implement `code/visualize.py` to generate a scatter plot of **residual power vs. year**.
 **Definition**: Residuals are `power_residual` from `data/derived/residuals.csv` (produced by T011c).
 **Input**: `data/derived/residuals.csv`.
 **Output**: Save plot to `results/power_drift_scatter.png`.
 **Verification**:
 - Ensure `results/power_drift_scatter.png` exists, has non-zero dimensions, and contains a regression line showing the drift trend **with 95% confidence intervals** (shaded region or error bars). (FR-009) **Depends on T012** (for model summary) and **T011c** (for residuals).

- [ ] T015 [US1] Add logging for User Story 1 operations and data filtering steps.

**Checkpoint**: At this point, User Story 1 (Core Drift Analysis) should be fully functional and testable independently

---

## Phase 4: User Story 2 - Robustness via Permutation & Sensitivity (Priority: P2)
**Depends on T012 completion**

**Goal**: Validate the power drift results against non-parametric permutation tests and alpha threshold sensitivity analysis.

**Independent Test**: The system can be tested by running the permutation test (sufficient iterations to ensure convergence) and the sensitivity sweep on the the same dataset, verifying that the p-value distribution and trend stability are reported.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Unit test `tests/unit/test_permutation.py::test_permutation_logic_small_count` for permutation logic with small iteration count.
- [X] T019 [P] [US2] Integration test `tests/integration/test_sensitivity.py::test_sensitivity_analysis_sweep` for sensitivity analysis sweep.

### Implementation for User Story 2

- [ ] T020 [US2] Implement `code/robustness.py` function for non-parametric permutation test: **shuffle `year` labels** (FR-004). **Target**: 10,000 permutations. **Fallback**: If `psutil.Process().memory_info().rss > 6 * 1024**3` bytes OR if the **estimated time to complete 10,000 permutations** (calculated as `time_per_perm * 10000` based on the first 10 permutations) exceeds **A duration of approximately two hours. (2 hours)**, fallback to **A large number of permutations** and flag as "approximate". **Detection Mechanism**: Use `psutil` to monitor memory and `time` to track duration of the first 10 permutations. **Input**: Drift coefficient (slope_year) from `results/lmm_final_summary.json` and `data/derived/cleaned_data.csv`. **Output**: Empirical p-value for the drift slope in `results/permutation_pvalue.json`. **Verification**: Ensure `results/permutation_pvalue.json` includes an `iterations_run` field (set to 10000 or 1000) and a `status` field (e.g., 'exact' or 'approximate'). **CRITICAL**: Verify that if `iterations_run` < 10000, the `status` field is explicitly set to "approximate". (FR-004) **Depends on T012**.

- [ ] T020b [US2] Implement `code/robustness.py` to load `results/lmm_final_summary.json` and `results/permutation_pvalue.json`, compare the parametric p-value with the empirical p-value, and generate `results/permutation_consistency.json`. **Logic**: Calculate `p_value_difference = abs(p_parametric - p_empirical)`. Generate a `robustness_statement` (string) describing whether the results are consistent (e.g., "p-values are within 0.01" or "p-values diverge"). **Output**: `results/permutation_consistency.json` containing `p_value_difference` (float) and `robustness_statement` (string). **Verification**: Ensure `results/permutation_consistency.json` contains the required keys and the difference is correctly calculated. (SC-002, US-2 Acceptance Scenario 1) **Depends on T020**.

- [ ] T021 [US2] Implement `code/robustness.py` function for sensitivity analysis sweeping alpha across a range of significance levels including conventional thresholds and report the resulting drift significance rates. **Input**: `results/lmm_final_summary.json`. **Output**: `results/sensitivity_report.json`. **Verification**: Ensure `results/sensitivity_report.json` contains entries for a range of alpha values including and 0.1. Each entry must include `drift_significant` (boolean) and `p_value` (float). Additionally, ensure the report explicitly contains a text statement concluding whether the drift is driven by a specific alpha choice or holds across the tested range. **Schema Validation**: Validate `results/sensitivity_report.json` against `contracts/sensitivity_report.schema.yaml`. (FR-005, SC-003, Plan T021) **Depends on T012**.

- [ ] T022 [US2] Integrate permutation and sensitivity results into the final report generation in `code/main.py`

- [X] T023 [US2] Add logic to handle permutation convergence failures and flag results as "approximate" (Edge Case)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Cross-Field Aggregation & Drift Validation (Priority: P3)
**Depends on T012 completion**

**Goal**: Combine evidence across heterogeneous fields using adaptive weighting and validate drift via input permutation framework.

**Independent Test**: The system can be tested by executing the adaptively weighted statistic aggregation and the input permutation validation on the full dataset, verifying that a combined drift statistic is produced.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T024 [P] [US3] Unit test `tests/unit/test_meta_analysis.py::test_dersimonian_laird_weighting` for DerSimonian-Laird weighting logic.
- [X] T025 [P] [US3] Integration test `tests/integration/test_input_permutation.py::test_input_permutation_framework` for input permutation validation.

### Implementation for User Story 3

- [ ] T025 [US3] Implement `code/robustness.py` to stratify the cleaned data by `field`, fit a separate LMM for each field using `power_residual ~ year + (1|field) + (1|original_study_id)` to extract the `year` slope and standard error. **Constraint**: **Skip fields** where `n_studies == 1` (as flagged in T011b) to avoid undefined random effects. **Note**: This uses the residualized power calculated in T011c (`power_residual` from `data/derived/residuals.csv`) to ensure we are aggregating **residual power drift estimates** as required by FR-006. **Input**: `data/derived/residuals.csv`. **Output**: Save `results/field_slopes.csv` with columns: `field`, `slope_year`, `se_slope`, `n_studies`. **Verification**: Ensure the file contains one row per valid field and that slopes are derived from `power_residual` (not raw power). (FR-006, US-3 Acceptance Scenario 1, Plan T025) **Depends on T011c**.

- [ ] T026 [US3] Implement `code/robustness.py` function for inverse-variance weighting with heterogeneity adjustment (DerSimonian-Laird) to combine **residual power drift estimates** (adjusted slopes) across fields. **Algorithm**: Calculate heterogeneity (Q-statistic, tau-squared) and apply inverse-variance weighting to the `slope_year` and `se_slope` from `results/field_slopes.csv` (produced by T025). **Input**: `results/field_slopes.csv`. **Output**: Aggregated drift estimate and confidence interval in `results/aggregated_drift.json`. **Comparison**: Generate `results/comparison_aggregated_vs_lmm.json` comparing the aggregated drift estimate against the primary mixed-model slope (from `results/lmm_final_summary.json` produced by T012). **Verification**: Ensure the file contains both values and the consistency check (keys: `consistency_score` float, `method` string). (FR-006, US-3 Acceptance Scenario 3, SC-004) **Depends on T025**.

- [ ] T027 [US3] Implement `code/robustness.py` function for input permutation framework: **shuffle `effect_size` and `sample_size` while holding `year` constant** (FR-007). **Target**: 10,000 permutations. **Fallback**: **A sufficient number of permutations** if `psutil.Process().memory_info().rss > 6 * 1024**3` bytes OR if the **estimated time to complete 10,000 permutations** (calculated as `time_per_perm * 10000` based on the first 10 permutations) exceeds **A duration of several hours. (2 hours)**. **Algorithm**:
 1. **Input**: Read `data/derived/cleaned_data.csv` (produced by T011a).
 2. **Load Pilot Model**: Load the **fixed coefficients** from `data/derived/pilot_ols_model.pkl` (produced by T011c). **DO NOT** re-estimate the OLS model.
 3. **Permutation**: For each iteration, randomly shuffle the `effect_size` and `sample_size` columns in the loaded data while keeping the `year` column unchanged.
 4. **Recalculation**: Recalculate `power_estimate` and `power_residual` for the permuted data by **applying the fixed coefficients** from the loaded pilot model.
 5. **Refit**: Refit the LMM (`power_residual ~ year + (1|field) + (1|original_study_id)`) on the recalculated residuals to generate a null distribution of slopes.
 6. **Output**:
    - Generate `results/null_distribution_implied_power.csv` with columns: `simulated_drift`, `count`.
    - **Generate `results/input_permutation_summary.json`**: This JSON must contain `observed_slope` (from T012), `p_value` (empirical p-value derived from comparing observed slope to the null distribution), and `methodology` (string describing the permutation process, explicitly stating "fixed pilot coefficients").
    - **Generate `results/input_permutation_pvalue.json`** for consistency.
 **Verification**: Ensure `results/input_permutation_summary.json` exists and contains the required keys. Ensure `results/null_distribution_implied_power.csv` contains a sufficient number of rows (with a fallback count) to support robust estimation. **CRITICAL**: Verify that the `year` column in the input data was held constant during the permutation process by including a metadata field `methodology: input_permutation_year_fixed` in the output JSON. (FR-007, US-3 Acceptance Scenario 2, Plan T027) **Depends on T012** (for observed slope), **T011c** (for pilot model and residuals logic), and **T011a** (for input data).

- [ ] T028 [US3] Implement `code/robustness.py` to perform the **Non-Linearity Check**.
 **Logic**: Fit a model with `ns(year, df=3)` (natural splines) and compare its AIC to the linear model (`power_residual ~ year`).
 **Input**: `data/derived/residuals.csv`.
 **Output**: `results/nonlinearity_check.json` containing `linear_aic`, `spline_aic`, `delta_aic`, and `preferred_model`.
 **Verification**: Ensure the file contains valid AIC values and a clear preferred model selection. (Plan T028) **Depends on T012**.

- [ ] T029 [US3] Update `code/visualize.py` to plot the null distribution of the input-permutation drift and compare observed slope (US-3)

- [X] T030 [US3] Integrate cross-field aggregation and input permutation results into the final report JSON (US-3)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Finalization, versioning, and pipeline orchestration

- [ ] T031 [P] Implement `code/main.py` pipeline orchestrator to sequence download, validation, LMM fitting, robustness checks, and reporting

- [X] T032 [P] Run `code/update_state.py` to compute SHA-256 hashes for all `data/derived/` and `results/` files (Phase 6). **Logic**:
 1. Compute SHA-256 hashes for every file in `data/derived/`, `results/*.json`, `results/*.csv`, and `results/*.png`.
 2. Update `state.yaml` with `artifact_hashes` map (keys are relative file paths from project root).
 3. **CRITICAL**: If a hash mismatch is detected compared to the previous state, **invalidate** or **reset** dependent review records/stages by updating the `current_stage` to `human_input_needed` or triggering a re-run flag.
 4. Update `updated_at` timestamp.
 **Verification**: Run `update_state.py` manually in the test environment and confirm it successfully modifies the `current_stage` key in the state file and includes the full file list in `artifact_hashes`. (FR-010, Constitution Principle V) **Depends on T031**.

- [X] T033a [P] **Create** `README.md` in project root with pipeline overview and usage instructions. **Content**: Must include sections: `[Project Overview, Installation, Usage, Output Artifacts]`. **Generation**: Use a concrete command (e.g., `cat > README.md << 'EOF'...`) to ensure the file is created with the specified content. **Verification**: Ensure `README.md` exists and contains all required sections. (Plan Phase 4)

- [X] T033b [P] Create `docs/methodology.md` documenting the LMM methodology, residualization process, and aggregation logic.
- [ ] T034 [P] Run full pipeline on a **static subset** (The initial rows of the dataset will be examined to identify patterns in the early-stage data distribution. of `data/raw/data.csv`) to verify end-to-end execution within **6-hour** CPU limit (FR-010). **Runner Constraints**: Verify on a runner with a multi-core processor and sufficient memory. **Verification**: Check for existence of `results/timing_report.json`.
- [X] T034a [P] Implement `code/timing.py` to instrument pipeline execution and generate `results/timing_report.json` with start/end times, total duration, and `phase_durations` dictionary. **Verification**: Ensure the JSON contains keys for `data_prep_duration`, `model_fitting_duration`, and `robustness_duration`. (Plan T032)
- [X] T035a [P] Run linter (ruff/flake8) on `code/` and fix all warnings (Success: zero warnings)
- [X] T035b [P] Run formatter (black) on `code/` and verify no changes are needed (Success: no diff)
- [X] T038 [P] [US1] Implement `code/download.py` "No Synthetic Fallback" guard. **Logic**: Raise `DataFetchError` if the primary dataset source is unreachable (network error, 404). **Exception**: If the dataset fetches successfully but is missing specific columns (variables) required for analysis, log a warning and proceed with the available data (per Spec Assumptions). This does NOT apply to missing *rows* (handled by T011a). **Verification**: Ensure the pipeline fails only on source unreachability, not on partial column availability. (Constitution Principle III, Spec Assumptions)

---

## Phase 7: Verification & Reporting (Revision Concerns)

**Purpose**: Address specific reviewer concerns regarding documentation completeness, pipeline timing verification, and end-to-end reproducibility.

- [X] T039 [P] [Review Concern] Update `docs/methodology.md` to explicitly detail the **Residualization Strategy**. **Content**: Must include the mathematical derivation of `power_residual = power_est - predicted_power` from the Pilot OLS model, explain why this step prevents tautology, and justify the choice of covariates (`effect_size`, `sample_size`). **Verification**: Ensure the document cites the specific formulas used and the logic for excluding `year` from the pilot model. (Addresses Reviewer Concern: Methodology Clarity)
- [X] T040 [P] [Review Concern] Enhance `code/timing.py` to generate a **Phase-Level Timing Report**. **Logic**: The script must track and log the duration of each major phase (Setup, Data Prep, Modeling, Robustness) separately, not just total runtime. **Output**: Append `phase_durations` dictionary to `results/timing_report.json`. **Verification**: Ensure the JSON contains keys for `data_prep_duration`, `model_fitting_duration`, and `robustness_duration`. (Addresses Reviewer Concern: Performance Bottleneck Identification)
- [X] T041 [P] [Review Concern] Implement `tests/integration/test_end_to_end.py::test_full_pipeline_reproducibility`. **Logic**: Run the full pipeline from scratch on a clean temporary directory, verify all output artifacts match the expected schema, and confirm `state.yaml` hashes are consistent. **Verification**: Ensure the test passes on a fresh runner without cached data. (Addresses Reviewer Concern: Reproducibility Guarantee)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Verification (Phase 7)**: Depends on completion of all User Stories and Polish phases

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Depends on T012 completion (slope extraction)
- **User Story 3 (P3)**: Depends on T012 completion (slope extraction) and T025 (field slopes)

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
- Phase 7 tasks (T039, T040, T041) can run in parallel as they are independent verification steps

### Specific Task Dependencies

- **T006** must complete before **T011a** (Streaming generator before preprocessing).
- **T011a** must complete before **T011b** (cleaning before grouping validation).
- **T011b** must complete before **T011c** (grouping validation before model fitting).
- **T011c** must complete before **T012** (Residuals produced before model verification).
- **T012** must complete before **T013** (residual generation and model fitting before visualization).
- **T012** must complete before **T020** (slope extraction before permutation validation).
- **T020** must complete before **T020b** (permutation result before consistency check).
- **T011c** must complete before **T025** (Residuals produced before field-specific modeling).
- **T025** must complete before **T026** (field slopes before aggregation).
- **T012**, **T011c**, and **T011a** must complete before **T027** (slope extraction, pilot model, and input data before input permutation validation).
- **T033a**, **T034**, **T034a** must complete before **T039**, **T040**, **T041** (Documentation and timing infrastructure must exist before verification tasks can be performed).

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (T011a, T011b, T011c, T012, T013)
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

### Revision Strategy

1. Complete all User Stories and Polish tasks first.
2. Execute Phase 7 tasks (T039, T040, T041) to address specific reviewer concerns regarding documentation, timing, and reproducibility.
3. Validate that all new documentation and timing reports meet the specified criteria.
4. Finalize the project state.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, cross-story dependencies that break independence
- **Data Integrity**: `code/download.py` (T006) MUST fail loudly on real data fetch failure; no synthetic fallbacks allowed. **Exception**: If the fetch succeeds but returns partial columns, proceed with available data (Spec Assumptions).
- **Methodology**: Tasks implement the Linear Mixed-Effects Model (LMM) as required by Spec FR-002, FR-003, and FR-009. The model includes random intercepts for `field` AND `original_study_id` **with conditional exclusion for single-level groups** to handle Edge Cases gracefully. The primary drift metric is the `slope_year` from the **Full Model** on `power_residual`.
- **Compute Feasibility**: All tasks are designed to run on CPU-only runners (multiple cores, sufficient RAM) within 6 hours. Permutation tests use vectorized `numpy` operations and chunked processing to fit memory constraints. Streaming logic (T006) is implemented as a conditional fallback for large files, respecting the Spec's assumption that the dataset fits in RAM.
- **Revision Concern**: T033a, T033b, T034, and T034a added to ensure documentation of the LMM methodology is complete and the pipeline is verified end-to-end within the **6-hour** CPU limit as required by FR-010 and the Constitution.
- **New Revision Concerns**: T039, T040, and T041 added to explicitly address reviewer concerns about methodology documentation, phase-level timing analysis, and end-to-end reproducibility verification.
- **Task Placement**: T006 now contains all data loading logic, removing the need for T036/T037. T011a depends on T006.
- **Critical Path**: T011a is the primary blocker for the entire pipeline. It must be implemented to generate `data/derived/cleaned_data.csv`.