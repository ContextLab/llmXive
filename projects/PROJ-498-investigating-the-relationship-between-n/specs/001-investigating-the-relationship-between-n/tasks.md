# Tasks: Investigating the Relationship Between Neural Synchrony and Attention Switching Costs

**Input**: Design documents from `/specs/001-investigating-neural-synchrony-attention-switching/`  
**Prerequisites**: `plan.md` (required), `spec.md` (required for user stories), `data-model.md`, `contracts/`

---

## Phase 1 – Setup & First End‑to‑End Analysis  

**Goal**: Establish a reproducible project skeleton and basic tooling.  

- [ ] T001 [P] Create directory structure  
  - `projects/PROJ-498-investigating-the-relationship-between-n/`  
  - `projects/PROJ-498-investigating-the-relationship-between-n/code/`  
  - `projects/PROJ-498-investigating-the-relationship-between-n/data/`  
  - `projects/PROJ-498-investigating-the-relationship-between-n/tests/`  
  - **Verification**: All directories exist on the filesystem.

- [ ] T002 [P] Initialise Python 3 project with pinned dependencies in `requirements.txt`  
  - Includes `mne==1.7.0`, `numpy==1.24.3`, `scipy==1.11.0`, `pandas==2.0.0`, `statsmodels==0.14.0`, `scikit-learn==1.3.0`, `pyyaml==6.0.1`, `openneuro-py==2.2.0`, `bids-validator==1.12.0`.  
  - **Verification**: `pip install -r requirements.txt` succeeds without version conflicts.

- [ ] T003 [P] Configure linting/formatting (`black`, `flake8`, `isort`) in the project root.  
  - **Verification**: `black --check .`, `flake8 .`, and `isort --check-only .` all return exit code 0.

- [ ] T004 Implement `code/update_state_hashes.py` to generate SHA‑256 hashes for all pipeline artifacts and write a `state_hashes.json` manifest.  
  - **Verification**: Running the script creates `state_hashes.json` with a non‑empty mapping.

- [ ] T005 Implement `code/config.py` with global paths, random seeds, and hyper‑parameters. Must define:  
  - `primary_window = (-500, 0)`  
  - `sensitivity_windows = [(-600, 0), (-400, 0)]`  
  - **Verification**: Importing `config` yields the two keys with the exact values above.

- [ ] T006 Implement logging infrastructure (`logs/processing.log`) and exclusion tracking (`data/exclusions.csv`).  
  - **Verification**: Log file is created on first write; `exclusions.csv` contains a header row.

- [ ] T007 Create contract `contracts/data_gap_report.schema.yaml` (schema for a Data Gap Report).  
  - **Verification**: `jsonschema` validates a sample report against the schema.

- [ ] T008 Create contracts `contracts/sensitivity_report.schema.yaml` and `contracts/trial_level_analysis.schema.yaml`.  
  - **Verification**: Both schemas load without syntax errors.

---

## Phase 2 – Foundational (Blocking Prerequisites)

**Goal**: Resolve dataset discovery and enforce overall runtime limits before any scientific computation.

- [ ] T010 Implement fallback logic that, when the designated dataset ID cannot be fetched, queries the OpenNeuro API for any dataset containing “task‑switching” events, writes the chosen ID to `data/selected_dataset_id.txt`, and, if **no** valid dataset is found, creates `data/results/data_gap_report.json` (conforming to `contracts/data_gap_report.schema.yaml`) and aborts the pipeline with exit code 1.  
  - **Verification**: Running the script with a bogus ID produces a valid `data_gap_report.json`, logs the failure to `logs/processing.log`, and exits with code 1.

- [ ] T009 Implement `code/download.py` to (1) read `data/selected_dataset_id.txt`, (2) download the identified OpenNeuro dataset into `data/raw/`, (3) generate `data/raw/checksums.json` (SHA‑256 per file), and (4) verify that the checksum manifest exists and matches computed hashes.  
  - **Verification**: After execution, `data/selected_dataset_id.txt` exists, `data/raw/` contains the downloaded BIDS hierarchy, `data/raw/checksums.json` lists a SHA‑256 entry for every file, and a validation step confirms the manifest’s integrity.

- [ ] T011 Implement a global runtime wrapper in `code/main.py` that records start/end timestamps, writes `data/metrics/runtime_log.json` (fields: `start_time`, `end_time`, `total_duration_minutes`, `status`, `passed_6h_limit`), and aborts with a clear error if total wall‑clock time exceeds 6 h.  
  - **Verification**: Simulating a long run (>6 h) triggers the abort and populates `runtime_log.json` with `status: "timeout"` and `passed_6h_limit: false`.

