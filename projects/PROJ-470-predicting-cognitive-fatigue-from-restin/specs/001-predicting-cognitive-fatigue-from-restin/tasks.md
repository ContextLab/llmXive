# Tasks: Predicting Cognitive Fatigue from Resting-State EEG Complexity

**Input**: Design documents from `specs/001-predicting-cognitive-fatigue-from-restin/`
**Prerequisites**: `plan.md` (required), `spec.md` (required for user stories), `research.md`, `data-model.md`, `contracts/`

**Tests**: Tests are bundled with the implementation they support; the spec's acceptance scenarios define the required checks.

**Organization**: Tasks are grouped by research phase (first end-to-end analysis → complete validation → results handoff) while mapping to user stories US1–US3.

**Format**: `- [ ] T### [P?] [USx?] description (file path)`; `[P]` = different files, no dependencies.

**Preserved work**: Setup, skeleton, config, logging, report‑stub, quickstart, monitoring, and download/validation tasks (former T001–T009, T026) are retained as verified. Tasks previously rejected (T012–T016, T024) are reopened below with the precise failing artifacts named. Non‑scientific polish tasks have been dropped per the smallest‑complete‑study rule; dataset checksumming is folded into T009.

---

## Phase 1: Setup and first end‑to‑end analysis

- [ ] T001 [P] Create project directory structure: `data/raw/`, `data/processed/`, `data/analysis/`, `code/`, `tests/`, `docs/` (verified in `tests/unit/test_setup.py`).
- [ ] T002 [P] Create code skeleton files: `code/config.yaml`, `code/download.py`, `code/preprocess.py`, `code/features.py`, `code/analysis.py`, `code/report.py` (verified in `tests/unit/test_skeleton.py`).
- [ ] T003 [P] Create docs skeleton files: `docs/README.md`, `docs/quickstart.md`.
- [ ] T004 [P] Create `code/requirements.txt` with pinned dependencies: `mne`, `scikit-learn`, `numpy`, `pandas`, `scipy`, `pyyaml`, `pytest`, `nolds`, `statsmodels`, `psutil`, `pyentropy`.
- [ ] T005 [P] Create `code/config.yaml` with pipeline parameters: `filter_low: 1.0`, `filter_high: 40.0`, `artifact_threshold_uV: 100.0`, `notch_frequency: 50.0`, `random_seed: 42`, `min_segment_duration_sec: 120.0`, `pe_dimension: 3`, `pe_lag: 1` (values fixed per FR‑002/FR‑003).
- [ ] T006 [P] Implement logging in `code/utils/logging.py` that writes exclusion events to `data/processed/exclusion_log.csv` with columns `[participant_id, reason, timestamp]` (verified in `tests/unit/test_logging.py`).
- [ ] T007 [P] Implement `code/report.py` stub that ingests CSVs from `data/analysis/` and renders them as markdown tables.
- [ ] T008 [P] Generate `docs/quickstart.md` with step‑by‑step pipeline commands.
- [ ] T026 [P] Implement monitoring in `code/utils/monitor.py` using `psutil` and `time` to capture `peak_rss_gb` and `total_runtime_hours`, written to `data/analysis/resource_usage.json`.

- [ ] T009 [US1] **Data retrieval, validation, and extraction (REDO).**
  1. Download a real public PhysioNet dataset containing paired pre/post resting‑state EEG and fatigue ratings (primary: `eegmat`; fallback: PhysioNet “EEG Motor Movement/Imagery” with a validated fatigue questionnaire).
  2. Stream files into `data/raw/eeg_restingstate/` (no full‑memory load).
  3. Validate presence of `eeg_data` and `fatigue_rating`; if missing, halt with clear error listing available variables.
  4. Count participants with complete pre/post pairs; if N < 30, halt with `"Sample size N < 30"` (SC‑001).
  5. Write `data/raw/download_manifest.json` conforming to `dataset.schema.yaml` (includes checksum, participant count, variables, status).
  6. Extract fatigue scores to `data/processed/fatigue_scores.csv`.
  7. Write `data/processed/validation_report.json` (`n_participants`, `variables_found`, `status`).
  **Verification**: manifest exists with real checksums; HEAD request succeeds; `fatigue_scores.csv` contains real rows.

