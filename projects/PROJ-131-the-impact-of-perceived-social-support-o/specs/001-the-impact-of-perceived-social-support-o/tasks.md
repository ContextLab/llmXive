# Tasks: The Impact of Perceived Social Support on Resilience to Online Harassment

**Input**: Design documents from `/specs/001-social-support-resilience/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

**⚠️ CRITICAL METHODOLOGICAL NOTE**:
The implementation **strictly follows the Plan's 'Revised Approach'** (Single-Dataset Analysis). The Spec's requirement for a 'Synthetic Cohort' (dual-dataset matching) is **methodologically invalid** per the Plan and is **excluded** from implementation. The pipeline ingests the Cyberbullying Survey to ensure the interaction term estimates a genuine psychological buffering effect without confounding by dataset source. [UNRESOLVED-CLAIM: c_b6e80fbe — status=not_enough_info]

## Format: `[ID] [P?] [Story] description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root
- **Project Root**: `projects/PROJ-131-the-impact-of-perceived-social-support-o/`

<!--
 ============================================================================
 IMPORTANT: The tasks below reflect the revised, single-dataset workflow
 as mandated by the Plan's 'Revised Approach'.
 ============================================================================
-->

## Phase 1: Setup & Kickback (Shared Infrastructure & Methodology Alignment)

**Purpose**: Project initialization and resolution of the spec/plan conflict. **Must run first to establish directory structure.**

- [ ] T001 [P] **Create Project Structure**: Create the directory hierarchy defined in the plan.
 **Action**:
 1. `cd projects/PROJ-131-the-impact-of-perceived-social-support-o/`
 2. Run `mkdir -p code/data code/analysis code/config code/tests data/raw data/results`.
 **Verification**: Run `tree code/ > data/results/setup_verification.txt` and `tree data/ >> data/results/setup_verification.txt`.
 **Deliverable**: Directory structure created and `data/results/setup_verification.txt` containing the tree output.
 **Dependency**: None (Standard setup).

- [ ] T002 [P] **Initialize Git Repository**: Initialize the git repository for the project.
 **Action**:
 1. `cd projects/PROJ-131-the-impact-of-perceived-social-support-o/`
 2. Run `git init`.
 **Verification**: Run `git status > data/results/git_status.log`.
 **Deliverable**: `.git` directory created and `data/results/git_status.log` containing the status output.
 **Dependency**: T001.

- [ ] T003 [P] **Create.gitignore**: Create a `.gitignore` file to exclude `data/raw/`, `data/results/`, `__pycache__/`, and `*.pyc`.
 **Action**:
 1. `cd projects/PROJ-131-the-impact-of-perceived-social-support-o/`
 2. Create file at repository root with EXACT content:
 ```
 data/raw/
 data/results/
 __pycache__/
 *.pyc
.env
 ```
 **Verification**: Run `cat.gitignore > data/results/gitignore_content.txt`.
 **Deliverable**: `.gitignore` file with correct entries and `data/results/gitignore_content.txt`.
 **Dependency**: T001.

- [X] T004 [P] **Define Scoring Scales**: Create `config/scales.yaml` defining standard scoring weights for CES‑D, GAD‑7, and PCL‑5. **[FR-006] [SC-002]**
 **Action**:
 1. Ensure `code/config/` directory exists (`mkdir -p code/config`).
 2. Create `code/config/scales.yaml` with the following content:
 ```yaml
 # Values derived from official instrument documentation:
 # 1. CES-D: Radloff, L. S. (n.d.). The CES-D Scale: A self-report depression scale for research in the general population.
 # - Items with negative indices and 6, 9, 10, 13, 14, 16, 17: Sum raw scores (0-3).
 # - Items 5, 7, 8, 11, 12, 15, 18, 19, 20: Reverse score (0->3, 1->2, 2->1, 3->0) then sum.
 # - Total Score: Sum of all items (Range from a minimum to a maximum possible value).
 # 2. GAD-7: Spitzer, R. L., et al. (2006). A Brief Measure for Assessing Generalized Anxiety Disorder.
 # - Items corresponding to the target construct: Sum raw scores (0-3). Total Score (Range 0-21).
 # 3. PCL-5: Weathers, F. W., et al. (2013). The PTSD Checklist for DSM-5 (PCL-5).
 # - Items: Sum raw scores. Total Score (Range non-negative).
 # NOTE: The dataset may provide aggregate scores directly. If raw items are missing, use the aggregate columns.
 # If raw items are missing, verify that the provided aggregate scores match the standard algorithm (e.g., by comparing a sample).
 CES-D:
 variable: 'depression' # Mapped from spec's Data Dictionary
 type: 'aggregate_score' # Or 'raw_items' if dataset provides them
 reverse_items: [5, 7, 8, 11, 12, 15, 18, 19, 20] # 1-indexed relative to raw item list
 GAD-7:
 variable: 'anxiety' # Mapped from spec's Data Dictionary
 type: 'aggregate_score' # Or 'raw_items' if dataset provides them
 PCL-5:
 variable: 'ptsd' # Mapped from spec's Data Dictionary
 type: 'aggregate_score' # Or 'raw_items' if dataset provides them
 ```
 **Verification**: Cross-reference these weights against the official instrument documentation (cited above) before hard-coding. **If raw items are missing, log a warning `W-AGGREGATE-SCORES-001` and verify the aggregate scores against the standard algorithm (e.g., by comparing a sample).**
 **Instruction**: The `variable` keys must match the column names from the spec's Data Dictionary (`depression`, `anxiety`, `ptsd`).
 **Constraint**: **If raw items are present in the dataset, the scoring logic MUST use them to calculate the scores. It cannot lazily use pre-aggregated columns.** If only aggregate columns are present, the code must verify them against the standard algorithm (e.g., by comparing a sample) and log a warning.
 **Deliverable**: `code/config/scales.yaml` AND `code/logs/scale_verification.txt` confirming the source URLs, DOIs, or document titles used.
 **Dependency**: T001.

