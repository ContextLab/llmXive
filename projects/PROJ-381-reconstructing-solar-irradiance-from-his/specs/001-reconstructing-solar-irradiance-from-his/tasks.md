# Tasks: Reconstructing Solar Irradiance from Historical Sunspot Records

**Input**: Design documents from `/specs/001-reconstructing-solar-irradiance/`  
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

- [X] T001a [P] Create project directory structure: `code/`, `tests/`, `data/raw/`, `data/processed/`, `code/models/`, `code/analysis/`
- [X] T001b [P] Create `__init__.py` files in all `code/` subdirectories and `tests/`
- [X] T001c [P] Create `.gitkeep` files in `data/raw/` and `data/processed/` to ensure directories are tracked
- [X] T002 Initialize Python 3.11 project with `requirements.txt` (pin `pandas`, `scikit-learn`, `numpy`, `scipy`, `requests`, `pyyaml`)
- [X] T003 [P] Configure linting (`ruff`) and formatting (`black`) tools by creating `pyproject.toml` with specific configuration rules for `ruff` and `black`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `code/config.py` with paths, random seeds, and constants (FR-002 gap logic, FR-009 thresholds)
- [X] T005 [P] Create `contracts/dataset_schema.schema.yaml` defining `SunspotRecord` and `TSIRecord` entities  <!-- prerequisite for ingestion -->
- [X] T006 [P] Create `contracts/output_schema.schema.yaml` defining reconstruction and validation report schemas  <!-- prerequisite for ingestion -->
- [X] T007 Implement `code/data/__init__.py` and base logging infrastructure
- [X] T008 [P] Configure environment variable management for data paths
- **Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Cycle-Specific TSI Reconstruction Model (Priority: P1) 🎯 MVP

**Goal**: Ingest GSN and TSI data, train non-linear models with Cycle ID features, and validate via Leave-One-Cycle-Out.

### Tests for User Story 1 (OPTIONAL)

- [X] T010 [P] [US1] Write unit test for data ingestion in `tests/test_ingestion.py::test_silso_url_reachable` (verify SILSO/SORCE URL reachability)
- [X] T011 [P] [US1] Write unit test for gap filling logic in `tests/test_preprocessing.py::test_gap_filling_tsi_proxy` (verify ≥1yr gaps use TSI proxy 1360.5 W/m², NOT GSN=0)
- [X] T012 [P] [US1] Write integration test for LOCO CV in `tests/test_model_training.py::test_loco_cv_logic` (verify cycle holdout logic)

### Implementation for User Story 1

- [X] T013a [US1] Implement `code/data/ingestion.py` to fetch GSN (SILSO) and TSI (SORCE/TIM) from verified URLs to `data/raw/`
- [X] T013b [US1] Implement `code/data/ingestion.py` (continued) to fetch 2007 Baseline and CMIP6 v3.2 data to `data/raw/`
- [X] T014a [US1] Implement `code/data/preprocessing.py` (Part 1): Linear interpolation for gaps < 1 year in GSN data.
- [X] T014b [US1] Implement `code/data/preprocessing.py` (Part 2): Apply **TSI proxy value 1360.5 W/m²** for gaps ≥ 1 year (per FR‑002). Detect cycle boundaries using SILSO method.
- [X] T014c‑ingest [US1] Ingest both satellite‑era (2003‑present) and pre‑satellite (1610‑2002) GSN data, write raw copies to `data/raw/gsn_satellite.csv` and `data/raw/gsn_presatellite.csv`.
- [X] T014c‑preprocess [US1] Apply gap‑filling, cycle detection, and feature engineering; output `data/processed/preprocessed_data.parquet` (atomic write).
- [X] T015 [US1] Implement `code/models/train.py`:
  - Use **Cycle ID** (categorical integer from official SILSO list) as a feature (fulfills FR‑003).
  - Train Random Forest (max_depth=10, n_estimators=100) and Gaussian Process (RBF kernel).
  - Execute **Leave‑One‑Cycle‑Out (LOCO)** cross‑validation across all available satellite cycles.
  - Compute per‑cycle RMSE and R²; store in `data/processed/cv_report.json`.
  - Save model artifacts to `code/models/artifacts/` (e.g., `rf_cycleid.joblib`, `gp_cycleid.joblib`).
