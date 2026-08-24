# Tasks: Predicting Individual Differences in Sensory Processing Speed from Resting‑State EEG Power Spectra

**Input**: Design documents from `/specs/001-predict-sensory-speed-from-eeg/`  
**Prerequisites**: `plan.md` (required), `spec.md` (required for user stories)

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `- [ ] T### [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)  
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)  
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root  
- **Web app**: `backend/src/`, `frontend/src/`  
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`  

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001a Create project directory structure (`code/`, `tests/`, `data/raw/`, `data/interim/`, `data/processed/`, `code/utils/`).  
- [X] T001b Create `code/requirements.txt` with pinned versions (mne, scikit-learn, pandas, numpy, scipy, matplotlib, seaborn, pyyaml).  
- [X] T003 [P] Configure linting (flake8/black) and formatting tools.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

- [X] T004a [P] Create `code/config.py` with paths, band definitions, ICA params, chunk sizes, `EPSILON=1e-9`, `OVERLAP=0.5`, `WINDOW_SIZE=2`. **Tag**: `[Plan-Override-FR-003]` (updates window size to 2 s per Constitution).  
- [X] T004b [P] Add configuration validation logic to `code/config.py`. Must run after T004a.  
- [X] T005 [P] Implement `code/utils/eeg_helpers.py` with band‑pass (1–40 Hz), notch (50/60 Hz), and variance‑rejection utilities. **Depends on** T004a & T004b.  
- [X] T006 [P] Implement `code/utils/stats_helpers.py` with Bonferroni correction, permutation utilities, and MDES calculations. **Depends on** T004a & T004b.  
- [ ] T007 [P] Create `code/01_download_data.py` to fetch the PhysioNet EEG Motor Movement/Imagery dataset and verify checksums (FR‑001). Generates `data/interim/data_source_manifest.json`. **Dependencies**: T001a, T001b, T003.  
- [ ] T008a [P] [Plan-Phase-0.5] [FR-001] Create `code/00_feasibility_check_join.py` to join EEG and RT datasets on `participant_id`.  
  - **Inputs**: `data/interim/data_source_manifest.json` (from T007).  
  - **Outputs**:  
    - `data/interim/joined_metadata.csv` (successful joins)  
    - `data/interim/feasibility_exclusion_log.csv` (columns: `participant_id` (str), `reason` (enum: missing_rt, short_epoch, channels_rejected_ratio), `channels_rejected_ratio` (float))  
    - If join fails or task mismatch, generate `data/processed/feasibility_report.md` with JSON schema `{ "status": "failed", "reason": "<string>", "matched_count": int, "task_mismatch": bool }` and **exit with code 1** (hard HALT). **Depends on** T007.

**Checkpoint**: Foundational ready – user story implementation can now begin.

---

## Phase 3: User Story 1 - Compute Band‑Power Features and Behavioral Metrics (Priority: P1)

**Goal**: Ingest raw EEG and behavioral data, preprocess, extract PSD features, and compute median RTs.

- [ ] T010 [US1] [FR-002] Implement `code/02_preprocess_eeg.py`:  
  - Apply 1–40 Hz band‑pass and 50/60 Hz notch filters.  
  - Reject channels with variance > 3 SD from the session mean.  
  - Apply ICA (retain high variance) to remove ocular/muscle artifacts.
  - Exclude participants if `rejected_channels / total_channels > 0.30`.  
  - **Outputs**: `data/interim/preprocessed_eeg/` (`.fif`), `data/interim/ica_cleaned_eeg/` (`.fif`), and `data/interim/exclusion_log.csv` (columns: `participant_id` (str), `reason` (enum: high_variance, ica_failure, short_epoch), `channels_rejected_ratio` (float)).  
  - **Dependencies**: T007, T008a, T005, T006.  

- [ ] T013 [US1] Implement `code/03_behavioral_parsing.py`:  
  - Parse RT logs, exclude outliers (`RT < 100 ms` or `RT > 2000 ms`).  
  - Retain participants with ≥ 70 % trials remaining.  
  - **Outputs**: `data/interim/behavioral_metrics.csv` (`participant_id`, `median_rt`, `n_trials`, `n_trials_excluded`) and `data/interim/behavioral_exclusion_log.csv` (`participant_id`, `reason`).  
  - **Dependencies**: T007, T008a.  

- [ ] T012 [US1] [FR-003] [FR-010] Implement `code/04_extract_features.py`:  
  - Compute Welch’s PSD on continuous 5‑minute epochs using **2‑second windows** with `OVERLAP=0.5`.  
  - Aggregate power into canonical bands (delta, theta, alpha, low-beta, high-beta, gamma).  
  - Calculate **relative power** (band / total 1‑40 Hz power).  
  - **Output**: `data/processed/features.csv` (columns: `participant_id`, `median_rt`, `delta_rel`, `theta_rel`, `alpha_rel`, `low_beta_rel`, `high_beta_rel`, `gamma_rel`).  
  - **Dependencies**: T010, T013, T007, T008a.  

- [ ] T012b [US1] [FR-010-Extension] Implement mandatory CLR transformation `code/04b_clr_transform.py` to satisfy compositional data constraints.  
  - Reads `data/processed/features.csv` and writes `data/processed/features_clr.csv`.  
  - **Dependencies**: T012.  