- [X] T005 [US1] **Implement `tests/test_scales.py`**: Unit tests verifying scoring logic matches the definitions in `config/scales.yaml`. **Dependency**: Must run after T004.
 **Action**: Create `tests/unit/test_scales.py` with the following test cases:
 1. `test_cesd_scoring`: The research question is whether a specific input pattern can be transformed into a corresponding output. The method involves processing an input sequence containing repeated values to generate a quantitative result, as described in [Reference]. The output will be a non-zero value derived from the input sequence.
 2. `test_gad7_scoring`: Input `[, 1, 2, 3, 0, 1, 2]` (all 3s) -> Output `21`.
 3. `test_reverse_coding`: Input `[, 1, 2, 3]` (reverse items) -> Output `[3, 2, 1, 0]`.
 **Dependency**: T004.

- [X] T006 [P] **Setup `code/data/ingestion.py` skeleton**: Create with read‑only raw data validation logic. <!-- FAILED: unspecified -->

- [X] T007 [P] **Create `code/data/cohort.py` skeleton**: Create empty file with docstring and function stubs for `load_cohort` and `filter_cohort`.
 **Action**: Create `code/data/cohort.py` with a docstring explaining its purpose and two empty function definitions: `def load_cohort(): pass` and `def filter_cohort(df): pass`.
 **Deliverable**: `code/data/cohort.py` with stubs.
 **Dependency**: T001.

- [ ] T008 [P] **Configure `main_pipeline.py` entry point**: Orchestrate modular steps (skeleton creation).

- [X] T009 [P] **Setup environment configuration**: Create `config/seeds.yaml` to define reproducible seeds.
 **Content**:
 ```yaml
 random_seed: 42
 ```
 **Instruction**: Ensure the file contains valid YAML with the integer value `42` for `random_seed`. This seed will be used for all random operations (imputation, bootstrapping, sampling).
 **Dependency**: T001.

- [X] T053c [P] [Plan-Constraints] **Define Bootstrap Configuration Data Model**: Create `code/config/bootstrap_config.yaml` to explicitly define the 'Bootstrap Configuration' Data Model entity.
 **Requirement**: This file must specify the resample count, confidence level, method (BCa), and seed source.
 **Action**: Link this configuration to the 'Technical Context' constraints in the plan.
 **Verification**: Ensure `main_pipeline.py` loads this config before running T021.
 **Dependency**: Must run after T009 (seeds.yaml).
 **Content**:
 ```yaml
 resample_count:
 confidence_level: a standard high threshold (e.g., 95%)
 method: 'bca'
 seed: 42
 ```

**Checkpoint**: Foundation ready – user story implementation can now begin in parallel.

---

## Phase 0.0: Data Source Provisioning (Blocking Prerequisite)

**Purpose**: ACQUIRE the mandatory real data source (Cyberbullying Survey 2021) if it is missing. This phase MUST complete before Phase 0.5. **T070-Init is the entry point.**

- [ ] T070-Init [P] **Initialize Data Source Provisioning**: Check if the "Cyberbullying Survey 2021" dataset ID/URL exists in `code/config/data_sources.yaml`.
 **Action**:
 1. Read `code/config/data_sources.yaml`.
 2. If the URL/ID is present and valid, proceed to T070a-Block.
 3. If the URL/ID is missing or the file does not exist, **create a placeholder** `code/config/data_sources.yaml` with `status: 'pending_user_input'` and log `E-NO-SOURCE-001: Data source missing. Manual intervention required. Please provide the verified URL for Cyberbullying Survey 2021.`
 4. **Do NOT halt the entire project indefinitely**; instead, update the config and log the error. The pipeline will halt at T070a-Block if the placeholder is not replaced, but this task ensures the "missing" state is handled gracefully and explicitly.
 **Deliverable**: `code/config/data_sources.yaml` with either a valid URL or a `pending_user_input` status.
 **Constraint**: Do NOT hard-code a specific dataset ID. Read from config. If config is missing, attempt to find one; if not found, mark as pending.
 **Dependency**: T001 (Ensure directory exists).

- [ ] T070-Resolve [P] **Resolve Missing Data Source**: Handle the case where the data source is missing by reading from environment variable or prompting.
 **Action**:
 1. Check for environment variable `DATA_SOURCE_URL`.
 2. If present, update `code/config/data_sources.yaml` with this URL and set `status: 'resolved'`.
 3. If not present, log `E-NO-SOURCE-002: No environment variable DATA_SOURCE_URL found. Manual intervention required.` and halt the pipeline.
 **Deliverable**: Updated `code/config/data_sources.yaml` or a halted state.
 **Dependency**: T070-Init.

- [ ] T070a-Block [P] **Check Data Source Availability**: Check if the verified URL or dataset ID for the Cyberbullying Survey 2021 exists in `code/config/data_sources.yaml` and is not in a `pending_user_input` state.
 **Action**:
 1. Read `code/config/data_sources.yaml`.
 2. If the URL/ID is present and valid, proceed to T070a-Verify.
 3. If the URL/ID is missing, invalid, or `pending_user_input`, **raise `DataSourceMissingError`** with message "E-NO-SOURCE-002: Data source not found or pending. Manual intervention required." This error halts the pipeline and requires user input.
 **Deliverable**: `code/config/data_sources.yaml` with the URL/ID or the error log.
 **Constraint**: Do NOT hard-code a specific dataset ID. Read from config. If config is missing the specific ID, HALT.
 **Dependency**: T070-Init, T070-Resolve.

- [X] T070c [P] **Document Waiting State**: Create `data/results/waiting_for_data.log` if T070a-Block fails due to `pending_user_input`.
 **Action**: Write a log file explaining that the pipeline is paused pending user input for the data source.
 **Deliverable**: `data/results/waiting_for_data.log`.
 **Dependency**: Must run after T070a-Block if it fails.

