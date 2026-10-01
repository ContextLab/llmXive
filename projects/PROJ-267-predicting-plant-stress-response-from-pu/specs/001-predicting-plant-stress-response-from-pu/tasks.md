# Tasks: Predicting Plant Stress Response from Publicly Available Proteomic Data

**Input**: Design documents from `/specs/001-predict-plant-stress-response/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.,g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root
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

## Phase 1: Setup & Verification (Shared Infrastructure)

**Purpose**: Project initialization, directory creation, and immediate citation verification.

- [ ] T001a [US1] Create project directories: `code/`, `tests/`, `logs/`, `results/`.
- [ ] T001b [US1] Create data directories: `data/raw/`, `data/processed/`.
- [ ] T001c [US1] Create `docs/` directory.

- [X] T002 [US1] Create `code/requirements.txt` and setup environment. **Logic**:
 1. Include `pandas`, `scikit-learn`, `matplotlib`, `seaborn`, `rpy2`, `requests`, `psutil`.
 2. **Critical Dependency Check**: `rpy2` is mandatory. If `pip install rpy2` fails, halt with "Tooling Unavailable" error.
 3. **R Environment Check**: Explicitly verify R is installed and `biomaRt` (version 2023-10) is available via shell command. If missing, trigger "Tooling Unavailable" halt.
 4. **LCM Fallback**: If `imp3` is missing, the task MUST define a custom LCM implementation using the **MinProb** algorithm in `code/utils/lcm.py`. Do NOT fallback to `scikit-learn`'s `MeanImputer` or `IterativeImputer`. Log the deviation in `docs/deviation_log.md`. (FR-002, Constitution VII).
- [ ] T003 [P] Configure linting (flake8) and formatting (black) tools.

- [X] T035 [P] [US1] Implement `code/data_ingestion/verify_sources.py`. **Input**: `research.md`. **Logic**: Fetch primary source metadata for all citations, verify title-token overlap ≥ threshold (from config.py). **Constraint**: This task MUST pass before T004 runs. If any citation fails validation, the pipeline MUST halt with a "Verified Accuracy Gate Failure" error. (Constitution Principle II).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Setup `code/utils/config.py` for random seeds, paths, species/stress constants, and **Reference-Validator threshold** (default 0.7, configurable).
- [ ] T005 [P] Implement data schema validation using Pydantic or simple dict checks for `data/raw/` and `data/processed/`.
- [ ] T006 [P] Setup logging infrastructure to capture warnings (e.g., dropped rows, missing data) to `logs/pipeline.log`.
- [X] T007 [P] Create base data loading utilities in `code/utils/data_utils.py` (CSV/Parquet I/O).
- [X] T008 [P] Implement checksum verification utility in `code/utils/checksums.py` for SHA-256 validation of raw downloads.
- [X] T023 [P] Create `docs/deviation_log.md` documenting the decision logic for (2604.10702, https://arxiv.org/abs/2604.10702). **This document must exist before T019 runs.** (Constitution Principle VI).

### Phase 2.5: Data Verification & Feasibility Gate (Critical)

**Purpose**: Ensure all data sources are real, reachable, and that no fabrication occurs. This phase runs AFTER Foundation but BEFORE User Story 1.

- [X] T036 [P] [US1] Implement `code/data_ingestion/sanity_check.py` to verify that the merged dataset contains **real** measured values (no `random.*` generated numbers, no constant columns with fake IDs). **Fail if any synthetic placeholder data is detected.**
- [X] T037 [P] [US1] Implement `code/data_ingestion/sample_check.py` to ensure at least 5 samples exist per stress condition for Arabidopsis, Rice, or Wheat. **If n < 5 for all species, trigger the "Data Unavailable" halt path and exit cleanly.**

**Checkpoint**: Data is verified real and sufficient. Proceed to User Story 1 only if T035-T037 pass.

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Automatically download, normalize, merge, and impute public proteomic and transcriptomic datasets for Arabidopsis, rice, and wheat under drought, salinity, and heat.

**Independent Test**: The pipeline can be fully tested by running the data ingestion script against a known subset of GEO/ProteomeXchange IDs and verifying that the output is a single, normalized CSV matrix containing protein abundances and matched gene expression values with no missing rows for the specified species/stress.

### Implementation for User Story 1

- [X] T011 [US1] Implement `code/data_ingestion/download.py` to fetch raw data from NCBI GEO/ProteomeXchange. **Input**: `research.md` (contains explicit URLs). **Logic**: Read URLs from research.md, validate domain (ncbi.nlm.nih.gov, proteomexchange.org, ebi.ac.uk), download files. Raise ValueError if file size < 1KB or domain invalid. (FR-001).
- [X] T012 [US1] Implement `code/data_ingestion/normalize.py` to filter low‑abundance proteins (<50% detection) and apply **Left-Censored Missing (LCM) imputation**. **Logic**:
 1. Attempt to use `imp3` (MinProb).
 2. If `imp3` is not available (as determined by T002), use the custom **MinProb** implementation located in `code/utils/lcm.py`.
 3. Do NOT use `scikit-learn`'s `IterativeImputer` or `MeanImputer`. Log the specific method used in `docs/deviation_log.md`. (FR-002).
- [X] T013 [US1] Implement `code/data_ingestion/merge.py` to map UniProt → Ensembl IDs. **Primary Method**: `biomaRt R package (version 2023-10)` via `rpy2`. **Logic**:
 1. Verify `rpy2` is functional (as ensured by T002).
 2. Attempt mapping.
 3. **Failure Handling**: If `biomaRt` mapping fails or returns no results for a significant portion of data, **log the drop count and proceed with the remaining matched rows**. Do NOT use fallbacks for mapping logic itself. Do NOT halt unless the final dataset size is < 5 (per T037). (FR-003, Constitution I).
- [X] T014 [US1] Implement `code/data_ingestion/pipeline.py` to orchestrate download → normalize → merge, handling metadata ambiguity (exclude or flag ambiguous records). Include logging for exclusion reasons. (FR-001‑FR‑003).

### Phase 3.6: Integration Metrics (Run AFTER T014)

**Purpose**: Verify implementation tasks and calculate metrics based on pipeline output.

- [X] T009 [US1] Unit test for **LCM (MinProb)** imputation logic in `tests/unit/test_ingestion.py`. **Functions**: `test_lcm_imputation_minprob`, `test_lcm_imputation_filter_low_abundance`. (Synthetic censored data).
- [X] T010 [US1] Unit test for identifier‑mapping logic in `tests/unit/test_ingestion.py`. **Functions**: `test_biomaRt_mapping`, `test_biomaRt_failure_raises_error`. (No fallbacks).
- [ ] T018 [US1] Implement `code/data_ingestion/completeness.py` to calculate `Data Completeness %` = (Retained Datasets / Initial Query Results) × 100 and write to `results/data_completeness.json`. **Input**: Output of T014 (pipeline.py). (SC‑004).

**Checkpoint**: At this point, User Story 1 should be fully functional, tested, and ready for modeling.

---

## Phase 4: User Story 2 - Baseline Model Training and Cross‑Stress Validation (Priority: P2)

**Goal**: Train Random Forest and SVR models using 5‑fold CV (if n ≥ 50) or LOOCV (if n < 50), include Stress-Blind baseline, Null model, and Target-Permutation control test.

**Independent Test**: The modeling module can be tested independently by feeding it a static, pre-saved CSV of the preprocessed data and verifying that it outputs a JSON report containing R² scores, RMSE values, and feature‑importance rankings for both within-stress and cross-stress validation splits.

### Phase 4.0: Modeling Infrastructure (Prerequisites)

**Purpose**: Essential infrastructure for modeling that must be ready before training begins

- [X] T032 [P] Implement checkpointing utility in `code/modeling/checkpoint.py` to save intermediate model state and partial results after each CV fold. **This utility must be available before T019 runs.** (Risk Mitigation).

### Implementation for User Story 2

- [ ] T019 [US2] Implement `code/modeling/train.py` to train `RandomForestRegressor` and `SVR`. **Logic**:
 * Read processed data.
 * **Check Sample Size Per Condition**: Count samples for **each stress condition**.
 * **If n >= 50 for ALL stress conditions**: Perform 5‑fold CV with `n_estimators=100`, `max_depth=10`.
 * **If n < 50 for ANY stress condition**: Switch to **Leave-One-Out Cross-Validation (LOOCV)**. **Constraint**: To satisfy Constitution VII (Resource Discipline), reduce hyperparameters to `n_estimators=10`, `max_depth=3` (or use `SVR` with linear kernel if RF is too heavy) to prevent 7GB RAM overflow. Perform a pre-flight memory check before initiating LOOCV.
 * All preprocessing (normalization, imputation, feature selection) must occur **inside** each CV fold (SC‑005).
 * Output: `results/within_stress_metrics.json` (R², RMSE per fold). (FR‑004, Plan Threshold n < 50).
- [ ] T024 [US2] Implement `code/modeling/cross_stress_eval.py` to perform **Cross-Stress Evaluation**. Logic:
 * Train models on **Stress A** (e.,g., Drought) and test on **Stress B** (e.,g., Salinity).
 * Repeat for all valid stress pairs.
 * Output: `results/cross_stress_metrics.json` (R², RMSE for each pair). (SC‑002, FR‑005).
- [ ] T020a [US2] Implement `code/modeling/baselines.py` to train the **Raw Feature Baseline** model (RF & SVR) on the original protein matrix **ignoring stress labels entirely**. This measures general proteome-expression correlation. Store R² and RMSE. (Addresses SC‑001).
- [ ] T021b [US2] Implement **Stress-Label Permutation Control Test**. Logic:
 * **Null Hypothesis**: The model predicts the stress label itself.
 * Shuffle `StressCondition` labels **globally** (not relative to predictors) to break the link between predictors and stress.
 * Retrain models with same CV strategy.
 * Perform **Permutation Test (1000 iterations)** to calculate p-value comparing real R² vs shuffled R².
 * **Output**: `results/shuffle_control.json` (p-value, mean R²). **Constraint**: Always write the file, regardless of p-value. Do NOT raise an error if p >= 0.05. The goal is to measure the drop, not to fail the build. (FR‑005, Control for Stress-Label Leakage).
- [ ] T020c [US2] Implement `code/modeling/metrics.py` to calculate the **'drop in R²'** metric for SC-002. **Logic**:
 * Read `results/within_stress_metrics.json` (from T019).
 * Read `results/shuffle_control.json` (from T021b, the Stress-Shuffled Baseline).
 * Calculate `Drop = R²(Within-Stress) - R²(Shuffled Baseline)`.
 * Output: `results/r2_drop.json`. (SC‑002).
- [ ] T021a [US2] Implement `code/modeling/evaluate.py` to perform Null Model comparison (predict mean) and calculate improvement in R² over RF/SVR (SC‑001).
- [ ] T022 [US2] Implement `code/modeling/feature_importance.py` to extract and rank the top proteins by absolute importance score for each model (FR‑006).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Visualization and Reproducibility Reporting (Priority: P3)

**Goal**: Generate publication‑ready figures (scatter, confusion matrix, feature importance) and runtime metrics report.

**Independent Test**: The reporting module can be tested by providing it with a dummy model object and a sample prediction array, verifying that it generates PNG files for all required plot types and a text summary of execution time and memory usage.

**Dependency**: This phase runs AFTER Phase 4 (US2) completes.

### Implementation for User Story 3

- [ ] T026 [US3] Implement `code/reporting/plots.py` to generate scatter plots (Predicted vs Actual with regression line & R² annotation), cross‑stress heatmaps, and feature‑importance bar charts (FR‑007).
- [ ] T027 [US3] Implement `code/reporting/metrics.py` to log total CPU time and peak memory usage to `results/runtime_metrics.json`. **Constraint**: Include an explicit assertion that if runtime > 6 hours or memory > 7GB, the script exits with a non-zero code and logs a "Resource Limit Exceeded" error. (FR‑008).
- [ ] T028 [US3] Integrate plotting and metrics into a final `code/reporting/generate_report.py` script that produces the summary JSON and PNGs.
- [ ] T029 [US3] Add a sanity‑check in `metrics.py` that verifies input data is not a mock object (e.,g., non‑zero variance, required attributes) before writing runtime metrics.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T030a [US3] Update `README.md` with installation steps, usage examples, **Data Sources**, and **Results** sections.
- [ ] T030b [P] Add docstrings to all public functions in `code/`.
- [ ] T030c [P] Extract common I/O logic into `code/utils/io.py`. Remove unused imports and variables.
- [ ] T033 [P] Additional unit tests in `tests/unit/` covering edge cases (all‑missing columns, mismatched IDs).
- [ ] T034 Run `quickstart.md` validation to ensure full pipeline reproducibility.