# Tasks: The Impact of Perceived Social Support on Resilience to Online Harassment

**Input**: Design documents from `/specs/001-social-support-resilience/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

**⚠️ CRITICAL METHODOLOGICAL NOTE**:
The current implementation **conforms to the original specification** (dual‑dataset synthetic cohort). The plan’s single‑dataset pivot is flagged for review via a dedicated kick‑back task (T041). Until the spec is amended, the pipeline must satisfy FR‑001, FR‑002, US‑1, and SC‑001.

## Format: `[ID] [P?] [Story] description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root

<!--
 ============================================================================
 IMPORTANT: The tasks below reflect the revised, spec‑compliant workflow.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per implementation plan (`code/data`, `code/analysis`, `code/config`, `code/tests`)
- [X] T002 Initialize Python 3.11 project with pinned dependencies (`requirements.txt`: pandas, numpy, scikit-learn, statsmodels, scipy, pyyaml)
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
 scoring: 0-3 per item, total 0‑60
 GAD-7:
 items: [gad1, gad2, gad3, gad4, gad5, gad6, gad7]
 reverse_items: []
 scoring: 0‑3 per item, total 0‑21
 PCL-5:
 items: [pcl1, pcl2, pcl3, pcl4, pcl5, pcl6, pcl7, pcl8, pcl9, pcl10, pcl11, pcl12, pcl13, pcl14, pcl15, pcl16, pcl17, pcl18, pcl19, pcl20, pcl21, pcl22, pcl23, pcl24, pcl25]
 reverse_items: []
 scoring: 0‑4 per item, total 0‑100
 ```
- [X] T005 [P] Implement `tests/test_scales.py` with unit tests verifying scoring logic matches the definitions in `config/scales.yaml`.
- [X] T006 [P] Setup `code/data/ingestion.py` skeleton with read‑only raw data validation logic.
- [X] T007 Create `code/data/cohort.py` skeleton for constructing the synthetic cohort.
- [ ] T008 [P] Configure `main_pipeline.py` entry point to orchestrate modular steps.
- [ ] T009 Setup environment configuration for data paths **and** create `config/seeds.yaml` to define reproducible seeds (e.g., `random_seed: a fixed integer for reproducibility`, `The specific value to remove/generalize: 'a fixed random seed'