- [ ] T070a-Verify [P] **Verify Data Source Configuration**: Write a script `code/data/verify_source.py` that checks the dataset configuration.
 **Action**: Read the dataset ID/URL from `code/config/data_sources.yaml`. If the URL/ID is missing, raise `RuntimeError` "E-NO-SOURCE-CONFIG: Configuration missing. Aborting." If present, attempt to fetch the dataset (or check local file). If fetch fails (network error, ID not found) AND local file is missing, raise `RuntimeError` "E-NO-REAL-SOURCE-001: Real data source not found. Aborting."
 **Success**: If the dataset loads successfully (via network fetch OR local file check in `data/raw/`), log `INFO: Source verified`.
 **Deliverable**: `code/data/verify_source.py` and execution log confirming success or halting with E-NO-REAL-SOURCE-001.
 **Dependency**: Must run after T070-Init and T070a-Block.

- [ ] T070b [US1] **Verify Data Columns**: Inspect the loaded dataset from T070a-Verify to confirm the presence of the `platform` column.
 **Action**:
 1. Load the dataset (using the verified source from config).
 2. **Log the full list of column names to `data/results/column_inspection.log`** (e.g., "Columns found: col1, col2,...").
 3. Check if `platform` exists.
 4. **Write `data/results/platform_status.json`** with keys: `platform_exists` (boolean), `platform_categories` (list of unique values if exists). **If `platform` is missing, set `platform_exists: false` and `platform_categories: []`. Do not skip writing the file.**
 **Deliverable**: `data/results/platform_status.json` and `data/results/column_inspection.log`.
 **Dependency**: Must run after T070a-Verify.

- [X] T071 [US1] **Finalize Data Source Config**: Update `code/config/data_sources.yaml` with the verified source ID and method. <!-- FAILED: unspecified -->
 **Action**: Write `dataset_id: <verified_id>`, `source: <source_type>`, `verified: true` to the config file. **Constraint**: This config MUST be committed as a static file. Do NOT allow runtime updates to the ID.
 **Dependency**: Must run after T070a-Verify and T070b. (If T070a-Verify fails, this task is skipped).

---

## Phase 0.5: Spec Correction Gate (Blocking Prerequisite)

**Purpose**: Ensure `spec.md` is aligned with the Plan's single-dataset approach BEFORE any implementation tasks begin. This phase MUST complete before Phase 1. **T072a is the entry point.**

- [X] T072a [P] **Verify Spec Alignment (FR-001/FR-002)**: Verify that `specs/001-social-support-resilience/spec.md` contains the "REMOVED" or "DEPRECATED" blocks for FR-001/FR-002 and "REVISED" block for SC-001.
 **Action**: Read the file and assert the presence of the required deprecation/revision text. **Also check that the phrase "Synthetic Cohort" does NOT appear as an active, proposed, or valid step.** It is acceptable if the phrase appears ONLY within a "Rejection" or "Invalid" section (e.g., under "Rejection of Dual-Dataset Matching"). **If FR-001/FR-002 are absent entirely (not marked REMOVED), this is considered FAIL.**
 **Success**: If the spec is already aligned (i.e., no active proposal of Synthetic Cohort and FRs marked REMOVED), log `INFO: Spec state verified as per Plan requirements.` and proceed.
 **Failure**: If the spec is NOT aligned (e.g., "Synthetic Cohort" narrative found as a proposed step, or FRs missing "REMOVED" marker), log `ERROR: Spec state mismatch.` and **HALT** the pipeline. **Manual intervention required to update spec.md.**
 **Deliverable**: Log confirmation.
 **Dependency**: None (independent of T001). **Status: PENDING** until spec alignment is confirmed.

- [X] T073a [P] **Verify Data Dictionary Alignment**: Verify that the Data Dictionary in `spec.md` lists the Cyberbullying Survey 2021 as the **sole** source for all variables. <!-- FAILED: unspecified -->
 **Action**: Check if every row in the Data Dictionary table has "(Sole Source)" in the "Source" column.
 **Success**: If aligned, log `INFO: Data Dictionary verified.` and proceed.
 **Failure**: If not aligned, log `ERROR: Data Dictionary mismatch.` and **HALT** the pipeline. **Manual intervention required to update spec.md.**
 **Deliverable**: Log confirmation.
 **Dependency**: None (independent of T001). **Status: PENDING** until spec alignment is confirmed.

- [X] T074a [P] **Verify Methodological Notes Alignment**: Verify that Section 5 "Methodological Notes" in `spec.md` contains the "Revised Approach" rationale and handles the "Synthetic Cohort" mention correctly.
 **Action**: Check if Section 5 contains the "Revised Approach" text. Check that the phrase "Synthetic Cohort" appears ONLY within the "Rejection of Dual-Dataset Matching" section (i.e., in the context of rejection). **Explicitly allow the phrase if it is used to describe the rejected approach.**
 **Success**: If aligned, log `INFO: Methodological Notes verified.` and proceed.
 **Failure**: If not aligned, log `ERROR: Methodological Notes mismatch.` and **HALT** the pipeline. **Manual intervention required to update spec.md.**
 **Deliverable**: Log confirmation.
 **Dependency**: None (independent of T001). **Status: PENDING** until spec alignment is confirmed.

---

## Phase 3: User Story 1 - Data Ingestion & Cohort Preparation (Priority: P1) 🎯 MVP

**Goal**: Ingest the Cyberbullying Survey 2021, harmonize variables, handle missingness, and prepare a clean analysis cohort. **Note**: The GSS dataset is excluded per the Plan's 'Revised Approach'. **T017 (Logging) must run first to ensure all processing is logged.**

### Tests for User Story 1 (OPTIONAL)

