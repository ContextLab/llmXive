---
description: "Task list template for feature implementation"
---

# Tasks: Predicting Individual Differences in Sensory Processing Speed from Resting‑State EEG Power Spectra

**Input**: Design documents from `/specs/001-predict-sensory-speed-from-eeg/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

## Format: `[ID] [P?] [Story] Description`

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

- [ ] T001a Create project directory structure (`code/`, `tests/`, `data/raw/`, `data/interim/`, `data/processed/`, `code/utils/`).
- [ ] T001b Create `code/requirements.txt` with pinned versions (mne, scikit-learn, pandas, numpy, scipy, matplotlib, seaborn, pyyaml, physionet).
- [ ] T003 [P] Configure linting (flake8/black) and formatting tools.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

- [ ] T004a [P] Create `code/config.py` with paths, band definitions, ICA params, chunk sizes, `EPSILON=1e-9`, `OVERLAP=0.5`, `WINDOW_SIZE=4`. **Note**: `OVERLAP=0.5` is the DEFAULT for the primary analysis. The code MUST support `--overlap` override for robustness checks. If `--overlap` is not provided, the system defaults to 0.5. The `[deferred]` status in the spec is resolved by this default, but override capability is mandatory for robustness. The `WINDOW_SIZE` is FIXED at 4 for the **primary analysis** per Spec FR-003. The code MUST support `--window-size` override for robustness checks (T025) only.
- [X] T004b [P] Add configuration validation logic to `code/config.py`. Must run after T004a.
- [X] T005 [P] Implement `code/utils/eeg_helpers.py` with band‑pass (low-frequency cutoff), notch (50/60 Hz), and variance‑rejection utilities. **Depends on** T004a & T004b.
- [~] T006 [P] [FR-006] [FR-007] [FR-011] Implement `code/utils/stats_helpers.py` with Bonferroni correction, permutation utilities, and MDES calculations. **Depends on** T004a & T004b.
 - **Functions to implement**:
 1. `bonferroni_correction(p_values: list[float], alpha: float = 0.05) -> list[float]`: Returns adjusted p-values.
 2. `permutation_r2(X, y, model_class, n_splits, n_permutations, seed) -> float`: **Shuffles labels on the training set only**. For each permutation:
 a. Split data using stored indices.
 b. Shuffle `y_train` labels randomly.
 c. **Instantiate a FRESH model** (do not use `warm_start` or carry over weights) and train on shuffled `X_train`, `y_train`.
 d. Evaluate R² on the held-out test set.
 e. Store the R² value.
 f. Repeat `n_permutations` times.
 g. Returns the null distribution of R² values.
 **Note**: Re-training from scratch is mandatory to generate a valid null distribution. Using `warm_start` is forbidden as it biases the null distribution.
 3. `calculate_mdes(effect_size_r2: float, alpha: float = 0.05, power: float = 0.80) -> int`: Uses `statsmodels.stats.power.FTestPower.solve_power` to return required sample size N.
 - **Note**: This task represents the complete implementation of the file; subsequent tasks do not overwrite this file.
- [~] T007a [P] [FR-001] Create `code/01_download_eeg_data.py` to fetch the PhysioNet EEG Motor Movement/Imagery Dataset.
 - **URL**: `
 - **Checksums URL**: `
 - **Logic**: Use the `physionet` Python package or `requests` to download raw EDF files. Verify cryptographic checksums against `checksums.txt` fetched from the dataset root. **Do not use placeholder checksums**. The script MUST fetch the `checksums.txt` from the dataset root to verify file integrity. If checksum verification fails, exit with code 1.
 - **Output**: `data/raw/eegmmidb/` and `data/interim/data_source_manifest.json` (containing file paths, verified hashes, and column `subject_id` for joining).
 - **Dependencies**: T001a, T001b, T003.
- [~] T007b [P] [FR-001] Create `code/01_download_rt_data.py` to fetch the Simple Reaction Time dataset (Dataset ID: **ds000224**, Source: OpenNeuro).
 - **URL**: `https://openneuro.org/datasets/ds000224`
 - **Logic**: Download behavioral logs for simple RT tasks using `datalad install -d data/raw/rt_data ds000224` and target specific file paths `sub-*/ses-*/beh/sub-*_task-rt_events.tsv` and `sub-*/task-rt_events.tsv`. Verify integrity. **Verification Step**: The script MUST verify that the downloaded dataset contains 'simple RT' task logs and that `participant_id` formats are compatible with the EEG dataset. If the dataset content is mismatched or IDs cannot be joined, the script MUST exit with code 1 and log a `halt_signal.json` with reason `dataset_mismatch`. **Note**: This dataset is distinct from the EEG dataset; linking will occur in T008a.
 - **Output**: `data/raw/rt_data/` and `data/interim/rt_data_manifest.json` (containing file paths and column `participant_id` for joining).
 - **Dependencies**: T001a, T001b, T003.
