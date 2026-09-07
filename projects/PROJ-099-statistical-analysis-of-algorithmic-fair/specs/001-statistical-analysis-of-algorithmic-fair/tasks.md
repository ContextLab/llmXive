# Tasks: Fairness Metric Divergence Analysis

**Input**: Design documents from `/specs/001-statistical-analysis-of-algorithmic-fair/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

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

- [X] T001 Create project directory skeleton with explicit paths and placeholder README files:
 - `code/`, `data/raw/`, `data/processed/`, `data/analysis/`, `logs/`, `tests/`, `state/`
 - Add empty `README.md` in each top‑level folder.
- [X] T002 Initialize a Python virtual environment and create `requirements.txt` pinning: scikit‑learn, statsmodels, pandas, numpy, scipy, requests, hashlib, joblib, pytest, black, flake8, isort.
- [X] T003 [P] Configure linting and formatting tools by adding `.black`, `.flake8`, and `.isort.cfg` configuration files at repository root.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create `code/data-model.py` defining `Dataset`, `Model`, `FairnessMetric`, and `DatasetCharacteristic` classes with type hints and docstrings.
- [X] T005 [P] Setup logging infrastructure: create `logs/exclusion.log` with CSV header `timestamp,dataset_id,missing_variable_name,reason`.
- [X] T005a [P] Create `logs/` directory structure explicitly using `os.makedirs('logs', exist_ok=True)` in a setup script or as part of T005 to ensure the directory exists before any logging tasks run.
- [X] T006 [P] Create `code/utils/metrics.py` implementing fairness metric formulas (docstrings include LaTeX notation and citations to Appendix A).
- [X] T007 [P] Create `code/utils/dataset_loaders.py` with URL‑based fetchers for:
 - UCI Adult (`)
 - COMPAS (`)
 - Bank Marketing (`)
 - German Credit (`)
 - Law School Admission (`)
- [X] T008 [P] Create `code/utils/validators.py` providing:
 - SHA‑256 checksum verification function.
 - Variable presence validation function that checks for protected attribute, outcome, and predictions columns.
- [X] T009 Create `state/projects/PROJ-099-statistical-analysis-of-algorithmic-fair.yaml` with project metadata and an empty `artifact_hashes` map.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Dataset Acquisition and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Download multiple public datasets containing binary protected attributes and outcomes, preprocess to extract fairness‑relevant features, ensure all required variables present, sample to ≤100k rows

**Independent Test**: Can be fully tested by verifying that all target datasets are downloaded, contain required columns, and are within size constraints (≤100k rows, <500 MB each), delivering a validated dataset repository

### Tests for User Story 1 (OPTIONAL)

- [X] T010 [P] [US1] Contract test for dataset download in `tests/contract/test_dataset_download.py`.
- [X] T011 [P] [US1] Integration test for preprocessing pipeline in `tests/integration/test_preprocessing.py`.
- [X] T012 [P] [US1] Unit test for checksum verification in `tests/unit/test_checksum.py`.
- [X] T013 [P] [US1] Unit test for variable presence validation in `tests/unit/test_variable_validation.py`.

### Implementation for User Story 1

- [ ] T014 [US1] Implement `01_data_acquisition.py` to download the five datasets, verify SHA‑256 checksums via `utils/validators.py`, store raw files under `data/raw/`, AND IMMEDIATELY record the raw file checksums in `state/projects/...yaml` before any processing occurs. Pin `random_state=42` for any stratified sampling or shuffling operations.
- [ ] T019b [US1] Explicitly verify that raw data files under `data/raw/` remain unchanged by comparing their current checksums to the raw checksums recorded in T014. Run `scripts/verify_raw_integrity.py` (which must be created as part of this task) to perform this check; fail if any modification detected.
- [ ] T016 [US1] Implement `02_preprocessing.py` to:
 - Load raw CSVs.
 - Extract binary protected attributes (e.g., gender 0/1, race 0/1) and binary outcomes.
 - Perform stratified sampling to ≤100k rows per dataset.
 - Log exclusions of datasets missing required variables to `logs/exclusion.log` (ensure `logs/` directory exists via T005a).
 - Save processed files under `data/processed/`.
