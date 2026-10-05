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

## Phase 0: Spec Amendment, Schema Recovery & Setup (Critical Prerequisite)

**Purpose**: Resolve contradiction between FR-001 (UK Biobank) and Plan (Synthetic Data). Ensure missing schemas are recovered. Establish data contracts before generation.

- [ ] T001 [P] **Formal Spec Amendment**: Update `spec.md` to replace FR-001 (Ingest UK Biobank) with "Ingest Synthetic Data for Pipeline Validation". Explicitly document that the project is a "Pipeline Validation Study" using a Null Hypothesis dataset. Update the "Assumptions" section to reflect that real UK Biobank data is unavailable. **Dependency**: Aligns with `plan.md` "Amended Scope". **Deliverable**: Commit updated `spec.md` with FR-001 amended to Synthetic Data Ingestion.
- [ ] T004a [P] **Recover Missing Schemas**: Verify existence of `contracts/raw_otu.schema.yaml`, `contracts/dataset.schema.yaml`, and `contracts/analysis_output.schema.yaml`. If missing, create them immediately based on the definitions below. **Constraint**: This task MUST complete before T009 can execute. **Deliverable**: Verified presence of all three schema files.
- [ ] T004b [P] **Create Raw OTU Schema**: Create `contracts/raw_otu.schema.yaml` defining the raw OTU/ASV table structure required for diversity calculation. Fields: `sample_id`, `otu_id`, `count`. **Note**: This is the source for diversity calculation (T018a).
- [ ] T004c [P] **Create Processed Cohort Schema**: Create `contracts/dataset.schema.yaml` defining the *processed* cohort with derived metrics. Fields: `participant_id` (str, PK), `age` (int, >=65), `sex` (enum), `bmi` (float), `cognitive_flexibility_score` (float), `shannon_diversity` (float), `simpson_diversity` (float), `chao1` (float), `dietary_fiber` (float), `antibiotic_use` (bool). **Note**: Strictly adhere to spec.md FR-002 covariates. Include ONLY the fields listed in spec.md FR-002. Field names must use snake_case (e.g., `dietary_fiber`) to match the regression logic.
- [ ] T005b [P] **Create Analysis Output Schema**: Create `contracts/analysis_output.schema.yaml` defining `AnalysisResult` entity with exact fields: `test_type` (str), `metric_name` (str), `correlation_coefficient` (float), `p_value` (float), `adjusted_p_value` (float), `confidence_interval` (array[float, float]), `r_squared` (float), `r_squared_baseline` (float).
- [ ] T002a [P] **Initialize Project Directories**: Create `src/`, `tests/`, `data/raw`, `data/processed`, `data/results`, `logs/` directories at repository root. **Command**: `mkdir -p src/analysis src/data src/viz src/power src/sensitivity src/utils tests/unit tests/integration tests/contract data/raw data/processed data/results logs`.
- [ ] T002b [P] **Initialize Python Packages**: Create `__init__.py` files in `src/`, `src/analysis`, `src/data`, `src/viz`, `src/power`, `src/sensitivity`, `src/utils`, `tests/`, `tests/unit`, `tests/integration`, `tests/contract`. **Command**: `touch src/__init__.py src/analysis/__init__.py...`.
- [ ] T003a [P] **Configure Dependencies**: Initialize `requirements.txt` with pinned dependencies (pandas, scikit-learn, scipy, statsmodels, biom-format, numpy, matplotlib, seaborn, pyyaml, scikit-bio). **Deliverable**: `requirements.txt` with exact versions.
- [ ] T003b [P] **Configure Logging & Linting**: Initialize `pyproject.toml` for linting (ruff) and formatting (black). Initialize Python logging configuration in `src/utils/logging_config.py` to set up the root logger writing to `logs/pipeline.log`. **Deliverable**: `pyproject.toml` and `src/utils/logging_config.py`.
- [ ] T006 [P] **Implement Config Module**: Implement `src/utils/config.py` with fixed random seeds and path configurations. **Specifics**: Define `RANDOM_SEED = 42`, `DATA_PATH = "data/raw"`, and function `set_seed(seed=RANDOM_SEED)`.
- [ ] T007 [P] **Setup Pytest Configuration**: Create `pytest.ini` with `testpaths = tests`, `python_files = test_*.py`, `python_functions = test_*`. **Deliverable**: `pytest.ini`.
- [ ] T008 [P] **Implement Validation Module**: Implement `src/utils/validation.py` to enforce schema contracts using `jsonschema` or `pydantic`.