- [ ] T035a [US1] Validate schema of `data/processed/features.csv` (no nulls, correct columns, RT range 100‑2000 ms). Run `pytest tests/contract/test_feature_schema.py`. Create contract file if missing (`contracts/feature_schema.schema.yaml`). **Depends on** T012.

**Checkpoint**: User Story 1 functional and testable.

---

## Phase 4: User Story 2 - Fit Predictive Models and Test Associations (Priority: P2)

**Goal**: Fit Linear/LASSO models, perform correlations, permutation tests, and non‑linear checks.

- [ ] T017 [US2] Implement `code/05_modeling.py`:  
  - Load `features_clr.csv` (from T012b).  
  - Perform an 80/20 train/test split **before** 5‑fold CV on the training set.  
  - Fit Multiple Linear Regression and LASSO (lambda tuned to minimize RMSE).  
  - **Outputs**: `data/interim/split_indices.json`, `data/processed/model_results.json` (keys: `adjusted_r2`, `optimal_lambda`, `rmse`, `test_r2`, `test_rmse`).  
  - **Tags**: `[FR-005]`.  
  - **Dependencies**: T012b, T013, T007, T008a.  

- [ ] T020 [P] Implement Pearson correlation script `code/06_correlations.py` (FR‑006).  
  - Reads `features_clr.csv`, computes correlation between each band’s relative power and median RT.  
  - **Output**: `data/interim/correlations_raw.csv` (`band`, `r_value`, `p_value`, `n`).  

- [ ] T021 [US2] Apply Bonferroni correction for 6 bands (α = 0.0083). Flag significant results and write `data/processed/correlations_corrected.csv`. **Tag**: `[FR-006]`.  

- [ ] T022a [US2] [FR-007] Implement permutation test `code/07_permutation_test.py`:  
  - Shuffle `median_rt` **only on the held‑out test set** (`config.PERMUTATION_SHUFFLES` defaults to 10 000).  
  - Compute R² for each shuffle, store in `data/interim/permutation_null_distribution.npy` (exactly 10 000 floats).  
  - **Dependencies**: T017.  

- [ ] T022b [US2] Compute p‑value by comparing observed test‑set R² (from T017) against the null distribution; update `model_results.json` with `permutation_p_value`.  

- [ ] T023 [US2] Perform post‑hoc power analysis (FR‑011) using `statsmodels`. Append `post_hoc_power_analysis` (fields: `required_n`, `power`, `effect_size`) to `model_results.json`.  

- [ ] T024 [US2] [FR-012] Implement non‑linear interaction analysis (`code/08_nonlinear_analysis.py`): add polynomial terms for alpha and beta (degree from `config.POLY_DEGREE`). Compare adjusted R² with linear model via F‑test; store results in `data/processed/non_linear_comparison.json`.  

- [ ] T025 [US3] Implement robustness pipeline `code/09_robustness.py`:  
  - Accept flags `--no-ica` and `--window-size {2,4}`.  
  - Re‑run preprocessing, feature extraction, and modeling accordingly.  
  - Produce `data/processed/robustness_report.csv` (columns: `condition`, `r2`, `rmse`, `delta_r2`).  
  - Generate sensitivity plot `data/processed/sensitivity_plot.png`.  
  - **Dependencies**: T017, T020, T024 (for model fitting under each condition).  

- [ ] T035b [US2] Validate schemas of `model_results.json`, `correlations_corrected.csv`, and `non_linear_comparison.json` via contract tests.  

**Checkpoint**: User Stories 1 & 2 functional.

---

## Phase 5: User Story 3 - Robustness Checks and Sensitivity Analysis (Priority: P3)

**Goal**: Re‑run analysis with alternative parameters and sweep significance thresholds.

- (Implemented within T025; no separate tasks required.)

---

## Phase 6: Reporting & Validation

**Purpose**: Aggregate results and verify success criteria.

- [ ] T031 [US3] Implement `code/10_generate_report.py` to compile all metrics (adjusted R², Bonferroni‑corrected p‑values, robustness deltas, sensitivity thresholds, feasibility logs) into `data/processed/final_report.md`.  

- [ ] T032 [US3] [SC-005] Implement feasibility measurement script `code/11_feasibility_check.py`:  
  - Estimate RAM usage (`psutil.virtual_memory().used`) and runtime (`participants * 0.05 s`).  
  - Log predictions to `data/processed/feasibility_metrics.log`. **No hard abort** – only records values.  

- [ ] T033 [P] Run unit tests for `utils/` helpers (`pytest tests/unit/`).  

- [ ] T034 [US3] Run integration test `tests/integration/test_pipeline.py` to ensure end‑to‑end execution works.  

- [ ] T036 [US3] Run contract tests for `feature_schema` and `result_schema` (`pytest tests/contract/`).  

**Checkpoint**: All user stories completed; final report generated.

---

## General Notes

- All tasks are deterministic; random seeds are pinned in `code/config.py`.  
- All data files are checksummed; hashes recorded in project state (outside this file).  
- No GPU code is used; all libraries are CPU‑compatible.  
- Tasks marked `[P]` may run in parallel provided their dependencies are satisfied.  
- CLR transformation (T012b) is now a mandatory step to ensure compositional data integrity.  