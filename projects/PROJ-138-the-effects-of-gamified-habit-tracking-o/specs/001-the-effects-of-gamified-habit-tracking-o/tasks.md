---
description: "Task list template for feature implementation"
---

# Tasks: The Effects of Gamified Habit Tracking on Long-Term Behavioral Change

**Input**: Design documents from `/specs/001-gamification-effects/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

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
 - Delivered as a MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure: Create the following directories at repository root: `code/data`, `code/analysis`, `code/reports`, `code/utils`, `code/tests`, `data/raw`, `data/processed`, `data/consent`. **Verification**: Assert all directories exist and create `.gitkeep` files in each to ensure they are tracked by git.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. **CRITICAL**: This phase includes the Synthetic Data Generation and Power Analysis to ensure the pipeline can run in Simulation Mode as authorized by Plan.md.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your project):

- [X] T002 [P] Initialize Python project with dependencies in `code/requirements.txt` (pandas, numpy, scikit-learn, statsmodels, lifelines, seaborn, matplotlib, pyyaml, pingouin, scipy, memory_profiler).
- [X] T003 [P] Configure linting (flake8/black) and formatting tools
- [X] T004 [P] Setup directory structure: `data/raw/`, `data/processed/`, `data/consent/`, `code/data/`, `code/analysis/`, `code/reports/`, `code/utils/`, `code/tests/`
- [X] T005 [P] Implement `code/utils/config.py` for random seed pinning and environment configuration
- [X] T006 [P] Setup `code/utils/logging.py` for structured logging of pipeline stages
- [X] T007 [P] Implement classes `User`, `BehavioralLog`, and `WeeklyAggregation` in `code/data/models.py` with attributes: `user_id` (str), `gamification_status` (bool), `conscientiousness_score` (float), `date` (datetime), `event_type` (str), `week_number` (int), `adherence_flag` (int), matching the Key Entities in spec.md. **Verification**: Assert `import code.data.models` succeeds and class attributes match spec.
- [X] T008 [P] Implement `code/utils/versioning.py` to calculate SHA-256 hashes of artifacts and update `state.yaml` (Constitution Principle V)
- [X] T009 [P] [US1] Setup `contracts/dataset.schema.yaml` defining required columns (User_ID, Gamified, Adherence, Conscientiousness, Need_for_Achievement) and valid tag values for `gamified_app_usage` for validation. **Verification**: Assert file exists and is valid YAML. (FR-001a)

- [ ] T048 [US1] Implement `code/data/power_analysis.py`: Add a pre-flight calculation script that estimates statistical power for the planned N=500 simulation given the target interaction effect size.
  1. **Logic**: Use `statsmodels.stats.power` to calculate power for a mixed-effects logistic regression approximation.
  2. **Parameters**: Hardcode `effect_size_f2 = 0.15`, `alpha = 0.05`, `target_power = 0.80` in the script. **Note**: The Plan.md section "Power Analysis Justification" is marked "[deferred]"; this task overrides that with explicit parameters to ensure executability. Log a WARNING if these differ from any future Plan update.
  3. **File Creation**: Ensure this script creates `code/data/power_analysis.py` with a `main()` entry point.
  4. **Output**: Write `data/processed/power_analysis_report.json` containing the estimated power, effect size, and sample size.
  5. **Validation**: **DO NOT HALT** the pipeline if power < 0.80. Instead, log a WARNING: "Power < 0.80 detected. Study proceeds with exploratory caveats." and set `power_status` to "low" in the JSON report. This resolves the logical deadlock caused by the '[deferred]' status in Plan.md. (Plan: "Power Analysis Justification")
 **Dependency**: Can run in parallel with T013a-1; its output is consumed by T032 for reporting.
 **Verification**: Assert the script runs successfully and generates the JSON report with a "low" status if power is insufficient, without exiting with code 1.

- [ ] T012a [US1] Implement `check_consent()` function in `code/data/validation.py`:
 1. **Check for Mode**: Check for the existence of `data/raw/synthetic_data_marker.json` **OR** a configuration flag `SIMULATION_MODE=true`.
 - **If Present (Synthetic Mode)**: **DO NOT** skip the check. Instead, generate a `data/consent/simulation_consent_placeholder.json` containing `{"type": "simulation", "timestamp": "<now>", "note": "No human subjects; synthetic data generated per Plan.md scope."}`. Log "Synthetic data detected. Generated consent placeholder for audit compliance." (FR-010, Constitution VI, Plan: "Crucial Scope Note").
 - **If Absent (Real Data Mode)**: Check for `data/consent/` directory and original consent documentation.
 - **If Missing**: **HALT** with `sys.exit(1)` and message "Error: Missing Consent for Real Data" (FR-010, Constitution VI).
 - **If Present**: Verify the file contains a `timestamp` field and a `signature` field. (FR-010)
 2. **Dependency**: Must run BEFORE T013a-1 to determine the data generation mode.
 **Verification**: Assert that missing real consent causes exit code 1. Assert that synthetic mode generates the placeholder file and logs the specific scope note.

- [ ] T013a-1 [US1] [FR-001-Synthetic] Implement `code/data/synthetic_generator.py` (Data Generation Algorithm):
 1. **Algorithm**: Use `numpy.random.default_rng(seed=42)`.
 2. **Traits**: Generate `conscientiousness_score` from N(3.5, 0.8).
 3. **Conditional Variable Logic**: **Deterministic Omission**: Check if `seed % 2 == 0`. If true, **omit** `need_for_achievement` column entirely to test the "missing variable" path. If false, generate `need_for_achievement` ~ N(3.5, 0.8) with a target correlation of rho=0.4 using Cholesky decomposition. This ensures reproducible testing of FR-002's conditional logic.
 4. **Gamification**: Set `gamified_status` = True if reported using gamified apps, False otherwise. Generate N=500 users total, ensuring [deferred] (150 users) are non-gamified. If initial random assignment fails, retry up to 5 times.
 5. **Logs**: Generate **synthetic longitudinal event logs** (NOT cross-sectional survey data) simulating multiple weeks of daily logs per user. Each log must have `date`, `event_type`, `user_id`.
 6. **Scope Note**: This task implements the "Simulation Study" scope authorized by Plan.md, providing a verified synthetic data source for this project iteration.
 7. **Output**: Return a DataFrame of synthetic data. (FR-008, FR-011)
 **Verification**: Assert the DataFrame contains specified columns and, if seed is even, `need_for_achievement` is missing.

- [ ] T013a-2 [US1] Implement `code/data/synthetic_generator.py` (Write Artifacts):
 1. **Action**: Write the DataFrame from T013a-1 to `data/raw/synthetic_data.csv`.
 2. **Marker**: Write `data/raw/synthetic_data_marker.json` with `{"source": "synthetic", "n": <variable>}`.
 3. **Verification**: Assert file exists and marker file is created.
 4. **Scope Note**: Verify that `code/data/synthetic_generator.py` contains the comment: `# Scope Note: This synthetic generator implements the Simulation Study scope authorized by Plan.md`.
 **Dependency**: T013a-1