- [~] T008a [P] [Plan-Phase-0.5] [FR-001] Create `code/00_feasibility_join.py` to join EEG and RT datasets on `subject_id` (from EEG manifest) and `participant_id` (from RT manifest).
 - **Inputs**: `data/interim/data_source_manifest.json` (from T007a, column `subject_id`) AND `data/interim/rt_data_manifest.json` (from T007b, column `participant_id`).
 - **Logic**:
 1. **Identify Segments**: For each participant, identify all continuous recording segments (epochs) from the raw EEG metadata.
 2. **Output**:
 - `data/interim/joined_metadata.csv` (successful joins, columns: `participant_id`, `eeg_file`, `rt_file`, `segment_id`, `segment_duration`)
 - `data/interim/feasibility_exclusion_log.csv` (columns: `participant_id` (str), `reason` (enum: missing_rt, missing_eeg), `segment_count` (int)).
 3. **Note**: This task ONLY joins and identifies segments. It does NOT filter based on duration or quality. That is handled by T008b.
 - **Dependencies**: T007a, T007b.
- [~] T008b [P] [Plan-Phase-0.5] [FR-001] Create `code/00_feasibility_filter_segments.py` to enforce the "continuous 5-minute epoch" constraint.
 - **Inputs**: `data/interim/joined_metadata.csv` (from T008a).
 - **Logic**:
 1. **Filter**: Retain ONLY participants who have at least ONE single continuous segment >= 5 minutes. **Do NOT sum segments**.
 2. **Exclusion**: Exclude participants where `max_continuous_duration < 5 minutes`.
 3. **Halt Condition**: If no participants remain after filtering, write `data/interim/halt_signal.json` with reason `no_continuous_segment` and **exit with code 1**.
 4. **Output**:
 - `data/interim/feasibility_filtered.csv` (final participant list)
 - `data/interim/feasibility_exclusion_log.csv` (appended: `participant_id`, `reason`='no_continuous_segment', `max_continuous_duration`).
 - **Dependencies**: T008a.

**Checkpoint**: Foundational ready – user story implementation can now begin.

---

## Phase 3: User Story 1 - Compute Band‑Power Features and Behavioral Metrics (Priority: P1)

**Goal**: Ingest raw EEG and behavioral data, preprocess, extract PSD features, and compute median RTs.

- [~] T008d [P] [Plan-Phase-0.5] [FR-001] Create `code/00_feasibility_check_channels.py` to perform the channel rejection check *after* preprocessing (T010) and filter the participant list.
 - **Inputs**: `data/interim/feasibility_filtered.csv` (from T008b) AND `data/interim/preprocessing_exclusion_log.csv` (from T010, containing `channels_rejected_ratio`).
 - **Logic**:
 1. **Read**: Load exclusion logs from T010 which contain `channels_rejected_ratio`.
 2. **Filter**: Exclude participants if `channels_rejected_ratio > 0.30`.
 3. **Halt Condition**: If no participants remain, write `data/interim/halt_signal.json` with reason `high_channel_rejection` and **exit with code 1**.
 4. **Output**:
 - `data/interim/final_participant_list.csv` (final list after all checks)
 - `data/interim/final_exclusion_log.csv` (appended: `participant_id`, `reason`='high_channel_rejection', `channels_rejected_ratio`).
 5. **Note**: This task is the 'Final Channel Rejection Gate'. T010 runs on the `feasibility_filtered` list (from T008b) and T008d filters the result. The 'Two-Stage Gate' design (T008b pre, T010 process, T008d post) is accepted to balance efficiency with data integrity.
 - **Dependencies**: T010, T008b.

