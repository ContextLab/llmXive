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

- [ ] T001 [P] Initialize Project Structure: Create `src/`, `tests/`, `data/raw`, `data/processed`, `data/results`, `logs/` directories at repository root.
- [X] T002 [P] Configure Dependencies & Logging: Initialize `requirements.txt` with pinned dependencies (pandas, scikit-learn, scipy, statsmodels, biom-format, numpy, matplotlib, seaborn, pyyaml, scikit-bio). Configure linting (ruff) and formatting (black). Initialize Python logging configuration in `src/utils/logging_config.py` to set up the root logger writing to `logs/pipeline.log`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin. Includes schema definitions and data generation logic.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T003 [P] Create `contracts/dataset.schema.yaml` defining entities with exact fields: `participant_id` (str, PK), `age` (int, >=0), `sex` (enum), `bmi` (float), `cognitive_flexibility_score` (float), `shannon_diversity` (float), `simpson_diversity` (float), `chao1` (float), `dietary_fiber` (float), `antibiotic_use` (bool). **Note**: Strictly adhere to spec.md FR-002 covariates. Do NOT include SES or dietary_pattern fields.
- [ ] T004 [P] Create `contracts/analysis_output.schema.yaml` defining `AnalysisResult` entity with exact fields: `test_type` (str), `metric_name` (str), `correlation_coefficient` (float), `p_value` (float), `adjusted_p_value` (float), `confidence_interval` (array[float, float]), `r_squared` (float).
- [ ] T005 [P] Implement `src/utils/config.py` with fixed random seeds and path configurations.
- [ ] T006 [P] Setup `pytest` configuration and test directory structure.
- [X] T007 [P] Implement `src/utils/validation.py` to enforce schema contracts.
- [ ] T008 [P] Implement `src/data/synthetic_gen.py` to generate synthetic data with fixed seeds. Explicitly generate `cognitive_flexibility_score` and `shannon_diversity` as statistically independent (Null Hypothesis). Ensure data types match `contracts/dataset.schema.yaml`. Output to `data/raw/synthetic_data.csv`.
- [ ] T009 [P] Validate `contracts/dataset.schema.yaml` against the generated synthetic data in `data/raw/synthetic_data.csv` to ensure strict type enforcement (int, float, bool, enum).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Cohort Filtering (Priority: P1) 🎯 MVP

**Goal**: Ingest synthetic 16S and cognitive data, filter for age >= 65 with complete data, and validate against schema.

**Independent Test**: Run ingestion on a small synthetic dataset with mixed ages and missing values; verify output contains ONLY rows matching age >= 65 and non-null metrics.

### Implementation for User Story 1

- [ ] T010 [US1] Implement `src/data/ingestion.py` to ingest 16S rRNA sequencing data and linked cognitive assessment data from `data/raw` (synthetic). **Logic**: Load synthetic 16S rRNA sequencing data and linked cognitive assessment data from `data/raw/synthetic_data.csv`. Merge on `participant_id` as per FR-001. Validate output against `contracts/dataset.schema.yaml`.
- [ ] T011 [US1] Implement `src/data/filtering.py` to filter for age >= 65, non-null Shannon/Cognitive scores, and required covariates (age, sex, BMI, dietary_fiber, antibiotic_use). **Action**: Save output to `data/processed/filtered_cohort.csv`.
- [X] T012 [US1] Add logic in `src/data/filtering.py` to handle zero-variance datasets by flagging and skipping correlation (Edge Case).
- [ ] T013 [US1] Implement listwise deletion for missing covariates in `src/data/filtering.py`. **Action**: Log the count of dropped rows to `logs/filtering.log` using the logger initialized in T002. **Constraint**: Strictly use listwise deletion for covariates defined in `contracts/dataset.schema.yaml` (age, sex, BMI, dietary_fiber, antibiotic_use). Do NOT attempt to handle SES or dietary_pattern as these are not in the schema.

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T014 [US1] Unit test for age filtering logic in `tests/unit/test_filtering.py`. **Prerequisite**: Must run after T011 implementation exists.
- [X] T015 [US1] Unit test for null-value exclusion in `tests/unit/test_filtering.py`.
- [ ] T016 [US1] Contract test validating `data/processed/filtered_cohort.csv` against `contracts/dataset.schema.yaml` in `tests/contract/test_schemas.py`. **Prerequisite**: Must run after T011 completes. Verify all rows have non-null `age`, `shannon_diversity`, `cognitive_flexibility_score`, and required covariates (age, sex, BMI, fiber, antibiotics). <!-- FAILED: unspecified -->

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Diversity Metric Calculation and Correlation Analysis (Priority: P2)