---

## Phase 1: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin. Includes data generation logic.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T009 [US1] **Implement Synthetic Data Generator (Null Hypothesis)**: Implement `src/data/synthetic_gen.py` to generate synthetic data with fixed seeds (42). **Logic**: 
    1. **Generate Raw OTU Table**: Create `data/raw/otu_table.csv` with random counts (independent of cognitive scores).
    2. **Calculate Alpha Diversity**: Calculate Shannon, Simpson, and Chao1 from the OTU table.
    3. **Generate Demographics**: Create participant demographics and cognitive scores (statistically independent of diversity).
    4. **Merge & Validate**: Merge all data into `data/raw/synthetic_data.csv`.
    5. **Self-Check**: Assert that `simpson_diversity` and `chao1` columns are present, non-null, and match the schema in `contracts/dataset.schema.yaml` BEFORE writing the file. If validation fails, raise an exception.
    **Dependency**: Must run after T001, T004a, T004b, T004c, T005b. **Deliverable**: `data/raw/synthetic_data.csv` and `data/raw/otu_table.csv` with checksums.

---

## Phase 2: User Story 1 - Data Ingestion and Cohort Filtering (Priority: P1) 🎯 MVP

**Goal**: Ingest synthetic 16S and cognitive data, filter for age >= 65 with complete data, and validate against schema.

**Independent Test**: Run ingestion on a small synthetic dataset with mixed ages and missing values; verify output contains ONLY rows matching age >= 65 and non-null metrics.

### Tests for User Story 1 (TDD: Write First)

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation. Depends on T009 (Data Generation).**

- [ ] T013 [US1] **Write Unit Test: Age Filtering**: Write unit test `test_filter_age_65` in `tests/unit/test_filtering.py`. **Prerequisite**: T009 (Data exists). Verify output contains ONLY rows with age >= 65.
- [ ] T014 [US1] **Write Unit Test: Null Exclusion**: Write unit test `test_filter_null_values` in `tests/unit/test_filtering.py`. **Prerequisite**: T009. Verify participants with missing cognitive scores or covariates are excluded.
- [ ] T015 [US1] **Write Unit Test: Zero Variance**: Write unit test `test_zero_variance_handling` in `tests/unit/test_filtering.py`. **Prerequisite**: T009. Verify that "ZERO_VARIANCE_DETECTED" is logged and a status flag is written if data has no variance.

### Implementation for User Story 1

- [ ] T016 [US1] **Implement Ingestion & Filtering**: Implement `src/data/ingestion.py` and `src/data/filtering.py` to ingest synthetic data from `data/raw/synthetic_data.csv`, merge on `participant_id`, and filter for age >= 65, non-null Shannon/Cognitive scores, and required covariates. **Logic**: Save output to `data/processed/filtered_cohort.csv`. **Edge Case Handling**: If the dataset has zero variance (all samples identical diversity), log "ZERO_VARIANCE_DETECTED" to `logs/filtering.log` AND write a status flag to `data/results/zero_variance_flag.json` with `{"status": "skipped", "reason": "zero_variance"}`. Return an empty dataframe with the correct schema. Do NOT attempt correlation on this data. **Constraint**: Strictly use listwise deletion for covariates defined in `contracts/dataset.schema.yaml`. **Prerequisite**: T013, T014, T015 (Test files must exist).
- [ ] T017 [US1] **Contract Test: Filtered Cohort**: Validate `data/processed/filtered_cohort.csv` against `contracts/dataset.schema.yaml` in `tests/contract/test_schemas.py`. **Prerequisite**: Must run after T016 completes. Verify all rows have non-null `age`, `shannon_diversity`, `cognitive_flexibility_score`, and required covariates. **Success Criteria**: assert pytest returns 0 and schema compliance is verified.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 3: User Story 2 - Diversity Metric Calculation and Correlation Analysis (Priority: P2)

**Goal**: Calculate alpha/beta diversity, perform correlation/regression with covariates, apply FDR correction, and handle non-normality.

**Independent Test**: Provide pre-calculated metrics and scores; verify correlation coefficients match manual calculation, regression converges, and FDR is applied.

### Implementation for User Story 2

