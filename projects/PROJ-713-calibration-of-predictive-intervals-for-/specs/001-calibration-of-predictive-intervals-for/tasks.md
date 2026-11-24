# Tasks: Calibration of Predictive Intervals for Time‑Series Forecasts  

**Inputs**: `spec.md`, `plan.md`, data‑model definitions, and contract schemas in `specs/001‑calibration‑of‑predictive‑intervals‑for/`.  

The checklist implements the smallest complete study that satisfies every functional requirement, provides an early end‑to‑end result, and includes all necessary validation artefacts.  
Unchecked items are pending implementation or revision; checked items have been verified to meet the specification.

---  

## Phase 1 – Project setup & basic infrastructure  

| Goal | Create required writable directories and a central configuration file. |
|------|-----------------------------------------------------------------------|

- [ ] T001a [P] Create `code/` directory (idempotent).  
  *Verification*: Run a Python script that creates the directory with `parents=True, exist_ok=True` and asserts `os.access('code', os.W_OK)`.

- [X] T001b [P] Create `tests/` directory (idempotent).  
  *Verification*: Same script as T001a with path `tests/`.

- [X] T001c [P] Create `data/raw/` directory (idempotent).  
  *Verification*: Same script as T001a with path `data/raw/`.

- [X] T001d [P] Create `data/processed/` directory (idempotent).  
  *Verification*: Same script as T001a with path `data/processed/`.

- [X] T001e [P] Create `results/` directory (idempotent).  
  *Verification*: Same script as T001a with path `results/`.

- [ ] T001f [P] Add `code/config.yaml` defining canonical paths (`paths.code`, `paths.tests`, `paths.data_raw`, `paths.data_processed`, `paths.results`).
  *Verification*: Load the YAML and assert all five keys exist and point to existing directories.

- [ ] T001g [P] Test idempotent creation of `code/` (run script twice, assert no error).  
- [ ] T001h [P] Test idempotent creation of `tests/` (run script twice, assert no error).  
- [ ] T001i [P] Test idempotent creation of `data/raw/` (run script twice, assert no error).  
- [ ] T001j [P] Test idempotent creation of `data/processed/` (run script twice, assert no error).  
- [ ] T001k [P] Test idempotent creation of `results/` (run script twice, assert no error).

---

## Phase 2 – Data acquisition & verification  

| Goal | Download real benchmark datasets, verify integrity, and provide a streaming loader. |
|------|------------------------------------------------------------------------------------|

- [ ] T000 [P] Implement `code/data/fetcher.py` to download **M4** (`[UNRESOLVED-CLAIM: https://github.com/M4Competition/m4-methodology/raw/master/Dataset/M4-data.zip` — HTTP 404]) and **UCI Electricity** (`[UNRESOLVED-CLAIM: https://archive.ics.uci.edu/static/public/321/electricity.zip` — HTTP 404]).  
  *Verification*: After execution, `data/raw/m4/` contains `M4-data.csv` and `data/raw/uci/` contains `electricity.csv`; SHA‑256 checksums match values stored in `code/config.yaml`. Errors abort with a non‑zero exit code and a clear message.

- [ ] T009 [P] Implement `code/utils/checksum.py::verify_checksums(data_dir: str) -> bool` that reads the manifest in `code/config.yaml` and raises `ValueError` on any mismatch.  
  *Verification*: Unit test in `tests/unit/test_checksum.py` creates a temporary file with a known hash and asserts the function returns `True` for a matching manifest and raises for a mismatch.

- [ ] T006a [P] Implement `code/data/loader.py` using `datasets.load_dataset(..., streaming=True)` to stream M4 and UCI series, yielding objects that conform to the `TimeSeries` schema (`specs/…/dataset.schema.yaml`).  
  *Verification*: A sanity‑check script loads the first streamed series and validates it with `jsonschema.validate`.

- [ ] T006c [P] Add variable validation inside `loader.py`; if a series lacks required `timestamp` or `value` fields, abort with `SystemExit(1)` and error code `ERR_DATA_001`.  
  *Verification*: Unit test feeds a malformed series and expects the process to exit with the specified code.

- [ ] T012 [P] Implement `code/data/splitter.py` to:  
  * split each series into the first **80 %** (training) and last **20 %** (test) windows;  
  * standardize training values to zero mean / unit variance and apply the same parameters to the test set;  
  * write split metadata for every sampled series to `data/processed/split_metadata.json`.  
  *Verification*: The JSON contains `series_id`, `split_index`, `train_mean`, `train_std`; a downstream script can reconstruct the test set using only the metadata and confirms the standardized test mean ≈ 0.

- [ ] T017 [P] Create `data/processed/sample_ids.json` listing the IDs of all series selected for the main pipeline (produced by `code/data/splitter.py`).  
  *Verification*: File exists, is valid JSON array, and each ID matches a series present in `data/processed/split_metadata.json`.

---

## Phase 3 – Baseline model implementations (User Story 1)  