---

## Phase 3 – User Story 1: Preprocess & Epoch Public Task‑Switching EEG Data (Priority P1)

**Goal**: Obtain clean, time‑locked epochs for each subject while respecting memory constraints.

- [ ] T012 Implement the **download step** for raw EEG files using the verified ID written by T009/T010.  
  - Reads `data/selected_dataset_id.txt`, fetches the dataset into `data/raw/`, and updates `data/raw/checksums.json`.  
  - **Verification**: After execution, `data/raw/` contains at least one subject folder and `checksums.json` lists a SHA‑256 entry for every file.

- [ ] T013 Apply a 1‑45 Hz band‑pass filter to all raw recordings (`code/preprocess.py`).  
  - **Verification**: The script writes a config file `data/processed/filter_config.json` containing `"low_cutoff": 1` and `"high_cutoff": 45`; a unit‑test confirms the filtered data’s frequency response matches this range.

- [ ] T042 Enforce a 7 GB RAM limit during preprocessing. The script monitors peak RSS per subject and aborts with exit code 1 if the limit is exceeded, writing `data/metrics/memory_log.json` with `peak_rss_gb` per subject.  
  - **Verification**: After preprocessing, `memory_log.json` exists and all `peak_rss_gb` entries are ≤ 7.0; any violation causes pipeline abort.

- [ ] T014 Apply a notch filter at 60 Hz (or the detected line‑noise frequency) **before** ICA. Log each application to `logs/processing.log` (format: `Notch filter applied at {freq}Hz for subject {id}`).  
  - **Verification**: Log entries appear for every subject where line noise > 0.5 µV; the filtered data is saved to a temporary in‑memory buffer for the subsequent ICA step.

- [ ] T015 Perform ICA decomposition on the band‑passed (and notch‑filtered) data using `mne.preprocessing.ICA(method='infomax', n_components='auto')`.  
  - **Verification**: ICA objects are instantiated for each subject without raising warnings; the fitted ICA is saved as `data/processed/ica_{subject_id}.fif`.

- [ ] T016 Reject ICA components with **kurtosis > 5** or a spectral peak > 30 Hz and write `data/processed/rejected_components.csv` (columns: `component_id`, `kurtosis`, `spectral_peak_freq`).  
  - **Verification**: The CSV exists, contains a header row, and lists any rejected components; if none are rejected, only the header is present.

- [ ] T017 Epoch the cleaned data from **‑1000 ms to +2000 ms** around stimulus onset and write per‑subject epoch files `data/processed/{subject_id}_epoched.fif`.  
  - **Verification**: Each epoch file loads via `mne.read_epochs` and contains the expected number of trials per condition.

- [ ] T018 Exclude subjects that (a) have < 10 valid trials per condition or (b) lose > 50 % of data after ICA rejection. Log exclusions to `data/exclusions.csv` with columns `subject_id`, `reason`, `details`.  
  - **Verification**: `exclusions.csv` contains at least the header and any rows matching the criteria.

- [ ] T019 If **all** subjects are excluded, generate a `data/results/data_gap_report.json` (using the same schema as T010) with `reason: "all_subjects_excluded"` and abort the pipeline with exit code 1.  
  - **Verification**: When no subjects survive, the JSON file is present, the pipeline exits with code 1, and the abort is logged.

- [ ] T020 Save the final clean epochs (`*_epoched.fif`) to `data/processed/` and verify their integrity with a checksum manifest `data/processed/epoch_checksums.json`. Additionally, confirm that `data/results/data_gap_report.json` is created when appropriate (as per T019).  
  - **Verification**: The manifest lists a SHA‑256 for each epoch file; re‑reading any epoch succeeds; presence/absence of `data_gap_report.json` is checked according to exclusion outcome.

- [ ] T040 Record peak RSS during preprocessing and assert it does not exceed 6.5 GB. The script writes `data/metrics/memory_usage.json` with `peak_rss_gb` and fails the pipeline if the limit is breached.  
  - **Verification**: `memory_usage.json` exists and all values ≤ 6.5; pipeline aborts otherwise.

---

## Phase 4 – User Story 2: Compute Pre‑Stimulus Frontoparietal Synchrony Metrics (Priority P2)

**Goal**: Derive wPLI/PLV values for theta and gamma bands in the –500 ms → 0 ms window.