- [ ] T010 [US1] [FR-002] Implement `code/02_preprocess_eeg.py`:
 - Apply a low-frequency band‑pass filter and a /60 Hz notch filter. Reject channels with variance (microvolts squared) > 3 SD from the session mean (per participant recording file). Apply ICA (retain high variance) to remove ocular/muscle artifacts.
 - **Logic**: **Calculate** rejection ratios for each participant. **Do NOT filter the participant list here**; output the exclusion logs for T008d to process.
 - **Outputs**: `data/interim/preprocessed_eeg/` (`.fif`), `data/interim/ica_cleaned_eeg/` (`.fif`), `data/interim/preprocessing_exclusion_log.csv` (columns: `participant_id` (str), `reason` (enum: high_variance, ica_failure, short_epoch), `channels_rejected_ratio` (float)), and `data/interim/channel_stats.csv` (preliminary stats for T008d).
 - **Note**: This task runs on the `feasibility_filtered` list (from T008b). T008d performs the final filter. The 'Two-Stage Gate' design (T008b pre, T010 process, T008d post) is accepted to balance efficiency with data integrity.
 - **Dependencies**: T007a, T008a, T008b.

- [~] T013 [US1] Implement `code/03_behavioral_parsing.py`:
 - Parse RT logs, exclude outliers (`RT < 100ms`, `RT > 2000ms`) **BEFORE** calculating the median. Retain participants with ≥ 70 % trials remaining.
 - **Outputs**: `data/interim/behavioral_metrics.csv` (`participant_id`, `median_rt`, `n_trials`, `n_trials_excluded`) and `data/interim/behavioral_exclusion_log.csv` (`participant_id`, `reason`).
 - **Dependencies**: T007b, T008a, T008b.

- [~] T012a [US1] [FR-003] Implement `code/04_extract_psd.py`:
 - Compute Welch's PSD on continuous epochs of sufficient duration using short windows.
 - **Windowing**: Use `config.WINDOW_SIZE` (a duration appropriate for the primary analysis). **Overlap**: Use `config.OVERLAP` (a substantial overlap ratio). The code MUST accept a `--overlap` flag.
 - **Truncation**: For recordings not exact multiples of 5 minutes, truncate to the nearest 5-minute mark (floor) BEFORE PSD calculation. Log the number of seconds truncated per participant in `data/interim/truncation_log.csv`.
 - **Parameters**: `fmin=1`, `fmax=40`, `n_fft=4*sfreq` (where `sfreq` is the sampling frequency), `n_overlap=0.5*n_fft`.
 - **CRITICAL CONSTRAINT**: This task implements the **PRIMARY** analysis. The output MUST be written to `data/interim/psd_spectra.npy` and MUST NOT be overwritten by any robustness runs (e.g., T025b). **Assertion**: The script MUST assert that `WINDOW_SIZE == 4` for the primary run to ensure compliance with Spec FR-003. **Note**: Spec FR-003 mandates 4s windows, overriding Constitution Principle VI's '2s' default for this specific project.
 - **Output**: `data/interim/psd_spectra.npy` (shape: [n_participants, n_channels, n_frequencies]).
 - **Dependencies**: T010, T013, T007a, T008a, T008b, T008d.

- [ ] T012b [US1] [FR-003] Implement `code/04b_aggregate_bands.py`:
 - Aggregate power into canonical bands (delta, theta, alpha, low-beta, high-beta, gamma) from `data/interim/psd_spectra.npy`.
 - **Output**: `data/interim/band_powers.csv` (columns: `participant_id`, `channel_id`, `delta`, `theta`, `alpha`, `low_beta`, `high_beta`, `gamma`).
 - **Dependencies**: T012a.

- [~] T012c [US1] [FR-010] [Gatekeeper] Implement `code/04c_relative_power.py`:
 - Calculate relative power (band / total power across the frequency range) for each band and channel.
 - **Gatekeeper Role**: This task is the final gatekeeper for the participant list. It MUST filter the data using `data/interim/final_participant_list.csv` (from T008d) before any aggregation or output.
 - Aggregate across channels (global mean) per participant.
 - **Output**: `data/processed/features.csv` (columns: `participant_id`, `median_rt`, `delta_rel`, `theta_rel`, `alpha_rel`, `low_beta_rel`, `high_beta_rel`, `gamma_rel`).
 - **Note on Plan vs Spec**: This task implements Relative Power as mandated by Spec FR-010. **DO NOT apply CLR transformation**. The Plan's Phase 1 CLR requirement is superseded by Spec FR-010. Traceability: Spec FR-010 takes precedence over Plan Phase 1 CLR requirement.
 - **Dependencies**: T012b, T013, T008a, T008b, T008d.

