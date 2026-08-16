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

- [ ] T001a [P] Create `projects/PROJ-150-detecting-statistical-power-drift-in-rep/` directory structure by running `mkdir -p data/raw data/derived code tests results state`
- [ ] T001b [P] Initialize `.gitignore` for Python data projects (exclude data/raw, data/derived, __pycache__,.env)
- [X] T001c [P] Create `requirements.txt` with pinned versions: pandas, numpy, scipy, statsmodels, scikit-learn, matplotlib, seaborn, pyyaml, pytest

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 [P] Create `code/__init__.py` and establish package structure
- [X] T006 Implement `code/download.py` with real data fetch logic (no synthetic fallbacks) using `huggingface_hub` to fetch `osf/reproducibility_project` dataset, specifically the `data.csv` file. **Verification**: Include a step to verify the dataset metadata (title-token-overlap ≥ 0.7) matches the "OSF Reproducibility Project" source to ensure data integrity.
- [X] T007 Implement `code/validate_source.py` for URL reachability and title-token-overlap (≥ 0.7) validation
- [X] T008 [P] Create `code/update_state.py` to compute SHA-256 hashes and update project state file
- [X] T009 Setup `pytest` configuration and base test fixtures in `tests/conftest.py`

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Core Power Drift Analysis (Priority: P1) 🎯 MVP

**Goal**: Compute post-hoc power estimates and test for temporal decline using a Linear Mixed-Effects Model (LMM) with `power_est` as the outcome, `year` as a fixed effect, and random intercepts for `field` AND `original_study_id`.

**Independent Test**: The system can be fully tested by running the power re-estimation and LMM scripts on a static subset of the OSF data, verifying that a slope coefficient and p-value are generated for the `year` predictor in the residual model.

### Pre-Implementation Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Tasks marked [P] are file-level independent (can be written in parallel). However, per TDD practice, these tests MUST be written and verified to FAIL before the corresponding implementation tasks (T011a-T016) are implemented.

- [X] T010 [P] [US1] Unit test `tests/unit/test_power_calc.py::test_power_calc_handles_nan` for power calculation logic.
- [X] T011 [P] [US1] Integration test `tests/integration/test_lmm_pipeline.py::test_lmm_pipeline_full_run` for the full LMM pipeline.

### Implementation for User Story 1

- [ ] T011a [US1] Implement `code/preprocess.py` to filter rows with missing `year`, `effect_size`, or `sample_size` (FR-008). Log warnings. **Verification**: Ensure `data/derived/cleaned_data.csv` exists and contains no NaN values in critical columns.
- [ ] T011b [US1] Implement `code/preprocess.py` to validate grouping variables (`field`, `original_study_id`) for variance and cardinality. **Logic**: Check that each grouping factor has > 1 unique level and non-zero variance in the target variable. If a factor has only 1 level or zero variance, log a warning and flag it for exclusion from the random effect structure. **Output**: Save `data/derived/grouping_validation.json` with status per factor. **Verification**: Ensure `data/derived/grouping_validation.json` exists and lists all factors with their validity status. (Edge Cases: Zero Variance) **Depends on T011a**.
- [X] T012 [US1] Implement `code/compute_trends.py` to:
 1. Fit a Linear Mixed-Effects Model: `power_est ~ year + effect_size + sample_size + (1|field) + (1|original_study_id)` using the validated grouping factors from T011b. If T011b flagged a factor as invalid, exclude it from the random effects but log a critical warning.
 2. **Critical Validation**: Verify the fitted model object reports non-zero variance for ALL included random effects. If convergence fails or variance is zero for any included factor, log a warning and exclude that specific factor from the model (do not halt execution), then re-fit.
 3. Fit a reduced model: `power_est ~ effect_size + sample_size + (1|field) + (1|original_study_id)` (excluding `year`) and save it to `data/derived/reduced_model.pkl` (required for visualization in T013).
 4. Perform a Likelihood-Ratio Test (LRT) comparing the full model against the reduced model.
 5. **Unified Output**: Save the full model summary, reduced model summary, LRT results (chi2, p-value, df), and the `year` slope/SE into a SINGLE file: `results/lmm_final_summary.json`. This file must contain keys: `slope_year`, `se_year`, `ci_lower`, `ci_upper`, `p_value_lrt`, `chi2_statistic`, `df_diff`.
 **Verification**:
 - Ensure `results/lmm_final_summary.json` exists with valid floats for all keys.
 - Ensure the model includes both random effects (or logs the exclusion of one). (FR-002, FR-003, Constitution Principle VII)
- [X] T013 [US1] Implement `code/visualize.py` to generate a scatter plot of **residual power vs. year**.
 **Definition**: Residuals are calculated as `observed_power - predicted_power_from_REDUCED_model` (where the reduced model excludes `year`). This isolates the `year` effect (drift) by removing only the variance explained by effect size, sample size, and random effects, leaving the temporal trend visible.
 **Output**: Save plot to `results/power_drift_scatter.png`. Additionally, save the underlying residual data used for the plot to `data/derived/residuals.csv` for programmatic verification.
 **Verification**:
 - Ensure `results/power_drift_scatter.png` exists, has non-zero dimensions, and contains a regression line showing the drift trend.
 - Ensure `data/derived/residuals.csv` exists and matches the residual definition (observed - reduced_model_pred). (FR-009)
- [ ] T014 [US1] Add error handling for missing data (skip row, log warning with row index and reason) and zero-variance fields (FR-008). Log format: `WARNING: Skipping row {index} due to {reason}`. Handle specific errors: `NaN` in `effect_size` or `sample_size`, and `ZeroDivisionError` in power calculation.
- [ ] T015 [US1] Add logging for User Story 1 operations and data filtering steps.