**Goal**: Calculate alpha/beta diversity, perform correlation/regression with covariates, apply FDR correction, and handle non-normality.

**Independent Test**: Provide pre-calculated metrics and scores; verify correlation coefficients match manual calculation, regression converges, and FDR is applied.

### Implementation for User Story 2

- [ ] T017 [US2] Implement `src/analysis/diversity.py` to calculate Alpha (Shannon, Simpson, Chao1) and Beta (Bray-Curtis, UniFrac) metrics from the filtered cohort.
- [ ] T018 [US2] Implement `src/analysis/correlation.py` to perform Pearson/Spearman correlation (auto-switch if skewness > 1.0 or Shapiro-Wilk p < 0.05) with a specified confidence interval. **Action**: Apply Benjamini-Hochberg correction to alpha diversity correlation p-values (FR-004) and output `adjusted_p_value` for each. Log the switch logic.
- [ ] T019 [US2] Implement `src/analysis/correlation.py` to run Linear Regression (Cognitive ~ Diversity + Covariates). **Covariates**: age, sex, BMI, dietary_fiber, antibiotic_use (Strictly as per spec FR-002). **Action**: Calculate R-squared and compare against a baseline model (covariates only) as per SC-002. Apply Benjamini-Hochberg correction to regression p-values.
- [ ] T020 [US2] Implement `src/analysis/beta_diversity.py` to perform PERMANOVA (using `skbio.stats.distance.permanova`) for Beta diversity. **Action**: Handle heavily skewed cognitive distributions by using db-RDA or PERMANOVA on cognitive quartiles, as per Spec Edge Cases.
- [ ] T021 [US2] Save `data/results/correlation_results.json` containing coefficients, p-values, adjusted p-values, CIs, and R-squared, verifying keys: `correlation_coefficient`, `p_value`, `adjusted_p_value`, `confidence_interval`, `r_squared` against `contracts/analysis_output.schema.yaml`.

### Tests for User Story 2

- [ ] T022 [US2] Unit test for Shannon/Simpson/Chao1 calculation in `tests/unit/test_diversity.py`.
- [ ] T023 [US2] Unit test for Pearson/Spearman auto-switch logic (skewness/Shapiro-Wilk) and logging of the switch in `tests/unit/test_correlation.py`.
- [ ] T024 [US2] Unit test for Benjamini-Hochberg correction in `tests/unit/test_correlation.py`.
- [ ] T025 [US2] Contract test validating `data/results/correlation_results.json` against `contracts/analysis_output.schema.yaml` in `tests/contract/test_schemas.py`. **Prerequisite**: Must run after T021 completes. Verify keys: `correlation_coefficient`, `p_value`, `adjusted_p_value`, `confidence_interval`, `r_squared` exist and are numeric.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Visualization and Power Estimation (Priority: P3)

**Goal**: Generate visualizations of diversity by cognitive quartiles and calculate power/sample size for future studies.

**Independent Test**: Run viz module on sample data; verify plots render and power output includes effect size and required N for [deferred] power.

### Implementation for User Story 3

- [ ] T026 [US3] Implement `src/viz/plots.py` to generate boxplots of alpha diversity stratified by cognitive flexibility quartiles (Q1-Q4).
- [ ] T027 [US3] Implement `src/power/estimation.py` to calculate required sample size for 80% power at α = 0.05. **Logic**: Read the observed effect size from `data/results/correlation_results.json` (T021 output). If `observed_effect_size` is NaN or zero (using `np.isnan()` or `np.isclose()`), fallback to a literature-derived effect size (r=0.15) with a logged warning. **Dependency**: Must run after T021.
- [ ] T028 [US3] Implement `src/sensitivity/confounding.py` to calculate E-values manually using `scipy` and `statsmodels`. Perform negative control test by randomly permuting diversity scores multiple times and re-running the regression to verify the null distribution centers at zero.
- [ ] T029 [US3] Implement stepwise sensitivity analysis in `src/sensitivity/confounding.py`: Run Model 1 (~Diversity), Model 2 (~Diversity + Age), Model 3 (~Diversity + Age + Sex + BMI + Fiber + Antibiotics). Calculate and log `delta_coefficient` = |beta_Model_N - beta_Model_1| for the diversity term. **Constraint**: Use ONLY spec-defined covariates.
- [ ] T030 [US3] Generate summary table in `data/results/summary_table.csv` with effect sizes, CIs, and adjusted p-values.