- [X] T010 [P] [US1] Contract test for data schema in `tests/contract/test_analysis_cohort_schema.py`
- [X] T011 [P] [US1] Unit test for CES‑D/GAD‑7 scoring logic in `tests/unit/test_scale_scoring.py`

### Implementation for User Story 1

- [ ] T017 [P] [US1] **Initialize Logging**: Set up the logging infrastructure for the pipeline.
 **Action**: Create `code/utils/logger.py` to initialize a logger that writes to `data/results/pipeline_run.log`. Ensure all subsequent tasks (T012-T016) use this logger.
 **Dependency**: T001 (Ensure `data/results` exists), T070a-Verify.

- [ ] T012 [US1] **[FR-003]** Implement `code/data/ingestion.py` to **download and load** the Cyberbullying Survey 2021 dataset:
 - **Source**: Use the dataset ID/URL from `code/config/data_sources.yaml` (verified in T070a-Verify).
 - **Harmonization**: Map raw columns to canonical names (`social_support`, `harassment_severity`, `depression`, etc.) as defined in the Data Dictionary.
 - **Validation**: Verify file integrity (checksum) and log E‑MISSING‑ if required items are absent.
 - **GSS Exclusion**: Do NOT attempt to load GSS 2022. If GSS is found in `data/raw`, log a warning that it is being ignored per the Plan's 'Revised Approach'.
 - **Fail Loudly**: If the real fetch fails, raise `RuntimeError` with message "Real data fetch failed. Aborting to prevent synthetic data fabrication."
 - **Dependency**: Must run after T070a-Verify, **T017**, T001.

- [ ] T013a-Config [P] [US1] **[FR-004]** **Configure MICE Imputation**: Configure the MICE imputer for the predictor matrix.
 **Action**: Define the predictor matrix as `['age','gender','education','income','social_support','harassment_severity']`. **If the `platform` column exists in the dataset (verified in T070b), include it in the matrix.** If `platform` is absent, log `W-NO-PLATFORM-001` and exclude it.
 **Configuration**: Use `sklearn.impute.IterativeImputer` with `m=5`, `max_iter=10`, `random_state=42`. **Use `max_iter=10` and `random_state=42` explicitly; do not rely on version-dependent defaults for these parameters.**
 **Dependency**: Must run after T012, T070b.

- [ ] T013a-Exec [P] [US1] **[FR-004]** **Execute MICE Imputation**: Apply Multiple Imputation by Chained Equation (MICE) to missing values in the **predictor matrix**.
 **Action**: Run the imputer configured in T013a-Config.
 **Constraint**: **Do not** impute the binary `harassment_exposure` directly. Impute the continuous `harassment_severity` first.
 **Dependency**: Must run after T013a-Config.

- [ ] T013a-Check [P] [US1] **[FR-004]** **Check MICE Convergence**: Verify that the MICE imputation converged.
 **Action**: Check the convergence status of the imputer.
 **Failure Handling**: If MICE fails to converge, log error `E-MICE-NONCONV-001` and **HALT** the pipeline. **Do NOT fall back to listwise deletion for predictors.** This is a deliberate design choice to prevent data fabrication or weak imputation; FR-004's "listwise deletion" applies only to outcome missingness (T013d), not predictor imputation failure. Halting is the correct behavior to preserve predictor matrix integrity.
 **Dependency**: Must run after T013a-Exec.

- [ ] T013b [US1] **Derive Binary Exposure**: Derive the binary `harassment_exposure` variable from the imputed `harassment_severity`.
 **Action**: `exposure = 1 if severity > 0 else 0`.
 **Dependency**: Must run after T013a-Check.

- [ ] T013c-Check [US1] **Check PCL-5 Availability**: Verify if PCL-5 columns exist in the dataset.
 **Action**: Check for PCL-5 columns. Log `W-PCL5-MISSING` if absent.
 **Deliverable**: Log entry.
 **Dependency**: Must run after T012.

- [ ] T013c-Score-Raw [US1] **Score Raw PCL-5 Items**: If raw PCL-5 items exist, score them.
 **Action**: Use weights from T004 to score raw items.
 **Dependency**: Must run after T013c-Check (if raw items exist).

- [ ] T013c-Use-Aggregate [US1] **Use Aggregate PCL-5 Scores**: If raw items are missing, use pre-aggregated scores.
 **Action**: Use pre-aggregated `ptsd` column and log `W-AGGREGATE-SCORES-001`.
 **Dependency**: Must run after T013c-Check (if raw items missing).

- [ ] T013d-Filter [US1] **[FR-004]** **Handle Outcome Missingness**: Perform listwise deletion **only** on rows where critical outcome variables (`depression`, `anxiety`, `ptsd`) are missing **after** predictor imputation (T013a).
 **Constraint**: Do NOT perform listwise deletion on predictor variables before imputation. This is a distinct step from T013a (predictor imputation). **Ordering**: Impute predictors first, then delete rows with missing outcomes.
 **Dependency**: Must run after T013c-Score-Raw or T013c-Use-Aggregate.

- [ ] T014 [US1] Implement `code/data/cohort.py` to:
 1. Filter the dataset to remove rows with critical missing values (harassment_severity, social_support, or at least one mental health outcome) based on the output of T013d-Filter.
 2. Ensure `harassment_severity` has sufficient variance (SD > 0.5, N > 30). If not, log `E-LOW-VAR-001` and halt.
 3. Output `data/results/analysis_cohort.csv`.
 **Dependency**: Must run after T013d-Filter.