- [ ] T013a-3 [US1] Implement `code/data/synthetic_generator.py` (Validate Group Sizes & Missing Columns):
 1. **Action**: Verify the generated dataset contains ≥30 non-gamified users AND ≥100 total valid records.
 2. **Missing Column Logic**: If `need_for_achievement` is missing (as per T013a-1 logic), log "Column 'need_for_achievement' omitted from source data." and ensure the pipeline is prepared to proceed with Conscientiousness only (FR-002).
 3. **Tiered Logic**:
 - If Total < 100: **HALT** with `sys.exit(1)` and log "CRITICAL: Data Insufficiency (< 100 records)." (FR-001).
 - If 100 <= Total < 500: Log "WARNING: Sample size < 500 (N=<actual>). Proceeding with caution."
 - If Total >= 500: Log "Success: Sample size target met."
 4. **Retry Logic**: If < 30 non-gamified users, retry generation up to 5 times. If still < 30 after 5 attempts, raise a fatal error.
 5. **Verification**: Assert count of non-gamified users >= 30 and total records >= 100.
 **Dependency**: T013a-2

- [X] T012b [US1] Implement `calculate_cronbach_alpha()` function in `code/data/validation.py`: Calculate Cronbach's α for personality scales using `pingouin`. Handle missing items by excluding them from the calculation and logging the exclusion count (FR-011). **Dependency**: Requires data from T017.
 **Verification**: Assert function returns a float between 0 and 1. Assert log contains alpha value.

