# Tasks: The Relationship Between Sleep Chronotype and Moral Judgement

**Input**: Design documents from `/specs/chronotype-moral-judgement/`
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
 - Delivered as an MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T002 Initialize R 4.3+ project with `renv` and dependencies (`tidyverse`, `lme4`, `car`, `effectsize`, `pwr`, `rmarkdown`, `knitr`, `data.table`, `testthat`, `lintr`, `emmeans`)
- [X] T003 [P] Configure `lintr` for code style and `renv.lock` generation

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your project):

- [X] T004 Setup `data/raw/`, `data/processed/`, `data/derived/`, and `logs/` directories and `.gitignore` rules
- [X] T005 [P] Create `code/measurements.md` with explicit sections for MEQ and MFQ: **exact version**, **item ordering**, and **scoring formula** (Constitution Principle VI)
- [X] T005.1 [P] Create `code/utils_state.R` to manage the global exclusion state JSON schema and read/write functions for `data/derived/global_exclusion_state.json`. This task establishes the infrastructure for tracking exclusion counts and reasons across the pipeline.
- [X] T005.5 [P] Generate `quickstart.md` with setup instructions, data requirements, and run commands (Plan.md Phase 1 output, now generated here to ensure artifact exists for T032)
- [X] T006 [P] Create `code/00_config.R` to manage environment variables and file paths
- [X] T006.1 [P] Create `code/config.yaml` with `run_mancova: false` and explicit comments stating "MANCOVA is NOT implemented per Spec FR-003. Only univariate ANCOVAs are required."
- [X] T007 Create base data validation utilities in `code/utils_validation.R`
- [X] T008 Setup logging infrastructure in `code/utils_logging.R` (warnings, aborts)
- [X] T014.1 [P] [US1] [SC-001] [Data Artifact] Implement `code/06.1_generate_benchmark.R`:
 - **Purpose**: Generate a synthetic benchmark dataset with **noisy** chronotype labels for testing SC-001.
 - **Method**: Generate data using `rnorm(n=100, mean=50, sd=10)` for `MEQ_score`. **Explicit Mapping**: Apply FR-002 logic to generate a "true" label, then **randomly flip the label for a small fraction of the rows** (simulating human error or scoring ambiguity). This ensures the benchmark is **not tautological** and tests the classifier's robustness against realistic error distributions.
 - **Execution Constraint**: The script **MUST** require the CLI flag `--mode=test`. If invoked without this flag, **ABORT immediately**.
 - **Output Constraint**: The script **MUST** write output **only** to `data/benchmark/`. Save the dataset as `data/benchmark/synthetic_benchmark.csv`. If the target directory is not `data/benchmark/`, **ABORT immediately**.
 - **Artifact**: This file `data/benchmark/synthetic_benchmark.csv` is a persistent artifact used by T014.2.
- [X] T048 [US1] [Const-I] [Review: Data Flow] Implement `code/01.5_validate_data_flow.R` to explicitly verify that the output of T011 (`cleaned_data.csv`) is consumed as the **sole** input for T012 (`classify.R`). This task adds a runtime assertion that `cleaned_data.csv` is created *before* `classify.R` is invoked, preventing race conditions in parallel CI environments. **Moved to Phase 2** as data flow is foundational.
- [X] T049 [US1/US2] [Const-I] [Review: Reproducibility] Implement `code/03.1_seed_manager.R` to enforce a global random seed (e.g., `set.seed(2026)`) at the start of **every** script (ingest, classify, analysis, report). This ensures that any stochastic elements (e.g., bootstrapping for CIs, if added later) are fully reproducible across runs. **Moved to Phase 2** as reproducibility is foundational.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Chronotype Classification (Priority: P1) 🎯 MVP

**Goal**: Ingest raw questionnaire data and obtain a reliable chronotype label for each participant.

**Independent Test**: Run the ingestion‑and‑classification script on a sample CSV and verify that the output table contains a `chronotype` column with values "morning", "intermediate", or "evening".

### Implementation for User Story 1

- [X] T010.1 [US1] [FR-001] [FR-007] Implement `code/00.1_check_data_existence.R`:
 - **Purpose**: Check for the existence of `data/raw/study_data.csv`.
 - **Action**: If the file is missing, **ABORT immediately** with a clear error message: "CRITICAL: Required data file `data/raw/study_data.csv` is missing. The pipeline cannot proceed without real data. Please provide the file or run `code/04_fetch_data.R` if configured."
 - **Constraint**: This task runs before any data processing. It does NOT generate synthetic data.