- [ ] T015 [US1] **Validate the analysis cohort**:
 - **Variance Check**: Check **variance of Harassment Exposure** (SD > 0.5, N > 30).
 - **Collinearity Check**: Compute **VIF** for the model matrix (`social_support`, `harassment_exposure`, interaction, plus covariates) using `statsmodels.stats.outliers_influence.variance_inflation_factor`.
 - **Centering**: Use `sklearn.preprocessing.StandardScaler` (with `with_mean=True`, `with_std=False`) to center variables before VIF calculation.
 - Ensure VIF < 5.
 - **Deliverable**: Generate `data/results/validation_report.json` containing the results of these checks (Pass/Fail status, calculated values).
 - **Logic**: If VIF >= 5 or Variance check fails, raise a `RuntimeError` with message "Cohort validity check failed. Aborting." to prevent downstream execution.
 - **Note**: This task implements the variance and collinearity checks required by the plan's 'Technical Context'.
 **Dependency**: Must run after T014.

- [ ] T016 [US1] Save the validated analysis cohort to `data/results/analysis_cohort.csv` **only after** successful T015.
 **Dependency**: Must run after T015. **Note: T016 runs ONLY if T015 passes. If T015 fails, T016 is skipped and the pipeline halts.** This task depends on the *output* of T015 (`validation_report.json` and pass status).

**Checkpoint**: User Story 1 is fully functional and produces a valid single-dataset cohort.

---

## Phase 4: User Story 2 - Interaction Analysis & Hypothesis Testing (Priority: P2)

**Goal**: Fit robust OLS models with interaction term, compute bias‑corrected bootstrapped CIs, and apply multiple‑comparison correction.

### Tests for User Story 2 (OPTIONAL)

- [ ] T018 [P] [US2] Contract test for regression results schema in `tests/contract/test_regression_results_schema.py`. **Note**: Validate schema for Cyberbullying Survey data only (no GSS references).
- [ ] T019 [P] [US2] Unit test for bootstrapping logic in `tests/unit/test_bootstrap_ci.py`

### Implementation for User Story 2

- [ ] T020 [P] [US2] Implement `code/analysis/models.py` to fit OLS models with heteroskedasticity‑consistent (HC3) standard errors for Depression, Anxiety, and PTSD (if PCL-5 present). Include interaction term `SocialSupport:HarassmentExposure`.
- [ ] T033 [P] [Plan-Constraints] **Bootstrap Runtime Estimator & Optimization**: Implement a pre-flight check in `code/analysis/models.py` to estimate bootstrap runtime and apply optimization if needed.
 **Requirement**: Run a quick "dry run" with a sufficient number of resamples using a **small representative subset of the full cohort** to estimate time per resample. If `1000 * estimated_time > 6 hours`, log error `E-COMPUTE-OVERFLOW-001` and **attempt to parallelize** the bootstrap using `multiprocessing` before halting. **Do not** reduce resamples to 500. Reducing resamples is strictly prohibited as it violates FR-007 and Constitution Principle I.
 **Action**: Read configuration from `code/config/bootstrap_config.yaml` (created in T053c). Ensure the resample count is strictly CPU-tractable on the available runner.; if the estimate is high, attempt parallelization. **Do not** reduce resamples to 500. Reducing resamples is strictly prohibited as it violates FR-007 and Constitution Principle I.
 **Data Source**: Use the `analysis_cohort.csv` generated by T016. If the cohort is sufficiently small to be fully processed, use the entire cohort..
 **Verification**: Run the dry-run on the CI runner and verify the estimated total time is logged and the pipeline halts only if parallelization fails to meet the limit.
 **Note**: This check runs BEFORE the full bootstrap in T021 to prevent overflow.
 **Dependencies**: T009, T053c, **T016**.
