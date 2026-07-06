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

- [ ] T001 Create project structure by executing: `mkdir -p code/data_ingestion code/modeling code/reporting code/utils tests data/raw data/processed results logs docs`
- [ ] T002 Create `code/requirements.txt` containing pinned versions for: pandas==2.0.3, scikit-learn==1.3.0, matplotlib==3.7.2, seaborn==0.12.2, mygene==3.2.2, impyute==0.2.3, wget==3.2
- [ ] T003 [P] Configure linting (flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Setup `code/utils/config.py` for random seeds, paths, and species/stress constants
- [ ] T005 [P] Implement data schema validation using Pydantic or simple dict checks for `data/raw/` and `data/processed/`
- [ ] T006 [P] Setup logging infrastructure to capture warnings (e.g., dropped rows, missing data) to `logs/pipeline.log`
- [ ] T007 Create base data loading utilities in `code/utils/data_utils.py` (CSV/Parquet I/O)
- [ ] T008 Implement checksum verification utility in `code/utils/checksums.py` for SHA-256 validation of raw downloads

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Automatically download, normalize, merge, and impute public proteomic and transcriptomic datasets for Arabidopsis, rice, and wheat under drought, salinity, and heat.

**Independent Test**: The pipeline can be fully tested by running the data ingestion script against a known subset of GEO/ProteomeXchange IDs and verifying that the output is a single, normalized CSV matrix containing protein abundances and matched gene expression values with no missing rows for the specified species/stress.

### Implementation for User Story 1

- [ ] T011 [P] [US1] Implement `code/data_ingestion/download.py` to fetch raw data from NCBI GEO/ProteomeXchange using `wget`/`curl` based on FR-001 (largest n, earliest date tie‑breaker)
- [ ] T012 [P] [US1] Implement `code/data_ingestion/normalize.py` to filter low‑abundance proteins (<50% detection) and apply **MinProb** imputation using a **strict 4-step Detection‑Limit (DL) hierarchy**:  
  1. **Reported**: If the dataset provides a reported DL, use it.  
  2. **Percentile**: If ≥5 non‑missing values exist, estimate DL as the 5th percentile of observed values.  
  3. **Small Sample**: If <5 non‑missing values exist, use the global minimum non‑zero value across the entire dataset as the DL.  
  4. **All Missing**: If a column has 0 non‑missing values, **drop the column** and log its identifier (do not attempt imputation).  
  (FR-002)
- [ ] T013 [US1] Implement `code/data_ingestion/merge.py` to map UniProt → Ensembl IDs using **mygene (Python) as the PRIMARY method** with **biomaRt (R) as a fallback** (FR-003). Log unmatched rows and drop them.
- [ ] T014 [US1] Implement `code/data_ingestion/pipeline.py` to orchestrate download → normalize → merge, handling metadata ambiguity (exclude or flag ambiguous records) (FR-001‑FR‑003)
- [ ] T015 [US1] Add validation in `code/data_ingestion/download.py` that raises `ValueError` if downloaded file size < 1 KB or URL domain is not in `[ncbi.nlm.nih.gov, proteomexchange.org]` (FR-001)
- [ ] T016 [US1] Add logging for exclusion reasons in `pipeline.py` (e.g., ambiguous stress label, missing transcriptomic match)

### Phase 3.5: Testing for User Story 1 (Run AFTER T011‑T014)

**Purpose**: Verify implementation tasks before proceeding to modeling

- [ ] T009 [US1] Unit test for **MinProb** imputation logic in `tests/unit/test_ingestion.py` (synthetic censored data, verifies correct DL hierarchy handling)
- [ ] T010 [US1] Unit test for identifier‑mapping fallback logic in `tests/unit/test_ingestion.py` (ensures mygene is attempted first, biomaRt used only if success‑rate < 80 %)
- [ ] T018 [US1] Implement `code/data_ingestion/completeness.py` to calculate `Data Completeness %` = (Retained Datasets / Initial Query Results) × 100 and write to `results/data_completeness.json` (SC‑004)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Baseline Model Training and Cross‑Stress Validation (Priority: P2)

**Goal**: Train Random Forest and SVR models using 5‑fold CV (if n ≥ 10) or LOOCV (if n < 10), include Stress‑Blind baseline, Null model, and Target‑Permutation control test.

**Independent Test**: The modeling module can be tested independently by feeding it a static, pre-saved CSV of the preprocessed data and verifying that it outputs a JSON report containing R² scores, RMSE values, and feature‑importance rankings for both within-stress and cross-stress validation splits.

### Prerequisite Documentation

- [ ] T023a [P] Create `docs/deviation_log.md` documenting the decision to use LOOCV when sample size < 10 (references Constitution VI) **before** any training code is written.

### Checkpointing for Runtime Limits

- [ ] T032 [P] Implement checkpointing inside the training loop (save intermediate model state and partial results after each CV fold) to allow graceful termination if total runtime approaches the 6‑hour GitHub Actions limit (Risk Mitigation). **MUST be implemented before T019.**

### Implementation for User Story 2

- [ ] T019 [US2] Implement `code/modeling/train.py` to train `RandomForestRegressor` and `SVR`. Logic:  
  * Detect sample size per stress condition.  
  * If n ≥ 10 → perform 5‑fold CV; else → perform LOOCV.  
  * All preprocessing (normalization, imputation, feature selection) must occur **inside** each CV fold (SC‑005).  
  * Hyperparameters: `n_estimators=100`, `max_depth=10` (RF); `kernel='rbf'`, `C=1.0` (SVR).  
  (FR‑004)
- [ ] T020a [US2] Train **Raw Feature Baseline** models (RF & SVR) on the original (non‑residualized) protein matrix using the same CV strategy as T019. Store R² and RMSE for later comparison. (Addresses SC‑002)
- [ ] T020b [US2] Implement **Stress‑Blind Baseline**: regress out `StressCondition` effects from protein features, then train RF & SVR on the residualized features (same CV). (Addresses SC‑002)
- [ ] T020c [US2] Implement calculation of the **'drop in R²'** metric by comparing the R² of T020b (Stress-Blind) against T020a (Raw Feature Baseline) and record the result in `results/r2_drop.json`. (SC‑002)
- [ ] T021a [US2] Implement `code/modeling/evaluate.py` to perform Null Model comparison (predict mean) and calculate improvement in R² over RF/SVR (SC‑001).
- [ ] T021b [US2] Implement **Target‑Permutation Control Test**: **shuffle the target gene expression values** (not stress labels) relative to the predictors, retrain the models with the same CV strategy, and verify that the real‑data R² is significantly higher than the shuffled‑data R² (p < 0.05). Raise an error if the condition is not met. (FR‑005)
- [ ] T022 [US2] Implement `code/modeling/feature_importance.py` to extract and rank the top 20 proteins by absolute importance score for each model (FR‑006).
- [ ] T023 [US2] Refactor `code/modeling/train.py` to ensure all preprocessing steps are called from `code/data_ingestion/normalize.py` and `merge.py` within each CV fold (SC‑005).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Visualization and Reproducibility Reporting (Priority: P3)

**Goal**: Generate publication‑ready figures (scatter, confusion matrix, feature importance) and runtime metrics report.

**Independent Test**: The reporting module can be tested by providing it with a dummy model object and a sample prediction array, verifying that it generates PNG files for all required plot types and a text summary of execution time and memory usage.

**Dependency**: This phase runs AFTER Phase 4 (US2) completes.

### Implementation for User Story 3

- [ ] T026 [US3] Implement `code/reporting/plots.py` to generate scatter plots (Predicted vs Actual with regression line & R² annotation), cross‑stress heatmaps, and feature‑importance bar charts (FR‑007)
- [ ] T027 [US3] Implement `code/reporting/metrics.py` to log total CPU time and peak memory usage to `results/runtime_metrics.json` (FR‑008)
- [ ] T028 [US3] Integrate plotting and metrics into a final `code/reporting/generate_report.py` script that produces the summary JSON and PNGs
- [ ] T029 [US3] Add a sanity‑check in `metrics.py` that verifies input data is not a mock object (e.g., non‑zero variance, required attributes) before writing runtime metrics

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T030a [P] Update `README.md` with installation steps and usage examples
- [ ] T030b [P] Add docstrings to all public functions in `code/`
- [ ] T031a [P] Extract common I/O logic into `code/utils/io.py`
- [ ] T031b [P] Remove unused imports and variables from all scripts
- [ ] T033 [P] Additional unit tests in `tests/unit/` covering edge cases (all‑missing columns, mismatched IDs)
- [ ] T034 Run `quickstart.md` validation to ensure full pipeline reproducibility