- [ ] T035a [US1] Validate schema of `data/processed/features.csv`.
 - **Logic**: Check that columns `[participant_id, median_rt, delta_rel, theta_rel, alpha_rel, low_beta_rel, high_beta_rel, gamma_rel]` exist. Verify `median_rt` is within a plausible response time range consistent with standard experimental paradigms and all values are non-null. Run `pytest tests/contract/test_feature_schema.py`. Create contract file `tests/contract/test_feature_schema.py` if missing.
 - **Dependencies**: T012c.
 - **Tag**: `[P]` (reads pre-CLR file, independent of other writes).

**Checkpoint**: User Story 1 functional and testable.

---

## Phase 4: User Story 2 - Fit Predictive Models and Test Associations (Priority: P2)

**Goal**: Fit Linear/LASSO models, perform correlations, permutation tests, and non‑linear checks.

- [~] T017 [US2] [FR-005] Implement `code/05_modeling.py`:
 - Load `features.csv` (from T012c).
 - Perform a train/test split before K-fold cross-validation on the training set.
 - **Crucial**: Store split indices to ensure permutation tests (T022) can access the data. **Mark this run as 'primary'** in the output file to ensure T022 consumes the correct indices.
 - **Outputs**: `data/processed/model_results.json` (keys: `adjusted_r2`, `optimal_lambda`, `rmse`, `test_r2`, `test_rmse`), `data/interim/split_indices_primary.json` (keys: `train_idx`, `test_idx`, `run_type: "primary"`).
 - **Dependencies**: T012c, T013, T007a, T008a, T008b, T008d.

- [~] T020 [US2] [FR-006] Implement Pearson correlation script `code/06_correlations.py` (FR‑006).
 - Reads `features.csv`, computes correlation between each band's relative power and median RT.
 - **Output**: `data/interim/correlations_raw.csv` (`band`, `r_value`, `p_value`, `n`).
 - **Dependencies**: T012c.

- [ ] T021 [US2] [FR-006] Apply Bonferroni correction for 6 bands (α = 0.0083). Flag significant results and write `data/processed/correlations_corrected.csv`.
 - **Logic**: Divide by 6. Compare raw p-values against this threshold.
 - **Dependencies**: T020, T012c.

- [~] T022 [US2] [FR-007] Implement permutation test `code/07_permutation_test.py`:
 - **Read** observed `test_r2` from `data/processed/model_results.json`, the full dataset from `features.csv`, and the split indices from `data/interim/split_indices_primary.json`.
 - **Validation**: **MUST verify** that `split_indices_primary.json` exists and contains `run_type == "primary"`. If not, exit with error to prevent leakage from robustness runs.
 - **Shuffle**: Perform permutation by **shuffling the `median_rt` labels (y) on the training set**. For each of **a substantial number of shuffles**:
 1. Apply the stored split indices to the full dataset to isolate the training and test sets.
 2. Shuffle the `median_rt` labels **only within the training set**.
 3. **Re-train the model from scratch** on the shuffled training set using the same hyperparameters. **Do NOT use `warm_start` or carry over weights from previous iterations.**
 4. Compute R² on the held-out test set (using the re-trained model).
 5. Store the R² value.
 - **Optimization**: Use vectorized R² calculation.
 - **Verification**: Ensure `split_indices_primary.json` are immutable and the shuffle does not alter training/test boundaries to prevent leakage.
 - **Store** null R² values in `data/interim/permutation_null_distribution.npy`.
 - **Compute** p-value by comparing observed R² against the null distribution.
 - **Write** results to `data/processed/permutation_results.json`.
 - **Note**: Shuffling only on the training set and re-training from scratch ensures statistical validity. The Plan's previous description of 'shuffling only on the held-out test set' is superseded by this statistically valid approach.
 - **Dependencies**: T017 (specifically the `split_indices_primary.json` artifact).