- [X] T016 [US1] Implement `code/models/predict.py` (basic inference for held‑out block validation) and generate validation report `data/processed/validation_report.json`.

### Phase 3.5: Fallback Model & Sensitivity Analysis (Critical for FR‑003, FR‑004, FR‑009)

- [X] T019 [US1] Implement `code/models/train_fallback.py` (Part 1):
  - Train a **Cycle‑Agnostic** model (GSN‑only) on the full satellite‑era dataset.
  - Save artifact to `code/models/artifacts/fallback_model.joblib`.
- [X] T018 [US1] Implement `code/models/train_fallback.py` (Part 2):
  - Load fallback model from T019.
  - For each satellite‑era cycle, compute **mean residual** (Observed TSI − Fallback‑Prediction) → per‑cycle baseline offset.
  - Store offsets in `data/processed/cycle_specific_offsets.json`.
- [X] T029 [US1] Implement `code/analysis/sensitivity.py`:
  - Load per‑cycle offsets (T018) and baseline model.
  - For each **inconsistency tolerance threshold** ∈ {0.01, 0.05, 0.1}:
    * Filter out cycles whose absolute offset exceeds the threshold.
    * Retrain the Cycle‑Specific model on remaining cycles.
    * Re‑evaluate via LOCO CV; record RMSE variance across thresholds.
  - Output `data/processed/sensitivity_report.json` containing threshold, filtered‑cycle count, RMSE variance, and recommendation.
- [X] T031 [US1] Write performance test `tests/test_performance.py::test_ram_limit` asserting peak RAM < 7 GB and total runtime < 6 h.

**Checkpoint**: All US1 components (model, fallback, offsets, sensitivity) are complete; Phase 3.5 no longer blocks US2 execution.

---

## Phase 4: User Story 2 - Pre‑Satellite TSI Reconstruction Generation (Priority: P2)

### Tests for User Story 2 (OPTIONAL)

- [X] T040 [P] [US2] Write unit test for Cycle‑Agnostic fallback logic in `tests/test_preprocessing.py::test_fallback_logic`.
- [X] T041 [P] [US2] Write unit test for bootstrap resampling in `tests/test_stats.py::test_bootstrap_1000` (verify 1000 iterations).
- [X] T042 [P] [US2] Write integration test for US2 output in `tests/test_model_prediction.py::test_reconstruction_file_generation` (verify `reconstruction_1610_2002.parquet` generation and schema compliance).

### Implementation for User Story 2

- [X] T020 [US2] Extend `code/models/predict.py`:
  - Load pre‑satellite GSN from `data/processed/preprocessed_data.parquet`.
  - For cycles present in training, apply the Cycle‑Specific model (from T015).
  - For unseen cycles, apply the Cycle‑Agnostic fallback model (from T019).
  - Generate **prediction intervals**:
    * For GP: use posterior variance to construct a 95 % credible interval.
 * For RF: use quantile regression ([deferred] / [deferred]) via `sklearn.ensemble.RandomForestRegressor` with `predict_quantile`.
  - Output `data/processed/reconstruction_1610_2002.parquet` containing columns: `date`, `tsi_pred`, `tsi_lower_95`, `tsi_upper_95`.
- [X] T021 [US2] Implement `code/analysis/stats.py`:
  - Perform bootstrap resampling (≥ 1000 iterations) of the reconstructed TSI for the Maunder, Dalton, and Modern minima periods.
  - Compute variance metrics and 95 % confidence intervals for each minimum.
  - Save results to `data/processed/variance_analysis.json`.

**Checkpoint**: US2 reconstruction and variance analysis are complete.

---

## Phase 5: User Story 3 - Baseline Comparison and Methodological Validation (Priority: P3)

### Tests for User Story 3 (OPTIONAL)

