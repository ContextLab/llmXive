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
 1. Include `pandas`, `scikit-learn`, `matplotlib`, `seaborn`, `rpy2`, `requests`, `psutil`, `datasets`.
 2. **Critical Dependency Check**: `rpy2` is mandatory. If `pip install rpy2` fails, halt with "Tooling Unavailable" error.
 3. **R Environment Check**: Explicitly verify R is installed and `biomaRt` (version 2023-10) is available via shell command. If missing, trigger "Tooling Unavailable" halt.
 4. **LCM Fallback**: If `imp3` is missing, the task MUST define a custom LCM implementation using the **MinProb** algorithm in `code/utils/lcm.py`. Do NOT fallback to `scikit-learn`'s `MeanImputer` or `IterativeImputer`. Log the deviation in `docs/deviation_log.md`. (FR-002, Constitution VII).
- [ ] T003 [P] Configure linting (flake8) and formatting (black) tools.

- [X] T035 [P] [US1] Implement `code/data_ingestion/verify_sources.py`. **Input**: `research.md`. **Logic**: Fetch primary source metadata for all citations, verify title-token overlap ≥ threshold (from config.py). **Constraint**: This task MUST pass before T004 runs. If any citation fails validation, the pipeline MUST halt with a "Verified Accuracy Gate Failure" error. (Constitution Principle II).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Setup `code/utils/config.py` for random seeds, paths, species/stress constants, and **Reference-Validator threshold** (default 0.7, configurable).
- [ ] T005 [P] Implement data schema validation using Pydantic or simple dict checks for `data/raw/` and `data/processed/`.
- [ ] T006 [P] Setup logging infrastructure to capture warnings (e.g., dropped rows, missing data) to `logs/pipeline.log`.
- [X] T007 [P] Create base data loading utilities in `code/utils/data_utils.py` (CSV/Parquet I/O).
- [X] T008 [P] Implement checksum verification utility in `code/utils/checksums.py` for SHA-256 validation of raw downloads.
- [X] T023 [P] Create `docs/deviation_log.md` documenting the decision logic for (2604.10702, https://arxiv.org/abs/2604.10702). **This document must exist before T019 runs.** (Constitution Principle VI).

### Phase 2.5: Data Verification & Feasibility Gate (Critical)

**Purpose**: Ensure all data sources are real, reachable, and that no fabrication occurs. This phase runs AFTER Foundation but BEFORE User Story 1.

- [X] T036 [P] [US1] Implement `code/data_ingestion/sanity_check.py` to verify that the merged dataset contains **real** measured values (no `random.*` generated numbers, no constant columns with fake IDs). **Fail if any synthetic placeholder data is detected.**
- [X] T037 [P] [US1] Implement `code/data_ingestion/sample_check.py` to ensure at least 5 samples exist per stress condition for Arabidopsis, Rice, or Wheat. **Logic**:
 1. Count samples `n` per stress condition in the merged dataset.
 2. **If n < 5 for ALL species/stress pairs**: Trigger the "Data Unavailable" halt path and exit cleanly.
 3. **If n < 5 for ANY specific species/stress pair (but not all)**: **Exclude ONLY that specific pair** from the merged matrix, log the exclusion reason in `logs/pipeline.log`, and set a flag `EXCLUDED_PAIRS` in `results/sample_stats.json`. **Proceed to T019 with remaining data.**
 4. **If 5 <= n < 50 for ANY condition**: Flag the pair for "Small Sample Warning", log to `logs/pipeline.log`, and set `LOOCV_REQUIRED=True` in `results/cv_strategy.json`. Proceed to T019.
 5. **If n >= 50 for ALL conditions**: Proceed to T019 (5-fold CV strategy). (Plan: "Statistical Rigor & Dataset Fit", Spec US-1 Acceptance 3).

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
- [X] T018 [US1] Implement `code/data_ingestion/completeness.py` to calculate `Data Completeness %` = (Retained Datasets / Initial Query Results) × 100 and write to `results/data_completeness.json`. **Input**: Output of T014 (pipeline.py). **Logic**: Read initial query count from `logs/pipeline.log` (T011) and retained dataset count from T014 output. Calculate percentage. (SC‑004).

**Checkpoint**: At this point, User Story 1 should be fully functional, tested, and ready for modeling.

---

## Phase 4: User Story 2 - Baseline Model Training and Cross‑Stress Validation (Priority: P2)

**Goal**: Train Random Forest and SVR models using 5‑fold CV (if n ≥ 50) or LOOCV (if n < 50), include Stress-Blind baseline, Null model, and Target-Permutation control test.

**Independent Test**: The modeling module can be tested independently by feeding it a static, pre-saved CSV of the preprocessed data and verifying that it outputs a JSON report containing R² scores, RMSE values, and feature‑importance rankings for both within-stress and cross-stress validation splits.

### Phase 4.0: Modeling Infrastructure (Prerequisites)

**Purpose**: Essential infrastructure for modeling that must be ready before training begins

- [X] T032 [P] Implement checkpointing utility in `code/modeling/checkpoint.py` to save intermediate model state and partial results after each CV fold. **This utility must be available before T019 runs.** (Risk Mitigation).

### Implementation for User Story 2

- [X] T019a [US2] Implement `code/modeling/strategy_selector.py` to determine CV strategy. **Logic**:
 * Read sample counts from `logs/pipeline.log` (generated by T037).
 * **If n >= 50 for ALL stress conditions**: Output config `strategy: "5-fold"`.
 * **If 5 <= n < 50 for ANY condition**: Output config `strategy: "LOOCV"`.
 * **If n < 5**: Halt (handled by T037, but double-check here).
 * Output: `results/cv_strategy.json`. (Plan: "Statistical Rigor & Dataset Fit").
- [X] T019b [US2] Implement `code/modeling/hyperparameter_config.py` to set hyperparameters based on strategy. **Logic**:
 * Read `results/cv_strategy.json`.
 * **If `strategy == "5-fold"`**: Set `n_estimators=100`, `max_depth=10`.
 * **If `strategy == "LOOCV"`**: Calculate `n_estimators = min(100, max(10, n_samples * 2))` to dynamically adjust for dataset complexity. If `n_estimators > 80` and RAM < 6GB, log a warning "High tree count may exceed RAM; consider sampling" but proceed. Set `max_depth=3` or linear SVR to prevent overfitting.
 * Output: `results/hyperparameters.json`. (Constitution VII).
- [X] T019c [US2] Implement `code/modeling/train.py` to train `RandomForestRegressor` and `SVR`. **Logic**:
 * Read processed data.
 * Read strategy from `results/cv_strategy.json` and hyperparameters from `results/hyperparameters.json`.
 * Perform CV (5-fold or LOOCV) ensuring all preprocessing (normalization, imputation) occurs **inside** each fold (SC‑005).
 * Output: `results/within_stress_metrics.json` (R², RMSE per fold). (FR‑004, Plan Threshold n < 50).
- [X] T024 [US2] Implement `code/modeling/cross_stress_eval.py` to perform **Cross-Stress Evaluation**. **Input**: `results/cv_strategy.json`. **Logic**:
 * **Read Strategy**: Check `results/cv_strategy.json`.
 * **For each valid stress pair (Source A, Target B)**:
 * **If Strategy == "5-fold"**: Train model on A (5-fold CV), aggregate predictions for A, then train on ALL of A and predict B.
 * **If Strategy == "LOOCV"**: Iterate i=1..n on Source A (train on A\i, predict A\i). Aggregate predictions for A. Then train a final model on ALL of A (or use the LOOCV ensemble) to predict the entire Target B dataset.
 * **Evaluation**: Calculate R² and RMSE for predictions on B (Ground Truth: actual expression in B).
 * Output: `results/cross_stress_metrics.json` (R², RMSE for each pair). (SC‑002, FR‑005).
- [X] T020a [US2] Implement `code/modeling/baselines.py` to train the **Raw Feature Baseline** model (RF & SVR) on the original protein matrix **ignoring stress labels entirely**. This measures general proteome-expression correlation. Store R² and RMSE. (Addresses SC‑001). Output: `results/raw_feature_baseline.json`.
- [X] T021b [US2] Implement **Stress-Label Permutation Control Test**. **Logic**:
 * **Null Hypothesis**: Stress labels are uncorrelated with protein features (model predicts label noise).
 * **Input**: Training set data from T019c.
 * **Action**: **MUST RUN** a permutation test (1000 iterations). In each iteration:
 1. **Shuffle** `StressCondition` labels **within the training set** (before CV split) to break the feature-label correlation.
 2. **Retrain** models with the same CV strategy and hyperparameters on the shuffled data.
 3. Calculate mean R² of the shuffled models.
 * **Output**: `results/shuffle_control.json` (mean R², p-value from permutation test). (FR‑005, SC‑005).
- [X] T020c [US2] Implement `code/modeling/metrics.py` to calculate the **'drop in R²'** metrics. **Input**: `results/within_stress_metrics.json` (T019c), `results/cross_stress_metrics.json` (T024), `results/raw_feature_baseline.json` (T020a). **Logic**:
 * Calculate `Drop_Cross = R²(Within-Stress) - R²(Cross-Stress Test)`.
 * Calculate `Drop_Raw = R²(Within-Stress) - R²(Raw Feature Baseline)`. **This is the primary SC-002 metric for stress-specificity.**
 * Verify `Drop_Raw` is non-negative (or log warning).
 * Output: `results/r2_drop.json` containing both `Drop_Cross` and `Drop_Raw`. (SC‑002, FR‑005).
- [X] T021a [US2] Implement `code/modeling/evaluate.py` to perform Null Model comparison (predict mean) and calculate improvement in R² over RF/SVR (SC‑001). **Logic**:
 * Calculate mean of target variable in training set.
 * Predict mean for all test samples.
 * Calculate R² and RMSE for this Null Model.
 * Compare against RF/SVR R².
 * Output: `results/null_model_metrics.json`. (SC‑001).
- [X] T022 [US2] Implement `code/modeling/feature_importance.py` to extract and rank the top proteins by absolute importance score for each model (FR‑006).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Visualization and Reproducibility Reporting (Priority: P3)

**Goal**: Generate publication‑ready figures (scatter, confusion matrix, feature importance) and runtime metrics report.

**Independent Test**: The reporting module can be tested by providing it a dummy model object and a sample prediction array, verifying that it generates PNG files for all required plot types and a text summary of execution time and memory usage.

**Dependency**: This phase runs AFTER Phase 4 (US2) completes.

### Implementation for User Story 3

- [X] T026 [US3] Implement `code/reporting/plots.py` to generate scatter plots (Predicted vs Actual with regression line & R² annotation), cross‑stress heatmaps, and feature‑importance bar charts (FR‑007).
- [ ] T027 [US3] Implement `code/reporting/metrics.py` to log total CPU time and peak memory usage to `results/runtime_metrics.json`. **Constraint**: Include an explicit assertion that if runtime > 6 hours or memory > 7GB, the script exits with a non-zero code and logs a "Resource Limit Exceeded" error. (FR‑008).
- [X] T028 [US3] Integrate plotting and metrics into a final `code/reporting/generate_report.py` script that produces the summary JSON and PNGs.
- [ ] T029 [US3] Add a sanity‑check in `metrics.py` that verifies input data is not a mock object (e.,g., non‑zero variance, required attributes) before writing runtime metrics.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T030a [US3] Update `README.md` with installation steps, usage examples, **Data Sources**, and **Results** sections.
- [ ] T030b [P] Add docstrings to all public functions in `code/`.
- [X] T030c [P] Extract common I/O logic into `code/utils/io.py`. Remove unused imports and variables.
- [ ] T033 [P] Additional unit tests in `tests/unit/` covering edge cases (all‑missing columns, mismatched IDs).
- [ ] T034 Run `quickstart.md` validation to ensure full pipeline reproducibility.

---

## Phase X: Review & Correction (Post-Analysis)

**Purpose**: Address specific concerns raised by the `analyze` stage regarding data flow, streaming, and error handling.

- [X] T040 [US1] **Refactor Data Loading for Streaming**: Update `code/data_ingestion/download.py` and `code/data_ingestion/normalize.py` to support `streaming=True` for large datasets (e.g., via `datasets.load_dataset(..., streaming=True)`). **Constraint**: Do NOT fallback to synthetic data if a stream fails; the task must raise a clear error if the real source is unreachable. (Constitution Principle: Real Data Only).
- [ ] T041 [US1] **Implement Strict Error Handling for Data Fetch**: Remove any `try/except` blocks in `download.py` that catch network errors and fall back to `generate_synthetic_*()` or mock data. Ensure that any failure to fetch real data results in an immediate, loud failure (Exception) to prevent fabrication. (Constitution Principle: No Synthetic Fallback).
- [~] T042 [US2] **Verify Data Flow Order**: Add a pre-flight check in `code/main.py` that ensures `data/processed/merged_matrix.csv` exists and is non-empty before `train.py` is invoked. If the file is missing or empty, halt with "Data Dependency Error: Preprocessing did not complete successfully." (Fix Data Flow Order).
- [X] T043 [US2] **Add Sample Size Logging**: Enhance `code/modeling/train.py` to explicitly log the sample size `n` used for each stress condition and the resulting CV strategy (5-fold vs LOOCV) to `logs/pipeline.log` before training starts. (Transparency).
- [X] T044 [US3] **Validate Plot Inputs**: Add a check in `code/reporting/plots.py` to ensure input arrays have non-zero variance before generating scatter plots, preventing runtime errors on degenerate datasets. (Robustness).