- [X] T012c [US1] Implement `report_cronbach_alpha()` function in `code/utils/report-utils.py`:
 1. **Action**: Retrieve the Cronbach's Alpha value calculated in T012b.
 2. **Output**: Write the value to `data/processed/psychometrics.json` with the key `cronbach_alpha`.
 3. **Verification**: Assert the JSON file is created and contains the alpha value. (FR-011)
 **Dependency**: Requires output from T012b.
 **Note**: This value will be consumed by T032 for injection into the final report.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition, Validation, and Aggregation (Priority: P1) 🎯 MVP

**Goal**: Ingest data from a verified longitudinal source (or synthetic generator), validate schema, and aggregate daily logs into weekly bins.

**Independent Test**: The pipeline can be tested by running the data ingestion script on a sample and verifying that the output CSV contains unique user IDs with non-null values for gamification status, weekly adherence counts, and personality scores.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST (TDD Red), ensure they FAIL before implementation**

- [X] T010 [P] [US1] Contract test: Add function `test_schema_validation()` in `code/tests/test_ingestion.py` that asserts the ingestion script raises a `ValueError` if `data/consent/` is missing (for real data) or if required columns are absent in the dataset. **Context**: This is a TDD Red task; the script does not exist yet.
- [X] T011 [P] [US1] Integration test: Add function `test_weekly_aggregation()` in `code/tests/test_aggregation.py` that asserts the aggregation script correctly generates `week_number` and `weekly_adherence_flag` columns from raw daily logs. **Context**: This is a TDD Red task; the script does not exist yet.

### Implementation for User Story 1

- [X] T013b [US1] Implement `code/data/ingestion.py`:
 1. **Priority**: Check for the existence of `data/raw/synthetic_data_marker.json` (validated by T012a).
 - **If Present**: Load `data/raw/synthetic_data.csv`.
 - **If Absent**: Attempt to fetch data from `HABITICA_API_URL` (from env).
 2. **Schema Validation (FR-001a)**:
 - **Action**: Validate the loaded data against `contracts/dataset.schema.yaml`.
 - **If Missing Tags**: If required tags (e.g., `gamified_app_usage`) are missing, **HALT** with `sys.exit(1)` and generate `data/reports/data_schema_mismatch_report.json` with error details. (FR-001a)
 3. **Data Source Availability**:
 - **If API Fetch Fails**: If `HABITICA_API_URL` is configured and fetch fails (network error, 404, auth failure), generate `data/reports/data_insufficiency_report.json` containing the error details and exit with code 0 (graceful failure). (FR-001a, Edge Cases)
 - **If Unconfigured**: If `HABITICA_API_URL` is not set, generate `data/reports/data_insufficiency_report.json` and exit with code 0. (FR-001a, Edge Cases)
 4. **Validation**: Ensure non-gamified group size ≥ 30 (FR-008). If total valid records < 100 or non-gamified group < 30, generate a "Data Insufficiency" report and exit gracefully. (FR-001, FR-001a, FR-008)
 **Dependency**: Must run after T012a (consent).
 **Verification**: Assert that missing real consent causes exit code 1. Assert that synthetic mode skips consent check.

- [X] T014 [US1] Implement `code/data/aggregation.py`: Aggregate daily logs into `week_number` (sequential integers ≥ 1) and `weekly_adherence_flag` (binary 1/0) per user (FR-001b).
 **Dependency**: Requires output from T013b.

- [ ] T017 [US1] Generate merged CSV in `data/processed/merged_data.csv` with all required columns.
 1. **Action**: Call `code/data/aggregation.py` to process the data from T014.
 2. **Schema**: The output CSV MUST contain exactly these columns: `User_ID`, `gamified_status`, `conscientiousness_score`, `weekly_adherence_flag`, `week_number`.
 3. **Conditional Column**: If `need_for_achievement` exists in the source data, include it as `need_for_achievement`. If not, **exclude** it from the output.
 4. **Logging**: If `need_for_achievement` is excluded, log the exact message: "Column 'need_for_achievement' omitted from merged dataset as it was not present in source."
 5. **Verification**: Assert file exists and contains 'User_ID', 'gamified_status', 'conscientiousness_score', 'weekly_adherence_flag', 'week_number'. (FR-001b)
 **Dependency**: Requires output from T014.

- [X] T012b [US1] Implement `calculate_cronbach_alpha()` function in `code/data/validation.py`: Calculate Cronbach's α for personality scales using `pingouin`. Handle missing items by excluding them from the calculation and logging the exclusion count (FR-011). **Dependency**: Requires data from T017.
 **Verification**: Assert function returns a float between 0 and 1. Assert log contains alpha value.

