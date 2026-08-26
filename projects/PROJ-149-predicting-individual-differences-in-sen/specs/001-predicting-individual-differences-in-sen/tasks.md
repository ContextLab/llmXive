# Tasks: Predicting Individual Differences in Sensory Processing Speed from Resting‑State EEG Power Spectra

**Input**: Design documents from `/specs/001-predict-sensory-speed-from-eeg/`
**Prerequisites**: `plan.md` (required), `spec.md` (required for user stories)

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

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

- [X] T004a [P] Create `code/config.py` with paths, band definitions, ICA params, chunk sizes, `EPSILON=1e-9`, `OVERLAP=0.5`, `WINDOW_SIZE=4`. **Note**: Configuration MUST default to Spec FR-003 requirement (4-second windows). The Spec's explicit acceptance criteria (US1) overrides any generic constitution defaults.
- [X] T004b [P] Add configuration validation logic to `code/config.py`. Must run after T004a.
- [X] T005 [P] Implement `code/utils/eeg_helpers.py` with band‑pass (1–40 Hz), notch (50/60 Hz), and variance‑rejection utilities. **Depends on** T004a & T004b.
- [X] T006 [P] Implement `code/utils/stats_helpers.py` with Bonferroni correction, permutation utilities, and MDES calculations. **Depends on** T004a & T004b.
- [X] T007a [P] Create `code/01_download_data.py` to fetch the PhysioNet EEG Motor Movement/Imagery dataset and verify checksums (FR‑001). Generates `data/interim/data_source_manifest.json`. **Dependencies**: T001a, T001b, T003.
- [X] T007b [P] Create `code/01_download_rt_data.py` to fetch the associated behavioral/reaction-time dataset (e.g., from a verified mirror or package) and verify checksums. Generates `data/interim/rt_data_manifest.json`. **Dependencies**: T001a, T001b, T003.
- [X] T008a [P] [Plan-Phase-0.5] [FR-001] Create `code/00_feasibility_check_join.py` to join EEG and RT datasets on `participant_id`.
 - **Inputs**: `data/interim/data_source_manifest.json` (from T007a) AND `data/interim/rt_data_manifest.json` (from T007b).
 - **Outputs**:
 - `data/interim/joined_metadata.csv` (successful joins)
 - `data/interim/feasibility_exclusion_log.csv` (columns: `participant_id` (str), `reason` (enum: missing_rt, short_epoch, channels_rejected_ratio), `channels_rejected_ratio` (float))
 - **Logic**: Exclude participants if epoch duration < 5 minutes (`short_epoch`) or if `channels_rejected_ratio` > 0.30.
 - **Dependencies**: T007a, T007b.
- [X] T008b [P] [Plan-Phase-0.5] [FR-001] Create `code/00_feasibility_report.py` to generate the feasibility report.
 - **Inputs**: `data/interim/feasibility_exclusion_log.csv` (from T008a).
 - **Logic**: If no participants remain after joining or if task mismatch is detected, write `data/processed/feasibility_report.md` with JSON schema `{ "status": "failed", "reason": "<string>", "matched_count": int, "task_mismatch": bool }` and **exit with code 1** (hard HALT).
 - **Dependencies**: T008a.

**Checkpoint**: Foundational ready – user story implementation can now begin.

---

## Phase 3: User Story 1 - Compute Band‑Power Features and Behavioral Metrics (Priority: P1)

**Goal**: Ingest raw EEG and behavioral data, preprocess, extract PSD features, and compute median RTs.

- [X] T010 [US1] [FR-002] Implement `code/02_preprocess_eeg.py`:
 - Apply a low-frequency band‑pass filter and a 50/60 Hz notch filter.
 - Reject channels with variance > 3 SD from the session mean.
 - Apply ICA (retain high variance) to remove ocular/muscle artifacts.
 - Exclude participants if `rejected_channels / total_channels > 0.30`.
 - **Outputs**: `data/interim/preprocessed_eeg/` (`.fif`), `data/interim/ica_cleaned_eeg/` (`.fif`), and `data/interim/exclusion_log.csv` (columns: `participant_id` (str), `reason` (enum: high_variance, ica_failure, short_epoch), `channels_rejected_ratio` (float)).
 - **Dependencies**: T007a, T008a, T005, T006.