- [ ] T017a [US1] Record SHA‑256 checksums of the *processed* datasets in `state/projects/...yaml` as distinct artifacts from the raw checksums.
- [ ] T017b [US1] Verify that the processed datasets are distinct artifacts from the raw datasets (different file paths, different checksums). Run `scripts/verify_artifact_distinction.py` (which must be created as part of this task) and output results to `data/analysis/artifact_distinction_log.json`.
- [ ] T018 [US1] Add the FR‑008 disclaimer ("Findings are associational only; no causal claims are made.") to all console output, log messages, AND any generated Markdown reports or research paper drafts.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Fairness Metric Computation (Priority: P2)

**Goal**: Train multiple baseline models per dataset and compute multiple fairness metrics (demographic parity difference, equalized odds difference, predictive parity, calibration within groups, disparate impact ratio, false positive rate disparity)

**Independent Test**: Can be fully tested by running the metric computation pipeline on a single dataset and verifying all relevant metrics are calculated for each model, delivering a metrics matrix

### Tests for User Story 2 (OPTIONAL)

- [X] T021 [P] [US2] Contract test for model training in `tests/contract/test_model_training.py`.
- [X] T022 [P] [US2] Integration test for fairness metric computation in `tests/integration/test_fairness_metrics.py`.
- [X] T023 [P] [US2] Unit test for demographic parity difference formula in `tests/unit/test_demographic_parity.py`.
- [X] T024 [P] [US2] Unit test for equalized odds difference formula in `tests/unit/test_equalized_odds.py`.

### Implementation for User Story 2

- [ ] T025 [US2] Implement `03_model_training.py`:
 - Perform stratified train/test split (random_state=42).
 - Train Logistic Regression, Random Forest, and Gradient Boosting models (CPU‑only) using scikit-learn.
 - Save trained models under `data/processed/models/` with metadata (model_id, model_type, dataset_id).
- [ ] T026 [US2] In `04_fairness_metrics.py`, compute the six required metrics for each model, applying stratified balancing when class‑imbalance ratio > 10:1.
- [ ] T027 [US2] Store metrics in `data/analysis/metrics.csv` with columns: `model_id,dataset_id,protected_attribute,metric_name,metric_value`. Ensure each row includes traceability fields (model_id, dataset_id, protected_attribute) as required by FR‑004.
- [ ] T028 [US2] Document each metric's formula in `utils/metrics.py` docstrings (LaTeX + citations to Appendix A).
- [ ] T029 [US2] Add the FR‑008 disclaimer to all metric report headers, console output, AND any generated Markdown reports or research paper drafts.

**Checkpoint**: User Stories 1 AND 2 should now both work independently

---

## Phase 5: User Story 3 - Correlation Analysis and Predictive Modeling (Priority: P3)

**Goal**: Compute pairwise correlations between all metric pairs, fit fixed‑effects regression models to predict discrepancies from dataset characteristics, perform bootstrap resampling for confidence intervals

**Independent Test**: Can be fully tested by running the analysis pipeline on existing metric outputs and verifying correlation matrices, regression coefficients, and bootstrap confidence intervals are generated, delivering the final research artifacts

### Tests for User Story 3 (OPTIONAL)

- [X] T032 [P] [US3] Contract test for correlation analysis in `tests/contract/test_correlation_analysis.py`.
- [X] T033 [P] [US3] Integration test for regression analysis in `tests/integration/test_regression_analysis.py`.
- [X] T034 [P] [US3] Unit test for Benjamini‑Hochberg FDR correction in `tests/unit/test_fdr_correction.py`.
- [ ] T035 [P] [US3] Unit test for bootstrap resampling in `tests/unit/test_bootstrap.py`.

### Implementation for User Story 3