- [X] T012c [US1] Implement `report_cronbach_alpha()` function in `code/utils/report-utils.py`:
 1. **Action**: Retrieve the Cronbach's Alpha value calculated in T012b.
 2. **Output**: Write the value to `data/processed/psychometrics.json` with the key `cronbach_alpha`.
 3. **Verification**: Assert the JSON file is created and contains the alpha value. (FR-011)
 **Dependency**: Requires output from T012b.
 **Note**: This value will be consumed by T032 for injection into the final report.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Modeling and Interaction Analysis (Priority: P2)

**Goal**: Fit mixed-effects logistic regression and survival analysis models to predict adherence and dropout.

**Independent Test**: The modeling script can be tested by running it against a synthetic dataset with known interaction coefficients and verifying that the model recovers the interaction term within an acceptable margin of error.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Contract test: Add function `test_model_convergence()` in `code/tests/test_modeling.py` that asserts the mixed-effects model converges and recovers known coefficients within 0.01 variance on a synthetic test set.
- [X] T019 [P] [US2] Integration test: Add function `test_survival_event_count()` in `code/tests/test_survival.py` that asserts the survival analysis halts and outputs descriptive stats if dropout events < 10 per group.

### Implementation for User Story 2

- [X] T021 [US2] Implement VIF calculation and variable drop logic in `code/analysis/modeling.py`:
 1. **First**, check if `need_for_achievement` column exists.
 2. If yes, calculate VIF for Conscientiousness and Need for Achievement using `statsmodels.stats.outliers_influence.variance_inflation_factor`.
 3. If VIF > 5, **log** the removal to `logs/model_fallback.log` with message "Dropped Need for Achievement due to VIF > 5", and flag the variable for removal. (FR-002)
 4. **Apply Drop**: If flagged, remove it from the model formula immediately.
 5. If column does not exist, log omission and proceed with Conscientiousness only.
 **Dependency**: Requires data from T017.

- [X] T020b [US2] Implement `code/analysis/modeling.py` (Spec-Compliant Model):
 1. **Action**: Fit a mixed-effects logistic regression model with **random intercepts**: `(1 | user_id)`.
 2. **Justification**: This adheres to Spec.md FR-002 and User Story 2 which explicitly mandate "random intercepts for users".
 3. **Convergence Check**: Immediately after fitting, check for convergence warnings or singularity.
 - **If Convergence Fails**: Log a WARNING: "Model convergence failed with random intercepts. Falling back to Fixed Effects with Robust SEs." and fit a fixed-effects model with `cov_type='HC3'`.
 - **If Convergence Succeeds**: Proceed with random intercepts.
 4. **Output**: Save results to `data/processed/model_intercept_results.json` and include a `convergence_status` field ("success" or "fallback").
 5. **Verification**: Assert the model outputs the specified JSON and handles convergence failures gracefully. (FR-002, Plan: "Complexity Tracking")
 **Dependency**: Must run after T021.

- [X] T022 [US2] Implement Benjamini-Hochberg (FDR) correction for multiple comparison tests in `code/analysis/modeling.py` and verify output.
 1. **Scope**:
 - Dynamically determine the set of terms to correct: Include `Gamification_x_Conscientiousness` and `Gamification_x_NeedForAchievement` **only if** the corresponding main effects are present in the model.
 - **Explicitly EXCLUDE** `week_number`, `time`, or any column containing temporal indices from the correction set as they are repeated measures (FR-007).
 2. **Action**: Apply correction to the selected set of interaction terms and secondary personality traits.
 3. **Verification**: Assert the correction list does not contain 'week_number' or temporal indices. (FR-007)
 4. **Output**: Write a verification log to `logs/fdr_verification.log` confirming the exclusion of temporal indices and listing the corrected terms. (FR-007)
 5. **Verification**: Assert the output contains corrected p-values for the interaction terms. (FR-007)
 **Dependency**: Requires output from T020b.

- [X] T023 [US2] Implement Leave-One-User-Out (LOUO) cross-validation in `code/analysis/modeling.py`; report average AUC and variance (US-2 Scenario 3).

