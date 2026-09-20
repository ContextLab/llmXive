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
 # Values MUST be derived from official instrument documentation:
 # 1. CES-D: Radloff, L. S. (1977). The CES-D Scale: A self-report depression scale for research in the general population. DOI: 10.1177/014662167700100306
 # 2. GAD: Spitzer, R. L., et al. (2006). A Brief Measure for Assessing Generalized Anxiety Disorder.
 # 3. PCL: Weathers, F. W., et al. (2013). The PTSD Checklist for DSM-5 (PCL-5). Available from the National Center for PTSD.
 # Reference-Validator must verify these citations against primary sources before writing.
 CES-D:
 items: [depressed1, depressed2,...] # Must match official item list
 reverse_items: [depressed5, depressed9,...] # Must match official reverse list
 scoring: [0, 1, 2, 3] # Standard 4-point Likert
 GAD-7:
 items: [gad1, gad2,...]
 reverse_items: []
 scoring: [0, 1, 2, 3]
 PCL-5:
 items: [pcl1, pcl2,...]
 reverse_items: []
 scoring: [0, 1, 2, 3, 4] # Standard 5-point Likert
 ```
 **Verification**: Cross-reference these weights against the official instrument documentation (cited above) before hard-coding.
 **Deliverable**: `config/scales.yaml` AND `code/logs/scale_verification.txt` confirming the source URLs, DOIs, or document titles used.
 **Note**: Do NOT hard-code specific values (e.g., "-3 per item") in the task description; derive them from the official source.

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

**Checkpoint**: Foundation ready – user story implementation can now begin in parallel.

---

## Phase 3: User Story 1 - Data Ingestion & Cohort Preparation (Priority: P1) 🎯 MVP

**Goal**: Ingest the Cyberbullying Survey 2021, harmonize variables, handle missingness, and prepare a clean analysis cohort. **Note**: The GSS dataset is excluded per the Plan's 'Revised Approach'.

### Tests for User Story 1 (OPTIONAL)

- [X] T010 [P] [US1] Contract test for data schema in `tests/contract/test_analysis_cohort_schema.py`
- [X] T011 [P] [US1] Unit test for CES‑D/GAD‑7 scoring logic in `tests/unit/test_scale_scoring.py`

### Implementation for User Story 1

- [X] T012 [US1] Implement `code/data/ingestion.py` to **download and load** the Cyberbullying Survey 2021 dataset:
 - **Source**: Use `ucimlrepo.fetch_dataset(dataset_id=123)` (Cyberbullying Survey 2021).
 - **Validation**: Verify file integrity (checksum) and log E‑MISSING‑ if required items are absent.
 - **GSS Exclusion**: Do NOT attempt to load GSS 2022. If GSS is found in `data/raw`, log a warning that it is being ignored per the Plan's 'Revised Approach'.
 - **Fail Loudly**: If the real fetch fails, raise `RuntimeError` with message "Real data fetch failed. Aborting to prevent synthetic data fabrication."
- [X] T013 [US1] Implement `code/data/preprocessing.py` to perform the following steps in **strict order**:
 1. **MICE Imputation**: Apply Multiple Imputation by Chained Equations (MICE) to missing values in the **predictor matrix** (`['age','gender','education','income','social_support','harassment_severity']`). Configure with `m=5`, `max_iter=10`, `random_state=42`. Use `sklearn.impute.IterativeImputer`.
 2. **Imputation Strategy**: If `harassment_severity` has missing values, impute the continuous variable first. **Do not** impute the binary `harassment_exposure` directly.
 3. **Derivation**: **After** MICE imputation is complete, derive the binary `harassment_exposure` variable from the imputed `harassment_severity` (e.g., `exposure = 1 if severity > 0 else 0`).
 4. **Scale Scoring**: Apply scoring algorithms defined in `config/scales.yaml` to raw item columns to generate `depression`, `anxiety`, and `ptsd` scores.
 5. **PCL-5 Handling**: **If PCL-5 columns are present in the dataset**, score them and include `ptsd` in the analysis. **If PCL-5 columns are absent**, log a warning `W-PCL5-MISSING` and proceed with `depression` and `anxiety` only. **Do not** drop `ptsd` if the data exists.
 6. **Listwise Deletion for Outcomes**: Perform listwise deletion **only** on rows where critical outcome variables (`depression`, `anxiety`, `ptsd`) are missing after imputation and derivation. Do NOT perform listwise deletion on predictor variables before imputation.
 7. **Convergence Check**: Verify MICE convergence by checking the trace of imputed values. **Metric**: Convergence is achieved if the mean of the absolute difference of imputed values for **all predictor variables** across the last 3 iterations is < 0.01. If convergence fails for predictors, **log error `E-MICE-NONCONV-001` and fall back to listwise deletion for predictor variables ONLY** (preserving Spec FR-004), then proceed. Do NOT increase `max_iter`.
 8. Output the processed DataFrame for downstream cohort construction.
- [X] T014 [US1] Implement `code/data/cohort.py` to:
 1. Filter the dataset to remove rows with critical missing values (harassment_severity, social_support, or at least one mental health outcome).
 2. Ensure `harassment_severity` has sufficient variance (SD > 0.5, N > 30). If not, log `E-LOW-VAR-001` and halt.
 3. Output `data/results/analysis_cohort.csv`.
- [X] T015 [US1] **Validate the analysis cohort**: **[REVISED SC-001]**
 - Check **variance of Harassment Exposure** (SD > 0.5, N > 30).
 - Compute **VIF** for the model matrix (`social_support`, `harassment_exposure`, interaction, plus covariates) using `statsmodels.stats.outliers_influence.variance_inflation_factor`.
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
- [X] T023 [P] [US2] Implement Benjamini‑Hochberg FDR correction across the set of outcome tests (Depression, Anxiety, PTSD if present) and attach adjusted p‑values to the results.
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
 - **Data Flow**: Generates an in-memory DataFrame of continuous severity results.
 - **Dependency**: Must run after T020.

- [X] T027b [US3] **Implement Platform Stratification**: Implement the logic to stratify analyses by **all available platforms** meeting the N >= 30 threshold.
 - **Column Reference**: Use the `platform` column as defined in the Data Dictionary.
 - **Edge Case Handling**: If a platform group has N < 30, log `E-SMALL-N-001` and exclude that group from stratification. **Do not** apply any "distinct categories" constraint; include all groups with N >= 30.
 - **Single Group Handling**: If only **one** valid platform group exists (N >= 30), **log warning `W-STRAT-SINGLE-001`** and proceed with the baseline model only (using baseline coefficients for comparison). This means skipping the stratification step and using the baseline coefficients; it does NOT re-run T020.
 - **Dependency**: Must run after T020 (to ensure baseline model exists for comparison).
 - **Data Flow**: Generates an in-memory DataFrame of stratified results.

- [X] T029 [US3] **Save Sensitivity Summary**: Save the sensitivity summary to `data/results/sensitivity_analysis.csv`.
 - **Dependency**: Must run immediately after **T027a** and **T027b** (after they complete successfully).
 - **Action**: Write the in-memory DataFrames from T027a/b to disk. Handle disk-write errors gracefully to prevent T028 failure.

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

- [X] T052 [US1] **Streaming/Chunking for Large Data**: Implement streaming logic in `code/data/ingestion.py` if the Cyberbullying Survey exceeds ~1GB.
 - **Requirement**: Use `datasets.load_dataset(..., streaming=True)` and iterate with `itertools.islice` if a full sample is needed for testing, ensuring the code handles chunked processing for statistics.
 - **Action**: If the dataset is small (<1GB), load fully into memory; otherwise, implement the streaming accumulator for mean/variance calculations to stay within 7GB RAM limits.
 - **Verification**: Unit test `tests/unit/test_streaming_logic.py` to ensure chunked processing yields identical statistics to full-load processing on a sample subset.

- [X] T053a [P] [Plan-Constraints] **Bootstrap Runtime Estimator**: Implement a pre-flight check in `code/analysis/models.py` to estimate bootstrap runtime.
 - **Requirement**: Run a quick "dry run" with 10 resamples using a **representative subsample of exactly 500 rows** of full cohort to estimate time per resample. If `1000 * estimated_time > 6 hours`, log error `E-COMPUTE-OVERFLOW-001` and **HALT** the pipeline immediately. Do not proceed with a warning.
 - **Action**: Read configuration from `code/config/bootstrap_config.yaml` (created in T053c). Ensure the resample count is strictly CPU-tractable on the 2-core runner; if the estimate is high, halt. **Do not** reduce resamples to 500. Reducing resamples is strictly prohibited as it violates FR-007 and Constitution Principle I.
 - **Verification**: Run the dry-run on the CI runner and verify the estimated total time is logged and the pipeline halts if the limit is exceeded.
 - **Note**: This check runs BEFORE the full bootstrap in T021/T033 to prevent overflow.

- [X] T053b [P] [Plan-Constraints] **Bootstrap Optimization Strategy**: Implement the code optimization strategy for the bootstrap loop.
 - **Requirement**: If T053a detects a risk, this task executes the optimization (e.g., vectorization, multiprocessing if allowed) to meet the 6-hour limit.
 - **Action**: Read configuration from `code/config/bootstrap_config.yaml` (created in T053c). If optimization fails to meet the limit, **log error `E-COMPUTE-OVERFLOW-001`** and **HALT** the pipeline. **Do not** proceed with a warning.
 - **Verification**: Run the optimized code and verify runtime < 6 hours.

- [X] T053c [P] [Plan-Constraints] **Define Bootstrap Configuration Data Model**: Create `code/config/bootstrap_config.yaml` to explicitly define the 'Bootstrap Configuration' Data Model entity.
 - **Requirement**: This file must specify the resample count, confidence level, method (BCa), and seed source.
 - **Action**: Link this configuration to the 'Technical Context' constraints in the plan.
 - **Verification**: Ensure `main_pipeline.py` loads this config before running T021.
 - **Dependency**: Must run after T009 (seeds.yaml) and before T021.

- [X] T054 [US3] **Stratification Edge Case Handling**: Update `code/analysis/sensitivity.py` to handle the "Low N" edge case rigorously.
 - **Requirement**: If a platform group has N < 30, the stratified model MUST NOT run. Log `E-SMALL-N-001` and exclude that group from stratification.
 - **Action**: Ensure the code does not attempt to fit a regression on a group with insufficient variance or sample size, which would cause convergence errors or spurious results.
 - **Verification**: Unit test `tests/unit/test_stratification_edge_cases.py` with a mock dataset containing a group of N=10 to confirm the model skips and logs the error.
 - **Note**: This logic is consolidated in T027b; this task ensures the implementation in T027b is robust.

- [X] T055a [P] **Initialize Baseline Hash**: Create a mechanism to initialize the baseline hash for reproducibility checks.
 - **Requirement**: On the first run (or if no baseline exists), generate the hash for `analysis_cohort.csv` and `regression_results.csv` and save it to `data/results/baseline_hashes.json`.
 - **Action**: If the baseline file does not exist, create it with the current run's hashes and log `INFO: Baseline hash initialized`. Do not fail.
 - **Verification**: Run the pipeline on a fresh environment and confirm `baseline_hashes.json` is created.

- [X] T055 [P] **Reproducibility Audit**: Add a final validation step in `main_pipeline.py` to hash the final `analysis_cohort.csv` and `regression_results.csv`.
 - **Requirement**: Implement a **self-consistency check** per Spec SC-003: Perform a local "dry-run" of the stochastic components (MICE imputation on a subset, bootstrapping on a subset) on the **current** data with the **same seed** immediately before the main run. Compare the hash of this subset run against the hash of the full run's subset. **Do not** require a pre-existing `baseline_hashes.json` for the pass/fail decision. If no baseline exists, initialize it (via T055a) and pass.
 - **Action**: Ensure all random number generators (numpy, pandas, statsmodels) are seeded explicitly before any operation.
 - **Hashing**: Use a cryptographic hash function. **Sort rows by index, sort columns alphabetically, exclude header row, encode as UTF-8**. Before hashing, use `pandas.DataFrame.to_csv` with `float_format='%.10f'`, `na_rep='NA'`, and `index=False` to ensure deterministic float serialization and NA representation.
 - **Deliverable**: `data/results/reproducibility_audit.json` containing the hash comparison results and pass/fail status.
 - **Dependency**: Must run after T031, T016, T024, and T029. **Must run after T055a**.

---

## Phase 8: Final Verification & Documentation (Revision Round 2)

**Goal**: Ensure the final deliverable meets all constitutional requirements and is ready for human review.

### Implementation for Final Verification

- [X] T061a **Ensure Research.md Existence**: Create `research.md` if it does not exist.
 - **Requirement**: If `research.md` is missing, generate a placeholder file with the project title, date, and a disclaimer stating: "This analysis follows the Single-Dataset Approach (Cyberbullying Survey) and excludes the Synthetic Cohort method due to methodological invalidity."
 - **Action**: Ensure the file exists at `projects/PROJ-131-the-impact-of-perceived-social-support-o/specs/001-the-impact-of-perceived-social-support-o/research.md` (or the path defined in the plan) before T061 runs.
 - **Verification**: Run `ls research.md` before T061 to confirm existence.
 - **Note**: This task is NOT [P] if T061 depends on it immediately.

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

- [X] T063 [P] **Final Code Review**: Run `ruff check.` and `pytest` to ensure all code is linted and all tests pass. <!-- ATOMIZE: requested -->
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

## Dependencies & Execution Order

- **Setup (Phase 1)** → **Foundational (Phase 2)** (blocking)
- **User Story 1** (T012‑T017) → **User Story 2** (T020‑T025) → **User Story 3** (T027a‑T030)
- **Polish (Phase 6)** runs after all user stories.
- **Execution Safety (Phase 7)** must be completed before the final production run to ensure data integrity and reproducibility.
- **Final Verification (Phase 8)** must be completed before the project is considered ready for human review.
- **Parallelizable tasks are marked [P]; ordering respects data flow and artifact hand‑offs as described below:**
 - T027a/T027b (Generate Data) → T029 (Save Data) → T028 (Read & Compare). T029 is NOT parallel; it must wait for T027a/b.
 - T061a (Create File) → T061 (Modify File). T061 must wait for T061a.
 - T055a (Init Baseline) → T055 (Audit Baseline). T055 handles missing baseline by initializing it (T055a) and passing, ensuring no circular dependency.

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