- [ ] T018a [US2] **Implement Alpha Diversity Calculation**: Implement `src/analysis/diversity.py` to calculate Alpha (Shannon, Simpson, Chao1) from `data/raw/otu_table.csv`. **Signature**: `calculate_alpha(otu_df: pd.DataFrame) -> dict`. **Input**: `data/raw/otu_table.csv`. **Output**: Append to `data/processed/diversity_metrics.csv`.
- [ ] T018b [US2] **Implement Beta Diversity Calculation**: Implement `src/analysis/diversity.py` to calculate Beta (Bray-Curtis, Weighted UniFrac) from `data/raw/otu_table.csv`. **Signature**: `calculate_beta(otu_df: pd.DataFrame) -> pd.DataFrame`. **Input**: `data/raw/otu_table.csv`. **Output**: Append to `data/processed/diversity_metrics.csv` as a distinct matrix or summary table.
- [ ] T018c [US2] **Save Beta Metrics**: Ensure `data/processed/diversity_metrics.csv` contains the calculated Beta diversity matrices. **Dependency**: T018b.
- [ ] T019 [US2] **Implement Correlation Analysis**: Implement `src/analysis/correlation.py` to perform Pearson/Spearman correlation (auto-switch if skewness > 1.0 or Shapiro-Wilk p < 0.05) with a specified confidence interval. **Action**: Apply Benjamini-Hochberg correction to alpha diversity correlation p-values (FR-004) and output `adjusted_p_value` for each. Log the switch logic.
- [ ] T020b [US2] **Baseline Model Comparison**: Implement baseline model (Cognitive ~ Covariates Only) to calculate R-squared for the null model. **Action**: Calculate R-squared and compare against a baseline model (covariates only) as per SC-002. **Output**: Add `r_squared_baseline` to results. **Prerequisite**: None.
- [ ] T020 [US2] **Implement Linear Regression**: Implement `src/analysis/correlation.py` to run Linear Regression (Cognitive ~ Diversity + Covariates). **Covariates**: age, sex, BMI, dietary_fiber, antibiotic_use (Strictly as per spec FR-002). **Action**: Calculate R-squared and compare against baseline (T020b). Apply Benjamini-Hochberg correction to regression p-values. **Dependency**: T020b (Baseline Model).
- [ ] T021 [US2] **Implement Beta Diversity Analysis**: Implement `src/analysis/beta_diversity.py` to perform PERMANOVA on continuous cognitive scores. **Logic**: Perform PERMANOVA on continuous cognitive scores by default. **Edge Case Handling**: If the cognitive flexibility score distribution is heavily skewed (skewness > 1.0 OR Shapiro-Wilk p < 0.05), log the skewness and switch to non-parametric permutation test (NOT binning) as per FR-005. **Constraint**: Do NOT use quartile binning. Do NOT use db-RDA unless explicitly authorized by the spec. **Prerequisite**: T018c (Beta Metrics).
- [ ] T022 [US2] **Save Correlation Results**: Save `data/results/correlation_results.json` containing coefficients, p-values, adjusted p-values, CIs, and R-squared, verifying keys: `correlation_coefficient`, `p_value`, `adjusted_p_value`, `confidence_interval`, `r_squared`, `r_squared_baseline` against `contracts/analysis_output.schema.yaml`.

### Tests for User Story 2

- [ ] T023 [US2] **Unit Test: Diversity Calculation**: Unit test for Shannon/Simpson/Chao1 calculation in `tests/unit/test_diversity.py`. Function: `test_alpha_diversity_values`.
- [ ] T024 [US2] **Unit Test: Correlation Switch**: Unit test for Pearson/Spearman auto-switch logic (skewness/Shapiro-Wilk) and logging of the switch in `tests/unit/test_correlation.py`. Function: `test_correlation_switch_logic`.
- [ ] T025 [US2] **Unit Test: FDR Correction**: Unit test for Benjamini-Hochberg correction in `tests/unit/test_correlation.py`. Function: `test_benjamini_hochberg_correction`.
- [ ] T025b [US2] **Validate FDR Threshold**: Validate that the FDR is measured against the 0.05 threshold as required by SC-004. Function: `test_fdr_threshold_validation`. **Prerequisite**: T025.
- [ ] T026 [US2] **Contract Test: Results**: Validate `data/results/correlation_results.json` against `contracts/analysis_output.schema.yaml` in `tests/contract/test_schemas.py`. **Prerequisite**: Must run after T022 completes. Verify keys exist and are numeric.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 4: User Story 3 - Visualization, Power Estimation & Sensitivity Analysis (Priority: P3)