- [X] T010.5 [US1] [FR-006] Implement `code/00.5_capture_original_count.R`:
 - **Depends on**: T010.1.
 - **Purpose**: Capture the total number of rows in the raw input file (`data/raw/study_data.csv`) BEFORE any filtering or exclusion logic.
 - **Action**: Read the raw file, count rows, and save the integer count to `data/derived/original_row_count.txt`.
 - **Constraint**: This task MUST NOT modify the data or apply any filters. It is a pure metadata capture step.

- [X] T011 [US1] Implement `code/01_ingest.R`:
 1. Load CSV.
 2. Verify presence of ALL required columns (`MEQ_score`, `MFQ_*`, `PSQI`, `acute_sleepiness`, `age`, `sex`). **ABORT immediately** if any column is missing (FR-001) **BEFORE** any processing.
 3. Check for missing `acute_sleepiness`. Exclude rows with missing values and log them to `logs/ingest_exclusions.log` (format: `row_id,reason=missing_acute_sleepiness,step=ingest`). **DO NOT ABORT** immediately.
 4. **Data Contract**: Ensure the script exits with code 0 only if the file is saved; exits with code 1 if aborted.
 5. Output: Save `data/processed/cleaned_data.csv` (excluding acute_sleepiness rows) and update `data/derived/global_exclusion_state.json` with the count of excluded rows for `missing_acute_sleepiness`.
 6. **Constraint**: This task logs exclusions and updates the global state. It does NOT calculate the total exclusion rate or perform any abort logic based on rate. **Global abort logic is enforced in T012.5.**

- [X] T012 [US1] Implement `code/02_classify.R`:
 - **Depends on**: T005 (scoring docs), T011 (cleaned data), T010.5 (original count).
 - Apply thresholds: `MEQ >= 59` -> "morning", `MEQ <= 41` -> "evening", else "intermediate".
 - Flag rows with `NA` or non-numeric `MEQ_score` (exclude and log to `logs/classify_exclusions.log` with format `row_id,reason=invalid_meq,step=classify`).
 - Exclude rows with out-of-range MFQ scores (per FR-006), logging each exclusion to `logs/classify_exclusions.log` with format `row_id,reason=invalid_mfq,step=classify`.
 - **Update Global Counter**: Read `data/derived/global_exclusion_state.json`, add new exclusions (invalid MEQ/MFQ), and save updated state.
 - **Constraint**: This task updates the counter. It does NOT calculate the total exclusion rate or perform any abort logic based on rate.
 - Save `data/derived/classified_data.csv` (provisional).

- [X] T012.5 [US1] [FR-006] Implement `code/02.5_final_exclusion_check.R`:
 - **Depends on**: T012, T010.5, T011.
 - **Unified Check**: Read `data/derived/global_exclusion_state.json` (containing counts for `missing_acute_sleepiness`, `invalid_meq`, `invalid_mfq`) and `data/derived/original_row_count.txt`.
 - **Calculation**: Calculate exclusion rate = (Total Count of ALL Excluded Rows, **INCLUDING** `missing_acute_sleepiness`) / (Original Row Count). **INCLUDE** rows missing `acute_sleepiness` in the numerator and denominator.
 - **Action**: If rate > 20%, **ABORT immediately** with a clear error message. **LOG THE SPECIFIC REASON** (e.g., "ABORT: Exclusion rate 25% exceeds 20% threshold. Primary reasons: missing_acute_sleepiness ([count]), invalid_meq ([count])") to `logs/abort.log`. **DO NOT** save `classified_data.csv` if this check fails.
 - If rate <= 20%, confirm final file `data/derived/classified_data.csv` exists and is valid.

### Phase 3.1: User Story 1 Validation (Post-Implementation)

**Purpose**: Validation tasks that MUST run after T012.5 completes.

- [X] T014.2 [US1] [SC-001] [Accuracy Test] Implement `code/06.2_verify_benchmark_accuracy.R`:
 - **Depends on**: T014.1 (Moved to Phase 2), T012.5.
 - **[SC-001] See SC-001**. **STRICTLY FOR BENCHMARK ACCURACY TEST ONLY**.
 - **Action**: Load `data/benchmark/synthetic_benchmark.csv`. Run the classifier logic (T011/T012) on this data. Compare predicted labels to the known (noisy) labels in the dataset.
 - **Verification**: Verify ≥95% accuracy (SC-001). The [deferred] noise ensures this is a robust test, not a tautology.
 - **Execution Constraint**: The script **MUST** require the CLI flag `--mode=test`.
 - **Output**: Save test results to `data/derived/benchmark_results.csv`.