- [ ] T023 [US2] [FR-011] Perform post‑hoc power analysis using `statsmodels`.
 - **Logic**:
 1. Load `adjusted_r2` from `data/processed/model_results.json` (or default to 0.10 if calculating required N for a target).
 2. Calculate `effect_size` (Cohen's f) corresponding to the target R²=0.10: f = sqrt(p / (1-p)), where p represents a specified proportion..
 3. Call `statsmodels.stats.power.FTestPower.solve_power(effect_size=f, alpha=0.05, power=0.80, nobs=None)` to find `required_n` (the unknown target).
 4. Calculate `observed_power` using the actual N from `features.csv` and the observed R².
 - **Output**: **Append** `post_hoc_power_analysis` block to `data/processed/model_results.json` with `required_n` (int), `observed_power` (float, **primary reported metric for post-hoc analysis**), `effect_size` (float). **Ensure `observed_power` is the headline figure in the final report generation (T031c)** to align with FR-011's requirement for 'post-hoc power analysis'.
 - **Dependencies**: T017.

- [~] T024a [US2] [FR-012] Implement `code/08a_prepare_polynomial_features.py`:
 - Load `features.csv` and add polynomial terms for alpha and beta (degree from `config.POLY_DEGREE`, default 2).
 - **Output**: `data/interim/poly_features.csv`.
 - **Dependencies**: T012c.

- [ ] T024b [US2] [FR-012] Implement `code/08b_fit_nonlinear_model.py`:
 - Fit a linear model and a polynomial model on `poly_features.csv`.
 - **Output**: `data/interim/nonlinear_model_results.json` (coefficients, R² for both models).
 - **Dependencies**: T024a.

- [~] T024c [US2] [FR-012] Implement `code/08c_compare_models.py`:
 - Compare adjusted R² of linear vs. polynomial model via F‑test.
 - **Mandatory Logic**: Automatically evaluate the F-test p-value against the established significance threshold (p < 0.05).
 - **Output**: Store results in `data/processed/non_linear_comparison.json` including a boolean field `significant_at_p05` and a string `interpretation` confirming the 'significance' status.
 - **Dependencies**: T024b.

- [ ] T025a-config [US3] [FR-008] Create configuration for robustness window check.
 - **Logic**: Write a JSON file to `data/interim/robustness_window_params.json` containing a configurable `window_size` parameter.
 - **Output**: `data/interim/robustness_window_params.json`.
 - **Dependencies**: T010 (script), T007a, T008a, T008b.

- [~] T025a-run [US3] [FR-008] Implement `code/09_robustness_preprocess_window.py` execution.
 - **Execute** `code/02_preprocess_eeg.py` by reading `data/interim/robustness_window_params.json` and passing the `--window-size 2 --output-dir data/interim/robustness_window_eeg/` flags.
 - **Command**: `python code/02_preprocess_eeg.py --window-size 2 --output-dir data/interim/robustness_window_eeg/`.
 - **Output**: `data/interim/robustness_window_eeg/` (`.fif`) and **a new exclusion log** `data/interim/robustness_window_exclusion_log.csv`.
 - **Note**: **Must not overwrite primary results (T012a)**. Primary analysis (T012a) remains fixed at 4s. **Must re-run the entire preprocessing pipeline (T010) with the new window size to ensure independence from the primary run. Do NOT reuse ICA components from the primary run.**
 - **Dependencies**: T025a-config, `code/02_preprocess_eeg.py`, T007a, T008a, T008b, T008d.

- [ ] T025a-verify [US3] [FR-008] Verify robustness window preprocessing output.
 - **Logic**: Check that `data/interim/robustness_window_eeg/` contains valid `.fif` files and that `data/interim/robustness_window_exclusion_log.csv` exists and is not empty.
 - **Dependencies**: T025a-run.

- [ ] T025f-config [US3] [FR-008] Create configuration for robustness ICA check.
 - **Logic**: Write a JSON file to `data/interim/robustness_ica_params.json` containing `{"no_ica": true}`.
 - **Output**: `data/interim/robustness_ica_params.json`.
 - **Dependencies**: T010 (script), T007a, T008a, T008b.

- [~] T025f-run [US3] [FR-008] Implement `code/09_robustness_preprocess_ica.py` execution.
 - **Execute** `code/02_preprocess_eeg.py` by reading `data/interim/robustness_ica_params.json` and passing the `--no-ica --output-dir data/interim/robustness_ica_eeg/` flags.
 - **Output**: `data/interim/robustness_ica_eeg/` (`.fif`) and **a new exclusion log** `data/interim/robustness_ica_exclusion_log.csv`.
 - **Note**: Ensure primary results are not overwritten by writing to distinct output directories.
 - **Dependencies**: T025f-config, `code/02_preprocess_eeg.py`, T007a, T008a, T008b, T008d.

- [~] T025b [US3] [FR-008] Implement `code/09_robustness_features_window.py`:
 - Re-run `code/04_extract_psd.py`, `code/04b_aggregate_bands.py`, `code/04c_relative_power.py` using the output from T025a-run (`robustness_window_eeg/`).
 - **Logic**: Calculate the R² delta between the robustness run and the primary run (T017). **Mandatory**: Check if `abs(robustness_r2 - primary_r2) < 0.05`. If not, flag in output.
 - **Dependencies**: T025a-run, `code/04_extract_psd.py`, `code/04b_aggregate_bands.py`, `code/04c_relative_power.py`.
 - **Output**: `data/processed/robustness_features_2s.csv`. **Must not overwrite primary `features.csv`**.

- [~] T025g [US3] [FR-008] Implement `code/09_robustness_features_ica.py`:
 - Re-run `code/04_extract_psd.py`, `code/04b_aggregate_bands.py`, `code/04c_relative_power.py` using the output from T025f-run (`robustness_ica_eeg/`).
 - **Dependencies**: T025f-run, `code/04_extract_psd.py`, `code/04b_aggregate_bands.py`, `code/04c_relative_power.py`.
 - **Output**: `data/processed/robustness_features_no_ica.csv`. **Must not overwrite primary `features.csv`**.

- [~] T025c [US3] [FR-008] Implement `code/09_robustness_modeling.py`:
 - Re-run `code/05_modeling.py` on `robustness_features_2s.csv` and `robustness_features_no_ica.csv`.
 - **Output**: `data/processed/robustness_model_results.json`.
 - **Dependencies**: T025b, T025g, `code/05_modeling.py`. **Note**: Must not overwrite T017's output (`model_results.json`).

- [ ] T025d [US3] [FR-006/FR-008] Implement robustness correlation analysis: Re-run `code/06_correlations.py` on `robustness_features_2s.csv` and `robustness_features_no_ica.csv`.
 - **Command**: `python code/06_correlations.py --input <file> --output <output>`.
 - **Output**: `data/processed/robustness_correlations_raw.csv`.
 - **Dependencies**: T025b, T025g, `code/06_correlations.py`. **Must not overwrite primary `correlations_raw.csv`**.

- [ ] T025e [US3] [FR-009] Implement robustness sensitivity analysis: Re-run `code/10_sensitivity_analysis.py` on `robustness_correlations_raw.csv`.
 - **Command**: `python code/10_sensitivity_analysis.py --input data/processed/robustness_correlations_raw.csv --output-report data/processed/robustness_sensitivity_report.csv --output-plot data/processed/robustness_sensitivity_plot.png`.
 - **Logic**: Sweep p-value threshold across a range of conventional significance levels in fine-grained increments. Record the **count of significant correlations** at each step.
 - **Output**: `data/processed/robustness_sensitivity_report.csv`, `data/processed/robustness_sensitivity_plot.png`.
 - **Dependencies**: T025d. **Must not overwrite primary `sensitivity_report.csv`**.

- [~] T026 [US3] [FR-009] Implement sensitivity analysis `code/10_sensitivity_analysis.py`:
 - Reads `data/interim/correlations_raw.csv`.
 - Sweeps p-value threshold across a range of low to moderate significance levels.
 - **Records** the count of significant correlations at each step.
 - **Output**: `data/processed/sensitivity_report.csv` (columns: `threshold`, `significant_count`).
 - **Output**: `data/processed/sensitivity_plot.png`.
 - **Dependencies**: T020, T021.

- [ ] T035b [US2] Validate schemas of `model_results.json`, `correlations_corrected.csv`, `non_linear_comparison.json`, and `permutation_results.json` via contract tests.
 - **Test Files**: `tests/contract/test_result_schema.py`.
 - **Command**: `pytest tests/contract/`.
 - **Dependencies**: T017, T020, T021, T022, T024c, T035a.

**Checkpoint**: User Stories 1 & 2 functional.

---

## Phase 5: User Story 3 - Robustness Checks and Sensitivity Analysis (Priority: P3)

**Goal**: Re‑run analysis with alternative parameters and sweep significance thresholds.

- (Implemented within T025a-g and T026; no separate tasks required.)

---

## Phase 6: Reporting & Validation

**Purpose**: Aggregate results and verify success criteria.

- [~] T031a [US3] [SC-001 to SC-004] Implement `code/11a_load_results.py` to ingest all metrics (adjusted R², Bonferroni‑corrected p-values, robustness deltas, sensitivity thresholds, feasibility logs) into a unified dictionary.
 - **Dependencies**: T017, T021, T024c, T022, T023, T025c, T025d, T025e, T026, T008b.
 - **Note**: Must include `observed_power` (primary metric) and `required_n` (secondary reference) from T023 in the loaded dictionary. Load primary results from `model_results.json` and robustness from `robustness_model_results.json`.

- [ ] T031b [US3] [SC-001 to SC-004] Implement `code/11b_format_tables.py` to generate Markdown tables from the ingested data.
 - **Dependencies**: T031a.
 - **Note**: Generate tables for both primary and robustness results, clearly separating them.

- [~] T031c [US3] [SC-001 to SC-004] Implement `code/11c_write_report.py` to assemble the final `data/processed/final_report.md`.
 - **Dependencies**: T031b, T023.
 - **Content**: Must include sections for:
 1. **Primary Results**: `adjusted_r2`, `test_r2`, `Bonferroni p-values`, `observed_power` (from T023, **headline metric for post-hoc analysis**).
 2. **Robustness Analysis**: R² deltas for 2s window and no-ICA runs.
 3. **Sensitivity Analysis**: Threshold sweep results.
 4. **Feasibility**: `feasibility_report.md` content if applicable.
 - **Note**: Explicitly highlight `observed_power` as the main finding for Power Analysis; **suppress emphasis on `required_n`** in the main findings if `observed_power` is the primary post-hoc metric.

- [ ] T008-report-gate [P] [Plan-Phase-0.5] [FR-001] Generate `data/processed/feasibility_report.md` for any halt condition or success confirmation.
 - **Inputs**: `data/interim/halt_signal.json` (from T008b or T008d) OR absence of `halt_signal.json` (success).
 - **Logic**: Check for existence of `halt_signal.json`. If present, read the `reason` field and generate `data/processed/feasibility_report.md` with the formal failure status. If absent, generate `data/processed/feasibility_report.md` with a success confirmation (listing the number of participants processed).
 - **Output**: `data/processed/feasibility_report.md` (always generated).
 - **Dependencies**: T008b, T008d.

- [~] T032 [US3] [SC-005] Implement feasibility measurement script `code/12_feasibility_check.py`:
 - Estimate RAM usage (`psutil.virtual_memory().used`) and runtime (proportional to the number of participants).
 - **Hard Abort**: If estimated RAM > 7GB or estimated runtime > 6h, log the violation and **exit with code 1**.
 - Log predictions to `data/processed/feasibility_metrics.log`.
 - **Note**: Estimates for the primary pipeline only.
 - **Dependencies**: T007, T010, T017.

- [~] T034 [US3] [SC-005] Run integration test `tests/integration/test_pipeline.py` to ensure end‑to‑end execution works.
 - **Note**: Verifies primary pipeline end-to-end.
 - **Dependencies**: T010, T012a, T017, T020, T022, T025a-run, T026, T037a (if wrapper exists).

- [~] T036a [US3] Run contract tests for `feature_schema` and `result_schema`.
 - **Test Files**: `tests/contract/test_feature_schema.py`, `tests/contract/test_result_schema.py`.
 - **Command**: `pytest tests/contract/`.
 - **Note**: Verifies schema of primary results.
 - **Dependencies**: T035a, T035b.

**Checkpoint**: All user stories completed; final report generated.

---

## Phase 7: Documentation & Execution Fix

**Purpose**: Resolve execution feedback mismatches and finalize documentation.

- [ ] T037a [P] Create `code/generate_report.py` as a convenience wrapper that orchestrates `code/11a_load_results.py`, `code/11b_format_tables.py`, and `code/11c_write_report.py`.
 - **Dependencies**: T031a, T031b, T031c.
 - **Note**: Orchestrates loading of both primary and robustness results.
- [ ] T037b [P] Update `specs/001-predict-sensory-speed-from-eeg/quickstart.md` and `plan.md` to either invoke `code/generate_report.py` (if T037a was created) or explicitly list the sequence `11a -> 11b -> 11c`.
 - **Dependencies**: T037a.
 - **Note**: Documentation must reflect the distinction between primary and robustness analysis paths.

---

## Phase 8: Revision & Gap Resolution

**Purpose**: Address specific gaps identified in plan/spec review regarding data alignment and non-linear analysis.

- [~] T038 [US2] [FR-012] [Review] Implement explicit polynomial degree selection and F-test reporting.
 - **Issue**: Plan mentions "polynomial terms" but does not specify the degree or the exact statistical test for comparing models.
 - **Action**: Update `code/08a_prepare_polynomial_features.py` to accept `--degree` (default 2) and `code/08c_compare_models.py` to perform an F-test comparing the nested linear vs. polynomial models.
 - **Output**: Ensure `data/processed/non_linear_comparison.json` explicitly contains `f_statistic`, `p_value`, `linear_r2`, `polynomial_r2`, and `significant_at_p05`.
 - **Dependencies**: T024a, T024b, T024c.

- [~] T039 [US1] [FR-001] [Review] Implement explicit participant ID alignment verification in `code/00_feasibility_join.py`.
 - **Issue**: The plan assumes `subject_id` and `participant_id` can be joined, but the datasets (PhysioNet vs OpenNeuro) may use different ID formats (e.g., `001` vs `sub-001`).
 - **Action**: Add logic in `code/00_feasibility_join.py` to normalize IDs (strip `sub-` prefix, zero-pad numbers) before attempting the join. Log any participants that fail to join due to format mismatch in `data/interim/feasibility_exclusion_log.csv` with reason `id_format_mismatch`.
 - **Output**: `data/interim/joined_metadata.csv` with verified, normalized IDs.
 - **Dependencies**: T007a, T007b, T008a.

- [ ] T041 [US3] [FR-008] [Review] Verify robustness run independence.
 - **Issue**: Ensure that robustness runs (T025a-g) do not inadvertently reuse ICA components or split indices from the primary run.
 - **Action**: Add an assertion in `code/09_robustness_preprocess_window.py` and `code/09_robustness_preprocess_ica.py` that checks for the absence of `ica_components.fif` from the primary run in the robustness output directory. If found, raise an error.
 - **Output**: Verified robustness outputs in distinct directories.
 - **Dependencies**: T025a-run, T025f-run.

---

## General Notes

- All tasks are deterministic; random seeds are pinned in `code/config.py`.
- All data files are checksummed; hashes recorded in project state (outside this file).
- No GPU code is used; all libraries are CPU‑compatible.
- Tasks marked `[P]` may run in parallel provided their dependencies are satisfied.
- **FR-010 Precedence**: The Spec's FR-010 mandates Relative Power. The Plan's suggestion of CLR is superseded by the Spec. This task implements Relative Power and explicitly omits CLR. **Explicitly overrides Plan Phase 1 CLR requirement.**
- **Data Integrity**: All data loading tasks (T007a, T007b) MUST fail loudly if the real source is unavailable; no synthetic fallbacks are permitted.
- **Constitution VI vs Spec**: Window size is fixed at 4s per Spec FR-003 and US-1 for the **primary analysis**. The Plan's reference to '2s' windows is superseded by the Spec's explicit acceptance criteria. Robustness checks use 2s only as a secondary test.
- **Plan vs Spec Conflict**: The Plan's mention of CLR is superseded by Spec FR-010. This is noted in T012c.
- **Feasibility Gate**: T008b and T008d are the final gates. T008-report-gate generates `feasibility_report.md` if a halt signal is detected OR if absent (success).
- **Primary vs Robustness**: All robustness tasks (T025a-g, T025c-e) must write to distinct output directories/files to avoid overwriting primary results.
- **Permutation Test Safety**: T022 MUST verify it is using split indices from the primary T017 run only (via `split_indices_primary.json`).