**Goal**: Generate visualizations, calculate power, and perform rigorous sensitivity analysis to rule out confounding artifacts.

**Independent Test**: Run viz module on sample data; verify plots render and power output includes effect size. Run sensitivity analysis to verify stability of coefficients.

### Implementation for User Story 3

- [ ] T027a [US3] **Implement Boxplot Visualization**: Implement `src/viz/plots.py` to generate boxplots of alpha diversity stratified by cognitive flexibility quartiles (Q1-Q4). **Output**: `data/results/alpha_diversity_boxplot.png`.
- [ ] T027b [US3] **Implement Scatter Plot Visualization**: Implement `src/viz/plots.py` to generate correlation scatter plots (Diversity vs Cognitive Score). **Output**: `data/results/correlation_scatter.png`.
- [ ] T027c [US3] **Implement Regression Diagnostics**: Implement `src/viz/plots.py` to generate regression diagnostic plots (Residuals vs Fitted, Q-Q Plot). **Output**: `data/results/regression_diagnostics.png`.
- [ ] T041a [US3] **Implement Positive Control Generator**: Implement `src/data/synthetic_gen.py` (or new module) to generate a dataset with a known non-zero correlation (r=0.3) for power validation. **Logic**: **Scope**: This dataset is for Power Validation ONLY. It must NOT be used for the primary Null Hypothesis results. Tag output as "positive_control". **Constraint**: Must not violate FR-001 (Null Hypothesis) for the main pipeline. **Output**: `data/raw/positive_control_data.csv`.
- [ ] T041b [US3] **Positive Control Power Validation**: Run power estimation on the positive control dataset (T041a) and verify the calculated power meets the conventional threshold for adequate statistical power for a future study (SC-003). **Output**: `data/results/power_validation_report.json`. **Prerequisite**: T041a.
- [ ] T041 [US3] **Implement Power Estimation**: Implement `src/power/estimation.py` to calculate required sample size for 80% power at α = 0.05. **Logic**: Read the observed effect size from `data/results/correlation_results.json` (T022 output). **Constraint**: If the observed effect size is zero or NaN, report the calculated power based on the null result and log a warning. **Dependency**: T041b (Positive Control).
- [ ] T044a [US3] **Implement Confounder Data Generator**: Implement `src/data/synthetic_gen.py` (or new module) to generate a dataset with a "Lurking Variable" (SES proxy) that correlates with both diversity and cognition. **Logic**: **Scope**: This is a Negative Control test. The generated data contains SES, but the analysis script must NOT include SES in the regression model unless explicitly overridden for this specific test run. The main pipeline must remain SES-free. **Constraint**: Explicitly cite FR-002 Exclusion to ensure SES is not accidentally included in the main analysis. **Output**: `data/raw/confounder_data.csv`.
- [ ] T044 [US3] **Implement Sensitivity Confounder Injection**: Run the analysis pipeline on the confounder data (T044a) to verify that the pipeline correctly identifies the correlation as confounded or that the effect size changes drastically when the common cause is controlled for (if controllable). **Goal**: Verify that the pipeline correctly identifies the correlation as confounded or that the effect size changes drastically when the common cause is controlled for. This directly addresses the "Sensitivity & Validation" requirement (Plan Section; Constitution Principle VII). **Output**: `data/results/confounding_sensitivity.json`. **Prerequisite**: T044a.
- [ ] T040 [US3] **Leave-One-Out Sensitivity Analysis**: Implement stepwise sensitivity analysis in `src/analysis/confounding.py`. **Logic**: Run Model 1 (~Diversity), then run multiple models excluding each single covariate individually (Model without Age, Model without Sex, Model without BMI, Model without Fiber, Model without Antibiotics). Calculate and log `delta_coefficient` = |beta_Model_Exclude_N - beta_Model_1| for the diversity term. **Constraint**: Use ONLY spec-defined covariates. **Rationale**: Addresses Constitution Principle VII requirement for "Sensitivity analyses excluding any single covariate". **Dependency**: T022 (Results Saved).
- [ ] T029 [US3] **Generate Summary Table**: Generate summary table in `data/results/summary_table.csv` with effect sizes, CIs, and adjusted p-values.
- [ ] T045 [US3] **Unit Test: Lurking Variable Injection**: Unit test for the "Lurking Variable" injection logic in `tests/unit/test_confounding.py`. Verify that when a common cause is injected, the unadjusted model shows a significant correlation, but the model controlling for the injected cause shows a reduced or null effect. **Prerequisite**: T044. **Traceability**: Plan Section: Sensitivity & Validation; Constitution Principle VII.