- [X] T013 [US1] Implement `code/03_behavioral_parsing.py`:
 - Parse RT logs, exclude outliers (`RT < 100 ms` or `RT > 2000 ms`).
 - Retain participants with ≥ 70 % trials remaining.
 - **Outputs**: `data/interim/behavioral_metrics.csv` (`participant_id`, `median_rt`, `n_trials`, `n_trials_excluded`) and `data/interim/behavioral_exclusion_log.csv` (`participant_id`, `reason`).
 - **Dependencies**: T007b, T008a.

- [X] T012a [US1] [FR-003] Implement `code/04_extract_psd.py`:
 - Compute Welch's PSD on **continuous 5-minute epochs** using **4-second windows** (Spec FR-003 mandates 4s, overriding Plan's generic '2s' reference).
 - **Windowing**: Use `config.WINDOW_SIZE` (4s) and `config.OVERLAP` (0.5, default [deferred] overlap) as defined in `code/config.py`.
 - **Output**: `data/interim/psd_spectra.npy` (shape: [n_participants, n_channels, n_frequencies]).
 - **Dependencies**: T010, T013, T007a, T008a.

- [X] T012b [US1] [FR-003] Implement `code/04b_aggregate_bands.py`:
 - Aggregate power into canonical bands (delta, theta, alpha, low-beta, high-beta, gamma) from `data/interim/psd_spectra.npy`.
 - **Output**: `data/interim/band_powers.csv` (columns: `participant_id`, `channel_id`, `delta`, `theta`, `alpha`, `low_beta`, `high_beta`, `gamma`).
 - **Dependencies**: T012a.

- [X] T012c [US1] [FR-010] Implement `code/04c_relative_power.py`:
 - Calculate **relative power** (band / total 1‑40 Hz power) for each band and channel.
 - **Join Logic**: Explicitly joins `data/interim/band_powers.csv` (from T012b) with `data/interim/behavioral_metrics.csv` (from T013) on `participant_id` before aggregation.
 - Aggregate across channels (global mean) per participant.
 - **Output**: `data/processed/features.csv` (columns: `participant_id`, `median_rt`, `delta_rel`, `theta_rel`, `alpha_rel`, `low_beta_rel`, `high_beta_rel`, `gamma_rel`).
 - **Dependencies**: T012b, T013.

- [X] T035a [US1] Validate schema of `data/processed/features.csv` (no nulls, correct columns, RT range 100‑2000 ms). Run `pytest tests/contract/test_feature_schema.py`. Create contract file if missing (`contracts/feature_schema.schema.yaml`). **Depends on** T012c. **Tag**: `[P]` (reads pre-CLR file, independent of T012d write).

**Checkpoint**: User Story 1 functional and testable.

---

## Phase 4: User Story 2 - Fit Predictive Models and Test Associations (Priority: P2)

**Goal**: Fit Linear/LASSO models, perform correlations, permutation tests, and non‑linear checks.

- [X] T017 [US2] [FR-005] Implement `code/05_modeling.py`:
 - Load `features.csv` (from T012c).
 - Perform an 80/20 train/test split **before** 5‑fold CV on the training set.
 - Fit Multiple Linear Regression and LASSO (lambda tuned to minimize RMSE).
 - **Crucial**: Store split indices to ensure permutation tests (T022) can access the data. **Note**: Permutation tests (T022) must shuffle labels across the **held-out test set** (using these indices) to generate a valid null distribution for the model's R², as required by FR-007.
 - **Outputs**: `data/interim/split_indices.json`, `data/processed/model_results.json` (keys: `adjusted_r2`, `optimal_lambda`, `rmse`, `test_r2`, `test_rmse`).
 - **Dependencies**: T012c, T013, T007a, T008a.

- [X] T020 [P] Implement Pearson correlation script `code/06_correlations.py` (FR‑006).
 - Reads `features.csv`, computes correlation between each band's relative power and median RT.
 - **Output**: `data/interim/correlations_raw.csv` (`band`, `r_value`, `p_value`, `n`).
 - **Dependencies**: T012c.

