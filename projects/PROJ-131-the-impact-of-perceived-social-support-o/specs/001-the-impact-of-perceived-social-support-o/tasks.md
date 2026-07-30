# Tasks: The Impact of Perceived Social Support on Resilience to Online Harassment

**Input**: Design documents from `/specs/001-social-support-resilience/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

**⚠️ CRITICAL METHODOLOGICAL NOTE**:
The implementation **conforms to the revised plan** (`plan.md`) and **updated spec** (`spec.md`), which explicitly adopts a **single-dataset approach** (Cyberbullying Survey 2021) where both Harassment and Social Support vary naturally. The GSS 2022 dataset is excluded. The spec has been updated to remove dual-dataset requirements (FR-001, FR-002, US-1) and replace them with single-dataset requirements (FR-001-Single, FR-002-Single, US-1-Single).

## Format: `[ID] [P?] [Story] description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root

<!--
 ============================================================================
 IMPORTANT: The tasks below reflect the revised, single-dataset workflow.
 ============================================================================
-->

## Phase 1: Setup & Kickback (Shared Infrastructure & Methodology Alignment)

**Purpose**: Project initialization and resolution of the spec/plan conflict.

- [ ] T041 [P] **Kickback Task**: Update `specs/001-social-support-resilience/spec.md` to formally adopt the single-dataset approach (removing FR-001, FR-002, and US-1's dual-dataset requirements) and update SC-001 to reflect single-dataset validation (SC-001-Single). **Fallback**: If PR is not merged by 2023-11-15, create `specs/001-social-support-resilience/spec-waiver.md` formally waiving FR-001/FR-002 for this feature branch, allowing T012+ to proceed. **Note**: This task is parallel to T012-T017; do not wait for PR merge to start data tasks.
- [X] T001 Create project structure per implementation plan (`code/data`, `code/analysis`, `code/config`, `code/tests`)
- [X] T002 Initialize Python project with pinned dependencies (`requirements.txt`: pandas, numpy, scikit-learn, statsmodels, scipy, pyyaml)
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

- [X] T004 [P] Create `config/scales.yaml` defining standard scoring weights for CES‑D, GAD‑7, and PCL‑5.
 **Content outline** (example values):
 ```yaml
 CES-D:
 items: [depressed1, depressed2, depressed3, depressed4, depressed5, depressed6, depressed7, depressed8, depressed9, depressed10, depressed11, depressed12, depressed13, depressed14, depressed15, depressed16, depressed17, depressed18, depressed19, depressed20]
 reverse_items: [depressed5, depressed9, depressed12, depressed16, depressed18]
 scoring: -3 per item, total 0‑60
 GAD-7:
 items: [gad1, gad2, gad3, gad4, gad5, gad6, gad7]
 reverse_items: []
 scoring: ‑3 per item, total 0‑21
 PCL-5:
 items: [pcl1, pcl2, pcl3, pcl4, pcl5, pcl6, pcl7, pcl8, pcl9, pcl10, pcl11, pcl12, pcl13, pcl14, pcl15, pcl16, pcl17, pcl18, pcl19, pcl20, pcl21, pcl22, pcl23, pcl24, pcl25]
 reverse_items: []
 scoring: ‑4 per item, total 0‑100
 ```
- [X] T005 [P] Implement `tests/test_scales.py` with unit tests verifying scoring logic matches the definitions in `config/scales.yaml`.
- [X] T006 [P] Setup `code/data/ingestion.py` skeleton with read‑only raw data validation logic.
- [X] T007 Create `code/data/cohort.py` skeleton for constructing the analysis cohort.
- [X] T008 [P] Configure `main_pipeline.py` entry point to orchestrate modular steps.
- [X] T009 [P] Create `config/seeds.yaml` defining reproducible seeds. **Deliverable**: A YAML file with key `random_seed: 42` (or a specific fixed integer) and `bootstrap_seed: 42`. This file is referenced by downstream tasks.

**Checkpoint**: Foundation ready – user story implementation can now begin in parallel.

---

## Phase 3: User Story 1 - Data Ingestion & Single-Dataset Cohort Construction (Priority: P1) 🎯 MVP

**Goal**: Ingest the Cyberbullying Survey 2021, harmonize variables, handle missingness, and construct a clean analysis cohort. The GSS 2022 dataset is excluded per `plan.md` and `spec.md`.

### Tests for User Story 1 (OPTIONAL)

- [X] T010 [P] [US1] Contract test for data schema in `tests/contract/test_analysis_cohort_schema.py`
- [X] T011 [P] [US1] Unit test for CES‑D/GAD‑7 scoring logic in `tests/unit/test_scale_scoring.py`

### Implementation for User Story 1

- [X] T012 [US1] Implement `code/data/ingestion.py` to **download and load** the Cyberbullying Survey 2021 dataset.
 - **Source**: Fetch from a verified, persistent URL (e.g., specific GitHub release asset or `ucimlrepo` package).
 - **Validation**: Verify file integrity (checksum if available) and validate that required columns exist (`age`, `gender`, `education`, `income`, `social_support_items`, `harassment_severity_items`, `depression_items`, `anxiety_items`, `ptsd_items`, `platform`).
 - **Failure Logic**: If the Cyberbullying Survey source is missing or invalid, raise an error. Do NOT attempt to load GSS 2022. Log `E-MISSING-001` only if the *Cyberbullying Survey* is missing.
- [ ] T012b [US1] Document the exclusion of GSS 2022 in `research.md` and `data-model.md`.
 - **Content**: Explicitly state that GSS 2022 was excluded due to methodological invalidity for interaction analysis (confounding with dataset source) and lack of verified PCL-5 items. Cite the Plan's "Methodological Rationale" section.
- [X] T013a [P] [US1] Implement `code/data/preprocessing.py` (Part 1): **Missingness Handling**.
 - Perform listwise deletion for variables with >5% missingness.
 - Log the number of dropped rows and the reason.
 - **Dependency**: Requires T004 (scales.yaml) to be complete for variable naming consistency.
- [X] T013b [P] [US1] Implement `code/data/preprocessing.py` (Part 2): **Imputation**.
 - For remaining missing values in predictor/outcome columns, apply **MICE** imputation (`m=5`, `max_iter=10`, `random_state=42`) on the predictor matrix: `['age','gender','education','income','social_support','harassment_severity','depression','anxiety','ptsd']`.
 - **Dependency**: Requires T004 (scales.yaml) and T013a (missingness handling).
- [X] T013c [P] [US1] Implement `code/data/preprocessing.py` (Part 3): **Scoring**.
 - Apply scale scoring using `config/scales.yaml` (including conditional PCL‑5 handling).
 - **Dependency**: Requires T004 (scales.yaml) and T013b (imputed data).
- [X] T014a [US1] Implement `code/data/cohort.py` (Part 1): **Derive Variables**.
 - Derive `harassment_exposure` as a binary flag (1 if `harassment_severity` > 0, else 0).
 - Retain `harassment_severity` as a continuous variable.
 - Output an intermediate DataFrame.
- [X] T014b [US1] Implement `code/data/cohort.py` (Part 2): **Filter**.
 - Filter out rows with invalid scores (e.g., negative values, out-of-range sums).
 - Log the number of filtered rows.
- [X] T014c [US1] Implement `code/data/cohort.py` (Part 3): **Write Intermediate**.
 - Write the unvalidated cohort to `data/results/intermediate_cohort.csv`.
- [ ] T015 [P] [US1] Validate the analysis cohort:
 - **Input**: `data/results/intermediate_cohort.csv`.
 - **Checks**:
 1. **Variance of Harassment Exposure**: SD > 0.2 AND N > 30 for exposed group.
 2. **Variance of Social Support**: SD > 0.5.
 3. **Multicollinearity**: Compute VIF for the model matrix (`social_support`, `harassment_exposure`, interaction, plus covariates) and ensure VIF < 5.
 - **Deliverable**: Produce `data/results/validation_report.json` containing the check results.
 - **Failure Action**: If any check fails, raise an Exception with code `E-VALIDATION-001` and exit the pipeline. Do NOT proceed to T016.
- [ ] T016 [US1] Save the validated analysis cohort to `data/results/analysis_cohort.csv` **only after** successful T015.
 - Read `data/results/validation_report.json` to confirm success.
 - Move/Copy `intermediate_cohort.csv` to `analysis_cohort.csv`.
- [ ] T017 [P] [US1] Add comprehensive logging for ingestion, preprocessing, and validation steps.
 - **Format**: JSON logs to `data/logs/pipeline.log`.
 - **Level**: INFO.
 - **Rotation**: Max size 10MB, 3 backups.
 - **Events**: Must log specific event codes: `E-MISSING-001` (on missing columns), `E-NONCONV-001` (on model convergence), `E-VALIDATION-001` (on validation failure), `E-SKIP-001` (on skipped steps).

**Checkpoint**: User Story 1 is fully functional and produces a plan-compliant analysis cohort.

---

## Phase 4: User Story 2 - Interaction Analysis & Hypothesis Testing (Priority: P2)

**Goal**: Fit robust OLS models with interaction term, compute bias‑corrected bootstrapped CIs, and apply multiple‑comparison correction.

### Tests for User Story 2 (OPTIONAL)

- [X] T018a [P] [US2] Contract test for regression results schema in `tests/contract/test_regression_results_schema.py`
- [ ] T019 [P] [US2] Unit test for bootstrapping logic in `tests/unit/test_bootstrap_ci.py`

### Implementation for User Story 2

- [X] T020 [P] [US2] Implement `code/analysis/models.py` to fit OLS models with heteroskedasticity‑consistent (HC3) standard errors for Depression, Anxiety, and PTSD (if PCL‑5 present). Include interaction term `SocialSupport:HarassmentExposure`.
- [X] T021 [P] [US2] Compute **bias‑corrected accelerated (BCa) bootstrap CIs** with a sufficient number of resamples using `statsmodels.stats.bootstrap`. Seed the process with `bootstrap_seed` from `config/seeds.yaml`.
- [ ] T022 [P] [US2] Add fallback: if the robust model fails to converge, automatically refit a standard OLS model (no HCSE) and log status `E‑NONCONV‑001`.
- [X] T023 [P] [US2] Implement Benjamini‑Hochberg FDR correction across the set of **available** outcome tests (Depression, Anxiety, PTSD) and attach adjusted p‑values to the results.
 - **Logic**: Dynamically determine the "family" size based on which outcomes have valid data in the cohort (e.g., if PCL-5 is missing, family size is 2).
- [ ] T024 [P] [US2] Save regression outputs (coefficients, SEs, p‑values, bootstrap CIs, adjusted p‑values) to `data/results/regression_results.csv`.
- [X] T025 [P] [US2] Update `code/analysis/results.py` to read `analysis_cohort.csv` (produced by T016) and generate a summary report `data/results/regression_summary.md`.

**Checkpoint**: User Stories 1 & 2 are independently testable.

---

## Phase 5: User Story 3 - Sensitivity Analysis & Robustness Checks (Priority: P3)

**Goal**: Re‑run models with alternative harassment definitions and platform stratification.

### Tests for User Story 3 (OPTIONAL)

- [X] T026 [P] [US3] Contract test for sensitivity results schema in `tests/contract/test_sensitivity_results_schema.py`

### Implementation for User Story 3

- [X] T027 [P] [US3] Implement `code/analysis/sensitivity.py` to:
 1. Re‑fit models using **continuous harassment severity** instead of binary exposure.
 2. If a `platform` column exists, stratify analyses by platform. Only the **top three** most frequent platforms are kept; all others are grouped as `Other`.
 3. If fewer than two platforms are present, log `E‑SKIP‑001` and skip stratification.
- [X] T028 [P] [US3] Compare interaction coefficients from each sensitivity run against the baseline (from T020) and produce a table of coefficient shifts.
- [ ] T029 [P] [US3] Save the sensitivity summary to `data/results/sensitivity_analysis.csv`.
- [X] T030 [P] [US3] Add logging for each scenario, including data availability warnings.

**Checkpoint**: All user stories are now functional.

---

## Phase 6: Polish & Cross‑Cutting Concerns

- [X] T031 [P] Update `main_pipeline.py` to chain all phases: Ingestion → Preprocessing → Cohort Construction → Validation → Modeling → Sensitivity → Reporting.
- [X] T032 [P] Code cleanup and refactoring in `code/analysis/` to ensure modularity.
- [X] T033 [P] Performance optimization: Verify that bootstrapping (A sufficient number of resamples for up to three models) completes within 6 hours on a 2‑core CPU (profiling and possible parallelisation of bootstrap replicates).
- [X] T034 [P] Additional unit tests for edge cases (empty datasets, missing columns) in `tests/unit/`.
- [X] T035 [P] Run `quickstart.md` validation to ensure end‑to‑end pipeline execution.
- [X] T036 [P] Update `research.md` with placeholder interpretation that emphasizes associational findings and the exclusion of GSS.

---

## Dependencies & Execution Order

- **Kickback (T041)** is parallel to T012-T017. Implementation proceeds based on the Plan.
- **Setup (Phase 1)** → **Foundational (Phase 2)** (blocking)
- **User Story 1** (T012-T017) → **User Story 2** (T020-T025) → **User Story 3** (T027-T030)
- **Polish (Phase 6)** runs after all user stories.
- Parallelizable tasks are marked `[P]`; ordering respects data flow and artifact hand‑offs as described above.