**Checkpoint**: At this point, User Story 1 (Core Drift Analysis) should be fully functional and testable independently

---

## Phase 4: User Story 2 - Robustness via Permutation & Sensitivity (Priority: P2)
**Depends on T012 completion**

**Goal**: Validate the power drift results against non-parametric permutation tests and alpha threshold sensitivity analysis.

**Independent Test**: The system can be tested by running the permutation test (sufficient iterations to ensure convergence) and the sensitivity sweep on the same dataset, verifying that the p-value distribution and trend stability are reported.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Unit test `tests/unit/test_permutation.py::test_permutation_logic_small_count` for permutation logic with small iteration count.
- [X] T019 [P] [US2] Integration test `tests/integration/test_sensitivity.py::test_sensitivity_analysis_sweep` for sensitivity analysis sweep.

### Implementation for User Story 2

- [ ] T020 [US2] Implement `code/robustness.py` function for non-parametric permutation test: shuffle `year` labels. **Target**: 10,000 permutations. **Fallback**: If memory or time limits are exceeded, fallback to a minimum of 1,000 permutations. Terminate early if > 5 hours, flag as "approximate". **Input**: Drift coefficient (slope_year) from `results/lmm_final_summary.json` (produced by T012). **Output**: Empirical p-value for the drift slope in `results/permutation_pvalue.json`. **Verification**: Ensure `results/permutation_pvalue.json` includes an `iterations_run` field (must be 10000 or 1000) and a `status` field (e.g., 'exact' or 'approximate') reflecting whether the target or fallback count was used. (FR-004)
- [ ] T021 [US2] Implement `code/robustness.py` function for sensitivity analysis sweeping alpha across the set {0.01, 0.05, 0.1} and report the resulting drift significance rates. **Verification**: Ensure `results/sensitivity_report.json` contains entries for all three alpha values. (FR-005)
- [X] T022 [US2] Integrate permutation and sensitivity results into the final report generation in `code/main.py`
- [ ] T023 [US2] Add logic to handle permutation convergence failures and flag results as "approximate" (Edge Case)

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

- [ ] T026 [US3] Implement `code/robustness.py` function for inverse-variance weighting with heterogeneity adjustment (DerSimonian-Laird) to combine residual power drift estimates across fields. **Input**: Field-specific slopes from `results/lmm_final_summary.json` (or a stratified run). **Output**: Aggregated drift estimate and confidence interval in `results/aggregated_drift.json`. **Comparison**: Generate `results/comparison_aggregated_vs_lmm.json` comparing the aggregated drift estimate against the primary mixed-model slope (from `results/lmm_final_summary.json` produced by T012). **Verification**: Ensure the file contains both values and the consistency check. (FR-006, US-3 Acceptance Scenario 3, SC-004)
- [ ] T027 [US3] Implement `code/robustness.py` function for input permutation framework: shuffle `effect_size` and `sample_size`. **Target**: 10,000 permutations. **Fallback**: 1,000 permutations if resource limits are exceeded. Hold `year` constant to generate a null distribution for the drift slope. **Output**: Generate `results/null_distribution_implied_power.csv` with columns: `simulated_drift`, `count`. **Verification**: Ensure `results/null_distribution_implied_power.csv` contains 10000 (or fallback count) rows with a `simulated_drift` column, and that the file is non-empty. Compare observed slope against this distribution. (FR-007)
- [X] T028 [US3] Update `code/visualize.py` to plot the null distribution of the input-permutation drift and compare observed slope (US-3)
- [~] T029 [US3] Integrate cross-field aggregation and input permutation results into the final report JSON (US-3)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Finalization, versioning, and pipeline orchestration

- [X] T030 [P] Implement `code/main.py` pipeline orchestrator to sequence download, validation, LMM fitting, robustness checks, and reporting
- [X] T031 Run `code/update_state.py` to compute SHA-256 hashes for all `data/derived/` and `results/` files (Phase 6)
- [ ] T032 Verify that the `current_stage` is updated to `implemented` by checking `state/projects/PROJ-150-detecting-statistical-power-drift-in-rep/state.yaml` for `current_stage: implemented`.
- [~] T033 Documentation updates in `docs/` and `README.md` regarding the Linear Mixed-Effects Model methodology
- [~] T034 Run full pipeline on a static subset to verify end-to-end execution within 6-hour CPU limit (FR-010)
- [ ] T035a [P] Run linter (ruff/flake8) on `code/` and fix all warnings (Success: zero warnings)
- [ ] T035b [P] Run formatter (black) on `code/` and verify no changes are needed (Success: no diff)

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
- **User Story 2 (P2)**: Depends on T012 completion (slope extraction)
- **User Story 3 (P3)**: Depends on T012 completion (slope extraction)

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
- **T011b** must complete before **T012** (grouping validation before model fitting).
- **T012** must complete before **T013** (model fitting and reduced model saving before visualization).
- **T012** must complete before **T020** (slope extraction before permutation validation).
- **T012** must complete before **T026** (slope extraction before aggregation).
- **T012** must complete before **T027** (slope extraction before input permutation validation).

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (T011a, T011b, T012, T013)
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
- **Data Integrity**: `code/download.py` MUST fail loudly on real data fetch failure; no synthetic fallbacks allowed.
- **Methodology**: Tasks implement the Linear Mixed-Effects Model (LMM) as required by Spec FR-002, FR-003, and FR-009. The model includes random intercepts for `field` AND `original_study_id`.
- **Compute Feasibility**: All tasks are designed to run on CPU-only runners (multiple cores, 7GB RAM) within 6 hours. Permutation tests use vectorized `numpy` operations and chunked processing to fit memory constraints.