- [X] T021 [US2] [FR-006] Apply Bonferroni correction for 6 bands (α = 0.0083). Flag significant results and write `data/processed/correlations_corrected.csv`.
 - **Dependencies**: T020.

- [X] T022 [US2] [FR-007] Implement permutation test `code/07_permutation_test.py`:
 - **Read** observed `test_r2` from `data/processed/model_results.json` (key `test_r2`) and `split_indices.json` from T017.
 - **Shuffle** `median_rt` labels **ONLY on the held-out test set** (using indices from `split_indices.json`) to establish a valid null distribution for the model's R², as required by FR-007 and Constitution VII.
 - **Retrain**: For each shuffle, load the training data, retrain the model (using `sklearn.linear_model` with `warm_start` if applicable) on the training set, predict on the **shuffled test set**, and compute R².
 - **Optimization**: Use `warm_start=True` for LASSO and vectorized R² calculation where possible to ensure shuffles complete within the 6-hour runtime limit (SC-005).
 - **Store** null R² values in `data/interim/permutation_null_distribution.npy`.
 - **Compute** p-value by comparing observed R² against the null distribution.
 - **Write** results (observed R², p-value, null distribution path) to a **new** file `data/processed/permutation_results.json` to avoid atomicity conflicts with `model_results.json`.
 - **Dependencies**: T017.

- [ ] T023 [US2] [FR-011] Perform post‑hoc power analysis using `statsmodels`. Explicitly calculate `required_n`, `power`, and `effect_size` for the target R²=0.10 with power ≥ 0.80. Append `post_hoc_power_analysis` to `data/processed/model_results.json` alongside SC-001 metrics.
 - **Dependencies**: T017.

- [X] T024a [US2] [FR-012] Implement `code/08a_prepare_polynomial_features.py`:
 - Load `features.csv` and add polynomial terms for alpha and beta (degree from `config.POLY_DEGREE`).
 - **Output**: `data/interim/poly_features.csv`.
 - **Dependencies**: T012c.

- [X] T024b [US2] [FR-012] Implement `code/08b_fit_nonlinear_model.py`:
 - Fit a linear model and a polynomial model on `poly_features.csv`.
 - **Output**: `data/interim/nonlinear_model_results.json` (coefficients, R² for both models).
 - **Dependencies**: T024a.

- [X] T024c [US2] [FR-012] Implement `code/08c_compare_models.py`:
 - Compare adjusted R² of linear vs. polynomial model via F‑test.
 - **Mandatory Logic**: Automatically evaluate the F-test p-value against the established significance threshold.
 - **Output**: Store results in `data/processed/non_linear_comparison.json` including a boolean field `significant_at_0p05` and a string `interpretation`.
 - **Dependencies**: T024b.

- [X] T025a [US3] [FR-008] Implement `code/09_robustness_preprocess.py`:
 - Re-run `code/02_preprocess_eeg.py` with `--no-ica` flag.
 - **Output**: `data/interim/robustness_no_ica_eeg/`.
 - **Dependencies**: T010 (script), T004a (config).

- [X] T025b [US3] [FR-008] Implement `code/09_robustness_features.py`:
 - Re-run `code/04_extract_psd.py`, `code/04b_aggregate_bands.py`, `code/04c_relative_power.py` with `--window-size 2` flag.
 - **Output**: `data/processed/robustness_features_2s.csv`.
 - **Dependencies**: T025a, T012a-c (scripts).

- [X] T025c [US3] [FR-008] Implement `code/09_robustness_modeling.py`:
 - Re-run `code/05_modeling.py` on `robustness_features_2s.csv`.
 - **Output**: `data/processed/robustness_model_results.json`.
 - **Dependencies**: T025b, T017 (script).

- [ ] T025d [US3] [FR-006/FR-008] Implement robustness correlation analysis: Re-run `code/06_correlations.py` on `robustness_features_2s.csv`.
 - **Output**: `data/processed/robustness_correlations_raw.csv`.
 - **Dependencies**: T025b, T020 (script).