- [ ] T064a [US3] Implement pre-execution guard script `scripts/check_power_analysis.py` that verifies `research.md` contains required power analysis documentation before any Phase 5 tasks execute; exit 0 if present, exit 1 otherwise.
- [ ] T064b [US3] Execute `scripts/check_power_analysis.py` in the pipeline before Phase 5 tasks run.
- [ ] T036 [P] [US3] Implement `05_correlation_analysis.py` to compute **ALL** pairwise Pearson and Spearman correlations among the six fairness metrics. EXCLUDE the DP-difference vs DI-ratio pair due to theoretical circularity as per the plan. Store results with p-values, q-values, AND effect sizes (r) with interpretation (small/medium/large). NO other exclusions.
- [ ] T036a [US3] Document the exclusion of the DP-difference vs DI-ratio pair in `research.md` as a 'staged simplification' due to theoretical circularity, explicitly noting this is a deviation from the spec's 'all pairs' requirement (FR-005) justified by the plan.
- [ ] T037 [US3] Apply Benjamini‑Hochberg FDR correction (α = 0.05) to all correlation tests; store q‑values.
- [ ] T037b [US3] Verify that the correlation output (`correlations.csv`) includes effect size (`r`) and its interpretation (small/medium/large) for each pair.
- [ ] T038 [US3] Store the full correlation matrix in `data/analysis/correlations.csv` with columns: `metric_a,metric_b,pearson_r,pearson_p,pearson_q,spearman_r,spearman_p,spearman_q,interpretation`.
- [ ] T038b [US3] Merge bootstrap confidence intervals (from T046) into `data/analysis/correlations.csv` to ensure SC-003's requirement for CIs is met directly in the correlation analysis output. Add columns `lower_ci, upper_ci` to the correlation matrix.
- [ ] T040 [US3] Implement OLS regression in `06_regression_analysis.py` (per plan, not fixed-effects as per T006c). Exclude base rate difference for DP models due to theoretical circularity before VIF diagnostics. Use dataset and model as categorical covariates with predictors: feature_dimensionality, class_imbalance_ratio. Apply VIF diagnostics; exclude predictors with VIF > 5. Document n=15 observation limitation. Reference T006c for the architectural decision documentation.
- [ ] T041 [US3] Apply VIF diagnostics; automatically drop any predictor with VIF > 5 and log the action.
- [ ] T042 [US3] Output regression results to `data/analysis/regression_results.csv` including coefficients, standard errors, p‑values, VIFs, Cohen's f², R², adjusted R², and a note about the limited n = 15 observations.
- [ ] T043 [US3] Add an interpretation note linking base‑rate difference to demographic parity difference (per Constitution Principle VII) in the regression summary and CSV.
- [ ] T045 [US3] Implement `07_bootstrap_analysis.py`:
 - Perform multiple bootstrap resamples of the correlation matrix (reducible to a lower threshold if time‑threshold exceeded).
 - Compute confidence intervals for each correlation coefficient.
- [ ] T059a [US3] If elapsed runtime exceeds a significant duration, automatically reduce iterations to a sufficient number for convergence, log the reduction to `logs/exclusion.log`, and continue.
- [ ] T046 [US3] Store bootstrap confidence intervals in `data/analysis/bootstrap_results.csv` with columns: `metric_a,metric_b,method,lower_ci,upper_ci,iterations_used`.
- [ ] T049 [US3] Generate metric selection guidance in `08_metric_guidance.py` that maps dataset characteristics to associational findings about metric behavior. Use FR‑009 terminology "metric selection guidance" and frame all associations as non-causal per FR-008. Explicitly define 'actionable guidance' as associational mappings (e.g., 'High class imbalance is associated with high disparity in Metric X') that guide selection based on observed patterns without making causal claims.
- [ ] T050 [US3] Output guidance to `data/analysis/guidance.csv` with columns: `characteristic,associated_metric,association_strength,interpretation`. Ensure the interpretation field uses associational language (e.g., 'associated with', 'tends to be') and includes the FR‑008 disclaimer.
- [ ] T052 [US3] Ensure the FR‑008 disclaimer appears in the guidance CSV header, console output, AND any generated Markdown reports or research paper drafts.
- [ ] T078 [US3] Verify that all statistical output files (`correlations.csv`, `regression_results.csv`, `bootstrap_results.csv`, `guidance.csv`) contain required effect sizes and confidence intervals.
- [ ] T078b [US3] Add verification task that scans all statistical output files for required effect sizes and confidence intervals; run `scripts/verify_effect_sizes.py` and fail pipeline if any missing.
- [ ] T006c [US3] [depends on T040] Update `research.md` to document the architectural decision to use OLS regression instead of fixed-effects regression, citing the n=5 dataset limitation as the constraint preventing fixed-effects. Include this as a dedicated section "Architectural Decision: Regression Model Selection" and explicitly state this is a 'staged simplification' in the plan, not a spec change.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Cross‑Cutting & Compliance (Priority: P1)