- [ ] T010 [P] **Citation validation (Constitution II).** Verify all citations in `research.md` against the project's verified‑datasets block; fail if any citation is unreachable or mismatched. Runs after T009.

- [ ] T012 [US1] **Preprocessing (REDO).**
  Implement `code/preprocess.py` with pure function `process_segment(raw_data, config)` applying: 1‑40 Hz bandpass, 50 Hz notch, average re‑reference, artifact rejection at ±100 µV (FR‑002). Orchestrate over entries in `download_manifest.json`, discard segments < 120 s, write cleaned `.fif` files to `data/processed/cleaned_eeg/{participant_id}_{segment_type}.fif` with side‑car metadata per `processed_eeg.schema.yaml`.  
  Create `data/processed/exclusion_log.csv` (header `[participant_id, reason, timestamp]`) logging every rejected channel/epoch/short segment.  
  **Verification**: synthetic 120 s signal with 50 Hz sinusoid shows > 20 dB attenuation; real dataset yields `.fif` files for all validated participants and a populated `exclusion_log.csv`.

- [ ] T016 [US2] **Complexity feature extraction (REDO).**
  For each cleaned `.fif` in `data/processed/cleaned_eeg/`, compute per‑channel Lempel‑Ziv Complexity using `nolds.lz_complexity` (median quantization) and Permutation Entropy using `pyentropy.permutation_entropy` with `normalize=True`, `dimension=3`, `lag=1`. Write `data/analysis/complexity_metrics.csv` with columns `metric_id`, `segment_id`, `participant_id`, `segment_type`, `channel`, `metric_type`, `value`, `timestamp` (conforms to `complexity_metric.schema.yaml`).  
  **Verification**: synthetic signal yields LZC ≤ 1.0 and PE ≤ log2(3!)≈2.585; real dataset produces a non‑empty CSV with one row per (participant, segment, channel, metric).

- [ ] T018 [US3] **Delta computation, primary correlation, and effect‑size CIs (REDO).**
  1. Load `complexity_metrics.csv` and `fatigue_scores.csv`.
  2. Compute per‑channel deltas: `delta_complexity_lzc = post_lzc - pre_lzc`, `delta_complexity_pe = post_pe - pre_pe`. Output `data/analysis/delta_scores.csv` with columns `participant_id`, `channel`, `delta_complexity_lzc`, `delta_complexity_pe`, `delta_fatigue`.
  3. Perform **partial** Pearson and Spearman correlations controlling for confounds (age, time_of_day, baseline_complexity, medication_status) and compute 95 % CI for each correlation coefficient (Fisher Z).  
  4. Write `data/analysis/raw_correlation_results.csv` conforming to `analysis_result.schema.yaml` (includes CI fields).
  **Verification**: real run produces rows for each channel‑metric pair, includes CI columns, and respects confound control.

- [ ] T024 [US3] **Collinearity diagnostics (REDO).**
  Compute VIF for the full predictor set (`delta_fatigue`, `pre_complexity_lzc`, `pre_complexity_pe`, plus listed confounds). Log numeric VIFs to `data/analysis/vif_diagnostics.log` and write `data/analysis/vif_valid_predictors.json` listing predictors with VIF < 5. **Note:** This is a diagnostic only; the pipeline does **not** abort if any VIF ≥ 5 (intentional deviation from the original verification wording).  
  **Verification**: log contains a VIF per predictor; JSON may be empty if none pass.

- [ ] T020 [US3] **Multiple‑comparison correction and final correlation output (after T024).**
  Apply Benjamini‑Hochberg correction to raw p‑values from T018, read VIF values from T024, and add a `confounds_controlled` list (the confounds used in the partial correlation). Write `data/analysis/correlation_results.csv` conforming to `analysis_output.schema.yaml` (`vif` and `confounds_controlled` now populated). Also write `data/analysis/bh_corrected_pvalues.csv`.  
  **Verification**: `p_value_bh ≥ p_value`; `significant` matches `p_value_bh < 0.05`; VIF column present.