Rewritten passage:
The study will investigate [Research Question] using [Method] (Citation). A fixed random seed will be employed to ensure reproducibility of the computational procedures. `). This file is referenced by downstream tasks.

**Checkpoint**: Foundation ready – user story implementation can now begin in parallel.

---

## Phase 3: User Story 1 - Data Harmonization & Synthetic Cohort Construction (Priority: P1) 🎯 MVP

**Goal**: Ingest both GSS 2022 and Cyberbullying Survey 2021, harmonize variables, handle missingness, and generate a synthetic cohort via propensity‑score weighting/matching.

### Tests for User Story 1 (OPTIONAL)

- [ ] T010 [P] [US1] Contract test for data schema in `tests/contract/test_analysis_cohort_schema.py`
- [ ] T011 [P] [US1] Unit test for CES‑D/GAD‑7 scoring logic in `tests/unit/test_scale_scoring.py`

### Implementation for User Story 1

- [ ] T012 [US1] Implement `code/data/ingestion.py` to **download and load** both datasets:
 - **GSS 2022**: `https://gss.norc.org/files/stata/2022/2022_Stata.zip` (extract `GSS2022.dta`).
 - **Cyberbullying Survey 2021**: `.
 Include validation of file integrity (checksum) and log E‑MISSING‑001 if required items are absent.
- [ ] T018 [US1] Validate GSS 2022 structure; if PCL‑5 items or essential harassment variables are missing, log a warning and **skip** GSS ingestion, proceeding with the Cyberbullying dataset alone (fallback documented). This satisfies the plan’s concern about dataset suitability.
- [~] T013 [P] [US1] Implement `code/data/preprocessing.py` to:
 1. Perform listwise deletion for variables with >5 % missingness.
 2. For remaining missing values, apply **MICE** imputation (`m=5`, `max_iter=10`, `random_state=42`) **only on the predictor matrix**: `['age','gender','education','income','social_support','harassment_severity','depression','anxiety','ptsd']`.
 3. Apply scale scoring using `config/scales.yaml` (including conditional PCL‑5 handling).
 This merges the former T013a functionality.
- [~] T014 [P] [US1] Implement `code/data/cohort.py` to:
 1. Compute propensity scores for dataset source (GSS vs Cyberbullying) using demographics (`age`, `gender`, `education`, `income`).
 2. Perform **nearest‑neighbor matching** with caliper ≤0.2 SD of the logit of the propensity score.
 3. Apply inverse‑probability weighting to create a **synthetic cohort** where each row represents a weighted pair.
 4. Output `data/results/synthetic_cohort.csv`.
 If GSS was skipped (per T018), proceed with **weight‑only** adjustment on the single dataset and still produce `synthetic_cohort.csv`.
- [~] T015 [P] [US1] Validate the synthetic cohort:
 - Compute **standardized mean differences (SMD)** for each covariate; enforce SMD ≤ 0.1 (SC‑001).
 - Check **variance of Harassment Exposure** (SD > 0.5, N > 30).
 - Compute **VIF** for the model matrix (`social_support`, `harassment_exposure`, interaction, plus covariates) and ensure VIF < 5.
 - Log warnings if any check fails; the pipeline proceeds only if balance criteria are met.
- [~] T016 [US1] Save the validated synthetic cohort to `data/results/synthetic_cohort.csv` **only after** successful T015.
- [~] T017 [US1] Add comprehensive logging for ingestion, preprocessing, matching, and validation steps, including any fallback decisions.

**Checkpoint**: User Story 1 is fully functional and produces a spec‑compliant synthetic cohort.

---

## Phase 4: User Story 2 - Interaction Analysis & Hypothesis Testing (Priority: P2)

**Goal**: Fit robust OLS models with interaction term, compute bias‑corrected bootstrapped CIs, and apply multiple‑comparison correction.

### Tests for User Story 2 (OPTIONAL)

- [~] T018a [P] [US2] Contract test for regression results schema in `tests/contract/test_regression_results_schema.py`
- [~] T019 [P] [US2] Unit test for bootstrapping logic in `tests/unit/test_bootstrap_ci.py`

### Implementation for User Story 2

- [~] T020 [P] [US2] Implement `code/analysis/models.py` to fit OLS models with heteroskedasticity‑consistent (HC3) standard errors for Depression, Anxiety, and PTSD (if PCL‑5 present). Include interaction term `SocialSupport:HarassmentExposure`.
- [~] T021 [P] [US2] Compute **[deferred] bias‑corrected accelerated (BCa) bootstrap CIs** with 1,000 resamples using `statsmodels.stats.bootstrap`. Seed the process with `bootstrap_seed` from `config/seeds.yaml`.
- [~] T022 [P] [US2] Add fallback: if the robust model fails to converge, automatically refit a standard OLS model (no HCSE) and log status `E‑NONCONV‑001`.
- [~] T023 [P] [US2] Implement Benjamini‑Hochberg FDR correction across the set of outcome tests (Depression, Anxiety, PTSD) and attach adjusted p‑values to the results.
- [~] T024 [P] [US2] Save regression outputs (coefficients, SEs, p‑values, bootstrap CIs, adjusted p‑values) to `data/results/regression_results.csv`.
- [~] T025 [P] [US2] Update `code/analysis/results.py` to read `synthetic_cohort.csv` (produced by T016) and generate a summary report `data/results/regression_summary.md`.

**Checkpoint**: User Stories 1 & 2 are independently testable.

---

## Phase 5: User Story 3 - Sensitivity Analysis & Robustness Checks (Priority: P3)

**Goal**: Re‑run models with alternative harassment definitions and platform stratification.

### Tests for User Story 3 (OPTIONAL)

- [~] T026 [P] [US3] Contract test for sensitivity results schema in `tests/contract/test_sensitivity_results_schema.py`

### Implementation for User Story 3

- [~] T027 [P] [US3] Implement `code/analysis/sensitivity.py` to:
 1. Re‑fit models using **continuous harassment severity** instead of binary exposure.
 2. If a `platform` column exists, stratify analyses by platform. Only the **top three** most frequent platforms are kept; all others are grouped as `Other`.
 3. If fewer than two platforms are present, log `E‑SKIP‑001` and skip stratification.
- [~] T028 [P] [US3] Compare interaction coefficients from each sensitivity run against the baseline (from T020) and produce a table of coefficient shifts.
- [~] T029 [P] [US3] Save the sensitivity summary to `data/results/sensitivity_analysis.csv`.
- [~] T030 [P] [US3] Add logging for each scenario, including data availability warnings.

**Checkpoint**: All user stories are now functional.

---

## Phase 6: Polish & Cross‑Cutting Concerns

- [~] T031 [P] Update `main_pipeline.py` to chain all phases: Ingestion → Preprocessing → Matching → Validation → Modeling → Sensitivity → Reporting.
- [~] T032 Code cleanup and refactoring in `code/analysis/` to ensure modularity.
- [~] T033 Performance optimization: Verify that bootstrapping (1,000 resamples for up to three models) completes within 6 hours on a 2‑core CPU (profiling and possible parallelisation of bootstrap replicates).
- [~] T034 [P] Additional unit tests for edge cases (empty datasets, missing columns) in `tests/unit/`.
- [~] T035 Run `quickstart.md` validation to ensure end‑to‑end pipeline execution.
- [~] T036 Update `research.md` with placeholder interpretation that emphasizes associational findings.
- [~] T041 [P] **Kickback task**: Create a pull request that amends `specs/001-social-support-resilience/spec.md` to either (a) retain the dual‑dataset synthetic‑cohort requirements **or** (b) formally adopt the single‑dataset approach with revised FR/SC. Include a summary of the methodological justification and request review from the spec owner.

---

## Dependencies & Execution Order

- **Setup (Phase 1)** → **Foundational (Phase 2)** (blocking)
- **User Story 1** (T012‑T017) → **User Story 2** (T020‑T025) → **User Story 3** (T027‑T030)
- **Polish (Phase 6)** runs after all user stories.
- Parallelizable tasks are marked `[P]`; ordering respects data flow and artifact hand‑offs as described above.