- [X] T018 [US1] [SC-001] Implement `code/02.6_reliability.R`:
 - **Depends on**: T012.5.
 - Calculate Cronbach's alpha for all five MFQ subscales using the classified data.
 - Save results to `data/derived/reliability_metrics.csv` with columns: `subscale`, `cronbach_alpha`, `n_items`.
 - **Verify**: Ensure `data/derived/reliability_metrics.csv` exists and contains valid alpha values.

- [X] T018.5 [US1] [Constitution Principle VI] Implement `code/02.7_meq_reliability.R`:
 - **Depends on**: T012.5.
 - **[Constitution Principle VI] See Constitution Principle VI**.
 - **Verify MEQ item availability**:
 - **Step 1 (Check)**: Scan input data for raw MEQ items (e.g., `MEQ_Q1`, `MEQ_Q2`, etc.).
 - **Step 2 (Calc)**: If raw items are found, calculate Cronbach's α and save to `data/derived/meq_reliability.csv`.
 - **Step 3 (Fallback)**: If **only** a total `MEQ_score` column exists (as per FR-001), write a row with `subscale="MEQ_Total"`, `cronbach_alpha="N/A (single item)"`, `n_items=1`. **DO NOT attempt calculation.**
 - **Justification Step**: **MUST** append a paragraph to `code/measurements.md` (and the final report) explicitly justifying the use of a single-item proxy for MEQ, citing the input data constraints (FR-001) and referencing the Constitution Principle VI requirement for deviation justification.
 - **Constraint**: Since FR-001 defines the input as containing only `MEQ_score`, the "Secondary Path" for individual items is unreachable **unless** the source data actually contains them. This task now **checks** for them first.
 - **Report Integration**: Ensure the final report (T026) explicitly states "MEQ Internal Consistency: N/A (single item)" or the calculated alpha value, fulfilling Constitution Principle VI.
 - **Cross-Story Dependency**: This artifact (`meq_reliability.csv`) is a prerequisite for T027 (US3).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently. Note: T014.2, T018, T018.5 depend on T012.5 completion and run sequentially after it.

---

## Phase 4: User Story 2 - Controlled ANCOVA with Multiplicity Control (Priority: P2)

**Goal**: Run ANCOVA for each MFQ subscale, controlling for covariates, and apply Bonferroni correction.

**Independent Test**: Execute the analysis module on a pre‑validated dataset and compare the generated ANCOVA table to a reference R script; all p‑values must match within 0.01.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T017 [P] [US2] Unit test for ANCOVA model formula in `tests/test-analysis.R`
- [X] T020 [P] [US2] Unit test for Bonferroni correction logic in `tests/test-analysis.R` (Renumbered from duplicate T018)

### Implementation for User Story 2

- [X] T019 [US2] Implement `code/03_analysis.R`:
 - **Depends on**: T012.5 (Hard Gate).
 - **Primary Requirement**: Run ANCOVA (`MFQ_subscale ~ chronotype + PSQI + acute_sleepiness + age + sex`) for all subscales.
 - **MANCOVA Note**: **MANCOVA is NOT implemented**. **Per Spec FR-003, MANCOVA is excluded; implement only univariate ANCOVAs.** The plan.md Summary mentioning MANCOVA is superseded by the spec.
 - Apply Bonferroni correction (α = 0.05/5 = 0.01) to p-values **atomically** within this step (FR-003).
 - **Contrast Generation**: Use `emmeans` to explicitly generate **all** pairwise contrasts: `Morning_vs_Evening`, `Morning_vs_Intermediate`, `Evening_vs_Intermediate` for every significant subscale. **Explicitly define the set of contrasts as `c('Morning_vs_Evening', 'Morning_vs_Intermediate', 'Evening_vs_Intermediate')`**.
 - Calculate Cohen's d and 95% CI for significant contrasts (FR-004).
 - **Data Contract**: Explicitly output contrast definitions (e.g., `contrast_label="Morning_vs_Evening"`, `contrast_label="Morning_vs_Intermediate"`, `contrast_label="Evening_vs_Intermediate"`) for every significant result to `data/derived/ancova_results.csv`.
 - Calculate Variance Inflation Factors (VIF).
 - **If any VIF > 2**: Log warning to `logs/vif_warnings.log`, write "Invalid" flag to `data/derived/vif_flag.csv`, and **DO NOT ABORT** the pipeline (per FR-006), but mark the result as potentially unreliable for publication (honoring Assumptions).
 - If VIF OK, save `data/derived/ancova_results.csv` and `data/derived/effect_sizes.csv`.