- [ ] T029 [US3] **CI‑enhanced correlation file (REDO).**
  Combine CI columns from `raw_correlation_results.csv` with the BH‑corrected results from T020 to produce `data/analysis/correlation_results_with_ci.csv`. This file contains all schema fields from `analysis_output.schema.yaml` **plus** `effect_size_ci_lower` and `effect_size_ci_upper`. The original `correlation_results.csv` remains schema‑compliant; downstream reporting will use the CI‑enhanced file.  
  **Verification**: `correlation_results_with_ci.csv` contains required CI columns and matches rows from `correlation_results.csv`.

- [ ] T021 [US3] **ANCOVA secondary model (after T024).**
  Fit `Post_Complexity ~ delta_fatigue + Pre_Complexity + age + time_of_day + medication_status` using predictors listed in `vif_valid_predictors.json`. Write `data/analysis/ancova_results.csv`. If no valid predictors, log a warning but still produce an empty result file to satisfy downstream steps.  
  **Verification**: file exists when model runs; otherwise warning appears.

- [ ] T023 [US3] **Sensitivity analysis (single output).**
  Count significant electrodes at thresholds p ≤ 0.05 and p ≤ 0.01 for both raw and BH‑corrected p‑values. Write a single `data/analysis/sensitivity_table.csv` with columns `threshold`, `significant_electrodes_count`.  
  **Verification**: table contains two rows (0.05 and 0.01) and counts match `correlation_results.csv`.

- [ ] T027 [US3] **Resource and edge‑case checks.**
  Assert from `resource_usage.json` that `peak_rss_gb ≤ 7.0` and `total_runtime_hours ≤ 6.0`; fail with clear error if exceeded. Verify `exclusion_log.csv` records participants excluded for missing fatigue ratings and report the exclusion count.  
  **Verification**: assertions trigger informative errors; passing run logs counts.

## Phase 2: Complete the study and validate its evidence

- [ ] T025 [US3] **Final report.** Generate `docs/final_report.md` from actual CSV/LOG outputs: correlation results (including CIs from `correlation_results_with_ci.csv`), ANCOVA results (if any), sensitivity table, VIF summary, sample size, exclusion counts. Include an interpretation section that discusses both “adaptive simplification” and “degenerative noise” explanations, citing relevant literature and explicitly noting the limitation of using a single scalar complexity metric.  
  **Verification**: report exists, cites source files, renders tables from real CSVs, and contains the required interpretation paragraph.

- [ ] T028 [US3] **Reproducibility re‑run and paper‑stage handoff.** Re‑execute the entire workflow from raw data, confirm all unit tests and artifact checks pass, and append a handoff section to `docs/final_report.md` listing required result tables, figures, and interpretation for the paper pipeline.  
  **Verification**: clean re‑run reproduces identical `correlation_results.csv` (fixed seed); handoff section enumerates all artifacts.

## Phase 3: (no additional tasks)

**Dependencies and requirement coverage**

| Requirement | Task(s) | Order |
| :--- | :--- | :--- |
| FR‑001 dataset validation, N ≥ 30 gate | T009 | first |
| FR‑002 preprocessing, ±100 µV rejection | T012 | after T009 |
| FR‑003 LZC/PE on ≥ 120 s segments | T016 | after T012 |
| FR‑004 delta‑delta correlation with confounds | T018 | after T016 |
| FR‑005 BH correction | T020 | after T018 (and after T024) |
| FR‑006 sensitivity analysis | T023 | after T020 |
| SC‑001 N ≥ 30 gate | T009 | first |
| SC‑002/SC‑003 runtime/memory | T027 | after all analysis |
| SC‑004 VIF < 5 diagnostics | T024 | parallel with T020, but T020 now waits for T024 |
| Report & handoff | T025, T028 | last |

Execution order (enforced by task descriptions):  
T009 → T010 → T012 → T016 → T018 → T024 → T020 → T029 → T021 → T023 → T027 → T025 → T028. Setup tasks T001‑T008, T026 are completed beforehand.