**Purpose**: Verify that all constitutional principles and functional requirements are satisfied

- [ ] T054 [US3] Create contract test `tests/contract/test_framing_verification.py` that scans all generated CSV/MD files for the FR‑008 disclaimer.
- [ ] T055 [US3] Add script `scripts/check_guidance_framing.py` that parses `guidance.csv` and asserts the disclaimer is present.
- [ ] T064 [US3] Draft a Power‑Analysis section in `research.md` documenting detectable effect size given n = 15, α = 0.05, referencing Wikipedia: Power (statistics) (https://en.wikipedia.org/wiki/Power_(statistics)), and include the calculation.
- [ ] T076a [US3] Implement Reference-Validator Agent workflow at artifact write time: validate all citations in spec.md, plan.md, research.md before committing.
- [ ] T076 [US3] Execute Reference‑Validator Agent on `spec.md` and `plan.md`; fail the pipeline if any citation is unreachable or mismatched.
- [ ] T076b [US3] Implement Reference-Validator Agent workflow before research_accepted transition: re-validate all citations; block transition if any citation unreachable or mismatched.
- [ ] T077b [US3] Implement comprehensive seed-pinning audit script `scripts/seed_audit.py` that scans ALL code/ files for random calls without explicit seeds; fail pipeline if any found.
- [ ] T077 [US3] Execute `scripts/seed_audit.py` in the pipeline.

---

## Phase 7: Performance & Polish

- [ ] T057 [P] Update `README.md` with detailed sections:
 - Pipeline Overview
 - Dependency Installation
 - Execution Order (Phase 0 → Phase 7)
 - Example Commands
 - Troubleshooting
- [ ] T058 [P] Refactor codebase:
 - Remove duplicate utility functions.
 - Standardize error handling with try/except blocks.
 - Ensure all logging calls follow the format defined in `logs/exclusion.log`.
- [ ] T059 [P] Optimize bootstrap implementation using joblib parallelism and memoization of intermediate statistics.
- [ ] T060 [P] Add edge‑case unit tests for:
 - Missing protected attribute.
 - Class‑imbalance > 10:1.
 - Multicollinearity leading to high VIF.
- [ ] T061 [P] Whitelist dataset download domains (`archive.ics.uci.edu`, `raw.githubusercontent.com`, `datasets.load_dataset`) and add HTTP‑200 status checks before download.
- [ ] T062 [P] Create quickstart validation script `scripts/quickstart_check.py` that runs the full pipeline on a reduced sample and logs any failures to `logs/quickstart_errors.log` and `data/analysis/quickstart_diagnostic.json`.
- [ ] T063 [P] Generate FR/SC coverage matrix programmatically from code comments and test assertions; output to `data/analysis/fr_sc_coverage.json`.
- [ ] T065 [P] Verify dataset URLs are reachable (curl) and record status codes & response times in `data/analysis/url_verification.csv`.
- [ ] T066 [P] Add fallback handling in `06_regression_analysis.py` to catch non‑convergence exceptions and automatically switch to a reduced predictor set (drop highest VIF).

---

## Phase 8: Final Verification

- [ ] T070 [P] Run the full CI pipeline; ensure all tests pass, all compliance checks (T054‑T078) succeed, and the entire job completes within the designated A limited GitHub Actions time window

The research question, method, and references remain unchanged as per the planning phase requirements. using `gh run watch --job-id <id>`.