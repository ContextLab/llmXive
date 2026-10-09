# Tasks: Neural Entropy and Cognitive Flexibility in Aging

**Inputs**: `spec.md`, `plan.md`, existing research artifacts, and reviewer feedback.  
All tasks follow the canonical `- [ ] T### [P?] [USx?] description …` format. Checked boxes (`[X]`) indicate work that has already been verified and does not need modification.

---

## Phase 1: Project Setup (already verified)

- [ ] T001 Establish the project layout, create `code/`, `data/raw/`, `data/processed/`, `tests/`, and `specs/` directories; add a pinned `requirements.txt` (MNE 1.6.0, statsmodels 0.14.0, NumPy 1.24.0, pandas 2.0.0, PyYAML 6.0.1, requests 2.31.0, scikit‑learn 1.3.0, numba 0.58.0, jsonschema 4.19.0, huggingface_hub 0.19.0). **Verification**: `pip install -r requirements.txt` succeeds on a clean CI runner.

- [ ] T004 Setup `utils/resource_monitor.py` to log RAM/Disk usage and abort if >7 GB RAM or >14 GB disk is consumed. **Verification**: Log entry appears in `logs/resource_usage.log` during any script run.

- [ ] T005 [P] Implement `utils/entropy_utils.py` with CPU‑only Sample Entropy and Approximate Entropy (no CUDA). **Verification**: Unit tests in `tests/unit/test_entropy.py` pass.

- [ ] T006 [P] Implement `utils/stats_utils.py` providing OLS regression and Benjamini‑Hochberg FDR functions. **Verification**: `tests/unit/test_stats.py` passes.

- [ ] T007 Create data‑wide logging (`utils/logger.py`) to capture step‑wise messages and exclusion reasons. **Verification**: Log file `logs/pipeline.log` contains entries for each stage.

- [X] T008 [P] Add `code/config.py` with constants:
  ```python
  OPENNEURO_DATASET_IDS = ["ds000246", "ds003104"]
  SNR_THRESHOLD = 5.0
  ARTIFACT_THRESHOLD = 0.2
  SEED = 42
  ```  
  **Verification**: Importing `config` yields the exact values.

---

## Phase 2: Foundational Utilities (already verified)

- [ ] T010 [P] **Create `specs/001-neural-entropy-cognitive-flexibility/contracts/dataset.schema.yaml`** describing required columns (`participant_id`, `age`, `education`, `wcst_perseverative_errors`, `task_accuracy`, `neurological_condition`, `medication_use`, plus raw EEG file references).  
  **Verification**: `jsonschema validate --instance data/raw/example.parquet --schema contracts/dataset.schema.yaml` returns success.

- [ ] T011 [P] Unit test for entropy stability (`tests/unit/test_entropy.py`). **Verification**: Test passes.

- [ ] T012a [US1] **Implement `code/01_download_data.py`** to fetch OpenNeuro datasets `ds000246` and `ds003104` via `huggingface_hub`. Downloads original EDF/BDF EEG files (preserving native format) into `data/raw/` and records SHA‑256 checksums in `data/checksums.json`.  
  **Verification**: EDF/BDF files exist in `data/raw/`, checksum file contains matching entries.

- [ ] T012b [US1] **Implement `code/01_validate_data.py`** that loads each raw file, checks for the column `wcst_perseverative_errors`, flags missing‑variable datasets in `logs/validation_status.json`, and aborts with an error if no dataset passes.  
  **Verification**: `logs/validation_status.json` correctly lists excluded datasets and the script exits with an error when appropriate.

- [ ] T012c [US1] **Extract behavioral scores**: `code/02_extract_behavior.py` reads validated raw files, merges behavioral columns, and writes `data/processed/behavioral_scores.csv`.   <!-- FAILED-IN-EXECUTION: code/02_extract_behavior.py exit=1 -->
  **Verification**: CSV contains one row per participant with all required covariates and no missing values (except those intentionally excluded).

---

## Phase 3: User Story 1 – EEG Pipeline & Entropy (Priority P1)

- [ ] T013 [US1] **Implement `code/02_preprocess_eeg.py`**: <!-- FAILED-IN-EXECUTION: code/02_preprocess_eeg.py exit=1 -->
  - Load raw EDF/BDF files with MNE.
  - Apply 1‑45 Hz band‑pass filter and 50 Hz (or 60 Hz) notch filter.
  - Detect bad channels (variance > 5 SD) and interpolate.
  - Run ICA, automatically identify and remove EOG/EMG components.
  - Segment into 2‑second non‑overlapping epochs.
  - Save epoched data as `data/processed/epoched/<participant_id>-epochs.fif`.  
  **Verification**:
    - Epoch file exists and contains ≥30 epochs.
    - Metadata file `data/processed/preproc_metadata/<participant_id>.json` records that band‑pass, notch, bad‑channel interpolation, and ICA were applied.
    - A quick sanity check confirms that the power spectrum after preprocessing matches the 1‑45 Hz bandpass.

