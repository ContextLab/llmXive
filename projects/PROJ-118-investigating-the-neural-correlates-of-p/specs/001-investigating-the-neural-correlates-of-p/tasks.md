# Tasks: Investigating the Neural Response to Deviance in Auditory Perception

**Inputs**: `spec.md`, `plan.md`, contracts, and any existing artifacts.  
All tasks are expressed as checklist items following the canonical format.  
Each task lists the functional requirement(s) it satisfies, the concrete output
path(s), and the verification step(s) that the verifier will run.

---

## Phase 0 – Data acquisition

- [ ] T001 [FR-001] **Download OpenNeuro ds003645**  
  *Implementation*: `code/download.py` uses `wget` (or `curl`) with up‑to‑3 retries  
  (10 s back‑off) to fetch the BIDS‑structured dataset into `data/raw/`.  
  *Verification*:  
  – Presence of the expected directory tree under `data/raw/`.  
  – SHA‑256 checksum file `data/checksums.txt` matches each downloaded file
    (raised as an error on mismatch).

---

## Phase 1 – Preprocessing (raw → clean epochs)

- [ ] T002 [FR-001b] [FR-002] **Channel subsampling, band‑pass filtering, and re‑referencing**  
  *Implementation*: `code/preprocess.py` loads each raw file, keeps the standard
  montage (Fz, FCz, Cz, Pz, …), applies a 1–30 Hz FIR filter, and re‑references
  to the common average. Output saved as `data/processed/subsampled_raw.fif`.  
  *Verification*:  
  – File exists and contains only the specified channels (checked via schema).  
  – Filter parameters recorded in `code/config.yaml`.

- [ ] T004 [FR-003] **ICA blink‑component detection & removal**   <!-- FAILED-IN-EXECUTION: code/preprocess.py exit=1 -->
  *Implementation*: `code/preprocess.py` runs ICA on the subsampled continuous data,
  computes correlation of each component with frontal channels (Fz, FCz);
  removes components with correlation > 0.8 or frontal topography.  
  *Outputs*: cleaned continuous file `data/processed/subsampled_clean.fif` and log
  `data/processed/ica_removed.log` (listing removed component indices).  
  *Verification*:  
  – Cleaned file exists; log file present.

- [ ] T014 [FR-003] [CONTRACT-dataset] **Verify ICA variance reduction**  
  *Implementation*: Re‑compute variance on frontal channels before and after ICA;
  assert ≥ 10 % reduction. Logs result to `results/verification/ica_variance.log`.  
  *Verification*: Pass/fail log is examined by the verifier.

- [ ] T003 [FR-002] **Epoching into “standard” and “deviant” (-200 ms → 600 ms)**  
  *Implementation*: `code/preprocess.py` reads the ICA‑cleaned continuous file,
  creates MNE Epochs objects for each condition and writes `data/processed/epo_clean.fif`.  
  *Verification*:  
  – Epoch file present; each epoch labeled correctly; time window matches
    specification.

- [ ] T005 [SC-001] **Participant exclusion for excessive artifact rejection**  
  *Implementation*: After ICA and epoching, count rejected trials per participant; if > 50 % of trials are rejected, mark the participant as excluded.  
  *Outputs*: exclusion list `data/processed/rejected_participants.log` and filtered epochs file `data/processed/epo_clean_excluded.fif`.  
  *Verification*:  
  – Log file exists; number of excluded participants matches the count in the
    final statistics (`outlier_count`).

- [ ] T015 [CONTRACT-dataset] **Validate processed epoch files against dataset.schema.yaml**  
  *Implementation*: Script `code/validate_dataset.py` checks each epoch file against the JSON schema located at `specs/001-investigating-the-neural-correlates-of-p/contracts/dataset.schema.yaml`.  
  *Verification*: Validation report written to `results/validation/dataset_validation.log`; verifier ensures no schema violations.

---

## Phase 2 – Feature extraction (clean epochs → metrics)

- [ ] T006 [FR-004] **Compute standard, deviant, and difference‑wave ERPs**  
  *Implementation*: `code/extract.py` averages epochs per condition for each
  participant, computes the difference wave (Deviant − Standard), and writes:  
    - `data/processed/std_erp.fif`  
    - `data/processed/dev_erp.fif`  
    - `data/processed/diff_wave.fif`  
  *Verification*:  
  – All three files exist; dimensions match the schema for `EEG Dataset`.

- [ ] T007 [FR-004] [SC-005] **Peak detection, SNR, and metric CSV generation**  
  *Implementation*: `code/extract.py` scans the difference wave at electrodes
  Fz and FCz for the most negative peak within the primary window (150–250 ms)
  and, if absent, the fallback window (100–300 ms). A peak is accepted only
  if its amplitude ≤ ‑2.0 µV. For each participant the script records:  
    - `amplitude` (µV)  
    - `latency` (ms)  
    - `peak_detected` (bool)  
    - `peak_window` (“primary”, “fallback”, or null)  
    - `snr` (signal‑to‑noise ratio)  
    - `is_excluded` (from T005)  
  It also computes standard and deviant amplitudes/latencies (columns
  `standard_amplitude`, `standard_latency`, `deviant_amplitude`,
  `deviant_latency`).  
  *Output*: `results/metrics.csv` conforming to `mmn_metrics.schema.yaml`.  
  *Verification*:  
  – CSV header contains all required columns; rows validate against the schema.

- [ ] T016 [CONTRACT-mmn_metrics] **Validate metrics CSV against mmn_metrics.schema.yaml**  
  *Implementation*: `code/validate_metrics.py` runs JSON‑schema validation on
  `results/metrics.csv`.  
  *Verification*: Validation log written to `results/validation/metrics_validation.log`.

---

