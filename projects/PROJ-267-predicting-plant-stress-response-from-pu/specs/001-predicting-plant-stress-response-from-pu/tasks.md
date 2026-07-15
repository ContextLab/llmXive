# Tasks: Predicting Plant Stress Response from Publicly Available Proteomic Data

**Input**: Design documents from `/specs/001-predict-plant-stress-response/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001a [P] Create project directory structure: `mkdir -p code/data_ingestion code/modeling code/reporting code/utils tests data/raw data/processed results logs docs`.
- [ ] T001b [P] Verify directory structure exists and is writable.

- [X] T002 Create `code/requirements.txt` containing pinned versions for: pandas==2.0.3, scikit-learn==1.3.0, matplotlib==3.7.2, seaborn==0.12.2, rpy2==3.5.13, requests==2.31.0, psutil==5.9.5, imp3==1.2.0. **Note: `imp3` is required for LCM MinProb imputation.**
- [ ] T003 [P] Configure linting (flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Setup `code/utils/config.py` for random seeds, paths, species/stress constants, and **Reference-Validator threshold** (default 0.7, configurable).
- [ ] T005 [P] Implement data schema validation using Pydantic or simple dict checks for `data/raw/` and `data/processed/`.
- [ ] T006 [P] Setup logging infrastructure to capture warnings (e.g., dropped rows, missing data) to `logs/pipeline.log`.
- [X] T007 Create base data loading utilities in `code/utils/data_utils.py` (CSV/Parquet I/O).
- [X] T008 Implement checksum verification utility in `code/utils/checksums.py` for SHA-256 validation of raw downloads.
- [X] T023 [P] Create `docs/deviation_log.md` documenting the decision logic for LOOCV vs 5-fold CV (based on sample size n < 50). **This document must exist before T019 runs.** (Constitution Principle VI).

### Phase 2.5: Data Verification & Feasibility Gate (Critical)

**Purpose**: Ensure all data sources are real, reachable, and that no fabrication occurs. This phase runs AFTER Foundation but BEFORE User Story 1.

- [X] T035 [P] [US1] Implement `code/data_ingestion/verify_sources.py` to validate that all citations in `research.md` are verified against primary sources. **Input: `research.md`. Logic: Fetch primary source metadata, verify title-token overlap ≥ threshold (from config.py), verify semantic relevance. Fail if any citation fails validation.** (Constitution Principle II).
- [X] T036 [P] [US1] Implement `code/data_ingestion/sanity_check.py` to verify that the merged dataset contains **real** measured values (no `random.*` generated numbers, no constant columns with fake IDs). **Fail if any synthetic placeholder data is detected.**
- [X] T037 [P] [US1] Implement `code/data_ingestion/sample_check.py` to ensure at least 5 samples exist per stress condition for Arabidopsis, Rice, or Wheat. **If n < 5 for all species, trigger the "Data Unavailable" halt path and exit cleanly.**

**Checkpoint**: Data is verified real and sufficient. Proceed to User Story 1 only if T035-T037 pass.

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Automatically download, normalize, merge, and impute public proteomic and transcriptomic datasets for Arabidopsis, rice, and wheat under drought, salinity, and heat.

**Independent Test**: The pipeline can be fully tested by running the data ingestion script against a known subset of GEO/ProteomeXchange IDs and verifying that the output is a single, normalized CSV matrix containing protein abundances and matched gene expression values with no missing rows for the specified species/stress.

### Implementation for User Story 1

- [X] T011 [P] [US1] Implement `code/data_ingestion/download.py` to fetch raw data from NCBI GEO/ProteomeXchange. **Input: `research.md` (contains explicit URLs). Logic: Read URLs from research.md, validate domain (ncbi.nlm.nih.gov, proteomexchange.org, ebi.ac.uk), download files. Raise ValueError if file size < 1KB or domain invalid.** (FR-001).
- [ ] T012 [P] [US1] Implement `code/data_ingestion/normalize.py` to filter low‑abundance proteins (<50% detection) and apply **Left-Censored Missing (LCM) imputation** using the **`imp3` library (MinProb algorithm)**. **MUST pin `imp3` version in requirements.txt. If `imp3` is unavailable, document deviation in `docs/deviation_log.md`.** (FR-002).
- [X] T013 [US1] Implement `code/data_ingestion/merge.py` to map UniProt → Ensembl IDs. **Primary Method: `biomaRt R package (version 2023-10)` via `rpy2`.** **Logic: Install biomaRt v2023-10 via Rscript if missing. Attempt mapping. If biomaRt fails for any ID, raise `RuntimeError` and log failure. DO NOT use fallbacks.** (FR-003, Constitution I).
- [X] T014 [US1] Implement `code/data_ingestion/pipeline.py` to orchestrate download → normalize → merge, handling metadata ambiguity (exclude or flag ambiguous records). Include logging for exclusion reasons. (FR-001‑FR‑003).

### Phase 3.6: Integration Metrics (Run AFTER T014)

**Purpose**: Verify implementation tasks and calculate metrics based on pipeline output.

- [X] T009 [US1] Unit test for **LCM (MinProb)** imputation logic in `tests/unit/test_ingestion.py`. **Functions: `test_lcm_imputation_minprob`, `test_lcm_imputation_filter_low_abundance`.** (Synthetic censored data).
- [X] T010 [US1] Unit test for identifier‑mapping logic in `tests/unit/test_ingestion.py`. **Functions: `test_biomaRt_mapping`, `test_biomaRt_failure_raises_error`.** (No fallbacks).
- [~] T018 [US1] Implement `code/data_ingestion/completeness.py` to calculate `Data Completeness %` = (Retained Datasets / Initial Query Results) × 100 and write to `results/data_completeness.json`. **Input: Output of T014 (pipeline.py).** (SC‑004).

**Checkpoint**: At this point, User Story 1 should be fully functional, tested, and ready for modeling.

---

## Phase 4: User Story 2 - Baseline Model Training and Cross‑Stress Validation (Priority: P2)

**Goal**: Train Random Forest and SVR models using 5‑fold CV (if n ≥ 50) or LOOCV (if n < 50), include Stress-Blind baseline, Null model, and Target-Permutation control test.

**Independent Test**: The modeling module can be tested independently by feeding it a static, pre-saved CSV of the preprocessed data and verifying that it outputs a JSON report containing R² scores, RMSE values, and feature‑importance rankings for both within-stress and cross-stress validation splits.

### Phase 4.0: Modeling Infrastructure (Prerequisites)

**Purpose**: Essential infrastructure for modeling that must be ready before training begins

- [ ] T032 [P] Implement checkpointing utility in `code/modeling/checkpoint.py` to save intermediate model state and partial results after each CV fold. **This utility must be available before T019 runs.** (Risk Mitigation).

### Implementation for User Story 2

- [ ] T019 [US2] Implement `code/modeling/train.py` to train `RandomForestRegressor` and `SVR`. Logic:
 * Read sample size from `results/data_completeness.json` or runtime check.
 * If **n ≥ 50** → perform 5‑fold CV; else → perform LOOCV (per `docs/deviation_log.md` T023).
 * All preprocessing (normalization, imputation, feature selection) must occur **inside** each CV fold (SC‑005).
 * Hyperparameters: `n_estimators=100`, `max_depth=10` (RF); `kernel='rbf'`, `C=1.0` (SVR).
 * Output: `results/within_stress_metrics.json` (R², RMSE per fold). (FR‑004, Plan Threshold n < 50).
- [ ] T024 [US2] Implement `code/modeling/cross_stress_eval.py` to perform **Cross-Stress Evaluation**. Logic:
 * Train models on **Stress A** (e.g., Drought) and test on **Stress B** (e.g., Salinity).
 * Repeat for all valid stress pairs.
 * Output: `results/cross_stress_metrics.json` (R², RMSE for each pair). (SC‑002, FR‑005).
- [ ] T020a [US2] Implement `code/modeling/baselines.py` to train **Within-Stress Baseline** models (RF & SVR) on the original (non‑residualized) protein matrix using the same CV strategy as T019. Store R² and RMSE for comparison. (Addresses SC‑001, SC‑002 numerator).
- [ ] T020c [US2] Implement `code/modeling/metrics.py` to calculate the **'drop in R²'** metric. Logic:
 * Read `results/within_stress_metrics.json` (from T019/T020a).
 * Read `results/cross_stress_metrics.json` (from T024).
 * Calculate `Drop = R²(Within-Stress) - R²(Cross-Stress)`.
 * Output: `results/r2_drop.json`. (SC‑002).
- [ ] T021a [US2] Implement `code/modeling/evaluate.py` to perform Null Model comparison (predict mean) and calculate improvement in R² over RF/SVR (SC‑001).
- [ ] T021b [US2] Implement **Stress-Label Permutation Control Test**. Logic:
 * Shuffle `StressCondition` labels relative to predictors.
 * Retrain models with same CV strategy.
 * Perform **Permutation Test (1000 iterations)** to calculate p-value comparing real R² vs shuffled R².
 * Output: `results/shuffle_control.json` (p-value). Raise error if p >= 0.05. (FR‑005, Control for Stress-Label Leakage).
- [ ] T022 [US2] Implement `code/modeling/feature_importance.py` to extract and rank the top proteins by absolute importance score for each model (FR‑006).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Visualization and Reproducibility Reporting (Priority: P3)

**Goal**: Generate publication‑ready figures (scatter, confusion matrix, feature importance) and runtime metrics report.

**Independent Test**: The reporting module can be tested by providing it with a dummy model object and a sample prediction array, verifying that it generates PNG files for all required plot types and a text summary of execution time and memory usage.

**Dependency**: This phase runs AFTER Phase 4 (US2) completes.

### Implementation for User Story 3

- [ ] T026 [US3] Implement `code/reporting/plots.py` to generate scatter plots (Predicted vs Actual with regression line & R² annotation), cross‑stress heatmaps, and feature‑importance bar charts (FR‑007).
- [ ] T027 [US3] Implement `code/reporting/metrics.py` to log total CPU time and peak memory usage to `results/runtime_metrics.json` (FR‑008).
- [ ] T028 [US3] Integrate plotting and metrics into a final `code/reporting/generate_report.py` script that produces the summary JSON and PNGs.
- [ ] T029 [US3] Add a sanity‑check in `metrics.py` that verifies input data is not a mock object (e.g., non‑zero variance, required attributes) before writing runtime metrics.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T030 [P] Code Quality & Documentation: 1. Update `README.md` with installation steps and usage examples. 2. Add docstrings to all public functions in `code/`. 3. Extract common I/O logic into `code/utils/io.py`. 4. Remove unused imports and variables.
- [ ] T033 [P] Additional unit tests in `tests/unit/` covering edge cases (all‑missing columns, mismatched IDs).
- [ ] T034 Run `quickstart.md` validation to ensure full pipeline reproducibility.