### Phase 4.1: User Story 2 Validation (Post-Implementation)

- [X] T024 [US2] [SC-002] Implement `code/07_regression_test.R`:
 - **Depends on**: T019. **Also depends on presence of `data/raw/reference_data.csv`**.
 - **[SC-002] See SC-002**.
 - **Real Data Requirement**: This task **MUST** use a real, pre-validated dataset (e.g., `data/raw/reference_data.csv`) provided by the researcher for the **primary comparison**. **DO NOT** use synthetic data for the primary comparison.
 - **Action**: If `data/raw/reference_data.csv` exists, run the ANCOVA model on it and compare p-values with the pipeline output (T019). Verify tolerance ≤0.01.
 - **CI Fallback**: If `data/raw/reference_data.csv` is **missing**, the task **MUST FAIL** (exit code 1) with a clear error message: "SC-002 Verification Failed: Real reference data (`data/raw/reference_data.csv`) is missing. Synthetic data is NOT permitted for this validation. Please provide the real dataset." **NO synthetic fallback is generated.**
 - **Model Consistency**: Ensure the model formula used for comparison matches T019 exactly.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Reproducible Reporting & Sensitivity Analysis (Priority: P3)

**Goal**: Generate an R‑Markdown report with descriptive stats, effect sizes, power analysis, and sensitivity sweep.

**Independent Test**: Render the R‑Markdown report on the CI runner and run the validation script; it must confirm presence of all required sections and that the sensitivity table lists results for at least three alpha_corrected values.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T025 [P] [US3] Validation test for report structure in `tests/test-report.R`

### Implementation for User Story 3

- [X] T026 [US3] Implement `code/04_report.Rmd`: Include descriptive tables, ANCOVA results, Cohen's d, G*Power summary (FR-005). **Depends on**: T019, T018, T018.5, T012.5.
- [X] T027 [US3] [SC-004] Implement sensitivity analysis sweep in `code/05_sensitivity.R`:
 - **[SC-004] See SC-004**.
 - **Depends on**: T019, T018, T018.5, T012.5.
 - **Method**: Read existing p-values and **contrast labels** from `data/derived/ancova_results.csv`.
 - **Contrast Coverage**: Explicitly ensure the table includes results for **all** pairwise combinations: `Morning_vs_Evening`, `Morning_vs_Intermediate`, `Evening_vs_Intermediate` for each of the 5 subscales.
 - **Iterate** over each unique `contrast_label` (specifically `c('Morning_vs_Evening', 'Morning_vs_Intermediate', 'Evening_vs_Intermediate')`) and recalculate significance status for each alpha threshold **{0.01, 0.0125, 0.015}** (explicitly defined as a constant vector) **without re-fitting models**.
 - Generate a summary table listing significance status for **every MFQ subscale contrast** at each threshold.
 - **Output**: Save sensitivity table to `data/derived/sensitivity_sweep.csv` with columns: `subscale`, `contrast_label`, `alpha_threshold`, `p_value`, `significant` (boolean).
 - **Include**: Cronbach's alpha values (read from `data/derived/reliability_metrics.csv` calculated in T018 and `meq_reliability.csv` from T018.5) in the report.
 - **Include**: Data Exclusion Summary section (read from `data/derived/exclusion_counts.json` generated in T011/T012.5).
 - **Note**: This task generates the CSV data. It does NOT render the report.
- [X] T028 [US3] Generate `reports/chronotype_moral_analysis.html` (or PDF). **Depends on**: T019, T018, T018.5, T012.5, T027. **Reads `data/derived/sensitivity_sweep.csv` generated by T027**.
- [X] T029 [US3] Implement `code/05_validate_report.R`: Parse report, verify presence of all required sections (SC-003).

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T030 [P] Create `docs/README.md` with Setup, Run, and Data Source Note sections (replaces vague "Update documentation")
- [X] T031 [P] Code cleanup and refactoring: Run `lintr::lint_dir("code/", linters = list(cyclocomp_linter(limit = 10)))` to ensure cyclomatic complexity < 10, remove unused imports, and verify no TODOs remain. **Output**: Generate `reports/lint_report.txt` with the lint results. (Specific, Executable Criteria).
- [X] T032 [P] [US3] Validate `quickstart.md` (Depends on T005.5)
- [X] T033 [P] [US1/US2/US3] Verify CI runner compatibility: Create `.github/workflows/ci.yml` and execute it to produce `logs/ci_run.log` as evidence of compatibility with constrained CPU and limited RAM environments.
- [X] T034 [P] [US1/US2/US3] Add explicit "Data Source Note" to `README.md` and `code/01_ingest.R` header clarifying that the pipeline requires a user-provided merged CSV and will abort if columns are missing, preventing accidental synthetic fallbacks.
- [X] T035 [P] [US3] Add a "Limitations" section to `reports/chronotype_moral_analysis.html` explicitly stating the observational nature of the study and the lack of causal inference, per Spec Assumptions.
- [X] T036 [US1] Implement `code/08_low_balance_alert.R`:
 - **Depends on**: T012.5 (Hard Gate).
 - **Logic**: Read `data/derived/classified_data.csv`. Calculate the proportion of participants in the "intermediate" chronotype group.
 - **Action**: If proportion > 0.70, generate a warning file `data/derived/low_balance_alert.txt` with a clear message suggesting recruitment of extreme-type participants. **Also log to `logs/low_balance.log`** to satisfy FR-006's "log all" requirement.
 - **Report Integration**: **Add a code chunk in `code/04_report.Rmd` (T026) that reads `data/derived/low_balance_alert.txt` and prints its content if the file exists.**