## Phase 3 – Statistical analysis & robustness checks

- [ ] T008 [FR-005] **Primary paired‑sample tests & FDR correction**  
  *Implementation*: `code/stats.py` loads `results/metrics.csv`, filters out
  excluded participants and those without a detected peak, then performs:  
    - Paired t‑test (or Wilcoxon if Shapiro‑Wilk normality fails) for
      amplitude and latency at Fz and FCz (4 comparisons).  
    - Benjamini‑Hochberg FDR correction across the four p‑values.  
    - Cohen’s d and 95 % confidence intervals for each comparison.  
  *Output*: `results/statistics.json` (conforms to `contracts/results.schema.yaml`).  
  *Verification*:  
  – JSON file present; contains required fields for each electrode/metric.

- [ ] T009 [FR-006] **Cluster‑based permutation test & mixed‑effects model**  
  *Implementation*:  
    - Cluster‑based permutation (1000 permutations) over the full time‑course
      at fronto‑central electrodes, result stored as `cluster_p` in the JSON.  
    - Linear mixed‑effects model (`statsmodels` or `pingouin`) with `condition`
      as fixed effect and `subject` as random effect; p‑value stored as
      `mixed_effects_p`.  
  *Verification*:  
  – `results/statistics.json` now includes `cluster_p` and `mixed_effects_p`.

- [ ] T017 [CONTRACT-results] **Validate statistics.json against results.schema.yaml**  
  *Implementation*: `code/validate_statistics.py` validates `results/statistics.json`.  
  *Verification*: Validation log `results/validation/statistics_validation.log`.

- [ ] T018 [CONTRACT-stats_report] **Validate stats report against stats_report.schema.yaml**  
  *Implementation*: After generating a human‑readable report (`results/stats_report.json`), `code/validate_stats_report.py` checks it against the schema.  
  *Verification*: Validation log `results/validation/stats_report_validation.log`.

- [ ] T010 [SC-002] **Statistical significance gate & prevalence check**  
  *Implementation*: After T008/T009, a verification step asserts that the
  FDR‑corrected p‑value for the most significant amplitude comparison (e.g.,
  Fz) is < 0.05. It also computes the proportion of participants with
  `peak_detected=True` and asserts ≥ 0.80 (per SC‑005).  
  *Verification*:  
  – Pipeline fails with a clear error message if either condition is not met.

---

## Phase 4 – Visualization

- [ ] T011 [FR-007] **Grand‑average ERP plots & topographic maps**  
  *Implementation*: `code/viz.py` creates:  
    - `results/plots/erp_grand_average.png` (standard, deviant, and difference
      wave with shaded 95 % confidence intervals).  
    - `results/plots/topomap_Fz_FCz.png` (difference‑wave topomap at the
      group‑average peak latency).  
  *Verification*:  
  – Both PNG files exist; figure titles and axis labels match the specification.

- [ ] T019 [SC-004] **Measure total pipeline runtime and enforce ≤6 h**  
  *Implementation*: Wrapper script `code/run_pipeline.py` records wall‑clock time
  from start of T001 to completion of T011, writes duration to
  `results/runtime.log`, and aborts with an error if > 6 hours.  
  *Verification*: Verifier checks `results/runtime.log` for compliance.

---

## Phase 5 – Verification artifacts, testing, and documentation

- [ ] T012 [FR-001] [SC-004] **Dataset integrity, ICA variance, and latency‑prevalence verification**  
  *Implementation*:  
    - Compute SHA‑256 checksums for every file in `data/raw/` → `data/checksums.txt`.  
    - Re‑compute frontal‑channel variance before and after ICA; assert ≥ 10 %
      reduction (also performed in T014).  
    - Calculate the proportion of participants whose peak latency falls within
      the primary (150–250 ms) or fallback (100–300 ms) window; assert ≥ 0.80.  
  *Verification*:  
  – All three checks produce a pass/fail log `results/verification.log`.

- [ ] T013 [FR-001] **Integration & unit test suite, CI configuration, and documentation**  
  *Implementation*:  
    - Add `tests/unit/` and `tests/integration/` with pytest suites covering
      data loading, preprocessing, extraction, FDR correction, and
      visualization.  
    - Create `.pre-commit-config.yaml` (black & flake8 hooks) and
      `code/env.example` (optional `OPENNEURO_API_KEY` and data‑path vars).  
    - Provide `tests/conftest.py` exposing fixtures for raw, processed, and
      result paths.  
    - Update `README.md` and `specs/001-investigating-the-neural-correlates-of-p/quickstart.md`
      with the exact runnable command (see T020).  
    - Write `specs/001-investigating-the-neural-correlates-of-p/research_summary.md`
      linking each statistic in `results/statistics.json` and each figure in
      `results/plots/` to the corresponding artifact.  
  *Verification*:  
    – `pytest -q` runs with all tests passing.  
    – CI config files exist and are non‑empty.  
    – README and quickstart contain the command and list all output artifacts.  
    – `research_summary.md` references only real artifact filenames; every
      numeric value is copied verbatim from the JSON/CSV files.

- [ ] T020 [FR-001] **Create/Update quickstart.md with runnable command**  
  *Implementation*: Generates `specs/001-investigating-the-neural-correlates-of-p/quickstart.md` containing:  

  ```bash
  python -m code.download && \
  python -m code.preprocess && \
  python -m code.extract && \
  python -m code.stats && \
  python -m code.viz
  ```  

  *Verification*:  
  – File exists; command executes without error on a fresh runner.

--- 

**Note**: All tasks respect data‑flow ordering; a task that consumes a file
appears after the task that produces that file. Parallel‑safe `[P]` flags have
been removed from tasks that write to shared locations to avoid race conditions.  