| Goal | Fit ARIMA, Prophet, and LSTM; generate 0.80/0.95 predictive intervals; handle edge cases. |
|------|-------------------------------------------------------------------------------------------|

- [ ] T013 [US1] Implement `code/models/arima_model.py` wrapping `statsmodels.tsa.arima.model.ARIMA(order=(1,1,1))`.  
  * Generates Gaussian predictive intervals for the 0.80 and 0.95 nominal levels using the conditional variance.  
  * On non‑convergence, logs the `series_id` to `results/skipped_series.log` and returns `None`.  
  *Verification*: Unit test fits the model on a synthetic random walk and asserts interval arrays of shape `(horizon, 2)` are returned; a forced convergence failure creates a log entry.

- [ ] T014 [US1] Implement `code/models/prophet_model.py` that fits `prophet.Prophet()` and uses `model.predictive_samples(n=1000)` to obtain empirical quantiles for the required nominal levels.  
  *Verification*: Test on a short sinusoidal series checks that the 0.80 quantile lies between the 0.10 and 0.90 empirical quantiles.

- [ ] T015 [US1] Implement `code/models/lstm_model.py` (PyTorch CPU) with:  
  * Architecture: single hidden layer, 32 units;  
  * Training: max 50 epochs, early stopping patience = 5, learning rate = 1e‑3;  
  * Retry logic: if any interval bound is `NaN`/`Inf`, halve the learning rate and retry up to **2** times; after the final failure, write a JSON‑line to `results/skipped_series.log` (`{ "series_id": "...", "model": "LSTM", "reason": "numerical instability" }`).  
  *Verification*: Integration test forces a NaN by injecting `torch.nan` into the loss; asserts that after two retries a log entry appears and the script exits with status 0.

- [ ] T016 [US1] Create `code/metrics/coverage.py` that:  
  * receives predictive intervals and true test values;  
  * computes empirical coverage for nominal levels 0.80 and 0.95;  
  * writes rows to `results/coverage.csv` conforming to `coverage.schema.yaml`.  
  *Verification*: Run on a tiny synthetic series and compare the CSV row to a hand‑calculated coverage; schema validation passes.

- [ ] T019 [US1] Verify that each model outputs both 0.80 and 0.95 predictive intervals and that the interval files contain finite numeric bounds.  
  *Verification*: Script loads the interval objects for a sample series, checks shape `(horizon, 2)` and that `np.isfinite` holds for all entries; logs any violations to `results/interval_verification.log`.

---

## Phase 4 – Distributional calibration (User Story 2)  

| Goal | Compute PIT histograms, Ljung‑Box & KS tests, and CRPS scores. |
|------|-----------------------------------------------------------------|

- [ ] T021 [US2] Implement `code/metrics/pit.py` that:  
  * computes PIT values for each horizon;  
  * builds a histogram (e.g., 10 bins) and stores counts;  
  * runs **Ljung‑Box** test as the **primary** uniformity assessment (p‑value reported as `pit_p_value_lb`), and **Kolmogorov–Smirnov** as a secondary diagnostic (`pit_p_value_ks`);  
  * writes results to `results/distributional_metrics.csv` with columns `pit_p_value_ks`, `pit_p_value_lb`, `crps_score`.  
  *Verification*: Unit test on a perfectly calibrated Gaussian forecast expects both p‑values > 0.5.

- [ ] T022 [US2] Implement `code/metrics/crps.py` using `properscoring.crps_ensemble`.  
  *Verification*: Compare CRPS on a known deterministic forecast against a reference value; difference < 1e‑6.

---

## Phase 5 – Full end‑to‑end pipeline (integrates US 1 & 2)  

| Goal | Validate data, fit all models, compute all metrics, and write required CSVs. |
|------|--------------------------------------------------------------------------------|

- [ ] T018 Implement `code/evaluation/runner.py` (CLI entry point `python -m code.evaluation.runner`). It must:  
  1. Invoke the global data‑validation routine from `code/data/loader.py`; abort with `ERR_DATA_001` if required fields are missing.  
  2. Stream the sampled series (as defined by `data/processed/sample_ids.json`).  
  3. For each series, run ARIMA, Prophet, and LSTM (using the retry logic of T015).  
  4. Generate 0.80/0.95 predictive intervals.  
  5. Compute empirical coverage (T016), PIT & Ljung‑Box/KS (T021), and CRPS (T022).  
  6. Append rows to `results/coverage.csv` and `results/distributional_metrics.csv`.  
  7. Log any skipped series to `results/skipped_series.log`.  
  *Verification*: After a full run on a modest subset (e.g., 20 series), both CSV files exist, contain **≤ 20 × 3 = 60** coverage rows (allowing for skipped series), and pass JSON‑Schema validation against their respective schemas.

---

## Phase 6 – Statistical significance & conformal post‑hoc calibration (User Story 3)  