- [X] T049 [US2] Enhance `code/analysis/survival.py` to handle the "Zero Adherence" edge case explicitly.
 1. **Logic**: Identify users with `weekly_adherence_flag` = 0 for all observed weeks.
 2. **Action**: Mark these users as censored at `week_number=0` (or their last known active timestamp if any) in the survival analysis input.
 3. **Verification**: Ensure the Kaplan-Meier curve explicitly marks these censoring events to avoid bias in the hazard ratio calculation (Edge Case: "How does system handle users with zero adherence weeks?").
 **Dependency**: Requires data from T017.

- [X] T024 [US2] Implement `code/analysis/survival.py`: Count dropout events (consecutive weeks of non-adherence). If events < 10 per group, **generate a descriptive statistics report** and halt survival analysis (FR-009). If events ≥ 10, proceed to survival analysis.
 **Dependency**: Requires data from T017.

- [X] T025 [US2] Implement Kaplan-Meier curves and Cox proportional hazards model in `code/analysis/survival.py`, stratified by Conscientiousness quartiles (FR-003).
 **Dependency**: Requires output from T024.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Robustness Validation and Reporting (Priority: P3)

**Goal**: Execute bootstrapping for robustness and generate the final report with visualizations.

**Independent Test**: The validation script can be tested by running the analysis pipeline on a bootstrapped sample and verifying that the generated report includes a section comparing effect sizes across bootstrap iterations.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T027 [P] [US3] Contract test: Add function `test_bootstrap_variance` in `code/tests/test_robustness.py` that asserts the bootstrapping procedure generates a sufficient number of samples to report a coefficient variance (regardless of value).
- [X] T028 [P] [US3] Integration test: Add function `test_report_generation()` in `code/tests/test_report.py` that asserts the generated report contains Kaplan-Meier curves, sensitivity analysis tables, and the associational disclaimer.

### Implementation for User Story 3

- [X] T029 [US3] Implement `code/analysis/robustness.py`: Execute bootstrapping (sufficient iterations) to generate confidence interval for gamification effect size. **Logic**:
 1. Use `sklearn.model_selection.StratifiedShuffleSplit` to ensure the ratio of gamified to non-gamified users remains constant (within 5%) across all samples.
 2. **Report**: Report the coefficient variance across samples and the corresponding confidence interval.
 3. **Robustness Status**: **DO NOT HALT** the pipeline if variance >= 0.01. Instead, calculate the variance, and if `variance >= 0.01`, set `robustness_status` to "failed" in `data/processed/robustness_report.json`. If `variance < 0.01`, set to "passed".
 4. **Output**: Write `data/processed/robustness_report.json` with `variance`, `ci`, and `robustness_status`.
 5. **Verification**: Assert the report contains the variance value and the `robustness_status` flag. (FR-004, SC-004)
 **Dependency**: Requires output from T020b.

- [X] T031 [US3] Implement sensitivity analysis in `code/reports/generate_report.py`: Vary adherence thresholds over a set of discrete levels. (passed via `--thresholds` argument) and **calculate/report the stability of the effect size (coefficient variance)** across these thresholds (FR-005, SC-005). **Stability Criterion**: Variance < 0.05.
 **Verification**: Assert the analysis iterates over the provided thresholds and reports stability.

- [ ] T032 [US3] [FR-005, FR-006, FR-011] Generate final report artifact `data/reports/final_analysis.html` by executing `code/reports/generate_report.py`. **Requirements**:
 1. **Language Audit**: Scan all generated text blocks (Methodology, Results, Conclusion) for causal verbs (e.g., 'causes', 'leads to', 'determines') and replace them with associational terms (e.g., 'is associated with', 'predicts', 'correlates with').
 2. **Disclaimer Injection**: Inject a header disclaimer programmatically: "Findings are associational, not causal. The data is observational." (FR-005, FR-006).
 3. **Data Binding**: Read `data/processed/psychometrics.json` (from T012c) and inject the Cronbach's Alpha value into the "Psychometric Validity" section. (FR-011)
 4. **Limitations**: Include a "Data Limitations" section explicitly stating: "Sample size (N=<actual>), synthetic nature of data, lack of external validation, and potential underpowering for interaction effects."
 - **Source of Truth**: Read the actual sample size `N` from `data/processed/merged_data.csv` (count of unique `User_ID` rows) to populate `<actual>`. Do not use hardcoded values or planned N.
 5. **Methodology Limitations**: Append a "Methodology Limitations" subsection explicitly stating the "Simulation Study" nature, reliance on synthetic data with known ground truth, and the limitation of using a single random seed without multi-seed sensitivity analysis.
 6. **Robustness Flag**: If `data/processed/robustness_report.json` contains `robustness_status: "failed"`, inject a specific warning: "WARNING: Bootstrap variance (>= 0.01) exceeded the robustness threshold. Results should be interpreted with caution." (SC-004).
 7. **Verification**: Assert file exists, contains the "Data Limitations" section with the actual N, the Cronbach's Alpha value, the disclaimer, the robustness flag (if applicable), and no causal language. (FR-005, FR-006, FR-011, SC-004)
 **Dependency**: Requires output from T029, T031, T012c.

