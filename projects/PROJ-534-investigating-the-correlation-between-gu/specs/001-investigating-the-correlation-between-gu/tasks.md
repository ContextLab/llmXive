# Tasks: Investigating the Correlation Between Gut Microbiome Composition and Cognitive Flexibility in Aging

**Input**: Design documents from `/specs/001-gut-microbiome-cognitive-flexibility/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e., US1, US2, US3)
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

- [ ] T001a [P] Initialize Source Directories: Create `src/`, `src/data/`, `src/analysis/`, `src/viz/`, `src/power/`, `src/sensitivity/`, `src/utils/` directories at repository root.
- [ ] T001b [P] Initialize Data Directories: Create `data/raw`, `data/processed`, `data/results`, `logs/` directories at repository root.
- [ ] T001c [P] Initialize Test Directories: Create `tests/unit/`, `tests/integration/`, `tests/contract/` directories at repository root.
- [ ] T002a [P] Initialize `requirements.txt`: Pin dependencies (pandas, scikit-learn, scipy, statsmodels, biom-format, numpy, matplotlib, seaborn, pyyaml, scikit-bio).
- [ ] T002b [P] Configure Linting & Formatting: Initialize `ruff` and `black` configurations.
- [ ] T002c [P] Initialize Logging Configuration: Create `src/utils/logging_config.py` to set up the root logger writing to `logs/pipeline.log`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin. Includes schema definitions and data generation logic.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T003 [P] Create `contracts/dataset.schema.yaml` defining entities with exact fields: `participant_id` (str, PK), `age` (int, >=0), `sex` (enum), `bmi` (float), `cognitive_flexibility_score` (float), `shannon_diversity` (float), `simpson_diversity` (float), `chao1` (float), `dietary_fiber_intake` (float), `antibiotic_use_history` (bool). **Action**: Create `contracts/` directory if missing. **Acceptance Criterion**: The schema MUST include ONLY the covariates listed in `spec.md` FR-002 (age, sex, BMI, dietary_fiber_intake, antibiotic_use_history). Create `src/utils/schema_validator.py` to enforce this schema. **Dependency**: None.
- [ ] T004 [P] Create `contracts/analysis_output.schema.yaml` defining `AnalysisResult` entity with exact fields: `test_type` (str), `metric_name` (str), `correlation_coefficient` (float), `p_value` (float), `adjusted_p_value` (float), `confidence_interval` (array[float, float]), `r_squared` (float).
- [ ] T005 [P] Implement `src/utils/config.py` with fixed random seeds and path configurations.
- [ ] T006a [P] Setup `pytest` configuration: Create `pytest.ini` or `pyproject.toml` for test discovery.
- [ ] T006b [P] Create test directory structure: Ensure `tests/unit/`, `tests/integration/`, `tests/contract/` exist.
- [X] T007 [P] Implement `src/utils/validation.py` to enforce schema contracts.
- [ ] T008 [P] Implement `src/data/synthetic_gen.py` to generate synthetic data with fixed seeds (e.g., `seed=42`). **Null Hypothesis Logic**: Explicitly generate `cognitive_flexibility_score` and `shannon_diversity` as statistically independent by drawing from independent normal distributions (e.g., `np.random.normal`) with zero mean and fixed variance. This validates the pipeline's ability to detect no correlation (p > 0.05). Ensure data types match `contracts/dataset.schema.yaml` exactly (using field names `dietary_fiber_intake` and `antibiotic_use_history`). Output to `data/raw/synthetic_data.csv` AND `data/raw/feature_table.biom` (BIOM format v2.1.0, containing OTU/ASV counts). **Dependency**: Must run after T003 and T005.
- [ ] T009 [P] Validate `contracts/dataset.schema.yaml` against the generated synthetic data in `data/raw/synthetic_data.csv` to ensure strict type enforcement (int, float, bool, enum).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Cohort Filtering (Priority: P1) 🎯 MVP

**Goal**: Ingest synthetic 16S and cognitive data, filter for age >= 65 with complete data, and validate against schema.

**Independent Test**: Run ingestion on a small synthetic dataset with mixed ages and missing values; verify output contains ONLY rows matching age >= 65 and non-null metrics.

### Implementation for User Story 1

- [ ] T010 [US1] Implement `src/data/ingestion.py` to ingest 16S rRNA sequencing data and linked cognitive assessment data from `data/raw` (synthetic). **Logic**: Load synthetic 16S rRNA sequencing data and linked cognitive assessment data from `data/raw/synthetic_data.csv`. Merge on `participant_id` as per FR-001. Validate output against `contracts/dataset.schema.yaml`. **Dependency**: Must run after T008 produces `data/raw/synthetic_data.csv`.
- [ ] T011 [US1] Implement `src/data/filtering.py` to filter for age >= 65, non-null Shannon/Cognitive scores, and required covariates (age, sex, BMI, dietary_fiber_intake, antibiotic_use_history). **Action**: Save output to `data/processed/filtered_cohort.csv`. **Dependency**: Must run after T010 produces the merged dataset.
- [X] T012 [US1] Add logic in `src/data/filtering.py` to handle zero-variance datasets by flagging and skipping correlation (Edge Case).
- [ ] T013 [US1] Implement listwise deletion for missing covariates in `src/data/filtering.py`. **Action**: Log the count of dropped rows to `logs/filtering.log` using the logger initialized in T002. **Constraint**: Strictly use listwise deletion for covariates defined in `contracts/dataset.schema.yaml` (age, sex, BMI, dietary_fiber_intake, antibiotic_use_history). Do NOT attempt to handle SES or dietary_pattern as these are not in the schema.

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T014 [US1] Unit test for age filtering logic in `tests/unit/test_filtering.py`. **Prerequisite**: Must run after T011 implementation exists.
- [X] T015 [US1] Unit test for null-value exclusion in `tests/unit/test_filtering.py`.
- [ ] T016 [US1] Contract test validating `data/processed/filtered_cohort.csv` against `contracts/dataset.schema.yaml` in `tests/contract/test_schemas.py`. **Action**: Create `tests/contract/` directory if missing. **Prerequisite**: Must run after T011 completes. Verify all rows have non-null `age`, `shannon_diversity`, `cognitive_flexibility_score`, and required covariates (age, sex, BMI, dietary_fiber_intake, antibiotic_use_history). **Verification**: Assert that the test fails with `AssertionError` if any row contains null values for the required fields or if the schema validation raises a `ValidationError`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Diversity Metric Calculation and Correlation Analysis (Priority: P2)

**Goal**: Calculate alpha/beta diversity, perform correlation/regression with covariates, apply FDR correction, and handle non-normality.

**Independent Test**: Provide pre-calculated metrics and scores; verify correlation coefficients match manual calculation, regression converges, and FDR is applied.

### Implementation for User Story 2

- [ ] T017 [US2] Implement `src/analysis/diversity.py` to calculate Alpha (Shannon, Simpson, Chao1) and Beta (Bray-Curtis, UniFrac) metrics from the filtered cohort. **Output**: Must produce scalar alpha metrics AND the beta diversity distance matrix required for T020. **Dependency**: Must run after T011 produces `data/processed/filtered_cohort.csv`.
- [ ] T018 [US2] Implement `src/analysis/correlation.py` to perform Pearson/Spearman correlation (auto-switch if skewness > 1.0 or Shapiro-Wilk p < 0.05) with a specified confidence interval. **Action**: Apply Benjamini-Hochberg correction to alpha diversity correlation p-values (FR-004) and output `adjusted_p_value` for each to `data/results/correlation_results.json`. Log the switch logic. **Verification**: Assert that `adjusted_p_value` is calculated using Benjamini-Hochberg and logged. Verify log contains switch logic if non-normality detected. **Dependency**: Must run after T017 produces diversity metrics.
- [ ] T019 [US2] Implement `src/analysis/correlation.py` to run Linear Regression (Cognitive ~ Diversity + Covariates). **Covariates**: age, sex, BMI, dietary_fiber_intake, antibiotic_use_history (Strictly as per spec FR-002). **Action**: Calculate R-squared and apply Benjamini-Hochberg correction to regression p-values. **Dependency**: Must run after T017 and T018.
- [ ] T019b [US2] Implement `src/analysis/correlation.py` to run the **baseline model** (Cognitive ~ Covariates only) and calculate the delta R-squared (Full Model R-squared - Baseline Model R-squared) to measure **incremental predictive value** as per SC-002. **Action**: Save delta R-squared to `data/results/correlation_results.json`. **Dependency**: Must run after T019.
- [ ] T020 [US2] Implement `src/analysis/beta_diversity.py` to perform **PERMANOVA** using `skbio.stats.distance.permanova` for Beta diversity with continuous cognitive flexibility scores as predictors (FR-005). **Action**: Output `data/results/beta_diversity_results.json` containing pseudo-F statistic, R-squared, and p-value. **Constraint**: Do NOT use arbitrary quartile binning for modeling; use continuous scores. **Verification**: Assert that pseudo-F statistic, R-squared, and p-value are recorded in `data/results/beta_diversity_results.json`. **Dependency**: Must run after T017 produces beta diversity matrix.
- [ ] T021 [US2] Save `data/results/correlation_results.json` containing coefficients, p-values, adjusted p-values, CIs, R-squared, and delta R-squared, verifying keys: `correlation_coefficient`, `p_value`, `adjusted_p_value`, `confidence_interval`, `r_squared`, `delta_r_squared` against `contracts/analysis_output.schema.yaml`. **JSON Structure**: Must be a list of objects or a dictionary with keys for each metric. **Dependency**: Must run after T018, T019, T019b, and T020 produce their respective outputs.
- [ ] T021b [US2] Implement validation in `src/analysis/correlation.py` or a dedicated test `tests/unit/test_fdr_threshold.py` to validate that adjusted p-values are compared against the 0.05 significance threshold as required by SC-004. **Action**: Log the FDR status (Pass/Fail) to `logs/analysis.log`. **Dependency**: Must run after T021.

### Tests for User Story 2

- [ ] T022 [US2] Unit test for Shannon/Simpson/Chao1 calculation in `tests/unit/test_diversity.py`.
- [ ] T023 [US2] Unit test for Pearson/Spearman auto-switch logic (skewness/Shapiro-Wilk) and logging of the switch in `tests/unit/test_correlation.py`.
- [ ] T024 [US2] Unit test for Benjamini-Hochberg correction in `tests/unit/test_correlation.py`.
- [ ] T025 [US2] Contract test validating `data/results/correlation_results.json` against `contracts/analysis_output.schema.yaml` in `tests/contract/test_schemas.py`. **Prerequisite**: Must run after T021 completes. Verify keys: `correlation_coefficient`, `p_value`, `adjusted_p_value`, `confidence_interval`, `r_squared`, `delta_r_squared` exist and are numeric.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Visualization and Power Estimation (Priority: P3)

**Goal**: Generate visualizations of diversity by cognitive quartiles and calculate power/sample size for future studies.

**Independent Test**: Run viz module on sample data; verify plots render and power output includes effect size and required N for [deferred] power.

### Implementation for User Story 3

- [ ] T026 [US3] Implement `src/viz/plots.py` to generate boxplots of alpha diversity stratified by cognitive flexibility quartiles (Q1-Q4). **Dependency**: Must run after T021 produces results.
- [ ] T027 [US3] Implement `src/power/estimation.py` to calculate required sample size for 80% power at α = 0.05. **Logic**: Read the observed effect size from `data/results/correlation_results.json` (T021 output). **Constraint**: If `observed_effect_size` is NaN or zero (using `np.isnan()` or `np.isclose()`), **DO NOT** use a literature-derived fallback. Instead, report `required_sample_size` as "N/A" and `fallback_reason` as "Null Hypothesis Detected (Zero Effect)". This calculation must explicitly target the 80% power threshold (SC-003). **Output**: Save `data/results/power_analysis.json` with `required_sample_size` and `fallback_reason`. **JSON Structure**: `{"required_sample_size": number | "N/A", "fallback_reason": string, "observed_effect_size": number}`. **Dependency**: Must run after T018 (Alpha Correlation Results).
- [ ] T027b [US3] Implement validation in `src/power/estimation.py` or a dedicated test `tests/unit/test_power_threshold.py` to validate the calculated power against the 0.80 threshold as required by SC-003. **Action**: Log the power status (Pass/Fail) to `logs/power.log`. **Dependency**: Must run after T027.
- [ ] T030 [US3] Generate summary table in `data/results/summary_table.csv` with effect sizes, CIs, and adjusted p-values. **Dependency**: Must run after T021, T027.

### Tests for User Story 3

- [ ] T031 [US3] Unit test for power calculation logic in `tests/unit/test_power.py`.
- [ ] T032 [US3] Integration test verifying plot generation in `tests/integration/test_viz.py`.
- [ ] T033 [US3] Unit test for power estimation module output: Verify `required_sample_size` is calculated correctly for a given effect size in `tests/unit/test_power.py`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Final Validation & Polish (Addressing Reviewer Concerns)

**Purpose**: Cross-cutting concerns, final aggregation, end-to-end validation, and **System 2 Scrubbing** for lurking variables as requested by Daniel Kahneman review.

- [ ] T034 [US2] Generate specific synthetic dataset with known independence for Null Hypothesis validation. **Dependency**: Must run after T008.
- [ ] T035 [US2] Run full pipeline on generated data and assert p > 0.05 in `tests/unit/test_null_hypothesis.py`. **Dependency**: Must run after T034, T018, T019, and T021.
- [ ] T036 [US2] Aggregate results from T021 (correlation) and T027 (power) into a single canonical `data/results/statistical_results.json` (enforcing Single Source of Truth). **Action**: Merge T021 output and T027 output, preserving keys: `correlation_coefficient`, `p_value`, `adjusted_p_value`, `confidence_interval`, `r_squared`, `delta_r_squared`, `required_sample_size`. **JSON Structure**: `{"correlation_results": {...}, "power_results": {...}}`. **Dependency**: Must run after T021 and T027.
- [ ] T037a [P] Code cleanup for Memory Efficiency: Refactor data loading to use chunking if necessary; profile memory usage.
- [ ] T037b [P] Code cleanup for CPU Efficiency: Optimize loops and vectorized operations; profile CPU usage.
- [ ] T038 [P] Run full pipeline validation in `tests/integration/test_pipeline.py` to ensure end-to-end reproducibility.
- [ ] T039 [P] Additional unit tests for edge cases (zero variance, extreme skewness).
- [ ] T040a [P] Run `quickstart.md` execution: Execute the quickstart guide to ensure it runs successfully.
- [ ] T040b [P] Generate validation report for `quickstart.md` execution.
- [ ] T041a [P] Update `README.md` with installation instructions.
- [ ] T041b [P] Update `README.md` with usage examples.
- [ ] T042 [US2] Implement a validation step in `src/analysis/correlation.py` or a dedicated test `tests/unit/test_scope_control.py` that asserts the regression model **ONLY** includes the spec-defined covariates: `age`, `sex`, `BMI`, `dietary_fiber_intake`, `antibiotic_use_history`. **Prerequisite**: Must run after T013 (to ensure schema is stable) and T019. **Action**: If any other covariates are detected in the model formula, raise an error. **Dependency**: Must run after T013 and T019.
- [ ] T043 [US3] Add a specific validation test in `tests/unit/test_confounding.py`. Assert that `delta_coefficient` for the diversity term is < 0.1 between Model 1 and Model 3. If >= 0.1, log a warning that covariates confound the result. **Note**: This task depends on T029 and is **NOT** parallel-safe. **Dependency**: Must run after T029.
- [ ] T044 [US2] **System 2 Scrubbing**: Implement `src/sensitivity/confounding.py` to calculate the shift in correlation coefficient between the raw model and the full covariate-adjusted model. **Action**: Compare the calculated shift against `2 * SE` (two standard errors) to identify potential statistical artifacts. Generate a specific warning log entry if the shift exceeds `2 * SE`. **Constraint**: Use ONLY spec-defined covariates. **Dependency**: Must run after T019 and T029.
- [ ] T045 [US2] **Robustness Check**: Implement `src/sensitivity/confounding.py` to generate subset models by sequentially removing each allowed covariate (age, sex, BMI, dietary_fiber_intake, antibiotic_use_history) from the full model. Calculate the delta coefficients for each subset model compared to the full model. Generate the robustness report verifying that the pipeline correctly identifies if the result is unstable when a specific allowed covariate is removed. **Constraint**: Use ONLY spec-defined covariates. **Dependency**: Must run after T019 and must run before T036.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Final Validation (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
 - **T010 (Ingestion) depends on T008 (Synthetic Gen) producing `data/raw/synthetic_data.csv`**.
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 output (filtered cohort)
 - T034/T035 (Null Hypothesis Test) depends on T018 (Correlation) and T019 (Regression) and T021 (Results Saved)
 - T025 (Schema Validation) depends on T021 (Results Saved)
 - **T042 (Scope Control) depends on T013 (Filtering) and T019 (Regression) to verify only approved covariates are used.**
 - **T045 (Robustness Check) depends on T019 (Regression) to establish the baseline correlation before performing robustness checks.**
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 output (results)
 - T027 (Power Estimation) depends on T018 (Alpha Correlation Results) and can run in parallel with T026 (Viz)
 - T029 (Stepwise Confounding) depends on T019 (Regression)
- **Phase 6 (Final Validation)**:
 - T036 (Aggregation) depends on T021 and T027
 - T034/T035 (Null Hypothesis) depends on completion of US1 and US2
 - T043 (Confounder Validation) depends on T029
 - **T044 (System 2 Scrubbing) depends on T019 (Regression) and T029 (Stepwise Analysis) to perform the final artifact check.**
 - **T045 (Robustness Check) depends on T019 (Regression) and must run before T036 (Aggregation) to ensure the final report includes the robustness check.**

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Contracts before services
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
# Launch all tests for User Story 1 together (after implementation exists):
Task: "Unit test for age filtering logic in tests/unit/test_filtering.py"
Task: "Unit test for null-value exclusion in tests/unit/test_filtering.py"

# Launch implementation tasks (sequential due to data flow):
Task: "Implement src/data/synthetic_gen.py" -> "Implement src/data/ingestion.py" -> "Implement src/data/filtering.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Synthetic Gen + Filtering)
4. **STOP and VALIDATE**: Test US1 independently (Null Hypothesis check)
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
 - Developer A: User Story 1 (Data Pipeline)
 - Developer B: User Story 2 (Analysis Logic)
 - Developer C: User Story 3 (Viz & Power)
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
- **Critical Constraint**: All tasks must run on CPU-only CI with a limited number of cores and constrained RAM.

The research question remains: [Research Question].
The method remains: [Method].
References: [References]. No GPU, no 8-bit quantization, no large models.
- **Data Integrity**: All data is synthetic (Null Hypothesis) for this validation phase. No real UK Biobank data is used until the pipeline is proven.
- **Single Source of Truth**: T036 ensures a single canonical results file.
- **Null Hypothesis Validation**: T035 explicitly validates the pipeline returns p > 0.05 for independent variables.
- **Power Estimation Validation**: T027 uses a literature-derived effect size (r=0.15) as a fallback if observed effect is NaN/zero, aligning with Plan.md.
- **Confounding Control (Revision)**: T029 explicitly addresses the "System 1 vs System 2" review concern by performing stepwise sensitivity analysis using ONLY the spec-defined covariates (age, sex, BMI, dietary_fiber_intake, antibiotic_use_history) to ensure correlations are not artifacts of these factors.
- **Scope Control (Revision)**: T042 explicitly verifies that ONLY the spec-defined covariates are used, resolving the scope creep concern.
- **System 2 Scrubbing (New)**: T044 explicitly addresses the "Lurking Variable" check by implementing a final check that quantifies the shift in correlation coefficients relative to standard error (2 * SE) when full covariate adjustment is applied, ensuring the observed effect is not merely a statistical artifact of lifestyle factors within the allowed set.
- **Robustness Check (New)**: T045 addresses the Kahneman review's specific warning about "plausible stories" by explicitly testing the pipeline's ability to detect instability when individual allowed covariates are removed, ensuring the system does not blindly accept a correlation without rigorous scrutiny of potential confounders within the defined scope.