- [ ] T021 Implement electrode‑pair mapping in `code/synchrony.py`:  
  - DLPFC ≈ {F3, F4, FC3, FC4}  
  - Parietal ≈ {P3, P4, CP3, CP4}  
  - Frontoparietal pairs = `F3-P3`, `F3-P4`, `F4-P3`, `F4-P4`.  
  - **Verification**: A function `get_frontoparietal_pairs()` returns the four string identifiers exactly as above.

- [ ] T022 Filter each subject’s epoched data into **theta (4–7 Hz)** and **gamma (30–45 Hz)** bands **within the pre‑stimulus window** (`-500 ms to 0 ms`).  
  - **Verification**: For a test subject, the filtered arrays have the expected shape and frequency content (checked via `scipy.signal.welch`).

- [ ] T023 Compute the **weighted Phase‑Lag Index (wPLI)** for each frontoparietal pair, band, and subject using the standard wPLI formula (MNE implementation). Store results in memory for the next step.  
  - **Verification**: wPLI values lie in [0, 1]; a unit‑test on a synthetic 10 Hz phase‑locked signal yields wPLI ≈ 1.0 ± 0.05.

- [ ] T024 Write synchrony results to `data/metrics/synchrony_metrics.csv` with columns: `subject_id`, `condition` (`switch`/`stay`), `band` (`theta`/`gamma`), `pair_id` (`F3_P3` etc.), `wPLI`, `plv` (optional, may be empty), `mean_wPLI` (average across the four pairs for that subject‑band‑condition). Values are rounded to four decimal places.  
  - **Verification**: CSV contains exactly four rows per subject per band (one per pair) plus an additional summary row per subject‑band; the `band` column contains only the two allowed strings.

- [ ] T025 Enforce a **30‑minute per‑subject wall‑clock limit** for the entire synchrony pipeline (filtering + wPLI). If a subject exceeds this, log `subject_id,reason="synchrony_timeout"` to `data/exclusions.csv` and omit that subject from `synchrony_metrics.csv`.  
  - **Verification**: Timing wrapper writes durations to `data/metrics/synchrony_timing.json`; subjects over the limit are present in `exclusions.csv`.

---

## Phase 5 – User Story 3: Correlate Synchrony with Behavioral Switching Costs (Priority P3)

**Goal**: Produce subject‑level and trial‑level statistical evidence linking neural synchrony to attention‑switching costs.

- [ ] T026 Compute behavioral metrics (mean RT for switch/stay, switching cost, accuracies, trial counts) per subject from `data/raw/` events and write `data/metrics/behavioral_metrics.csv` adhering to `contracts/behavioral_metrics.schema.yaml`.  
  - **Verification**: JSON‑schema validation passes; the CSV contains one row per subject with all required fields.

- [ ] T027 Perform the **primary subject‑level correlation** between each subject’s mean pre‑stimulus wPLI (averaged across pairs) and its switching cost. Use Pearson for normally‑distributed data, otherwise Spearman. Store intermediate vectors in `data/results/subject_corr_input.json`.  
  - **Verification**: Correlation coefficient and raw p‑value are printed to stdout and saved to a temporary JSON.

- [ ] T028 Run a **permutation test** (default = 1000 iterations, fallback = 500 with a logged warning) shuffling the synchrony vector relative to the switching‑cost vector. Record the empirical p‑value.  
  - **Verification**: `data/metrics/permutation_log.json` records `n_permutations` and the empirical p‑value.

- [ ] T029 Apply **Bonferroni correction** for the two frequency bands and write `data/results/correlation_results.json` conforming to `contracts/correlation_results.schema.yaml`. Include both raw and corrected p‑values, the number of permutations, confidence interval (95 %), and an `interpretation` string containing the word “associational”.  
  - **Verification**: Schema validation succeeds; the `interpretation` field contains “associational”.

- [ ] T030 Generate trial‑level dataset `data/trial_level/per_trial_synchrony.csv` linking each trial’s reaction time to its theta and gamma synchrony values (extracted from the same pre‑stimulus window). Rows with missing synchrony are omitted. Schema matches `contracts/synchrony_metrics.schema.yaml` where appropriate.  
  - **Verification**: CSV loads without error; row count equals total valid trials across subjects.