- [X] T024 [P] [US3] Write unit test for error reduction calculation in `tests/test_comparison.py::test_error_reduction`.
- [X] T025 [P] [US3] Write unit test for FDR correction logic in `tests/test_stats.py::test_fdr_correction`.
- [X] T043 [P] [US3] Write integration test for final report generation in `tests/test_comparison.py::test_final_report_generation` (verify `final_report.md` includes associational framing).

### Implementation for User Story 3

- [X] T026 [US3] Implement `code/analysis/comparison.py`:
  - Load new reconstruction (`reconstruction_1610_2002.parquet`), 2007 baseline, and CMIP6 v3.2 data.
  - Restrict to overlapping satellite era (e.g., 2003‑present) and compute RMSE for each dataset.
  - Calculate **percentage error reduction** relative to the 2007 baseline (fulfills SC‑001).
  - Apply **multiple‑comparison correction** (choose FDR via Benjamini‑Yekutieli) for any hypothesis tests across cycles/minima.
  - Ensure all narrative sections explicitly state findings are **associational** (FR‑006).
  - Generate `data/processed/final_report.md` containing error‑reduction metric, variance comparison results, correction method, and associational disclaimer.

**Checkpoint**: All US3 validation and reporting tasks are complete.

---

## Phase N: Polish & Cross‑Cutting Concerns

- [X] T032a [P] Update `README.md` installation section with environment setup instructions (Python 3.11, virtualenv, `pip install -r requirements.txt`).
- [X] T032b [P] Update `README.md` usage section with pipeline execution commands (e.g., `python -m code.main run_all`).
- [X] T032c [P] Create `docs/data_dictionary.md` documenting input/output schemas based on `contracts/` definitions.
- [X] T033 [P] Refactor code to:
  * Reduce cyclomatic complexity of each module to < 10.
  * Remove all unused imports.
  * Add type hints for all public functions.
- [X] T034 [P] Run `quickstart.md` validation script to ensure full pipeline reproducibility; record success flag in `state/quickstart_status.yaml`.
- [X] T035 [P] Verify that every citation in `research.md` matches a dataset URL in `code/data/ingestion.py`; update any mismatches and log in `state/citation_audit.yaml`.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)** → **Foundational (Phase 2)** → **User Story 1 (Phase 3)** → **Phase 3.5 (Fallback & Sensitivity)** → **User Story 2 (Phase 4)** → **User Story 3 (Phase 5)** → **Polish (Phase N)**

### User Story Dependencies

- **US1** requires Phase 2 completion.
- **US2** requires:
  * US1 model artifacts (`T015`),
  * Cycle‑Agnostic fallback model (`T019`).
  * Does **not** require outputs of T018 or T029 (they are analysis‑only).
- **US3** requires US2 reconstruction output (`T020`) and variance analysis (`T021`).
- **Phase 3.5** (fallback offsets & sensitivity) is a **blocking prerequisite** for the *validation* stage of US3 but not for the generation stage of US2.

### Parallel Opportunities

- All `[P]` tasks within a phase may run concurrently provided their explicit prerequisites are satisfied.
- Tests marked `[P]` can be executed in parallel after their corresponding implementation tasks are completed.

---

## Notes

- All code runs on CPU‑only environment; no CUDA or GPU libraries are imported.
- Real datasets are fetched from verified SILSO and SORCE URLs; loaders raise exceptions on failure (no synthetic fallback).
- Uncertainty bands are derived from model‑based prediction intervals (GP variance or RF quantiles), not arbitrary values.
- Sensitivity analysis (T029) explicitly filters cycles based on the **inconsistency tolerance threshold** applied to per‑cycle calibration offsets, preserving FR‑009 semantics.
- Cycle‑Specific Calibration (Constitution Principle VI) is enforced by using **Cycle ID** as a categorical feature in T015, overriding the plan’s earlier suggestion to use Cycle Phase; this decision is documented in T015.
- Gap handling follows FR‑002: linear interpolation for gaps < 1 yr; for gaps ≥ 1 yr, the TSI proxy value **1360.5 W/m²** is used (not GSN = 0).
- All tasks now have concrete, verifiable implementations; no ambiguity remains.