- [ ] T025e [US3] [FR-009/FR-008] Implement robustness sensitivity analysis: Re-run `code/10_sensitivity_analysis.py` on `robustness_correlations_raw.csv`.
 - **Output**: `data/processed/robustness_sensitivity_report.csv`, `data/processed/robustness_sensitivity_plot.png`.
 - **Dependencies**: T025d, T026 (script).

- [X] T026 [US3] [FR-009] Implement sensitivity analysis `code/10_sensitivity_analysis.py`:
 - Reads `data/interim/correlations_raw.csv`.
 - Sweeps p-value threshold across a range of low to moderate significance levels.
 - **Records** the count of significant correlations at each step.
 - **Output**: `data/processed/sensitivity_report.csv` (columns: `threshold`, `significant_count`).
 - **Output**: `data/processed/sensitivity_plot.png`.
 - **Dependencies**: T020, T021.

- [ ] T035b [US2] Validate schemas of `model_results.json`, `correlations_corrected.csv`, `non_linear_comparison.json`, and `permutation_results.json` via contract tests.
 - **Dependencies**: T017, T021, T024c, T022.

**Checkpoint**: User Stories 1 & 2 functional.

---

## Phase 5: User Story 3 - Robustness Checks and Sensitivity Analysis (Priority: P3)

**Goal**: Re‑run analysis with alternative parameters and sweep significance thresholds.

- (Implemented within T025a-e and T026; no separate tasks required.)

---

## Phase 6: Reporting & Validation

**Purpose**: Aggregate results and verify success criteria.

- [X] T031a [US3] [SC-001 to SC-004] Implement `code/11a_load_results.py` to ingest all metrics (adjusted R², Bonferroni‑corrected p-values, robustness deltas, sensitivity thresholds, feasibility logs) into a unified dictionary.
 - **Dependencies**: T017, T021, T024c, T022, T023, T025c, T025d, T025e, T026, T008b.

- [X] T031b [US3] [SC-001 to SC-004] Implement `code/11b_format_tables.py` to generate Markdown tables from the ingested data.
 - **Dependencies**: T031a.

- [X] T031c [US3] [SC-001 to SC-004] Implement `code/11c_write_report.py` to assemble the final `data/processed/final_report.md`.
 - **Dependencies**: T031b, T023, T024c.

- [X] T032 [US3] [SC-005] Implement feasibility measurement script `code/12_feasibility_check.py`:
 - Estimate RAM usage (`psutil.virtual_memory().used`) and runtime (`participants * 0.05 s`).
 - **Hard Abort**: If estimated RAM > 7GB or estimated runtime > 6h, log the violation and **exit with code 1** to prevent wasted compute resources.
 - Log predictions to `data/processed/feasibility_metrics.log`.
 - **Dependencies**: T007, T010, T017.

- [ ] T033 [P] Run unit tests for `utils/` helpers (`pytest tests/unit/`).
 - **Dependencies**: T005, T006.

- [X] T034 [US3] Run integration test `tests/integration/test_pipeline.py` to ensure end‑to‑end execution works.
 - **Dependencies**: T010, T012a, T017, T020, T022, T025a, T026.

- [ ] T036a [US3] Run contract tests for `feature_schema` and `result_schema` (`pytest tests/contract/`).
 - **Dependencies**: T035a, T035b.

**Checkpoint**: All user stories completed; final report generated.

---

## General Notes

- All tasks are deterministic; random seeds are pinned in `code/config.py`.
- All data files are checksummed; hashes recorded in project state (outside this file).
- No GPU code is used; all libraries are CPU‑compatible.
- Tasks marked `[P]` may run in parallel provided their dependencies are satisfied.
- **FR-010 Precedence**: The Spec's FR-010 (Relative Power) is the binding requirement. The Plan's generic suggestion of CLR transformation is superseded by FR-010; T012c implements Relative Power as mandated.
- **Data Integrity**: All data loading tasks (T007a, T007b) MUST fail loudly if the real source is unavailable; no synthetic fallbacks are permitted.
- **Constitution VI vs Spec**: Window size is fixed at 4s per Spec FR-003 and US-1. The Plan's reference to '2s' windows is overridden by the Spec's explicit acceptance criteria.