### Tests for User Story 3

- [ ] T031 [US3] Unit test for power calculation logic in `tests/unit/test_power.py`.
- [ ] T032 [US3] Integration test verifying plot generation in `tests/integration/test_viz.py`.
- [ ] T033 [US3] Unit test for power estimation module output: Verify `required_sample_size` is calculated correctly for a given effect size in `tests/unit/test_power.py`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Final Validation & Polish

**Purpose**: Cross-cutting concerns, final aggregation, and end-to-end validation

- [ ] T034 [US2] Generate specific synthetic dataset with known independence for Null Hypothesis validation.
- [ ] T035 [US2] Run full pipeline on generated data and assert p > 0.05 in `tests/unit/test_null_hypothesis.py`.
- [ ] T036 [US2] Aggregate results from T021 (correlation) and T027 (power) into a single canonical `data/results/statistical_results.json` (enforcing Single Source of Truth).
- [ ] T037 [P] Code cleanup and refactoring for CPU/memory efficiency.
- [ ] T038 [P] Run full pipeline validation in `tests/integration/test_pipeline.py` to ensure end-to-end reproducibility.
- [ ] T039 [P] Additional unit tests for edge cases (zero variance, extreme skewness).
- [ ] T040 [P] Run `quickstart.md` validation.
- [ ] T041 [P] Update `README.md` with installation instructions and usage examples.
- [ ] T042 [US2] Implement a validation step in `src/analysis/correlation.py` or a dedicated test `tests/unit/test_scope_control.py` that asserts the regression model DOES NOT include `SES` or `dietary_pattern` as covariates, but MUST include `dietary_fiber`. **Prerequisite**: Must run after T013 (to ensure schema is stable) and T019. **Action**: If unapproved covariates are detected, raise an error.
- [ ] T043 [US3] Add a specific validation test in `tests/unit/test_confounding.py`. Assert that `delta_coefficient` for the diversity term is < 0.1 between Model 1 and Model 3. If >= 0.1, log a warning that covariates confound the result. **Note**: This task depends on T029 and is NOT parallel-safe.
- [ ] T044 [US2] Implement a final validation step in `src/sensitivity/confounding.py` to explicitly document the "Lurking Variable" check. This task generates a report comparing the raw correlation coefficient against the coefficient after full covariate adjustment. It must calculate the shift relative to the standard error and log a warning if the shift exceeds a statistically significant threshold, indicating a potential statistical artifact. **Constraint**: This task must run after T019 and T029.

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
 - **T042 (Scope Control) depends on T013 (Filtering) and T019 (Regression) to verify no unapproved covariates are used.**
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 output (results)
 - T027 (Power Estimation) depends on T021 (Results Saved) and can run in parallel with T026 (Viz)
 - T028 (Sensitivity) depends on T021 (Results Saved)
 - T029 (Stepwise Confounding) depends on T019 (Regression)
- **Phase 6 (Final Validation)**:
 - T036 (Aggregation) depends on T021 and T027
 - T034/T035 (Null Hypothesis) depends on completion of US1 and US2
 - T043 (Confounder Validation) depends on T029
 - **T044 (System 2 Scrubbing) depends on T019 (Regression) and T029 (Stepwise Analysis) to perform the final artifact check.**

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
- **Confounding Control (Revision)**: T029 explicitly addresses the "System 1 vs System 2" review concern by performing stepwise sensitivity analysis using ONLY the spec-defined covariates (age, sex, BMI, fiber, antibiotics) to ensure correlations are not artifacts of these factors.
- **Scope Control (Revision)**: T042 explicitly verifies that no unapproved covariates (SES, dietary_pattern) are introduced into the regression model, resolving the scope creep concern.
- **System 2 Scrubbing (New)**: T044 explicitly addresses the "Lurking Variable" check by implementing a final check that quantifies the shift in correlation coefficients relative to standard error when full covariate adjustment is applied, ensuring the observed effect is not merely a statistical artifact of lifestyle factors.