- [X] T037 [US1/US2] Implement `code/09_vif_visualization.R`:
 - **Depends on**: T019 (Hard Gate).
 - **Logic**: Read `data/derived/ancova_results.csv` (which contains VIF flags). Generate a bar plot of VIF values for all predictors across all 5 models.
 - **Output**: Save plot to `reports/vif_visualization.png`.
 - **Report Integration**: Include `reports/vif_visualization.png` in `code/04_report.Rmd` (T026) to provide visual evidence of collinearity checks.

- [X] T038 [US3] Implement `code/10_power_analysis.R`:
 - **Depends on**: T019 (Hard Gate).
 - **Logic**: Use the `pwr` package to conduct a post-hoc power analysis for the observed effect sizes (Cohen's f) from the ANCOVA results, assuming α = 0.01.
 - **Output**: Save power summary to `data/derived/power_analysis.csv` and generate a text summary for the report.
 - **Report Integration**: Ensure the G*Power summary section in `code/04_report.Rmd` (T026) reads and displays these calculated power values instead of generic placeholders.

---

## Phase 7: Final Verification & Handoff

**Purpose**: Final checks to ensure the pipeline is ready for execution on the free-tier runner with real data.

- [X] T039 [US1/US2/US3] [FR-001] [FR-006] [FR-007] Create `tests/testdata/schema_check_valid.csv` with **160 rows** of valid data types (n > 159) to verify column presence, type casting, **and** logic for exclusion rates (T012.5) and group balance (T036).
 - **[FR-001] [FR-006] [FR-007] See FR-001, FR-006, FR-007**.
 - **Strict Isolation**: This file is **ONLY** for CI schema and logic validation. **It MUST NOT be used for generating scientific results** (e.g., ANCOVA p-values), as it is synthetic. The pipeline must explicitly check for a test flag before loading this file for any logic validation.
 - **Content**: Exactly 160 rows with valid columns: `MEQ_score` (numeric), `MFQ_care` (numeric), `MFQ_fairness` (numeric), `MFQ_loyalty` (numeric), `MFQ_authority` (numeric), `MFQ_sanctity` (numeric), `PSQI` (numeric), `age` (numeric), `sex` (character), `acute_sleepiness` (numeric). The data distribution should be random but valid to ensure exclusion rate and group balance calculations are non-trivial and mathematically defined. **NO synthetic data values for analysis.**
 - **Rationale**: Replaces the 1-row `schema_check.csv` to satisfy the Spec Assumption of minimum n=159, ensuring that T036 (balance alert) and T012.5 (exclusion rate) can be tested with meaningful data.

- [X] T040 [US1/US2/US3] [FR-001] Create `tests/testdata/missing_columns.csv` with missing `acute_sleepiness` column to verify T011 aborts correctly.
 - **[FR-001] See FR-001**.
 - **Strict Isolation**: This file is **ONLY** for CI smoke tests. Must require `--mode=test`.
 - **Content**: Exactly 5 rows with all columns EXCEPT `acute_sleepiness`.

- [X] T041 [US1/US2/US3] [FR-006] [FR-007] Create `tests/testdata/high_exclusion_meq.csv` with 25 rows having `NA` in `MEQ_score` (out of 100 rows) to verify T011/T012.5 aborts correctly.
 - **[FR-006] [FR-007] See FR-006, FR-007**.
 - **Strict Isolation**: This file is **ONLY** for CI smoke tests. Must require `--mode=test`.
 - **Content**: Exactly 100 rows. 25 rows have `NA` in `MEQ_score`. 75 rows are valid. This triggers the >20% exclusion rate for MEQ.

- [X] T042 [US1/US2/US3] Write `run_all_tests.sh` script that executes `testthat::test_dir("tests")`, runs `code/06_benchmark_accuracy.R --mode=test`, runs `code/01_ingest.R` with `tests/testdata/missing_columns.csv` (verifying abort), runs `code/02.5_final_exclusion_check.R` with `tests/testdata/high_exclusion_meq.csv` (verifying abort), and renders `code/04_report.Rmd` using `tests/testdata/schema_check_valid.csv` (verifying logic on n=160).

- [X] T043 [US3] Update `quickstart.md` to include a "Troubleshooting" section explaining the specific abort conditions (missing columns, >20% exclusion) and how to fix them.

---

## Phase 8: Data Acquisition Strategy & Execution

**Purpose**: Define the concrete path to obtaining the real data required for the primary analysis, addressing the "Missing Data Source" gap identified in the plan.

**Goal**: Establish a reproducible, verifiable method to fetch the required real data (MEQ, MFQ, PSQI, Acute Sleepiness) or document the specific manual step required, ensuring the pipeline never falls back to synthetic data for primary results.

- [X] T044 [US1/US2] [FR-001] [Data Strategy] Implement `code/04_fetch_data.R` (Optional/Manual Trigger):
 - **Purpose**: Provide a script that attempts to fetch real data from known sources if available, or generates a structured "Data Request" template.
 - **Logic**:
 1. Attempt to load `data/raw/study_data.csv` if it exists.
 2. If missing, check for a configuration file `data/raw/data_source_config.yaml`.
 3. **Schema**: `data_source_config.yaml` must contain `source_type` (url/package), `source_id` (URL or package name), and `access_method` (download/load_dataset).
 4. **Example Configuration**: Provide a concrete example in the script: `source_type: url`, `source_id: ""`, `access_method: download`.
 5. If a URL is provided, attempt to download and validate the file (using `curl` or `download.file`).
 6. **CRITICAL**: If download fails or data is invalid, **ABORT** with a clear error message instructing the user to manually provide the file. **DO NOT** generate synthetic data.
 7. If no config is provided, generate a `data_raw/README_DATA_NEEDED.md` file that explicitly lists the required columns and suggests where the user can find or collect this data (e.g., "Contact Prolific for raw survey data", "Merge OSF MFQ dataset with local MEQ logs"). **Exact Content**: The generated README must contain the text: "Required Columns: MEQ_score, MFQ_care, MFQ_fairness, MFQ_loyalty, MFQ_authority, MFQ_sanctity, PSQI, age, sex, acute_sleepiness. No public dataset contains all these variables. You must provide this file manually or via a custom merge."
 - **Constraint**: This script must **NOT** be run automatically in CI unless `data/raw/study_data.csv` is present. It is a developer/researcher tool for data acquisition.

- [X] T045 [US1/US2] [FR-001] Create `data/raw/README_DATA_NEEDED.md`:
 - **Content**: A clear, human-readable document explaining that the pipeline requires a specific merged CSV.
 - **Details**:
 - List all required columns: `MEQ_score`, `MFQ_care`, `MFQ_fairness`, `MFQ_loyalty`, `MFQ_authority`, `MFQ_sanctity`, `PSQI`, `age`, `sex`, `acute_sleepiness`.
 - Provide a **template CSV** (empty or with 1 row of dummy data) in `data/raw/template_data.csv` for users to fill.
 - Explain the "Acute Sleepiness" requirement (FR-007) and suggest collection methods (24h diary, actigraphy).
 - State clearly: "No public dataset currently contains all these variables. You must provide this file manually or via a custom merge."
 - **Validation**: Ensure this file is included in the repository and referenced in `quickstart.md`.

- [X] T046 [US1/US2] [FR-001] Update `tests/test-classify.R` to explicitly test that the pipeline **ABORTS** if `data/raw/study_data.csv` is missing and no test flag is set (ensuring no silent synthetic fallback).

- [X] T047 [US1/US2] [SC-002] Implement `code/08_generate_ci_fallback.R`:
 - **Purpose**: Generate a small, deterministic synthetic dataset for CI fallback only when real reference data is missing (for T024).
 - **Logic**:
 1. Check if `data/raw/reference_data.csv` exists.
 2. If missing, generate a small dataset (n=10) with known, deterministic p-values (e.g., using a fixed seed and simple linear model).
 3. **Mark Output**: Save this file as `data/derived/ci_fallback_reference.csv` and include a metadata column `source="CI_FALLBACK_SYNTHETIC"`.
 4. **Constraint**: This file is **ONLY** for CI fallback. It is **NOT** used for primary analysis or SC-002 verification if real data exists.
 - **Usage**: Called by T024 when real reference data is missing. **NOTE: T024 now fails if real data is missing; this task is kept for internal CI debugging only if the CI environment is explicitly configured to allow synthetic fallbacks (which is not the default for SC-002).**

---

## Phase 9: Revision & Review Resolution

**Purpose**: Address specific reviewer concerns regarding data flow, reproducibility, and edge case handling identified in prior analysis.

- [X] T048 [US1] [Const-I] [Review: Data Flow] Implement `code/01.5_validate_data_flow.R` to explicitly verify that the output of T011 (`cleaned_data.csv`) is consumed as the **sole** input for T012 (`classify.R`). This task adds a runtime assertion that `cleaned_data.csv` is created *before* `classify.R` is invoked, preventing race conditions in parallel CI environments. **Moved to Phase 2**.
- [X] T049 [US1/US2] [Const-I] [Review: Reproducibility] Implement `code/03.1_seed_manager.R` to enforce a global random seed (e.g., `set.seed(2026)`) at the start of **every** script (ingest, classify, analysis, report). This ensures that any stochastic elements (e.g., bootstrapping for CIs, if added later) are fully reproducible across runs. **Moved to Phase 2**.
- [X] T050 [US1] [Review: Edge Cases] Enhance `code/02_classify.R` to handle **non-numeric** `MEQ_score` values (e.g., strings like "N/A", "Unknown") by attempting a strict numeric coercion and logging a specific `reason=non_numeric_meq` exclusion, distinct from `invalid_meq` (out of range).
- [X] T051 [US2] [Review: Statistical Rigor] Implement `code/03.2_assumption_check.R` to run Levene's test for homogeneity of variance and Shapiro-Wilk for normality of residuals for each ANCOVA model. Log violations to `logs/assumption_violations.log` and include a "Assumptions Check" table in the final report (T026) to satisfy reviewer demands for statistical transparency.
- [X] T052 [US3] [Review: Reporting] Add a "Data Provenance" section to `code/04_report.Rmd` (T026) that explicitly lists the checksum (MD5) of the input `data/raw/study_data.csv` and the exact git commit hash used to generate the report, ensuring full traceability of results to specific data and code versions.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Validation Sub-Phases (3.1, 4.1, 5.1)**: Depend on their respective Implementation Phases (3, 4, 5)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Data Acquisition (Phase 8)**: Can be started in parallel with Phase 3/4, but the *execution* of the analysis (T019) is blocked until real data is present.
- **Revision & Review (Phase 9)**: Must be completed after Phase 3-5 implementation to ensure all reviewer concerns are addressed before final handoff.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 output (`classified_data.csv`)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 output (`ancova_results.csv`)

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

### Hard Gates

- **T011 & T012.5**: Must complete successfully (exclusion rate <= 20%) before T019 (ANCOVA) or T026 (Report) can start. If T011 or T012.5 aborts, the pipeline stops immediately.
- **T019**: Must complete before T024 (Regression Test) and T027 (Sensitivity) can start.
- **Data Presence**: T019 and T026 will skip or abort if `data/raw/study_data.csv` is missing, unless running in test mode with synthetic data.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for chronotype thresholds in tests/test-classify.R"
Task: "Unit test for missing data handling in tests/test-classify.R"

# Launch all models for User Story 1 together:
Task: "Implement code/01_ingest.R"
Task: "Implement code/02_classify.R"
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
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Data Constraint**: The pipeline requires a user-provided merged dataset. No synthetic data generation is permitted for primary analysis.
- **Compute Constraint**: All tasks must run on free CPU-only CI with limited resources. No GPU or heavy model loading.
- **Data Hygiene**: Raw data in `data/raw/` must never be modified. All derived files go to `data/derived/`.
- **Psychometric Transparency**: Cronbach's alpha must be calculated and reported in the final output for **both** MEQ and MFQ (T018 and T018.5). **T018.5 now checks for raw items first.**
- **VIF Handling**: Pipeline must **Flag as Invalid** (not abort) if VIF > 2, per FR-006 and Assumptions.
- **Exclusion Reporting**: All exclusions (missing acute_sleepiness, out-of-range MFQ) must be logged and summarized in the final report.
- **Reliability Metrics**: Cronbach's alpha must be computed for all MFQ subscales (T018) and MEQ (T018.5) and saved to `data/derived/reliability_metrics.csv` for inclusion in the report (T027).
- **Sensitivity Analysis**: The sensitivity sweep must explicitly re-calculate significance status from existing p-values **without re-fitting models** to ensure efficiency, and must iterate over **all pairwise contrasts** (T019 output) to cover every required pairwise comparison (SC-004). **Explicit thresholds**: {0.01, 0.0125, 0.015}.
- **Exclusion Threshold**: The 20% exclusion rate check is a **hard gate** performed **at the end of the classification step** (T012.5) after all exclusions are complete, calculated against the *original* dataset size, **including** rows missing acute_sleepiness in the calculation.
- **Reference Baseline**: T024 now requires a real dataset for primary comparison; synthetic data is strictly a CI fallback and explicitly marked as such. **T024 now fails if real data is missing.**
- **Synthetic Data**: T014.1 uses synthetic data ONLY for SC-001 testing with a hard `--mode=test` flag and strict output path enforcement (`data/benchmark/`) to prevent leakage. **T014.1 now includes label noise to prevent tautology.**
- **Low Group Balance**: T036 implements the specific alert mechanism for >70% intermediate group dominance, ensuring the report reflects this limitation and logs to `logs/low_balance.log`.
- **Collinearity Visualization**: T037 adds a visual check for VIFs to complement the numeric flags, improving transparency for reviewers.
- **Power Analysis**: T038 ensures the post-hoc power analysis is calculated from the actual observed effect sizes, providing a more accurate G*Power summary than generic estimates.
- **Test Data Generation**: T039-T041 ensure robust CI testing by covering valid, missing column, and high exclusion scenarios, with strict isolation constraints and explicit row counts. **No synthetic data values are generated. T039 is strictly for schema validation.**
- **CI Automation**: T042 provides a single entry point for running all verification steps, including explicit abort tests.
- **Documentation**: T043 ensures users understand failure modes via `quickstart.md`.
- **Data Acquisition**: T044-T046 address the critical "Missing Data Source" gap by providing a structured, non-synthetic path for data acquisition and clear documentation for researchers.
- **Validation Phases**: Phases 3.1, 4.1, and 5.1 explicitly separate validation tasks from implementation tasks to ensure correct ordering.
- **T019.5 Removed**: The synthetic reference task T019.5 has been removed to comply with Constitution Principle II. SC-002 is now handled strictly by T024 using real data, with a CI fallback.
- **T010.5 Added**: Added to capture original row count for accurate exclusion rate calculation.
- **T018.5 Updated**: Added conditional check for raw MEQ items.
- **T024 Updated**: Removed "pass if no data" fallback; now fails if reference data is missing.
- **T027 Updated**: Explicitly listed alpha thresholds {0.01, 0.0125, 0.015}.
- **T031 Updated**: Specified output artifact `reports/lint_report.txt`.
- **T028 Updated**: Added T027 to explicit dependency list.
- **T039-T041 Updated**: Replaced synthetic data generation with schema-only tests. **T039 explicitly forbidden for logic tests.**
- **T012.5 Updated**: Now includes ALL exclusion types (including missing acute_sleepiness) in the rate calculation to satisfy FR-006.
- **T019 Updated**: Removed MANCOVA implementation to align with Spec FR-003.
- **T006.1 Added**: Created config file to explicitly disable MANCOVA.
- **T047 Added**: Created CI fallback generator for reference data.
- **T010.1 Added**: Added file existence check with clear error message.
- **T005.1 Added**: Added state management infrastructure.
- **T014 Split**: T014 split into T014.1 (Generate Artifact) and T014.2 (Verify Accuracy) to ensure benchmark dataset is a persistent, reusable artifact. **T014.1 moved to Phase 2.**
- **Phase 9 Added**: New phase to address specific reviewer concerns regarding data flow, reproducibility, statistical assumptions, and reporting provenance.
- **T048 Added**: Data flow validation to prevent race conditions. **Moved to Phase 2.**
- **T049 Added**: Global seed management for full reproducibility. **Moved to Phase 2.**
- **T050 Added**: Enhanced handling of non-numeric MEQ scores.
- **T051 Added**: Statistical assumption checks (Levene's, Shapiro-Wilk) for transparency.
- **T052 Added**: Data provenance tracking (checksums, git hash) in the final report.
- **T039 Updated**: Replaced 1-row `schema_check.csv` with 160-row `schema_check_valid.csv` to satisfy Spec Assumption of n=159, enabling valid testing of exclusion rate and group balance logic.