### Tests for User Story 3

- [ ] T031 [US3] **Unit Test: Power Logic**: Unit test for power calculation logic in `tests/unit/test_power.py`. Function: `test_power_calculation_logic`.
- [ ] T032 [US3] **Integration Test: Viz**: Integration test verifying plot generation in `tests/integration/test_viz.py`. Function: `test_plot_generation`.
- [ ] T033 [US3] **Unit Test: Power Sample Size**: Unit test for power estimation module output: Verify `required_sample_size` is calculated correctly for a given effect size in `tests/unit/test_power.py`. Function: `test_power_sample_size_calc`.
- [ ] T039 [US3] **Unit Test: Confounding Sensitivity**: Unit test for confounding sensitivity analysis in `tests/unit/test_confounding.py`. Assert that `delta_coefficient` for the diversity term is < 0.1 between Model 1 and any exclusion model. If >= 0.1, log a warning that covariates confound the result. **Note**: This task depends on T040 and is NOT parallel-safe. **Prerequisite**: T040.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 5: Final Validation & Polish

**Purpose**: Cross-cutting concerns, final aggregation, end-to-end validation, and **System 2 Scrubbing** for lurking variables as requested by Daniel Kahneman review.

- [ ] T034 [US2] **Generate Null Hypothesis Dataset**: Generate specific synthetic dataset with known independence for Null Hypothesis validation. **Parameters**: seed=42, N=1000. **Output**: `data/raw/null_hypothesis_data.csv`.
- [ ] T035 [US2] **Run Null Hypothesis Validation**: Run full pipeline on generated data (T034) and assert p > 0.05 in `tests/unit/test_null_hypothesis.py`. **Dependency**: T034, T022, T019, T020. **Note**: This task is sequential and depends on completion of US1 and US2.
- [ ] T036 [US2] **Aggregate Results**: Aggregate results from T022 (correlation) and T041 (power) into a single canonical `data/results/statistical_results.json` (enforcing Single Source of Truth). **Note**: This is for JSON aggregation only.
- [ ] T046a [US3] **Generate Null Hypothesis Validation Report**: Generate `data/results/null_hypothesis_validation_report.md` as a narrative document summarizing T035 results, confirming p > 0.05 for primary correlations, and validating pipeline robustness. **Deliverable**: Markdown report.
- [ ] T046b [US3] **Generate Power Estimation Report**: Generate `data/results/power_estimation_report.md` as a narrative document summarizing T041b results, power calculations, and sample size recommendations. **Deliverable**: Markdown report.
- [ ] T037 [P] **Run Pipeline Validation**: Run full pipeline validation in `tests/integration/test_pipeline.py` to ensure end-to-end reproducibility. **Constraint**: Verify memory usage < 7GB and runtime < 6h.
- [ ] T038 [US2] **Scope Control Validation**: Implement a validation step in `src/analysis/correlation.py` or a dedicated test `tests/unit/test_scope_control.py` that asserts the regression model DOES NOT include `SES` or `dietary_pattern` as covariates, but MUST include `dietary_fiber`. **Prerequisite**: Must run after T016 (to ensure schema is stable) and T020. **Action**: If unapproved covariates are detected, raise an error explicitly citing **FR-002 Exclusion** and **Constitution Principle VII**. **Note**: Not parallel-safe.
- [ ] T042 [P] **Run Quickstart Validation**: Execute `quickstart.md` commands and verify exit code 0. **Success Criteria**: All commands in `quickstart.md` run successfully without error.
- [ ] T043 [P] **Update README**: Update `README.md` with installation instructions and usage examples.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 0)**: No dependencies - can start immediately
- **Foundational (Phase 1)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 2+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Final Validation (Phase 5)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 1) - No dependencies on other stories
 - **T016 (Ingestion/Filtering) depends on T009 (Synthetic Gen) producing `data/raw/synthetic_data.csv`**.
 - **T016 depends on T013, T014, T015 (Test Files) to exist**.
 - **T013, T014, T015 depend on T009** (Data must exist to test filtering).