- [ ] T021 [P] [US2] Implement bootstrapping logic (Wikipedia: Bootstrapping (statistics), https://en.wikipedia.org/wiki/Bootstrapping_(statistics)) using `statsmodels.stats.bootstrap`. Seed the process with `random_seed` from `config/seeds.yaml`.
 **Dependency**: Must run after T033.
- [ ] T022 [P] [US2] Add fallback: if the robust model fails to converge, automatically refit a standard OLS model (no HCSE) and log status `E‑NONCONV‑001`.
- [ ] T023 [P] [US2] **[FR-008]** Implement Benjamini‑Hochberg FDR correction across the set of outcome tests (Depression, Anxiety, PTSD if present) and attach adjusted p‑values to the results.
- [ ] T024 [P] [US2] Save regression outputs (coefficients, SEs, p‑values, bootstrap CIs, adjusted p‑values) to `data/results/regression_results.csv`.
- [ ] T024b [P] [US2] **Create Results Module**: Implement `code/analysis/results.py` to handle report generation.
 - **Action**: Create the file with correct syntax.
 - **Content**: Functions to read `analysis_cohort.csv` and `regression_results.csv` and format them for markdown output.
- [ ] T025 [US2] **Generate Regression Summary Report**: Update `code/analysis/results.py` to read `analysis_cohort.csv` (produced by T016) and generate `data/results/regression_summary.md`.
 - **Deliverable**: `data/results/regression_summary.md` containing:
 - Model coefficients and standard errors.
 - Bootstrap confidence intervals.
 - FDR-adjusted p-values.
 - Interpretation of the interaction term.
 - **Dependency**: Must run after T016, T024, and **T024b**.

**Checkpoint**: User Stories 1 & 2 are independently testable.

---

## Phase 5: User Story 3 - Sensitivity Analysis & Robustness Checks (Priority: P3)

**Goal**: Re‑run models with alternative harassment definitions and platform stratification.

### Tests for User Story 3 (OPTIONAL)

- [ ] T026 [P] [US3] Contract test for sensitivity results schema in `tests/contract/test_sensitivity_results_schema.py`

### Implementation for User Story 3

- [ ] T027a [US3] **Implement Continuous Severity Model**: Re‑fit models using **continuous harassment severity** instead of binary exposure.
 - **Data Flow**: Write results to `data/results/sensitivity_raw_continuous.csv`.
 - **Dependency**: Must run after T020.

- [ ] T027b-Verify [US3] **[FR-005]** **Verify Platform Groups**: Check `data/results/platform_status.json` (from T070b) to confirm existence and count of valid platform groups (N >= 30).
 - **Action**: Read `platform_status.json`. If `platform_exists` is false, log `W-NO-PLATFORM-001` and skip stratification. If only one valid group exists (N >= 30), log `W-STRAT-SINGLE-001` and skip stratification. **If `platform_status.json` is missing (due to T070b failure), log `E-NO-PLATFORM-STATUS-001` and skip stratification.**
 - **Deliverable**: Log status and list of valid groups.
 - **Dependency**: Must run after T070b.

- [ ] T027b-Filter [US3] **[FR-005]** **Filter Valid Platform Groups**: Filter the dataset to include only platform groups meeting the N >= 30 threshold.
 - **Action**: Read `platform_status.json` and filter the cohort.
 - **Constraint**: **Do NOT** arbitrarily truncate the list of platforms to the "top three". All valid platforms meeting the N >= 30 threshold must be included.
 - **Dependency**: Must run after T027b-Verify.

- [ ] T027b-Exec [US3] **[FR-005]** **Execute Stratified Models**: Implement the logic to stratify analyses by **all available platforms** meeting the N >= 30 threshold.
 - **Action**: If valid groups exist (from T027b-Filter), run models for each group.
 - **Constraint**: **Do NOT** arbitrarily truncate the list of platforms to the "top three". All valid platforms meeting the N >= 30 threshold must be included.
 - **Data Flow**: Write results to `data/results/sensitivity_raw_stratified.csv`.
 - **Dependency**: Must run after T020 and T027b-Filter.

- [ ] T027b-Output [US3] **Generate Stratification Output**: Save the stratification results.
 - **Action**: If stratification was skipped (from T027b-Verify), create `data/results/sensitivity_raw_stratified.csv` containing **ONLY the CSV header row**. If stratification was executed, write the full data.
 - **Verification**: Run `wc -l data/results/sensitivity_raw_stratified.csv`. If skipped, it must return `1` (header only). If data exists, it must return `>1`.
 - **Dependency**: Must run after T027b-Exec.

- [ ] T029 [US3] **Save Sensitivity Summary**: Save the sensitivity summary to `data/results/sensitivity_analysis.csv`.
 - **Dependency**: Must run immediately after **T027a** and **T027b-Output** (after they complete successfully).
 - **Action**: Read `data/results/sensitivity_raw_continuous.csv` (from T027a). If `data/results/sensitivity_raw_stratified.csv` (from T027b-Output) exists, **check if it contains data rows** (row count > 1). If it contains data rows, read and append. If it is header-only (row count == 1), skip this file and proceed with continuous results only.
 - **Logic**: Handle missing files gracefully. If no stratification file exists, log reason and proceed.
 - **Deliverable**: `data/results/sensitivity_analysis.csv`.

- [ ] T028 [US3] **Generate Coefficient Comparison Table**: Compare interaction coefficients from each sensitivity run against the baseline (from T020) and produce a table of coefficient shifts.
 - **Deliverable**: `data/results/coefficient_comparison.csv` containing the baseline and sensitivity coefficients with calculated shifts.
 - **Logic**: Read the **disk files generated by T029** (`data/results/sensitivity_analysis.csv`) and merge with baseline results. Compute `shift = sensitivity_coef - baseline_coef`.
 - **Dependency**: Must run after **T029**.

- [ ] T030 [P] [US3] Add logging for each scenario, including data availability warnings.

**Checkpoint**: All user stories are now functional.

---

## Phase 6: Polish & Cross‑Cutting Concerns

- [ ] T031 [US1-US3] **Orchestrate Pipeline**: Update `main_pipeline.py` to chain all phases: Ingestion → Preprocessing → Validation → Modeling → Sensitivity → Reporting.
 - **Deliverable**: `main_pipeline.py` that executes T012-T030 sequentially and outputs a single run log at `data/results/pipeline_run.log`.
 - **Content Requirements**:
 - Import `ingestion`, `preprocessing`, `cohort`, `models`, `sensitivity`, `results`.
 - Execute `ingestion.load()`.
 - Execute `preprocessing.clean()`.
 - Execute `cohort.build()`.
 - Execute `models.fit()`.
 - Execute `sensitivity.run()`.
 - Execute `results.generate_report()`.
 - Handle exceptions: If any step fails, log error and halt.
 - **Verification**: The file must be syntactically correct and executable.
 - **Reproducibility Check**: **After** the main run, re-run the pipeline in a fresh container (simulated by re-executing `main_pipeline.py` in a new Python environment) and compare hashes of `analysis_cohort.csv` and `regression_results.csv`. Log results to `data/results/reproducibility_audit.json`.
 - **Dependency**: Must run after all phase tasks are complete.
- [ ] T032 Code cleanup and refactoring in `code/analysis/` to ensure modularity.
- [ ] T034 [P] Additional unit tests for edge cases (empty datasets, missing columns) in `tests/unit/`.
- [ ] T035 Run `quickstart.md` validation to ensure end‑to‑end pipeline execution.
- [ ] T036 Update `research.md` with placeholder interpretation that emphasizes associational findings.

---

## Phase 7: Execution Safety & Data Integrity (Revision Round 1)

**Goal**: Address specific execution risks identified in the analysis phase: ensuring real data sources are used, preventing synthetic fallbacks, and validating compute feasibility.

### Implementation for Execution Safety

- [ ] T050 [US1] **Hardening Ingestion**: Modify `code/data/ingestion.py` to strictly enforce the "Fail Loudly" rule.
 - **Requirement**: Remove any `try/except` blocks that catch download errors and fall back to `generate_synthetic_*()` or `mock_*()` functions.
 - **Action**: If the real fetch (via `ucimlrepo` or `load_dataset`) fails, the script MUST raise a `RuntimeError` with a clear message: "Real data fetch failed. Aborting to prevent synthetic data fabrication."
 - **Verification**: Unit test `tests/unit/test_ingestion_failures.py` must confirm that a missing network or invalid dataset ID raises an exception rather than returning mock data.

- [ ] T051 [US1] **Dataset Source Verification**: Update `code/data/ingestion.py` to log the exact source URL and dataset ID used.
 - **Requirement**: The log output must explicitly state: "Source: [URL/ID] | Method: [ucimlrepo/load_dataset]".
 - **Action**: If a "VERIFIED REAL DATA SOURCE" block is provided in execution feedback, the code MUST update the fetch logic to use that exact package/recipe instead of guessing.
 - **Verification**: Run the pipeline and grep logs for "Source:" to confirm the real dataset is being referenced.

- [ ] T052 [US1] **Streaming/Chunking for Large Data**: Implement streaming logic in `code/data/ingestion.py` if the Cyberbullying Survey exceeds a substantial volume.
 - **Requirement**: Use `datasets.load_dataset(..., streaming=True)` and iterate with `itertools.islice` if a full sample is needed for testing, ensuring the code handles chunked processing for statistics.
 - **Action**: If the dataset is small (<1GB), load fully into memory; otherwise, implement the streaming accumulator for mean/variance calculations to stay within 7GB RAM limits.
 - **Verification**: Unit test `tests/unit/test_streaming_logic.py` to ensure chunked processing yields identical statistics to full-load processing on a sample subset.

- [ ] T054 [US3] **Stratification Edge Case Handling**: Update `code/analysis/sensitivity.py` to handle the "Low N" edge case rigorously.
 - **Requirement**: If a platform group has N < 30, the stratified model MUST NOT run. Log `E-SMALL-N-001` and exclude that group from stratification.
 - **Action**: Ensure the code does not attempt to fit a regression on a group with insufficient variance or sample size, which would cause convergence errors or spurious results.
 - **Verification**: Unit test `tests/unit/test_stratification_edge_cases.py` with a mock dataset containing a group of N=10 to confirm the model skips and logs the error.
 - **Note**: This logic is consolidated in T027b; this task ensures the implementation in T027b is robust.

- [ ] T055 [US1-US3] **Reproducibility Audit (Local)**: Trigger a **local re-run** of the pipeline to validate reproducibility.
 **Requirement**: Re-run the pipeline in a fresh Python environment (simulated by deleting `__pycache__` and re-running `main_pipeline.py`) and compare hashes of `analysis_cohort.csv` and `regression_results.csv`.
 **Action**:
 1. After the main run completes, delete `__pycache__` and re-run `main_pipeline.py`.
 2. Compute hashes of `analysis_cohort.csv` and `regression_results.csv` from the re-run.
 3. Compare with the original run's hashes.
 **Deliverable**: `data/results/reproducibility_audit.json` containing the hash comparison results and pass/fail status.
 **Dependency**: Must run after T031, T016, T024, and T029.

---

## Phase 8: Final Verification & Documentation (Revision Round 2)

**Goal**: Ensure the final deliverable meets all constitutional requirements and is ready for human review.

### Implementation for Final Verification

- [ ] T061a [P] **Ensure Research.md Existence & Content**: Create `research.md` if it does not exist.
 **Requirement**: Ensure the file exists at `projects/PROJ-131-the-impact-of-perceived-social-support-o/specs/001-the-impact-of-perceived-social-support-o/research.md` (or the path defined in the plan).
 **Action**:
 1. **Pre-check**: Read `spec.md`. If `spec.md` contains "Synthetic Cohort" as an active step, log `E-SPEC-MISMATCH-001` and halt. T061a cannot proceed until Phase 0.5 is complete.
 2. If missing, create a file with the following content:
 ```markdown
 # Research: The Impact of Perceived Social Support on Resilience to Online Harassment

 ## Methodological Approach
 This project strictly follows a **Single-Dataset Approach** using the Cyberbullying Survey 2021. The dual-dataset matching approach (Synthetic Cohort) was rejected as methodologically invalid due to confounding by dataset source.

 ## Prerequisites
 - Python
 - Verified data source (Cyberbullying Survey 2021)

 ## Data Sources
 - Cyberbullying Survey 2021 (Sole Source)

 ## Expected Outputs
 - `data/results/analysis_cohort.csv`
 - `data/results/regression_results.csv`
 - `data/results/regression_summary.md`
 ```
 2. If the file exists, verify it contains the "Single-Dataset" narrative.
 **Verification**: Run `ls research.md` before T061 to confirm existence.
 **Deliverable**: `research.md` with correct content.

- [ ] T060 [P] **Final Data Lineage Audit**: Create `data/results/data_lineage_report.md` that traces every metric back to its raw source variable and transformation step.
 - **Requirement**: Explicitly list the dataset ID, version, and fetch method used for the Cyberbullying Survey 2021.
 - **Action**: Verify that no synthetic data generation functions were called during the run.
 - **Verification**: Run `grep -r "generate_synthetic" code/` and ensure no matches are found in the execution logs.

- [ ] T061 [P] **Methodological Consistency Check**: Review `research.md` and `data/results/regression_summary.md` to ensure they explicitly state the "Single-Dataset" approach and do not mention the deprecated "Synthetic Cohort" or GSS 2022 matching.
 - **Requirement**: Any mention of GSS 2022 must be framed as "excluded due to methodological invalidity".
 - **Action**: If inconsistencies are found, update the documentation to reflect the Plan's Revised Approach.
 - **Dependency**: Must run after **T061a** (Ensure Research.md Existence) to guarantee the file exists before modification.

- [ ] T062-Check [P] **Compute Resource Verification**: Confirm that the entire pipeline (including a sufficient number of bootstrap resamples) completes within an acceptable time limit on a standard 2-core CPU runner.
 - **Requirement**: If the dry-run (T033) indicated a risk, optimize the code (e.g., parallelize bootstrap loops using `multiprocessing` if allowed, or reduce overhead). **Do not** reduce resamples to 500.
 - **Action**: If optimization fails to meet the 6-hour limit, log `E-COMPUTE-OVERFLOW-001` to signal an infrastructure constraint.
 - **Deliverable**: `data/results/performance_report.json` with timing logs and optimization status. **This task MUST generate this file.**
 - **Verification**: If `performance_report.json` is missing, run the check again to generate it.

- [ ] T062-Report [P] **Generate Performance Report**: Write the final `performance_report.json` with the results of T062-Check.
 **Dependency**: Must run after T062-Check.

- [ ] T063-Lint [P] **Run Linter**: Run `ruff check.` to ensure all code is linted.
 - **Requirement**: Zero linting errors.
 - **Action**: Fix any remaining issues before marking this task complete.
 - **Deliverable**: `data/results/lint_report.txt`. **This task MUST generate this file.**

- [ ] T063-Test [P] **Run Tests**: Run `pytest` to ensure all tests pass.
 - **Requirement**: **[deferred] test pass rate** for all tests in `tests/unit/` and `tests/contract/`.
 - **Action**: Run pytest, capture output to `data/results/test_report.txt`. If any tests fail, the task is incomplete; the implementer must fix the code until all tests pass.
 - **Deliverable**: `data/results/test_report.txt`. **This task MUST generate this file.**

- [ ] T063-Report [P] **Generate Test Report**: Combine T063-Lint and T063-Test results into a single report.
 **Action**: Concatenate `data/results/lint_report.txt` and `data/results/test_report.txt` into `data/results/combined_report.txt`.
 **Deliverable**: `data/results/combined_report.txt`. **This task MUST generate this file.**

- [ ] T064 [P] **Generate Final Readme**: Update `README.md` with instructions on how to run the pipeline, including prerequisites, data sources, and expected outputs.
 - **Requirement**: Include a section on "Methodological Approach" explaining the single-dataset choice, a "Prerequisites" section, a "Data Sources" section, and an "Expected Outputs" section.
 - **Action**: Ensure the README is clear and actionable for a new developer.
 - **Deliverable**: Updated `README.md` file. **This task MUST generate the file.**
 - **Verification**: If `README.md` is missing or incomplete, generate the full content now.

---

## Dependencies & Execution Order

- **Setup (Phase 1)** → **Foundational (Phase 2)** (blocking)
- **User Story 1** (T012‑T017) → **User Story 2** (T020‑T025) → **User Story 3** (T027a‑T030)
- **Polish (Phase 6)** runs after all user stories.
- **Execution Safety (Phase 7)** must be completed before the final production run to ensure data integrity and reproducibility.
- **Final Verification (Phase 8)** must be completed before the project is considered ready for human review.
- **New Data Verification (Phase 0)** must be completed before T012 is considered valid.
- **Spec Alignment (Phase 0.5)** is a **BLOCKING GATE** and must be completed to ensure the documentation matches the code. The project cannot advance without this.
- **Final Documentation Audit (Phase 9)** is a **BLOCKING GATE** and must be completed to ensure the final deliverable is correct. The project cannot advance without this.
- **Parallelizable tasks are marked [P]; ordering respects data flow and artifact hand‑offs as described below:**
 - T027a/T027b-Execute (Generate Data) → T029 (Save Data) → T028 (Read & Compare). T029 is NOT parallel; it must wait for T027a/b.
 - T061a (Create File) → T061 (Modify File). T061 must wait for T061a.
 - **T070-Init (Provision) → T070-Resolve → T070a-Block (Acquire) → T070a-Verify (Verify Source) → T071 (Finalize Config)**. T071 cannot proceed until T070a-Verify confirms the source.
 - **T070b (Verify Platform) → T027b-Verify**. T027b-Verify relies on T070b's output.
 - **T053c (Config) → T033**. T033 depends on T053c.
 - **T016 (Cohort) → T033**. T033 depends on T016 for the data subset.
 - **T061a → T061**: Strict serial chain.
 - **T017 (Logging) → T012**: T012 depends on T017 to ensure logging is initialized.
 - **T072a/T073a/T074a**: These are blocking gates. If they fail, the pipeline halts.
 - **T001 (Setup) → T004 (Scales)**: T004 depends on T001 to ensure directory exists.
 - **T033 → T021**: T021 depends on T033 to ensure bootstrap is feasible.
 - **T001 → T017**: T017 depends on T001 to ensure `data/results` exists.
 - **T001 → T070-Init**: T070-Init depends on T001 to ensure `code/config` exists.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T009)