- [ ] T014 [US1] **Compute median SNR** in `code/03_compute_snr.py`:
  - For each participant, compute signal power in 1‑45 Hz band and noise power in 46‑60 Hz band.
  - Median SNR (dB) = 10 · log10(signal/noise).
  - Write `data/processed/snr_metrics.json` mapping participant IDs to SNR values (float).  
  **Verification**:
    - JSON is valid and contains a numeric SNR for every participant.
    - At least one participant has SNR ≥ 5 dB; a summary printed to the console.

- [ ] T015 [US1] **Implement `code/04_compute_entropy.py`**:
  - Load epoched data, band‑pass each epoch into the five standard bands (delta 1‑4 Hz, theta 4‑8 Hz, alpha 8‑12 Hz, beta 12‑30 Hz, gamma 30‑45 Hz).
  - Compute Sample Entropy (m=2, r=0.2·std) and Approximate Entropy for each band using `utils.entropy_utils`.
  - Aggregate across epochs (mean per participant) and write `data/processed/entropy_metrics.csv` with columns: `participant_id`, `band`, `entropy_type` (SampEn/ApEn), `value`.  
  **Verification**:
    - CSV has exactly 10 rows per participant (5 bands × 2 entropy types).
    - No NaN/Inf values.
    - Header includes a comment confirming the parameters `m=2` and `r=0.2·std`.

- [ ] T016 [US1] **Data‑quality exclusion** (`code/04_quality_checks.py`):
  - Exclude participants with total valid EEG < 60 s, > 20 % corrupted epochs, or SNR < 5 dB (using `snr_metrics.json`).
  - Write exclusion decisions to `data/processed/exclusion_log.csv` (columns: `participant_id`, `reason`).  
  **Verification**: Log contains at least one excluded participant and the reasons match the criteria.

- [ ] T017 **Add resource‑monitoring calls**:
  - Insert `utils.resource_monitor.record()` at the start and end of `02_preprocess_eeg.py` and `04_compute_entropy.py`.
  - Ensure `logs/resource_usage.log` records peak RAM and total runtime for each script.  
  **Verification**: Log entries show peak RAM ≤ 6.5 GB and total runtime ≤ 4 h for the full dataset on CI.

---

## Phase 4: User Story 2 – Statistical Correlation (Priority P2)

- [ ] T018 [US2] **Create `specs/001-neural-entropy-cognitive-flexibility/contracts/correlation_results.schema.yaml`** defining columns: `participant_id`, `band`, `entropy_type`, `partial_r`, `p_raw`, `p_bonferroni`, `vif`.  
  **Verification**: `jsonschema validate --instance data/processed/correlation_results_partial.csv --schema contracts/correlation_results.schema.yaml` succeeds.

- [ ] T020a [US2] **Implement `code/05_partial_correlation.py`**:
  - Load `entropy_metrics.csv` and `behavioral_scores.csv`.
  - For each (band × entropy_type) compute a **Partial Pearson** correlation (using an appropriate library such as `pingouin.partial_corr`) between the entropy metric and WCST perseverative errors, controlling for age, education, and task accuracy.
  - Output raw results to `data/processed/correlation_results_partial.csv`.  
  **Verification**: CSV exists, contains rows for all 10 predictor combinations, and includes a `partial_r` column.

- [ ] T021 [US2] **Bonferroni correction & VIF handling** (extend `05_partial_correlation.py`):
  - Compute VIF for all predictors; if any VIF > 5, drop the Approximate Entropy predictor for that band and re‑run the partial correlation.
  - Apply Bonferroni correction across the final set of tests (≤ 10) and add column `p_bonferroni`.
  - Write `data/processed/correlation_results_corrected.csv`.  
  **Verification**: Adjusted p‑values are ≤ 1.0 and the file passes the schema from T018.

- [ ] T022 [US2] **Effect‑size calculation** (`code/06_effect_sizes.py`):
  - Convert partial correlation `partial_r` to effect size (Cohen’s q) and compute 95 % CI.
  - Flag clinically meaningful effects (|partial_r| ≥ 0.3).
  - Write `data/processed/effect_sizes.json`.  
  **Verification**: JSON contains a `clinically_meaningful` boolean for each test.

- [ ] T023 [US2] **Methodology notes**:
  - Generate `logs/methodology_notes.md` summarizing:
    - Explicit “Associational” disclaimer.
    - Covariate control summary (age, education, task accuracy, binary covariates).
    - Brief statement of the Bonferroni correction method.
  - **Verification**: Markdown file contains the required disclaimer line and a table of covariates.