- **User Story 2 (P2)**: Can start after Foundational (Phase 1) - Depends on US1 output (filtered cohort)
 - T035 (Null Hypothesis Test) depends on T019 (Correlation) and T020 (Regression) and T022 (Results Saved)
 - T026 (Schema Validation) depends on T022 (Results Saved)
 - **T038 (Scope Control) depends on T016 (Filtering) and T020 (Regression) to verify no unapproved covariates are used.**
 - **T020b (Baseline Model) is a prerequisite for T020 and must be completed first.**
- **User Story 3 (P3)**: Can start after Foundational (Phase 1) - Depends on US2 output (results)
 - T041 (Power Estimation) depends on T022 (Results Saved) and T041b (Positive Control).
 - T040 (Sensitivity) depends on T022 (Results Saved).
 - T040 (Leave-One-Out) depends on T020 (Regression).
 - **T039 (Confounder Validation) depends on T040** (and is NOT parallel-safe).
 - **T045 (Lurking Variable Test) depends on T044 (Lurking Variable Injection)**.
- **Phase 5 (Final Validation)**:
 - T036 (Aggregation) depends on T022 and T041
 - T035 (Null Hypothesis) depends on completion of US1 and US2
 - T039 (Confounder Validation) depends on T020 (US2) and T040 (US3)
 - **T039 (Confounder Validation) depends on T020 (Regression) and T040 (Stepwise Analysis) to perform the final artifact check.**
 - **T046a (Null Report) depends on T035**.
 - **T046b (Power Report) depends on T041**.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Contracts before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 0, except T009 which depends on T004b/T004c/T005b/T001)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows), **EXCEPT**:
 - T041 (Power Estimation) and T040 (Sensitivity) in US3 depend on US2 results and cannot start until US2 is complete.
 - T039 (Confounder Validation) depends on T020 (US2) and T040 (US3).
 - T020b depends on T020 (sub-step).
 - T045 depends on T044.
 - **T035 (Null Hypothesis Validation) is a blocking task in Phase 5 and cannot run until US1 and US2 are complete.**
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members (with the exceptions noted above)

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (after implementation exists and T009 is done):
Task: "Write Unit test for age filtering logic in tests/unit/test_filtering.py (T013)"
Task: "Write Unit test for null-value exclusion in tests/unit/test_filtering.py (T014)"

# Launch implementation tasks (sequential due to data flow):
Task: "Implement src/data/synthetic_gen.py (T009)" -> "Implement src/data/ingestion.py (T016)" -> "Implement src/data/filtering.py (T016)"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 0: Spec Amendment & Schema Recovery
2. Complete Phase 1: Foundational (Synthetic Gen)
3. Complete Phase 2: User Story 1 (Synthetic Gen + Filtering)
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
 - Developer C: User Story 3 (Viz & Power & Sensitivity) - **Note**: Developer C must wait for Developer B to complete T022.
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
- **Single Source of Truth**: T036 ensures a single canonical results JSON. T046a/T046b ensure narrative reports are generated.
- **Null Hypothesis Validation**: T035 explicitly validates the pipeline returns p > 0.05 for independent variables.
- **Power Estimation Validation**: T041b validates the power calculation logic against a known signal (SC-003).
- **Confounding Control (Sensitivity Analysis)**: T040 explicitly addresses the "Sensitivity & Validation" requirement (Plan Section; Constitution Principle VII) by performing Leave-One-Out sensitivity analysis using ONLY the spec-defined covariates (age, sex, BMI, fiber, antibiotics) to ensure correlations are not artifacts of these factors.
- **Lurking Variable Injection**: T044a and T045 explicitly address the "Sensitivity & Validation" requirement by simulating a scenario where a "lurking variable" (SES) causes both gut and brain metrics, verifying the pipeline can distinguish this from a direct causal link. **Constraint**: Main pipeline remains SES-free (FR-002 Exclusion).
- **Scope Control**: T038 explicitly verifies that no unapproved covariates (SES, dietary_pattern) are introduced into the regression model, resolving the scope creep concern. **Citation**: FR-002 Exclusion, Constitution Principle VII.