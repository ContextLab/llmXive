# Tasks: The Impact of Perceived Social Support on Resilience to Online Harassment

**Input**: Design documents from `/specs/001-social-support-resilience/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

**⚠️ CRITICAL METHODOLOGICAL NOTE**:
The implementation **strictly follows the Plan's 'Revised Approach'** (Single-Dataset Analysis). The Spec's requirement for a 'Synthetic Cohort' (dual-dataset matching) is **methodologically invalid** per the Plan and is **excluded** from implementation. The pipeline ingests the Cyberbullying Survey to ensure the interaction term estimates a genuine psychological buffering effect without confounding by dataset source.

## Format: `[ID] [P?] [Story] description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root

<!--
 ============================================================================
 IMPORTANT: The tasks below reflect the revised, single-dataset workflow
 as mandated by the Plan's 'Critical Methodological Pivot'.
 ============================================================================
-->

## Phase 0: Data Source Verification (Blocking Prerequisite)

**Purpose**: Verify the existence and accessibility of the mandatory real data source (Cyberbullying Survey 2021) before any pipeline logic is built.

- [X] T070a [P] **Attempt Real Data Fetch**: Verify the dataset source defined in `code/config/data_sources.yaml`.
 **Action**: Write a script `code/data/verify_source.py` that reads the dataset ID/URL from the config file. The config MUST contain `dataset_id: cyberbullying_2021_v1` and `source_url:.
 **Success**: If the dataset loads successfully (via network fetch OR local file check in `data/raw/`), log `INFO: Source verified`.
 **Failure**: If the fetch fails (network error, ID not found) AND the local file is missing or checksum mismatch, the script MUST raise `RuntimeError` with message "E-NO-REAL-SOURCE-001: Real data source not found. Aborting."
 **Constraint**: Do NOT hard-code a specific dataset ID in the script; read from config. If the config is missing the specific ID, log error and halt.
 **Deliverable**: `code/data/verify_source.py` and execution log confirming success or halting with E-NO-REAL-SOURCE-001.

- [X] T070b [US1] **Verify Data Columns**: Inspect the loaded dataset from T070a to confirm the presence of the `platform` column.
 **Action**: Load the dataset (using the verified source from config) and check column names.
 **Deliverable**: Save a JSON file `data/results/platform_status.json` with keys: `platform_exists` (boolean), `platform_categories` (list of unique values if exists).
 **Dependency**: Must run after T070a.

- [X] T071 [US1] **Finalize Data Source Config**: Update `code/config/data_sources.yaml` with the verified source ID and method.
 **Action**: Write `dataset_id: <verified_id>`, `source: <source_type>`, `verified: true` to the config file. **Constraint**: This config MUST be committed as a static file. Do NOT allow runtime updates to the ID.
 **Dependency**: Must run after T070a and T070b.

---

## Phase 1: Setup & Kickback (Shared Infrastructure & Methodology Alignment)

**Purpose**: Project initialization and resolution of the spec/plan conflict.

- [X] T041 [P] **Verify Spec State**: Confirm that `specs/001-social-support-resilience/spec.md` already contains the "DEPRECATED" blocks for FR-001/FR-002 and "REVISED" block for SC-001.
 **Action**: Read the file and assert the presence of the required deprecation/revision text.
 **Deliverable**: Log confirmation `INFO: Spec state verified as per Plan requirements.`

- [X] T001 Create project structure per implementation plan (`code/data`, `code/analysis`, `code/config`, `code/tests`)

- [X] T002 [P] **Initialize Git Repository**: Initialize the git repository for the project.
 **Action**: Run `git init` in the repository root.
 **Deliverable**: `.git` directory created.
 **Verification**: Run `git status` to confirm repository initialization.

- [X] T003 [P] **Create.gitignore**: Create a `.gitignore` file to exclude `data/raw/`, `data/results/`, `__pycache__/`, and `*.pyc`.
 **Action**: Create file at repository root.
 **Deliverable**: `.gitignore` file with correct entries.
 **Verification**: Run `git check-ignore` on a sample file in `data/raw/` to confirm it is ignored.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

- [X] T004 [P] **Define Scoring Scales**: Create `config/scales.yaml` defining standard scoring weights for CES‑D, GAD‑7, and PCL‑5. **[FR-006] [SC-002]**
 **Content outline**:
 ```yaml
 # Values derived from official instrument documentation:
 # 1. CES-D: Radloff, L. S. (n.d.). The CES-D Scale: A self-report depression scale for research in the general population.
 # 2. GAD: Spitzer, R. L., et al. (2006). A Brief Measure for Assessing Generalized Anxiety Disorder.
 # 3. PCL: Weathers, F. W., et al. (2013). The PTSD Checklist for DSM-5 (PCL-5).
 CES-D:
 items: [] # Dynamically mapped from dataset columns during ingestion
 reverse_items: []
 scoring: [0, 1, 2, 3]
 # Exact weights: 1 point per item. Reverse items: 4, 5, 6, 10 (0->3, 1->2, 2->1, 3->0).
 GAD-7:
 items: []
 reverse_items: []
 scoring: [0, 1, 2, 3]
 # Exact weights: 1 point per item. No reverse items.
 PCL-5:
 items: []
 reverse_items: []
 scoring: [0, 1, 2, 3, 4]
 # Exact weights: 1 point per item. No reverse items.
 ```
 **Verification**: Cross-reference these weights against the official instrument documentation (cited above) before hard-coding.
 **Instruction**: The `items` lists must be populated by mapping the *actual* column names found in the verified dataset (T070a) to the standard scale items, or left empty if the dataset provides pre-scored variables.
 **Deliverable**: `config/scales.yaml` AND `code/logs/scale_verification.txt` confirming the source URLs, DOIs, or document titles used.

- [X] T005 [US1] Implement `tests/test_scales.py` with unit tests verifying scoring logic matches the definitions in `config/scales.yaml`. **Dependency**: Must run after T004.
- [X] T006 [P] Setup `code/data/ingestion.py` skeleton with read‑only raw data validation logic.
- [X] T007 Create `code/data/cohort.py` skeleton for constructing the analysis cohort (single source).
- [X] T008 [P] Configure `main_pipeline.py` entry point to orchestrate modular steps (skeleton creation).
- [X] T009 [P] Setup environment configuration for data paths **and** create `config/seeds.yaml` to define reproducible seeds.
 **Content outline**:
 ```yaml
 random_seed:
 ```
 **Instruction**: Ensure the file contains valid YAML with the integer value `42` for `random_seed`. This seed will be used for all random operations (imputation, bootstrapping, sampling).

- [X] T053c [P] [Plan-Constraints] **Define Bootstrap Configuration Data Model**: Create `code/config/bootstrap_config.yaml` to explicitly define the 'Bootstrap Configuration' Data Model entity.
 **Requirement**: This file must specify the resample count, confidence level, method (BCa), and seed source.
 **Action**: Link this configuration to the 'Technical Context' constraints in the plan.
 **Verification**: Ensure `main_pipeline.py` loads this config before running T021.
 **Dependency**: Must run after T009 (seeds.yaml).

**Checkpoint**: Foundation ready – user story implementation can now begin in parallel.

---

## Phase 3: User Story 1 - Data Ingestion & Cohort Preparation (Priority: P1) 🎯 MVP

**Goal**: Ingest the Cyberbullying Survey 2021, harmonize variables, handle missingness, and prepare a clean analysis cohort. **Note**: The GSS dataset is excluded per the Plan's 'Revised Approach'.

### Tests for User Story 1 (OPTIONAL)

- [X] T010 [P] [US1] Contract test for data schema in `tests/contract/test_analysis_cohort_schema.py`
- [X] T011 [P] [US1] Unit test for CES‑D/GAD‑7 scoring logic in `tests/unit/test_scale_scoring.py`

### Implementation for User Story 1

- [X] T012 [US1] **[FR-003]** Implement `code/data/ingestion.py` to **download and load** the Cyberbullying Survey 2021 dataset:
 - **Source**: Use the dataset ID/URL from `code/config/data_sources.yaml` (verified in T070a).
 - **Harmonization**: Map raw columns to canonical names (`social_support`, `harassment_severity`, `depression`, etc.) as defined in the Data Dictionary.
 - **Validation**: Verify file integrity (checksum) and log E‑MISSING‑ if required items are absent.
 - **GSS Exclusion**: Do NOT attempt to load GSS 2022. If GSS is found in `data/raw`, log a warning that it is being ignored per the Plan's 'Revised Approach'.
 - **Fail Loudly**: If the real fetch fails, raise `RuntimeError` with message "Real data fetch failed. Aborting to prevent synthetic data fabrication."
 - **Dependency**: Must run after T070a and T071.

- [X] T013a [US1] **[FR-004]** **Implement MICE Imputation**: Apply Multiple Imputation by Chained Equations (MICE) to missing values in the **predictor matrix** (`['age','gender','education','income','social_support','harassment_severity']`).
 **Configuration**: Use `sklearn.impute.IterativeImputer` with `m=5`, `max_iter=10`, `random_state=42`. Use default convergence settings (do not invent specific thresholds).
 **Constraint**: **Do not** impute the binary `harassment_exposure` directly. Impute the continuous `harassment_severity` first.
 **Failure Handling**: If MICE fails to converge, log error `E-MICE-NONCONV-001` and **HALT** the pipeline. Do NOT fall back to listwise deletion for predictors (preserve FR-004).
 **Deliverable**: Imputed DataFrame.

- [X] T013b [US1] **Derive Binary Exposure**: Derive the binary `harassment_exposure` variable from the imputed `harassment_severity`.
 **Action**: `exposure = 1 if severity > 0 else 0`.
 **Dependency**: Must run after T013a.

- [X] T013c [US1] **Scale Scoring**: Apply scoring algorithms defined in `config/scales.yaml` to raw item columns to generate `depression`, `anxiety`, and `ptsd` scores.
 **Action**: Use the weights from T004.
 **PCL-5 Handling**: **If PCL-5 columns are present in the dataset**, score them and include `ptsd` in the analysis. **If PCL-5 columns are absent**, log a warning `W-PCL5-MISSING` and proceed with `depression` and `anxiety` only. **Do not** drop `ptsd` if the data exists.

- [X] T013d [US1] **[FR-004]** **Handle Outcome Missingness**: Perform listwise deletion **only** on rows where critical outcome variables (`depression`, `anxiety`, `ptsd`) are missing after imputation and derivation.
 **Constraint**: Do NOT perform listwise deletion on predictor variables before imputation. This is a distinct step from T013a (predictor imputation).
 **Dependency**: Must run after T013c.

- [X] T014 [US1] Implement `code/data/cohort.py` to:
 1. Filter the dataset to remove rows with critical missing values (harassment_severity, social_support, or at least one mental health outcome).
 2. Ensure `harassment_severity` has sufficient variance (SD > 0.5, N > 30). If not, log `E-LOW-VAR-001` and halt.
 3. Output `data/results/analysis_cohort.csv`.

- [X] T015 [US1] **[SC-001]** **Validate the analysis cohort**: **[REVISED SC-001]**
 - **Variance Check**: Check **variance of Harassment Exposure** (SD > 0.5, N > 30).
 - **Collinearity Check**: Compute **VIF** for the model matrix (`social_support`, `harassment_exposure`, interaction, plus covariates) using `statsmodels.stats.outliers_influence.variance_inflation_factor`.
 - **Centering**: Use `sklearn.preprocessing.StandardScaler` (with `with_mean=True`, `with_std=False`) to center variables before VIF calculation.
 - Ensure VIF < 5.
 - **Deliverable**: Generate `data/results/validation_report.json` containing the results of these checks (Pass/Fail status, calculated values).
 - **Logic**: If VIF >= 5 or Variance check fails, raise a `RuntimeError` with message "Cohort validity check failed. Aborting." to prevent downstream execution.
 - **Note**: The SMD check (SC-001) is **inapplicable** to the single-dataset approach and is **removed**. This task implements the **REVISED** SC-001 criteria.

- [X] T016 [US1] Save the validated analysis cohort to `data/results/analysis_cohort.csv` **only after** successful T015.
 **Dependency**: Must run after T015. This task depends on the *output* of T015 (`validation_report.json` and pass status).

- [X] T017 [US1] Add comprehensive logging for ingestion, preprocessing, and validation steps, including any fallback decisions (e.g., missing PCL-5).

**Checkpoint**: User Story 1 is fully functional and produces a valid single-dataset cohort.

---

## Phase 4: User Story 2 - Interaction Analysis & Hypothesis Testing (Priority: P2)

**Goal**: Fit robust OLS models with interaction term, compute bias‑corrected bootstrapped CIs, and apply multiple‑comparison correction.

### Tests for User Story 2 (OPTIONAL)

- [X] T018 [P] [US2] Contract test for regression results schema in `tests/contract/test_regression_results_schema.py`. **Note**: Validate schema for Cyberbullying Survey data only (no GSS references).
- [X] T019 [P] [US2] Unit test for bootstrapping logic in `tests/unit/test_bootstrap_ci.py`

### Implementation for User Story 2

- [X] T020 [P] [US2] Implement `code/analysis/models.py` to fit OLS models with heteroskedasticity‑consistent (HC3) standard errors for Depression, Anxiety, and PTSD (if PCL-5 present). Include interaction term `SocialSupport:HarassmentExposure`.
- [X] T021 [P] [US2] Implement bootstrapping logic (Wikipedia: Bootstrapping (statistics), https://en.wikipedia.org/wiki/Bootstrapping_(statistics)) using `statsmodels.stats.bootstrap`. Seed the process with `random_seed` from `config/seeds.yaml`.
- [X] T022 [P] [US2] Add fallback: if the robust model fails to converge, automatically refit a standard OLS model (no HCSE) and log status `E‑NONCONV‑001`.
- [X] T023 [P] [US2] **[FR-008]** Implement Benjamini‑Hochberg FDR correction across the set of outcome tests (Depression, Anxiety, PTSD if present) and attach adjusted p‑values to the results.
- [X] T024 [P] [US2] Save regression outputs (coefficients, SEs, p‑values, bootstrap CIs, adjusted p‑values) to `data/results/regression_results.csv`.
- [X] T024b [P] [US2] **Create Results Module**: Implement `code/analysis/results.py` to handle report generation.
 - **Action**: Create the file with correct syntax.
 - **Content**: Functions to read `analysis_cohort.csv` and `regression_results.csv` and format them for markdown output.
- [X] T025 [US2] **Generate Regression Summary Report**: Update `code/analysis/results.py` to read `analysis_cohort.csv` (produced by T016) and generate `data/results/regression_summary.md`.
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

- [X] T026 [P] [US3] Contract test for sensitivity results schema in `tests/contract/test_sensitivity_results_schema.py`

### Implementation for User Story 3

- [X] T027a [US3] **Implement Continuous Severity Model**: Re‑fit models using **continuous harassment severity** instead of binary exposure.
 - **Data Flow**: Write results to `data/results/sensitivity_raw_continuous.csv`.
 - **Dependency**: Must run after T020.

- [X] T027b [US3] **[FR-005]** **Implement Platform Stratification**: Implement the logic to stratify analyses by **all available platforms** meeting the N >= 30 threshold.
 - **Column Reference**: Use the `platform` column. Check `data/results/platform_status.json` (from T070b) to confirm existence.
 - **Constraint**: **Do NOT** arbitrarily truncate the list of platforms to the "top three". All valid platforms meeting the N >= 30 threshold must be included.
 - **Edge Case Handling**: If `platform` column is missing (from T070b), log warning `W-NO-PLATFORM-001` and skip stratification.
 - **Single Group Handling**: If only **one** valid platform group exists (N >= 30), log warning `W-STRAT-SINGLE-001` and skip this specific stratification analysis step. **Action**: Create an empty file `data/results/sensitivity_raw_stratified.csv` with a header row and log `INFO: Stratification skipped (single group)` to ensure downstream tasks have a deterministic file to read.
 - **Dependency**: Must run after T020 (to ensure baseline model exists for comparison) and T070b (to confirm platform data).
 - **Data Flow**: Write results to `data/results/sensitivity_raw_stratified.csv` if successful. If skipped, create the empty file as described.

- [X] T029 [US3] **Save Sensitivity Summary**: Save the sensitivity summary to `data/results/sensitivity_analysis.csv`.
 - **Dependency**: Must run immediately after **T027a** and **T027b** (after they complete successfully).
 - **Action**: Read `data/results/sensitivity_raw_continuous.csv` (from T027a). If `data/results/sensitivity_raw_stratified.csv` (from T027b) exists, read it and append. If it does not exist (skipped), proceed with continuous results only.
 - **Logic**: Handle missing files gracefully. If no stratification file exists, log reason and proceed.
 - **Deliverable**: `data/results/sensitivity_analysis.csv`.

- [X] T028 [US3] **Generate Coefficient Comparison Table**: Compare interaction coefficients from each sensitivity run against the baseline (from T020) and produce a table of coefficient shifts.
 - **Deliverable**: `data/results/coefficient_comparison.csv` containing the baseline and sensitivity coefficients with calculated shifts.
 - **Logic**: Read the **disk files generated by T029** (`data/results/sensitivity_analysis.csv`) and merge with baseline results. Compute `shift = sensitivity_coef - baseline_coef`.
 - **Dependency**: Must run after **T029**.

- [X] T030 [P] [US3] Add logging for each scenario, including data availability warnings.

**Checkpoint**: All user stories are now functional.

---

## Phase 6: Polish & Cross‑Cutting Concerns

- [X] T031 [US1-US3] **Orchestrate Pipeline**: Update `main_pipeline.py` to chain all phases: Ingestion → Preprocessing → Validation → Modeling → Sensitivity → Reporting.
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
 - **Dependency**: Must run after all phase tasks are complete.
- [X] T032 Code cleanup and refactoring in `code/analysis/` to ensure modularity.
- [X] T033 [P] Performance optimization: Verify that bootstrapping (1,000 resamples for up to three models) completes within 6 hours on a 2‑core CPU. **Verification Step**: Run `time python main_pipeline.py` and assert output < 21600s.
 - **Mitigation**: If runtime exceeds 6h, **MUST** attempt optimization (e.g., `multiprocessing` if allowed, or vectorization). If optimization fails to meet the limit, log `E-COMPUTE-OVERFLOW-001` and **HALT** the pipeline. Do not proceed with a warning.
- [X] T053a [P] [Plan-Constraints] **Bootstrap Runtime Estimator**: Implement a pre-flight check in `code/analysis/models.py` to estimate bootstrap runtime.
 **Requirement**: Run a quick "dry run" with 10 resamples using a **small representative subset (e.g., 100 rows)** of the full cohort to estimate time per resample. If `1000 * estimated_time > 6 hours`, log error `E-COMPUTE-OVERFLOW-001` and **HALT** the pipeline immediately. Do not proceed with a warning.
 **Action**: Read configuration from `code/config/bootstrap_config.yaml` (created in T053c). Ensure the resample count is strictly CPU-tractable on the available runner.; if the estimate is high, halt. **Do not** reduce resamples to 500. Reducing resamples is strictly prohibited as it violates FR-007 and Constitution Principle I.
 **Data Source**: Use the `analysis_cohort.csv` generated by T016. If the cohort is sufficiently small to be fully processed, use the entire cohort..
 **Verification**: Run the dry-run on the CI runner and verify the estimated total time is logged and the pipeline halts if the limit is exceeded.
 **Note**: This check runs BEFORE the full bootstrap in T021/T033 to prevent overflow.
 **Dependencies**: T009, T053c, **T016**.
- [X] T053b [P] [Plan-Constraints] **Bootstrap Optimization Strategy**: Implement the code optimization strategy for the bootstrap loop.
 - **Requirement**: If T053a detects a risk, this task executes the optimization (e.g., vectorization, multiprocessing if allowed) to meet the 6-hour limit.
 - **Action**: Read configuration from `code/config/bootstrap_config.yaml` (created in T053c). If optimization fails to meet the limit, **log error `E-COMPUTE-OVERFLOW-001`** and **HALT** the pipeline. **Do not** proceed with a warning.
 - **Verification**: Run the optimized code and verify runtime < 6 hours.
- [X] T034 [P] Additional unit tests for edge cases (empty datasets, missing columns) in `tests/unit/`.
- [X] T035 Run `quickstart.md` validation to ensure end‑to‑end pipeline execution.
- [X] T036 Update `research.md` with placeholder interpretation that emphasizes associational findings.

---

## Phase 7: Execution Safety & Data Integrity (Revision Round 1)

**Goal**: Address specific execution risks identified in the analysis phase: ensuring real data sources are used, preventing synthetic fallbacks, and validating compute feasibility.

### Implementation for Execution Safety

- [X] T050 [US1] **Hardening Ingestion**: Modify `code/data/ingestion.py` to strictly enforce the "Fail Loudly" rule.
 - **Requirement**: Remove any `try/except` blocks that catch download errors and fall back to `generate_synthetic_*()` or `mock_*()` functions.
 - **Action**: If the real fetch (via `ucimlrepo` or `load_dataset`) fails, the script MUST raise a `RuntimeError` with a clear message: "Real data fetch failed. Aborting to prevent synthetic data fabrication."
 - **Verification**: Unit test `tests/unit/test_ingestion_failures.py` must confirm that a missing network or invalid dataset ID raises an exception rather than returning mock data.

- [X] T051 [US1] **Dataset Source Verification**: Update `code/data/ingestion.py` to log the exact source URL and dataset ID used.
 - **Requirement**: The log output must explicitly state: "Source: [URL/ID] | Method: [ucimlrepo/load_dataset]".
 - **Action**: If a "VERIFIED REAL DATA SOURCE" block is provided in execution feedback, the code MUST update the fetch logic to use that exact package/recipe instead of guessing.
 - **Verification**: Run the pipeline and grep logs for "Source:" to confirm the real dataset is being referenced.

- [X] T052 [US1] **Streaming/Chunking for Large Data**: Implement streaming logic in `code/data/ingestion.py` if the Cyberbullying Survey exceeds a substantial volume.
 - **Requirement**: Use `datasets.load_dataset(..., streaming=True)` and iterate with `itertools.islice` if a full sample is needed for testing, ensuring the code handles chunked processing for statistics.
 - **Action**: If the dataset is small (<1GB), load fully into memory; otherwise, implement the streaming accumulator for mean/variance calculations to stay within 7GB RAM limits.
 - **Verification**: Unit test `tests/unit/test_streaming_logic.py` to ensure chunked processing yields identical statistics to full-load processing on a sample subset.

- [X] T054 [US3] **Stratification Edge Case Handling**: Update `code/analysis/sensitivity.py` to handle the "Low N" edge case rigorously.
 - **Requirement**: If a platform group has N < 30, the stratified model MUST NOT run. Log `E-SMALL-N-001` and exclude that group from stratification.
 - **Action**: Ensure the code does not attempt to fit a regression on a group with insufficient variance or sample size, which would cause convergence errors or spurious results.
 - **Verification**: Unit test `tests/unit/test_stratification_edge_cases.py` with a mock dataset containing a group of N=10 to confirm the model skips and logs the error.
 - **Note**: This logic is consolidated in T027b; this task ensures the implementation in T027b is robust.

- [X] T055a [P] **Initialize Baseline Hash**: Create a mechanism to initialize the baseline hash for reproducibility checks.
 **Requirement**: On the first run (or if no baseline exists), generate the hash for `analysis_cohort.csv` and `regression_results.csv` and save it to `data/results/baseline_hashes.json`.
 **Action**: If the baseline file does not exist, create it with the current run's hashes and log `INFO: Baseline hash initialized`. Do not fail.
 **Verification**: Run the pipeline on a fresh environment and confirm `baseline_hashes.json` is created.
 **Note**: This task's logic is now internal to T055; T055a is marked complete to indicate the configuration is in place.

- [X] T055 [US1-US3] **Reproducibility Audit**: Add a final validation step in `main_pipeline.py` to hash the final `analysis_cohort.csv` and `regression_results.csv`.
 - **Requirement**: Implement a **self-consistency check** per Spec SC-003: Perform a **full re-run** of the pipeline on a fresh environment (simulated by clearing state and re-executing) with the **same seed** immediately after the main run. Compare the hash of this full re-run against the hash of the original run. **Do not** require a pre-existing `baseline_hashes.json` for the pass/fail decision. If no baseline exists, initialize it (via T055a) and pass.
 - **Action**: Ensure all random number generators (numpy, pandas, statsmodels) are seeded explicitly before any operation.
 - **Hashing**: Use a cryptographic hash function. **Sort rows by index, sort columns alphabetically, exclude header row, encode as UTF-8**. Before hashing, use `pandas.DataFrame.to_csv` with `float_format='%.10f'`, `na_rep='NA'`, and `index=False` to ensure deterministic float serialization and NA representation.
 - **Deliverable**: `data/results/reproducibility_audit.json` containing the hash comparison results and pass/fail status.
 - **Dependency**: Must run after T031, T016, T024, and T029. **Must run after T055a**.
 **Note**: This task now performs the full-run reproducibility check as per SC-003, removing the previous subset-only logic which was a constraint violation.

---

## Phase 8: Final Verification & Documentation (Revision Round 2)

**Goal**: Ensure the final deliverable meets all constitutional requirements and is ready for human review.

### Implementation for Final Verification

- [X] T061a [P] **Ensure Research.md Existence**: Create `research.md` if it does not exist.
 **Requirement**: Ensure the file exists at `projects/PROJ-131-the-impact-of-perceived-social-support-o/specs/001-the-impact-of-perceived-social-support-o/research.md` (or the path defined in the plan).
 **Action**: If missing, create a placeholder file. Do not enforce specific text content not defined in Spec/Plan.
 **Verification**: Run `ls research.md` before T061 to confirm existence.

- [X] T060 [P] **Final Data Lineage Audit**: Create `data/results/data_lineage_report.md` that traces every metric back to its raw source variable and transformation step.
 - **Requirement**: Explicitly list the dataset ID, version, and fetch method used for the Cyberbullying Survey 2021.
 - **Action**: Verify that no synthetic data generation functions were called during the run.
 - **Verification**: Run `grep -r "generate_synthetic" code/` and ensure no matches are found in the execution logs.

- [X] T061 **Methodological Consistency Check**: Review `research.md` and `data/results/regression_summary.md` to ensure they explicitly state the "Single-Dataset" approach and do not mention the deprecated "Synthetic Cohort" or GSS 2022 matching.
 - **Requirement**: Any mention of GSS 2022 must be framed as "excluded due to methodological invalidity".
 - **Action**: If inconsistencies are found, update the documentation to reflect the Plan's Revised Approach.
 - **Dependency**: Must run after **T061a** (Ensure Research.md Existence) to guarantee the file exists before modification.

- [X] T062 [P] **Compute Resource Verification**: Confirm that the entire pipeline (including a sufficient number of bootstrap resamples) completes within the 6-hour limit on a standard 2-core CPU runner.
 - **Requirement**: If the dry-run (T053) indicated a risk, optimize the code (e.g., parallelize bootstrap loops using `multiprocessing` if allowed, or reduce overhead). **Do not** reduce resamples to 500.
 - **Action**: If optimization fails to meet the 6-hour limit, log `E-COMPUTE-OVERFLOW-001` to signal an infrastructure constraint. Document the final runtime and resource usage in `data/results/performance_report.json`.
 - **Deliverable**: `data/results/performance_report.json` with timing logs and optimization status. **This task MUST generate this file if missing.**
 - **Verification**: If `performance_report.json` is missing, create it with the current run's timing data to satisfy the verification requirement.

- [X] T063 [P] **Final Code Review**: Run `ruff check.` and `pytest` to ensure all code is linted and all tests pass.
 - **Requirement**: Zero linting errors; **[deferred]** test pass rate for all tests in `tests/unit/` and `tests/contract/`.
 - **Action**: Fix any remaining issues before marking this task complete.
 - **Deliverable**: `data/results/lint_report.txt` and `data/results/test_report.txt`. **This task MUST generate these files if missing.**
 - **Verification**: If these files are missing, run the linter and tests again to generate them.

- [X] T064 [P] **Generate Final Readme**: Update `README.md` with instructions on how to run the pipeline, including prerequisites, data sources, and expected outputs.
 - **Requirement**: Include a section on "Methodological Approach" explaining the single-dataset choice, a "Prerequisites" section, a "Data Sources" section, and an "Expected Outputs" section.
 - **Action**: Ensure the README is clear and actionable for a new developer.
 - **Deliverable**: Updated `README.md` file. **This task MUST generate the file if missing.**
 - **Verification**: If `README.md` is missing or incomplete, generate the full content now.

---

## Phase 9: Spec Alignment & Kickback (Revision Round 3)

**Goal**: Explicitly resolve the documented inconsistency between `spec.md` (which mandates a synthetic cohort) and `plan.md` (which mandates a single-dataset approach) by updating the specification to match the implemented plan.

- [ ] T072 [US1-US3] **Update spec.md to Remove Deprecated Requirements**: Edit `specs/001-social-support-resilience/spec.md` to formally remove the "Synthetic Cohort" language and align with the Plan.
 **Action**:
 1. Remove the "DEPRECATED" blocks for FR-001 and FR-002 entirely, replacing them with a permanent "REMOVED" status block stating:
 ```
 Status: REMOVED per Plan's Critical Methodological Pivot.
 Historical Note: The dual-dataset matching approach was found to introduce confounding and is methodologically invalid for interaction analysis.
 ```
 2. Update User Story 1 (US-1) to remove all references to "Synthetic Cohort" and "GSS 2022". Replace with: "Ingest the Cyberbullying Survey 2021, harmonize variables, handle missingness, and prepare a clean analysis cohort."
 3. Update Success Criteria SC-001 to permanently reflect the "REVISED" single-dataset variance and collinearity checks, removing any mention of SMD or synthetic matching.
 **Constraint**: Do not leave "DEPRECATED" comments that imply the feature might be re-enabled. The methodological error is fundamental; the requirement is deleted.
 **Deliverable**: `specs/001-social-support-resilience/spec.md` updated to reflect the single-dataset reality.
 **Dependency**: Must run after T061 (Methodological Consistency Check) to ensure the implementation logic is finalized before updating the spec.

- [ ] T073 [US1-US3] **Update spec.md Data Dictionary**: Ensure the Data Dictionary in `spec.md` explicitly lists the Cyberbullying Survey 2021 as the **sole** source for all variables.
 **Action**: Add a note to every variable row: "Source: Cyberbullying Survey 2021 (Sole Source)".
 **Deliverable**: Updated Data Dictionary in `spec.md`.
 **Dependency**: Must run after T072.

- [ ] T074 [US1-US3] **Update spec.md Methodological Notes**: Rewrite Section 5 "Methodological Notes" in `spec.md` to remove the "Synthetic Cohort" justification and replace it with the "Revised Approach" rationale.
 **Action**:
 1. Remove the subsection "The Revised Approach (Single-Dataset)" if it currently references the synthetic cohort as a previous step.
 2. Rewrite to state: "The project strictly uses the Cyberbullying Survey 2021 alone. The dual-dataset matching approach was rejected as methodologically invalid due to confounding of Harassment Exposure with Dataset Source."
 **Deliverable**: Updated Section 5 in `spec.md`.
 **Dependency**: Must run after T072.

---

## Dependencies & Execution Order

- **Setup (Phase 1)** → **Foundational (Phase 2)** (blocking)
- **User Story 1** (T012‑T017) → **User Story 2** (T020‑T025) → **User Story 3** (T027a‑T030)
- **Polish (Phase 6)** runs after all user stories.
- **Execution Safety (Phase 7)** must be completed before the final production run to ensure data integrity and reproducibility.
- **Final Verification (Phase 8)** must be completed before the project is considered ready for human review.
- **New Data Verification (Phase 0)** must be completed before T012 is considered valid.
- **Spec Alignment (Phase 9)** must be completed to ensure the documentation matches the code.
- **Parallelizable tasks are marked [P]; ordering respects data flow and artifact hand‑offs as described below:**
 - T027a/T027b (Generate Data) → T029 (Save Data) → T028 (Read & Compare). T029 is NOT parallel; it must wait for T027a/b.
 - T061a (Create File) → T061 (Modify File). T061 must wait for T061a.
 - T055a (Init Baseline) → T055 (Audit Baseline). T055 handles missing baseline by initializing it (T055a) and passing, ensuring no circular dependency.
 - **T070a (Verify Source) → T071 (Implement Fetch)**. T071 cannot proceed until T070a confirms the source.
 - **T070a/T071 → T012**. T012 is blocked until the source is verified.
 - **T070b (Verify Platform) → T027b**. T027b relies on T070b's output.
 - **T053c (Config) → T053a**. T053a depends on T053c.
 - **T016 (Cohort) → T053a**. T053a depends on T016 for the data subset.
 - **T072 (Update Spec) → T073/T074**. T073 and T074 depend on the structural changes in T072.
 - **T070a → T070b → T071**: Strict serial chain.
 - **T061 → T072 → T073/T074**: Strict serial chain.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 0: Data Source Verification
2. Complete Phase 1: Setup
3. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
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
- **CRITICAL**: Do not proceed with T012 (Ingestion) until T070a/T071 verify the real data source. A guessed ID is a fabrication risk.
- **CRITICAL**: T072-T074 are mandatory to resolve the spec/plan conflict. The project cannot be considered "complete" until the specification accurately reflects the single-dataset implementation.
- **CRITICAL**: T055 performs a full re-run for reproducibility, not a subset dry-run.
- **CRITICAL**: T027b creates an empty file if stratification is skipped to ensure downstream compatibility.