2. Complete Phase 0.0: Data Source Provisioning (including T070-Init, T070-Resolve)
3. Complete Phase 0.5: Spec Correction (including T072a)
4. Complete Phase 3: User Story 1 (T012-T017)
5. **STOP and VALIDATE**: Test User Story 1 independently
6. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 (with verified data) → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Data Ingestion)
 - Developer B: User Story 2 (Modeling)
 - Developer C: User Story 3 (Sensitivity)
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
- **CRITICAL**: Do not proceed with T012 (Ingestion) until T070a-Verify confirms the real data source. A guessed ID is a fabrication risk.
- **CRITICAL**: T072a-T074a are mandatory to verify the spec/plan alignment. The project cannot be considered "complete" until the specification accurately reflects the single-dataset implementation. **This is a blocking gate.**
- **CRITICAL**: T017 (Logging) must complete before T012 (Ingestion) to ensure all data processing is logged.
- **CRITICAL**: T070-Init is the entry point; it handles the 'missing' state gracefully.
- **CRITICAL**: T061a generates the full narrative for `research.md` if missing.
- **CRITICAL**: T004 depends on T001 to ensure the directory structure exists.
- **CRITICAL**: T070b depends on T070a-Verify. If T070a-Verify fails, T070b is skipped.
- **CRITICAL**: T027b-Verify handles the absence of `platform_status.json` gracefully.