| Goal | Paired bootstrap tests and Self‑Calibrating Conformal Prediction (SCCP) wrapper. |
|------|------------------------------------------------------------------------------------|

- [ ] T031a [US3] Implement `code/evaluation/bootstrap_test.py` that:  
  * performs a paired bootstrap with **1000** resamples at the *series* level for any two models;  
  * compares a chosen metric (e.g., `coverage_deviation`).  
  * writes results to `results/significance_test.csv` adhering to `significance_test.schema.yaml`.  
  *Verification*: Run on synthetic paired data where the true difference is zero; the output p‑value distribution is uniform and the CSV validates.

- [ ] T031b [US3] Implement `code/calibration/conformal_orchestrator.py` that:  
  * wraps a baseline model with the **Self‑Calibrating Conformal Prediction** algorithm (SCCP);  
  * uses a calibration subset (first 60 % of the training window) to adjust interval widths;  
  * recomputes coverage, PIT, and CRPS on the hold‑out test set;  
  * writes `results/conformal_results.csv` with columns `series_id`, `model`, `nominal_level`, `empirical_coverage_before`, `empirical_coverage_after`, `improvement_delta`.  
  *Verification*: After running on a small subset, the CSV exists, contains the required columns, and `improvement_delta` equals `after - before` for every row.

- [ ] T032 [US3] Implement `code/evaluation/aggregator.py` that merges `coverage.csv`, `distributional_metrics.csv`, `significance_test.csv`, and `conformal_results.csv` into a single aggregated file `results/output.csv` matching `output.schema.yaml`.  
  *Verification*: Schema validation succeeds; the file includes the `is_significant` flag derived from the bootstrap p‑value.

---

## Phase 7 – Edge‑case handling & quality‑assurance tests  

| Goal | Verify robustness to pathological series and confirm test coverage. |
|------|---------------------------------------------------------------------|

- [ ] T036 [P] Add unit tests in `tests/unit/test_edge_cases.py` that:  
  * confirm ARIMA and LSTM **skip** series with zero variance (log entry appears in `results/skipped_series.log`);  
  * confirm NaN/Inf interval bounds from LSTM trigger the retry logic and, after two failures, produce a correctly formatted JSON line in the log;  
  * run the full suite with `pytest -q` and expect **0** failures.  
  *Verification*: CI run reports “0 failed, 0 errors”.

- [ ] T035a Run the pipeline on a tiny subset (`python -m code.evaluation.runner --subset 10`).  
  *Must finish within 10 minutes on the default CPU runner.*  
  *Verification*: Capture execution time; assert `real ≤ 600s`; assert `results/coverage.csv` contains exactly `10 × 3 = 30` rows (or fewer if skips occur, which is acceptable).

---

## Phase 8 – Documentation & hand‑off  

| Goal | Provide reproducible usage instructions and a concise methods/results summary. |
|------|---------------------------------------------------------------------------------|

- [ ] T007 [US*] Write `quickstart.md` at the repository root describing:  
  * environment setup (`pip install -r code/requirements.txt`);  
  * how to run the full pipeline (`python -m code.evaluation.runner`);  
  * expected artefacts (`results/coverage.csv`, `results/distributional_metrics.csv`, `results/significance_test.csv`, `results/conformal_results.csv`, `results/output.csv`).  
  *Verification*: The file exists and a fresh clone can execute the described commands without modification.

- [ ] T008 [US*] Create `paper/summary.md` that links each reported metric to the exact row(s) in the CSV files (e.g., “ARIMA coverage on series M4‑1001 = 0.78 (see `results/coverage.csv` line 42)”).  
  *Verification*: The markdown contains at least one reference for coverage, PIT, CRPS, and bootstrap significance; all referenced line numbers are within the corresponding CSVs.

---  

## Phase 9 – Governance amendment (Constitution VI)  

| Goal | Align the Constitution’s primary calibration metric with the specification. |
|------|-----------------------------------------------------------------------------|

- [ ] T040 [Governance] Document the need to keep Kolmogorov–Smirnov as a secondary diagnostic and Ljung‑Box as the primary PIT test in future amendment proposals (no direct edit to `constitution.md`).  
  *Verification*: Task produces a `governance/notes.md` file summarizing the proposed amendment without modifying the Constitution file.

---  

### Dependency & execution order summary  

| Phase | Must complete before |
|-------|----------------------|
| 1 – Setup | – |
| 2 – Data acquisition | Phase 1 |
| 3 – Model implementations | Phase 2 |
| 4 – Metric computation | Phase 3 |
| 5 – Full pipeline | Phases 2 & 3 (needs data & models) |
| 6 – Significance & conformal | Phase 5 (needs coverage & PIT/CRPS) |
| 7 – Edge‑case tests | Phases 3 & 5 (models & runner) |
| 8 – Documentation | Phase 6 (results must exist) |
| 9 – Governance | Independent of code but should be completed before final verification |

---  

*All tasks marked `[P]` may run in parallel as long as their file‑dependency constraints are respected.*  