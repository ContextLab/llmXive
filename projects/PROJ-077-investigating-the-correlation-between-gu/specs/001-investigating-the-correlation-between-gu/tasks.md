# Tasks: Investigating the Correlation Between Gut Microbiome Diversity and Cognitive Performance

**Input**: Design documents from `/specs/001-gene-regulation/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., User Story 1, User Story 2)
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

- [X] T001 [P] Initialize project directory structure: Execute `mkdir -p data/raw data/processed code tests` under `projects/PROJ-investigating-the-correlation-between-gu/`.

Research Question: What is the correlation between gut microbiome diversity and cognitive performance?
Method: Correlation analysis using processed data.
References: N/A

- [X] T002 [P] Initialize Python 3.11 project: Create `requirements.txt` at the repository root with pinned dependencies: `pandas==2.0.3`, `numpy==1.24.3`, `scikit-bio==0.5.9`, `scikit-learn==1.3.0`, `statsmodels==0.14.0`, `matplotlib==3.7.2`, `seaborn==0.12.2`, `pyyaml==6.0.1`, `scipy==1.11.1`.

- [X] T003a [P] Create `pyproject.toml`: Initialize the file at the repository root with basic project metadata.
- [X] T003b [P] Configure linting: Add `[tool.flake8]` and `[tool.black]` sections to `pyproject.toml` with standard configuration.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Create `code/config.py` defining paths (`INPUT_PATHS` dict), `RANDOM_SEED=42`, and `SAMPLE_LIMIT=50000` (Per Plan Complexity Tracking) to ensure CI memory safety.
- [X] T005 [P] Implement deterministic data loading utility in `code/data_utils.py` to handle chunked reading of large CSVs.
- [X] T006 [P] Setup logging infrastructure in `code/logging_config.py` to record provenance and warnings (e.g., zero variance detection).

**Data Source Verification & Execution Safety (Moved from Phase O)**
**Purpose**: Address the "Verified Accuracy" FAIL in the Constitution Check by ensuring the pipeline fails loudly on missing data rather than fabricating, and by defining a streaming fallback for large datasets.

- [X] T050 [P] [User Story 1] Implement `code/data_fetcher.py`: Create a module to attempt downloading UK Biobank data from a verified real source (e.g., `datasets.load_dataset('ukbiobank/microbiome-cognitive', streaming=True)`). If the download fails, raise a `FileNotFoundError` immediately. Do NOT implement any `try/except` fallback to synthetic data. If the remote dataset is unavailable, the task MUST verify the existence of local files in `data/raw/` as a fallback for CI, but the code must be written to prefer the remote source.
- [X] T051 [P] [User Story 1] Implement streaming loader: Update `code/data_utils.py` to support `streaming=True` via `datasets.load_dataset` or chunked CSV reading. Ensure the `SAMPLE_LIMIT=50000` is enforced via `itertools.islice` on the stream, not by loading the full file into memory first.
- [X] T052 [User Story 1] Add data provenance check: In `code/main.py`, verify that the input files in `data/raw/` have valid checksums or metadata headers before starting. If missing, halt with a clear error message directing the user to the data access channel.
- [X] T053 [P] [User Story 1] Write test `test_data_fetcher_fails_loudly` in `tests/unit/test_data_fetcher.py`: Verify that attempting to fetch from a non-existent URL raises an exception rather than returning a mock dataset.
- [ ] T054 [User Story 1] Document data access: Update `README.md` with explicit instructions on how to obtain the UK Biobank data and where to place it in `data/raw/`, referencing the specific data fields required (microbiome, cognitive, dietary).

**Spec Override Tasks (Moved to Foundational)**
**Purpose**: Formally document and amend deviations from the Spec that are methodologically required by the Plan. These MUST be completed before any implementation tasks that rely on them.

- [X] T045 [Spec Override] Amend `spec.md` to remove FR-003 (CLR on Alpha Diversity) as mathematically invalid. Define the corrected requirement: "System MUST compute Shannon Index on **raw** counts." Also create `docs/spec_override_FR003.md` documenting the rejection. **Exact Text to Insert**: "FR-002: System MUST compute alpha diversity (Shannon index) using `scikit-bio` on the OTU/ASV tables **using raw counts** (not CLR-transformed)."
- [X] T046 [Spec Override] Amend `spec.md` to remove SC-001 (CLR-transformed alpha diversity) as the measurement target. Define the corrected target: "System MUST measure correlation of **Raw Shannon Index**." Also create `docs/spec_override_SC001.md`. **Exact Text to Insert**: "SC-001: The correlation coefficient and p-value between **Raw Shannon Index** and fluid intelligence are measured against the Spearman rank correlation test results."
- [X] T047 [Spec Override] Amend `spec.md` to remove FR-007 (Median for Sex) as invalid for categorical data. Define the corrected requirement: "System MUST impute Sex using **Mode**." Also create `docs/spec_override_FR007.md`. **Exact Text to Insert**: "FR-007: System MUST impute missing numeric covariate values (age, BMI, DQS) using the median of the available data, and missing categorical values (sex) using the mode. "

**Configuration Validation (Critical Implementation)**
**Purpose**: Ensure critical error handling paths are actually implemented, not just listed.

- [X] T008 [P] Implement configuration validation: In `code/config.py` or `code/main.py`, implement checks to ensure required input files exist (`os.path.exists`) and are non-empty before pipeline start. Raise a `FileNotFoundError` if missing.
- [X] T014b [User Story 1] Implement DQS error handling: In `code/data_ingestion.py`, if DQS is required (per FR-008) but raw dietary data is missing, raise a fatal error and halt the pipeline. This ensures the 'MUST' in FR-008 is respected.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Load UK Biobank data, filter for complete outcomes, and impute covariates correctly (Mode for Sex, Median for others).

**Independent Test**: Run `code/data_ingestion.py` and verify the output CSV contains non-null values for alpha diversity, fluid intelligence, and covariates, with correct imputation logic applied.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these failing test stubs FIRST**

- [X] T009 [P] [User Story 1] Write failing test stub `test_imputation_sex_mode_returns_most_frequent` in `tests/unit/test_data_ingestion.py`. Use fixture file `tests/fixtures/sample_imputation.csv` containing a sample with majority 'M', minority 'F', and one NaN. Expect output **'M'** for NaN.
- [X] T010 [P] [User Story 1] Write failing test stub `test_filtering_excludes_null_primary_outcomes` in `tests/unit/test_data_ingestion.py`. Input a small sample with null 'fluid_intelligence' values; expect a reduced output row count.

### Implementation for User Story 1

- [X] T008a [P] [User Story 1] Create test fixture: Generate `tests/fixtures/sample_imputation.csv` with the data described in T009 (columns: age, sex, bmi, dqs, with specific NaN values).
- [X] T017 [P] [User Story 1] Create test fixture: Generate `tests/fixtures/sample_taxa_matrix.csv` with the 3-row wide taxa matrix described in T017 (columns: SpeciesA, SpeciesB, SpeciesC; values: [[10, 0, 0], [5, 5, 0], [0, 0, 10]]).
- [X] T018 [P] [User Story 1] Create test fixture: Generate `tests/fixtures/sample_clr_taxa.csv` with the 2-row taxa matrix described in T018 (columns: TaxaA, TaxaB, TaxaC; values: [[10, 10, 10], [20, 20, 20]]).
- [X] T019 [P] [User Story 1] Create test fixture: Generate `tests/fixtures/mock_correlation.csv` using `np.random.seed(42)` to create 20 synthetic rows with a known correlation of 0.8 as described in T019.
- [X] T031 [P] [User Story 1] Create test fixture: Generate `tests/fixtures/mock_plot_data.csv` with mock data for visualization testing as described in T031.

- [X] T011 [User Story 1] Implement `code/data_ingestion.py` to load raw microbiome and cognitive data from `data/raw/` and merge by participant ID column `participant_id` (FR-001). **Dependency**: T008a, T050 (Data Fetcher).
- [ ] T014a [P] [User Story 1] Implement DQS existence check: In `code/data_ingestion.py`, check for the existence of `data/raw/dietary_data.csv` or required columns (e.g., 'fruit', 'vegetable'). If missing, raise a fatal error as per T014b.
- [X] T014c [User Story 1] Implement DQS calculation: In `code/data_ingestion.py`, implement the full HEI-2015 standard formula for DQS calculation if raw dietary data is present (FR-008). **Specific Components**: Total Fruits (5 pts), Whole Fruits (5 pts), Total Vegetables (5 pts), Greens and Beans (5 pts), Whole Grains (10 pts), Dairy (10 pts), Total Protein Foods (5 pts), Seafood and Plant Proteins (5 pts), Refined Grains (10 pts), Sodium (10 pts), Empty Calories (20 pts). Do not use placeholders.
- [X] T012 [User Story 1] Implement filtering logic: In `code/data_ingestion.py`, filter out participants with null alpha diversity, fluid intelligence, or DQS (User Story 1, FR-001). **Dependency**: T014b (Error Handling). **Note**: Does NOT depend on T014c (Full Calculation) to allow filtering if DQS is pre-calculated.
- [X] T013 [User Story 1] Implement imputation logic: In `code/data_ingestion.py`, apply Median for Age, BMI, DQS; Mode for Sex. **Dependency**: None (implements Plan logic directly). Log imputation strategy to `provenance.log` (Data Hygiene Principle III).
- [ ] T015 [User Story 1] Save cleaned dataset: Write the processed DataFrame to `data/processed/cleaned_data.csv` with a header containing column definitions.
- [ ] T016 [User Story 1] Add error handling: Implement checks for missing files and empty datasets (edge case: zero participants) in `code/data_ingestion.py`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Correlation and Regression Analysis (Priority: P2)

**Goal**: Compute Shannon index, apply CLR only to taxa (not Shannon), run Spearman correlation, and fit multivariate regression.

**Independent Test**: Execute `code/analysis.py` and verify output CSVs contain correlation matrices with p-values and regression tables with coefficients, std_err, and p-values.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T017 [P] [User Story 2] Write failing test stub `test_shannon_calculation_known_values` in `tests/unit/test_diversity.py`. Input: fixture `tests/fixtures/sample_taxa_matrix.csv`. Expect output `shannon_index` values reflecting the diversity profiles of the samples (or calculated known values).
- [ ] T018 [P] [User Story 2] Write failing test stub `test_clr_transform_sum_logs_zero` in `tests/unit/test_transformation.py`. Input: fixture `tests/fixtures/sample_clr_taxa.csv`. Expect sum of log-transformed columns to be zero (within tolerance).
- [ ] T019 [P] [User Story 2] Write failing test stub `test_spearman_correlation_pvalue_calc` in `tests/integration/test_analysis.py`. Input: fixture `tests/fixtures/mock_correlation.csv`. Expect `p-value < 0.05`.

### Implementation for User Story 2

- [ ] T020 [User Story 2] Implement `code/diversity.py` to calculate Shannon Index (alpha diversity) from **raw** counts using `scikit-bio`. **Dependency**: None (implements Plan logic directly). Input: wide format taxa matrix. Output column: `shannon_index` (FR-002).
- [ ] T021 [User Story 2] Implement `code/transformation.py` to apply Centered Log-Ratio (CLR) transformation **only** to taxa abundance matrices (Secondary Path), not alpha diversity (FR-003, Plan Correction).
- [ ] T022 [User Story 2] Implement Spearman rank correlation in `code/analysis.py` between **raw** `shannon_index` and fluid intelligence. **Dependency**: None (implements Plan logic directly). Output schema: `r_value`, `p_value`, `n_obs` (User Story 2, SC-001 corrected).
- [ ] T023 [User Story 2] Implement multivariate linear regression in `code/analysis.py` using `statsmodels` with predictors: `shannon_index`, Age, Sex, BMI, DQS (FR-004). **Dependency**: Requires DQS column in `data/processed/cleaned_data.csv` (output of T015).
- [ ] T024 [User Story 2] Implement multicollinearity diagnostics (VIF) in `code/analysis.py` to check for unstable coefficients (Plan: Complexity Tracking).
- [ ] T025a [User Story 2] Implement edge case detection: In `code/analysis.py`, detect zero variance in fluid intelligence scores.
- [ ] T025c [User Story 2] Implement edge case logging: If zero variance is detected (T025a), skip correlation and log a warning to `data/processed/analysis_warnings.log`.
- [ ] T025b [User Story 2] Implement Residual Normality Validation: In `code/analysis.py`, perform Shapiro-Wilk test on regression residuals. Save validation report to `data/processed/regression_diagnostics.json` (Plan: Constitution Check).
- [ ] T026 [User Story 2] Save correlation results: Write `r_value`, `p_value`, `n_obs` to `data/processed/correlation_results.csv`.
- [ ] T027 [User Story 2] Save regression summary: Write `coefficient`, `std_err`, `p-value` for all predictors to `data/processed/regression_results.csv`.

### Success Criteria Validation (User Story 2)

- [ ] T028 [User Story 2] Implement validation script `code/validate_sc001.py`: Read `correlation_results.csv`, verify `r_value` is a float and `p_value < 0.05`. **Reference**: Validates Plan-corrected Raw Shannon against Spec Override T046 (replacing SC-001).
- [ ] T029 [User Story 2] Implement validation script `code/validate_sc002.py`: Read `regression_results.csv`, verify `coefficient` is a float and `p-value < 0.05` for the Shannon predictor. **Reference**: Validates Plan-corrected Raw Shannon regression against Spec Override T046 (replacing SC-002).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Correction and Visualization (Priority: P3)

**Goal**: Apply FDR correction to p-values and generate publication-quality plots.

**Independent Test**: Run `code/visualization.py` and verify `data/processed/` contains PNG scatter/histogram plots and a CSV with q-values.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T030 [P] [User Story 3] Write failing test stub `test_fdr_correction_qvalue_calc` in `tests/unit/test_analysis.py`. Input a sequence of p-values ranging from low to moderate significance. Expect corresponding q-values calculated via Benjamini-Hochberg.
- [ ] T031 [P] [User Story 3] Write failing test stub `test_visualization_png_generation` in `tests/integration/test_visualization.py`. Input: fixture `tests/fixtures/mock_plot_data.csv`. Expect output file `scatter_shannon_fi.png` exists and is > 1KB.

### Implementation for User Story 3

- [ ] T032 [User Story 3] Implement FDR correction (Benjamini-Hochberg) in `code/analysis.py` to adjust p-values from multiple tests (FR-005).
- [ ] T033 [User Story 3] Save corrected q-values: Write the adjusted p-values to `data/processed/corrected_results.csv`.
- [ ] T034a [User Story 3] Implement scatter plot generation: In `code/visualization.py`, generate the scatter plot object showing `shannon_index` vs. Fluid Intelligence with regression line. Filename: `scatter_shannon_fi.png`.
- [ ] T034b [User Story 3] Save scatter plot: Save the plot object from T034a to `data/processed/plots/scatter_shannon_fi.png` with X-axis: 'Shannon Index', Y-axis: 'Fluid Intelligence', Title: 'Gut Microbiome Diversity vs. Cognitive Performance' (FR-006).
- [ ] T035 [User Story 3] Implement histogram generation: In `code/visualization.py`, generate the histogram showing distribution of `shannon_index`. Filename: `diversity_histogram.png`. X-axis: 'Shannon Index', Title: 'Distribution of Alpha Diversity' (FR-006).
- [ ] T036 [User Story 3] Save plots: Ensure all plots are saved as high-resolution PNGs to `data/processed/plots/`.
- [ ] T037 [User Story 3] Implement negative result labeling: If all q-values > 0.05, generate a report file `data/processed/negative_results_report.txt` explicitly stating "No significant association found" (Spec Edge Case).
- [ ] T038 [User Story 3] Implement validation script `code/validate_sc003.py`: Read `data/processed/corrected_results.csv`, check column `q_value`, and verify all reported significant findings have `q_value < 0.05` (SC-003).
- [ ] T039 [User Story 3] Implement validation script `code/validate_sc004.py`: Read `data/processed/cleaned_data.csv`, calculate completeness metric as `(non_null_rows / total_rows) * 100`, and log 'PASS' if > 95% against SC-004.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T040 [P] Create `code/main.py` to orchestrate the full pipeline (Data Ingestion -> Diversity -> Analysis -> Visualization).
- [ ] T041 [P] Write `README.md` with instructions to run the pipeline and expected outputs.
- [ ] T042 [P] Add `pytest` configuration and run full test suite to ensure CI compatibility.
- [ ] T043 [P] Verify all output files match the schema defined in `contracts/` (if created).
- [ ] T044 [P] Run quickstart.md validation to ensure the project is reproducible in a fresh environment.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on clean data from User Story 1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on results from User Story 2

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
Task: "Write failing test stub test_imputation_sex_mode_returns_most_frequent in tests/unit/test_data_ingestion.py"
Task: "Write failing test stub test_filtering_excludes_null_primary_outcomes in tests/unit/test_data_ingestion.py"

# Launch all models for User Story 1 together:
Task: "Implement data ingestion script in code/data_ingestion.py"
Task: "Implement DQS calculation in code/data_ingestion.py"
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
- [Story] label maps task to specific user story for traceability (e.g., "User Story 1")
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical**: Ensure `code/diversity.py` uses **raw** counts for Shannon Index, NOT CLR-transformed data, as per Plan Correction (replaces FR-003).
- **Critical**: Ensure `code/data_ingestion.py` uses **Mode** for Sex imputation, NOT Median, as per Plan Correction (replaces FR-007).
- **Critical**: Ensure data loading respects the `SAMPLE_LIMIT=50000` constraint to prevent OOM on CI.
- **Critical**: Phase 4 tasks T022 (Spearman) and T023 (Regression) depend on T020 (Shannon) but NOT T021 (CLR Taxa). T021 is for Secondary Path only.
- **Critical**: Phase 5 tasks strictly depend on Phase 4 completion.
- **Critical**: T014b (DQS Error Handling) is a hard dependency for T012 and T023.
- **Critical**: T025b (Residual Validation) is required for Secondary Path regression compliance.