- [X] T033 [US3] Run `code/utils/versioning.py` to hash all final artifacts and update `state.yaml` (Constitution Principle V).

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T034 [P] Documentation updates: Update `README.md` with project overview and `specs/001-gamification-effects/quickstart.md` with execution instructions. **Specifics**: Ensure `quickstart.md` includes steps for synthetic data generation and consent verification.
- [X] T035 [P] Refactor `code/analysis/robustness.py` to use **chunked processing or generator-based iteration** to ensure peak memory usage remains under **4GB** during bootstrapping, verified by a **memory_profiler** test. **Verification**: Add `tests/test_memory.py::test_peak_memory_under_GB` and assert it passes.
- [X] T036 [P] Optimize `code/analysis/robustness.py` by implementing **multiprocessing** for 1,000 bootstrap iterations to reduce runtime on **GitHub Actions free-tier (2 CPU, 7GB RAM)** to < 30 minutes. **Verification**: Assert runtime < 30 minutes in CI logs.
- [X] T037 [P] Additional unit tests for edge cases: Implement `code/tests/test_edge_cases.py` with functions `test_vif_high_collinearity` (verifies VIF > 5 handling) and `test_low_event_count` (verifies survival halt logic).
- [ ] T038 [US3] Run quickstart.md validation: Create `quickstart.sh` if it does not exist (copying steps from `quickstart.md`), make it executable, then run `bash quickstart.sh`. Assert exit code 0, verify `data/processed/merged_data.csv` exists, and run pre-flight dependency checks. **Pre-flight Check**: Assert that all dependency files (T009, T013a, T014) exist before execution. (FR-001b, Constitution V)
 **Verification**: Assert exit code 0 and `data/processed/merged_data.csv` exists.

- [ ] T052 [US3] Implement `code/main.py` orchestration script to unify the pipeline execution flow.
 1. **Logic**: Create a sequential runner that imports and executes the following functions in order:
 - `code.data.power_analysis.main()`
 - `code.data.validation.check_consent()`
 - `code.data.synthetic_generator.main()`
 - `code.data.ingestion.main()`
 - `code.data.aggregation.main()`
 - `code.analysis.modeling.main()`
 - `code.analysis.survival.main()`
 - `code.analysis.robustness.main()`
 - `code.reports.generate_report.main()`
 2. **Error Handling**: Implement try/except blocks to capture failures in any stage and write a structured error log to `logs/pipeline_error.log`.
 3. **Dependency**: Must run after T051 (Run-book reconciliation) and after all US1/US2/US3 implementations.
 4. **Verification**: Assert that running `python code/main.py` successfully produces `data/reports/final_analysis.html` without manual intervention. (Plan: "Orchestration script")

**Checkpoint**: All user stories should now be independently functional

---

## Phase N+1: Revision & Compliance (Post-Analysis Fixes)

**Purpose**: Address specific issues raised by `/speckit.analyze` regarding power analysis, edge case handling, and documentation completeness.

- [X] T050 [US3] Update `code/reports/generate_report.py` to include a "Methodology Limitations" subsection.
 1. **Content**: Explicitly state the "Simulation Study" nature of the work, the reliance on synthetic data with known ground truth, and the specific limitation of using a **single random seed (42)** without reporting sensitivity to seed variation. Acknowledge that multi-seed sensitivity analysis was not performed as it is outside the scope of the "Crucial Scope Note" in Plan.md.
 2. **Action**: Append this section to the final report after the "Data Limitations" section.
 3. **Verification**: Assert the report contains the phrase "Simulation Study", "known ground truth", and "single random seed" in the limitations section. (Plan: "Crucial Scope Note")

- [X] T058 [US3] Reconcile run-book vs implementation for `code/main.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/main.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist.

**Checkpoint**: All user stories should now be independently functional