- [ ] T031 Fit a **Linear Mixed‑Effects (LME) model** (`RT ~ synchrony_theta + (1|subject_id)`) using `statsmodels`. Apply Bonferroni correction across the two bands. Write results to `data/results/trial_level_analysis.json` following `contracts/lmm_results.schema.yaml`.  
  - **Verification**: JSON validates; fixed‑effect coefficient for synchrony is present, and the `interpretation` field contains “associational”.

- [ ] T032 Conduct **sensitivity analysis**: repeat the primary correlation for the shifted pre‑stimulus windows `[-600, 0]` and `[-400, 0]`. Store each window’s `r` and `p` in `data/results/sensitivity_raw.json`.  
  - **Verification**: `sensitivity_raw.json` contains entries for `primary`, `shift_-600_0`, and `shift_-400_0`.

- [ ] T033 Compute **sensitivity metrics** (maximum absolute `r` change, whether all shifted `p` < 0.05) and write the final `data/results/sensitivity_report.json` conforming to `contracts/sensitivity_report.schema.yaml`. Include a boolean `stable` flag (True ⇔ `r_change_max < 0.1` **and** all shifted `p` < 0.05).  
  - **Verification**: The JSON validates; `stable` is True for simulated data that meets the criteria.

- [ ] T034 Consolidate final outputs: ensure `data/results/correlation_results.json`, `data/results/trial_level_analysis.json`, and `data/results/sensitivity_report.json` all exist, and generate a short human‑readable `results_summary.md` that explicitly states the findings are **associational** and notes any stability failures from the sensitivity report.  
  - **Verification**: `results_summary.md` contains the word “associational” and mentions the `stable` flag.

- [ ] T035 Add a programmatic assertion in `code/analysis.py` that aborts with exit code 1 if any of the final JSON files or `results_summary.md` lack the required “associational” phrasing. Log the failure to `data/validation_log.txt`.  
  - **Verification**: Running the pipeline with a deliberately malformed summary triggers the abort and writes a clear error line to `validation_log.txt`.

---

## Phase 6 – Reproducible Results & Paper Handoff  

**Goal**: Provide a clean hand‑off for downstream manuscript generation.

- [ ] T036 Implement `code/main.py` orchestrator to run phases sequentially (Setup → Foundational → US1 → US2 → US3) and respect the global runtime wrapper.  
  - **Verification**: `python code/main.py` completes the full pipeline on a small test dataset within the 6‑hour limit and exits with code 0.

- [ ] T037 Update `README.md` (located at the project root) with a **Usage** section that:  
  1. Describes the command `python code/main.py`.  
  2. Explains that the pipeline reads `data/selected_dataset_id.txt` (produced by the dynamic OpenNeuro search).  
  3. Notes that if the file is missing, the README should direct the user to the generated `data_gap_report.json`.  
  - **Verification**: The README contains the three bullet points; no MkDocs build is required.

- [ ] T038 Run `code/update_state_hashes.py` after the full pipeline to refresh `state_hashes.json`.  
  - **Verification**: Manifest timestamps are newer than the previous run.

- [ ] T039 Validate `quickstart.md` by executing its commands in a fresh virtual environment using the script `scripts/validate_quickstart.sh`; ensure all exit codes are 0 and expected artifacts appear.  
  - **Verification**: The CI test invokes `scripts/validate_quickstart.sh` and reports success.

- [ ] T041 Verify CPU‑only execution environment. The script checks that `CUDA_VISIBLE_DEVICES` is unset or empty and that `torch.cuda.is_available()` (if torch is present) returns `False`.  
  - **Verification**: The check passes on the CI runner; any detection of GPU capability aborts with a clear error message.

---

### Dependency & Execution Order Summary  

| Phase | Must complete before | Notes |
|-------|---------------------|-------|
| Phase 1 (Setup) | – | All tasks independent (`[P]`). |
| Phase 2 (Foundational) | Phase 1 | T010 must run before T009; both provide the dataset ID required by downstream tasks. |
| Phase 3 (User Story 1) | Phase 2 | Generates clean epochs and exclusion logs; includes memory‑usage and checksum verification. |
| Phase 4 (User Story 2) | Phase 3 | Requires `data/processed/*_epoched.fif`. |
| Phase 5 (User Story 3) | Phases 3 & 4 | Needs both synchrony metrics and behavioral metrics. |
| Phase 6 (Polish) | All previous phases | Final orchestration, documentation, and CPU‑only verification. |

--- 

*All tasks marked `[P]` may be executed in parallel where their file targets differ. Tasks without `[P]` have explicit data‑flow dependencies and must respect the ordering shown above.* 