- [ ] T024 [US2] **Verify WCST instrument** (`code/03_verify_wcst.py`):
  - Check that the WCST version present in the dataset matches a validated version (e.g., Heaton et al., 1993) and record the citation.
  - Write `logs/wcst_validation.log` with the validation result and citation reference.  
  **Verification**: Log contains a line “WCST validated against Heaton et al., 1993” or aborts with an error if validation fails.

---

## Phase 5: User Story 3 – Sensitivity & Reporting (Priority P3)

- [ ] T027 [US3] **Sensitivity‑exclusion analysis**:
  - Re‑run the full partial‑correlation pipeline after removing participants flagged with `neurological_condition == True` or `medication_use == True`.
  - Write `data/processed/sensitivity_exclusion_results.csv`.  
  **Verification**: CSV exists and the participant count (`n`) is lower than in the primary analysis.

- [ ] T028 [US3] **Threshold‑sweep analysis**:
  - Iterate over three artifact‑threshold offsets `{0.0, 0.05, 0.10}` and three SNR‑threshold offsets `{0.0, 0.05, 0.10}` (total 9 configurations).
  - For each configuration, re‑run preprocessing → entropy → partial correlation → Bonferroni.
  - Append results to `data/processed/sensitivity_threshold_results.csv` with columns `config_id`, `artifact_offset`, `snr_offset`, `band`, `entropy_type`, `partial_r`, `p_bonferroni`.  
  **Verification**: CSV has 9 × 10 = 90 rows and includes a `config_id` column.

- [ ] T029 [US3] **Aggregate sensitivity report**:
  - Summarize headline correlation coefficients and p‑values across exclusion and sweep scenarios.
  - Compute coefficient‑of‑variation (CV) of `partial_r` per band/entropy.
  - Write `data/processed/sensitivity_report.json` with fields: `scenario`, `r_mean`, `r_cv`, `p_mean`, `n_excluded`.  
  **Verification**: JSON is valid and contains at least two scenario entries (`exclusion`, `threshold_sweep`).

- [ ] T030 [US3] **Final reproducible report**:
  - `code/07_generate_report.py` reads all processed artifacts and produces `reports/final_report.md` containing:
    - Correlation matrix (raw and Bonferroni‑adjusted).
    - Effect‑size table with clinical relevance flags.
    - Sensitivity tables and CV metrics.
    - The associational disclaimer (copied from `logs/methodology_notes.md`).
  - Commit the markdown in the repo.  
  **Verification**: The report renders correctly on GitHub preview and includes all required sections.

- [ ] T031 [US3] **Validate correlation results against schema**:
  - Run `jsonschema validate --instance data/processed/correlation_results_corrected.csv --schema contracts/correlation_results.schema.yaml`.
  - Write outcome to `logs/validation_results.txt`.  
  **Verification**: Log contains the word “PASS”.

- [ ] T032 [US3] **Validate sensitivity report against schema**:
  - Create `specs/001-neural-entropy-cognitive-flexibility/contracts/sensitivity_report.schema.yaml` defining the JSON structure from T029.
  - Run `jsonschema validate --instance data/processed/sensitivity_report.json --schema contracts/sensitivity_report.schema.yaml` and write results to `logs/validation_results_json.txt`.  
  **Verification**: Log contains “PASS”.

- [ ] T033 [US3] **Data‑flow diagram**:
  - Produce `docs/diagrams/data_flow.png` illustrating the flow: Raw → Validation → Preprocess → SNR → Epochs → Entropy → Partial Correlation → Sensitivity → Report.  
  **Verification**: PNG file exists and is referenced in `README.md`.

---

## Phase 6: Polishing & Cross‑Cutting (optional, but useful)

- [ ] T034 [P] Refactor `utils/entropy_utils.py` with `@numba.jit` for faster entropy loops.  
  **Verification**: Benchmark shows ≥ 30 % speed‑up on a sample participant.

- [ ] T035 [P] Verify peak memory < 6 GB for the entire pipeline on CI (run full pipeline and inspect `logs/resource_usage.log`).  
  **Verification**: Log entry confirms peak RAM ≤ 6 GB.

- [ ] T036 [P] Add edge‑case unit tests for:
  - Short recordings (< 60 s) → proper exclusion.
  - NaN/Inf entropy values → re‑compute with `float64` then exclude if persistent.  
  **Verification**: New tests in `tests/unit/` pass.

- [ ] T037 [P] Update `quickstart.md` with a one‑line command (`python -m code.main`) and expected runtime (< 6 h).  
  **Verification**: Running the command on a fresh CI runner completes successfully within the time limit.

