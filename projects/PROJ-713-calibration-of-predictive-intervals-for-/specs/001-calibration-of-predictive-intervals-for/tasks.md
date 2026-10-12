# Tasks: Calibration of Predictive Intervals for Time‑Series Forecasts

**Inputs**: `spec.md`, `plan.md`, data‑model definitions, and contract schemas in `specs/001‑calibration‑of‑predictive‑intervals‑for/`.

The following checklist implements the smallest complete study that satisfies every functional requirement, provides an early end‑to‑end result, and includes the necessary validation artefacts.  
Unchecked items are pending implementation or revision; checked items have been verified to meet their specification.

---

## Phase 1 – Project setup & basic infrastructure  

| Goal | Create the required directory tree and confirm write‑access. |
|------|-------------------------------------------------------------|

- [ ] **T001a** [P] Create `code/` directory (idempotent).  
  *Verification*: Run `python -c "import pathlib, os; p=pathlib.Path('code'); p.mkdir(parents=True, exist_ok=True); assert p.is_dir() and os.access(p, os.W_OK)"`.  

- [ ] **T001b** [P] Create `tests/` directory (idempotent).  
  *Verification*: Same script as T001a with path `tests/`.  

- [ ] **T001c** [P] Create `data/raw/` directory (idempotent).  
  *Verification*: Same script as T001a with path `data/raw/`.  

- [ ] **T001d** [P] Create `data/processed/` directory (idempotent).  
  *Verification*: Same script as T001a with path `data/processed/`.  

- [ ] **T001e** [P] Create `results/` directory (idempotent).  
  *Verification*: Same script as T001a with path `results/`.  

- [ ] **T001f** [P] Define canonical paths in `code/config.yaml` (keys `paths.code`, `paths.tests`, `paths.data_raw`, `paths.data_processed`, `paths.results`).  
  *Verification*: `yaml.safe_load` of the file contains all five keys with correct relative values.

---

## Phase 2 – Data acquisition & verification  

| Goal | Download real benchmark datasets, verify integrity, and make them available via streaming loaders. |
|------|-----------------------------------------------------------------------------------------------|

- [ ] **T000** [P] Implement `code/data/fetcher.py` to:  
  * Download **M4** from `[UNRESOLVED-CLAIM: https://github.com/monash-university-forecasting/m4-competition/raw/master/M4-Competition.zip` — HTTP 404].  
  * Download **UCI Electricity** from `[UNRESOLVED-CLAIM: https://archive.ics.uci.edu/static/public/321/electricity.zip` — HTTP 404].  
  * Verify SHA‑256 checksums against official values stored in `code/config.yaml`; any mismatch must raise `SystemExit(1)`.  
  * Extract archives to `data/raw/m4/` and `data/raw/uci/`.  
  * **Verification**: After execution, `data/raw/m4/m4-train.csv` and `data/raw/uci/electricity.csv` must exist; a checksum mismatch aborts with a clear error code.

- [ ] **T009** [P] Implement `code/utils/checksum.py::verify_checksums(data_dir: str) -> bool` that reads a manifest `code/config.yaml` and raises `ValueError` on any mismatch. Tested by unit tests in `tests/unit/test_checksum.py`.

- [ ] **T006a** [P] Implement `code/data_loader.py` with streaming support (`datasets.load_dataset(..., streaming=True)`) for both M4 and UCI, returning objects that conform to the `TimeSeries` schema.  
  * **Verification**: `code/data_loader.py` returns a `TimeSeries` object that validates against `dataset.schema.yaml`.

- [ ] **T006b** [P] Implement `code/data/sampler.py::stratified_sampler` to select a balanced subset (≈ 500 series) across frequencies/load‑profile types; sampler writes the selected IDs to `data/processed/sample_ids.json`.

- [ ] **T006c** [P] Add variable validation in `code/data_loader.py`; if required `timestamp` or `value` variables are missing, the pipeline MUST abort immediately with `SystemExit(1)` and error code `ERR_DATA_001`.

- [ ] **T012** [P] Implement `code/data/splitter.py` to:  
  * Split each series into training (first 80%) and test (last 20%) windows.  
  * Standardize training values to zero mean and unit variance; apply the same parameters to the test set.  
  * Record exact split boundaries and standardization parameters in `data/processed/split_metadata.json`.  
  * **Verification**: `data/processed/split_metadata.json` contains the `split_index` for every sampled series, and test values are standardized using training parameters.

---

## Phase 3 – User Story 1: Empirical coverage assessment (P1)  

| Goal | Fit baseline models, generate 0.80/0.95 predictive intervals, and compute empirical coverage. |
|------|-----------------------------------------------------------------------------------------------|

- [ ] **T013** [US1] Implement `code/models/arima_model.py` (Statsmodels ARIMA(1,1,1) wrapper) with Gaussian interval generation via conditional variance; includes convergence‑failure handling.  
  * **Verification**: Unit test fits ARIMA on a synthetic series and asserts that the returned predictive intervals have the correct shape and the script exits with status 0.

- [ ] **T014** [US1] Implement `code/models/prophet_model.py` (Prophet wrapper) that uses `uncertainty_samples=1000` and residual simulation to produce 0.80/0.95 quantiles.  
  * **Verification**: Unit test runs the Prophet wrapper on a known series and asserts that the generated 0.80/0.95 quantiles match expected values within tolerance.

- [ ] **T015** [US1] Implement `code/models/lstm_model.py` (PyTorch CPU):  
  * Architecture: single hidden layer, 32 units, max 50 epochs, early stopping patience = 5.  
  * On failure to produce finite interval bounds, retry up to **2** times with a reduced learning rate (×0.5).  
  * After exhausting retries, **log** the series ID, model name, and failure reason to `results/skipped_series.log` (JSON line per failure) and **skip** the series for LSTM metrics.  
  * **Verification**: Presence of `results/skipped_series.log` with correctly formatted JSON entries; the LSTM runner must exit with status 0 even when a series is skipped.

- [ ] **T016** [US1] Implement `code/metrics/coverage.py` that computes empirical coverage for nominal levels 0.80 and 0.95 and writes rows to `results/coverage.csv` adhering to `coverage.schema.yaml`.

- [ ] **T017** [US1] Create `code/evaluation/runner_single_coverage.py`: command‑line interface `python -m code.evaluation.runner_single_coverage --series-id <ID> --model <ARIMA|Prophet|LSTM>`.  
  * Outputs a **single JSON object** with keys `coverage_0.80` and `coverage_0.95` (float).  
  * **Verification**: Running the script on a known test series produces a valid JSON file; schema matches the two‑key requirement (no extra fields).

- [ ] **T018** [US1 & US2] Implement the **full pipeline** `code/evaluation/runner.py`:  
  * Invokes global data‑validation routine via `code/data_loader.py`; aborts with `ERR_DATA_001` if variables are missing.  
  * Streams each selected series, fits ARIMA, Prophet, and LSTM (using the retry logic of T015).  
  * Generates predictive intervals (0.80 & 0.95) and computes:  
    - Empirical coverage (writes `results/coverage.csv`).  
    - PIT values and **both** Kolmogorov–Smirnov (Constitution VI) and Ljung‑Box (Spec Primary) p‑values (writes `results/distributional_metrics.csv`).  
    - CRPS scores (same CSV).  
  * Aggregates all rows, treating Ljung‑Box as the primary calibration metric for the spec while ensuring KS is reported for the Constitution.  
  * Logs per‑series failures to `results/skipped_series.log`.  
  * **Verification**: After execution, `results/coverage.csv` and `results/distributional_metrics.csv` exist, contain >0 rows, and pass JSON‑Schema validation against `coverage.schema.yaml` and `distributional_metrics.schema.yaml`.

---

## Phase 4 – User Story 2: Distributional calibration (P2)  

| Goal | Produce PIT histograms, perform uniformity tests, and compute CRPS. |
|------|---------------------------------------------------------------------|

- [ ] **T021** [US2] Implement `code/metrics/pit.py`: computes PIT values, builds histogram bin counts, and runs **Ljung‑Box** (primary for Spec) and **Kolmogorov–Smirnov** (required by Constitution) tests, returning both p‑values and histogram data.  
  * **Verification**: Unit test computes PIT on a synthetic uniform forecast and asserts the KS p‑value is > 0.5.

- [ ] **T022** [US2] Implement `code/metrics/crps.py` using `properscoring.crps_ensemble`.  
  * **Verification**: Unit test compares the CRPS output against a known reference implementation on a small ensemble.

---

## Phase 5 – User Story 3: Significance testing & conformal calibration (P3)  

| Goal | Assess statistical significance of calibration differences and evaluate a conformal post‑hoc wrapper. |
|------|----------------------------------------------------------------------------------------------------------|

- [ ] **T031a** [US3] Implement `code/evaluation/bootstrap_test.py`: paired bootstrap (1000 resamples) at the *series* level for any two models, comparing a chosen metric (e.g., `coverage_deviation`). Writes rows to `results/significance_test.csv` following `significance_test.schema.yaml`.

- [ ] **T031b** [US3] Implement `code/calibration/conformal_orchestrator.py`:  
  * Wraps any baseline model with the **Self‑Calibrating Conformal Prediction** (SCCP) algorithm.  
  * Adjusts the nominal level `α` based on empirical coverage on a calibration set.  
  * Produces calibrated predictive intervals, then recomputes coverage, PIT, and CRPS.  
  * Writes `results/conformal_results.csv` with columns `series_id`, `model`, `nominal_level`, `empirical_coverage_before`, `empirical_coverage_after`, and `improvement_delta`.  
  * **Verification**: The CSV exists, contains all required columns, and `improvement_delta = after – before` is numeric for every row.

- [ ] **T032** [US3] Implement `code/evaluation/aggregator.py` to consolidate results from `coverage.csv`, `distributional_metrics.csv`, and `significance_test.csv` into a final aggregated report `results/output.csv` conforming to `output.schema.yaml`.  
  * **Verification**: `results/output.csv` exists and passes JSON-Schema validation against `output.schema.yaml`.

- [ ] **T031** [US3] Create `code/evaluation/significance_orchestrator.py`:  
  * Reads `results/coverage.csv`, `results/distributional_metrics.csv`, and `results/conformal_results.csv`.  
  * Executes `bootstrap_test.py` (T031a) for each model pair and metric, and aggregates conformal improvement statistics.  
  * Writes final `results/significance_test.csv` (if not already produced) and updates `results/conformal_results.csv` with a `is_significant` flag per series.  
  * **Verification**: After a full run, both CSVs exist, schema‑validate, and at least one `is_significant` field is `true` when appropriate.

---

## Phase 6 – Edge‑case handling & quality checks  

| Goal | Ensure robustness to pathological series and verify test coverage. |
|------|--------------------------------------------------------------------|

- [ ] **T036** [P] Implement `tests/unit/test_edge_cases.py` that:  
  * Verifies ARIMA and LSTM **skip** series with zero variance (asserts log entry appears in `results/skipped_series.log`).  
  * Verifies that NaN/Inf interval bounds from LSTM trigger the retry logic and, after two failed attempts, produce a log entry in `results/skipped_series.log`.  
  * **Verification**: Running `pytest -q tests/unit/test_edge_cases.py` yields all tests passing.

- [ ] **T035a** [P] Run the pipeline on a small subset (10 series) via `python -m code.evaluation.runner --subset 10`.  
  * Must finish within **10 minutes** on the default CPU runner.  
  * **Verification**: Run `time python -m code.evaluation.runner --subset 10` and assert `real duration ≤ 600s`; also assert that `results/coverage.csv` contains 10 × 3 = 30 rows (3 models).

- [ ] **T034c** [P] Audit all source files to replace any hard‑coded filesystem paths with references to `code/config.yaml`.  
  * **Verification**: Grep for literal strings like `"data/raw"` or `"results/"` and confirm none remain outside of configuration loading.

---

## Phase 7 – Documentation & handoff  

| Goal | Provide a concise methods/results description and a reproducible handoff for the paper pipeline. |
|------|-----------------------------------------------------------------------------------------------|

- [ ] **T007** [US*] Write `quickstart.md` at the repository root describing:  
  * Required environment (`pip install -r code/requirements.txt`).  
  * How to run the full pipeline (`python -m code.evaluation.runner`).  
  * Expected artefacts (`results/coverage.csv`, `results/distributional_metrics.csv`, `results/significance_test.csv`, `results/conformal_results.csv`, `results/output.csv`).  
  * **Verification**: The file exists and the commands execute without error on a fresh clone.

- [ ] **T008** [US*] Create a short methods/results markdown (`paper/summary.md`) that links each reported metric to the exact row(s) in the CSV files (e.g., “empirical coverage for ARIMA on series M4‑1001 = 0.78 (see `results/coverage.csv` line 42)”).  
  * **Verification**: The file contains at least one explicit reference per metric type and can be rendered without broken links.

---

### Dependency & execution order summary  

| Phase | Must complete before |
|-------|----------------------|
| 1 – Setup | – |
| 2 – Data acquisition | Phase 1 |
| 3 – US 1 (coverage) | Phase 2 |
| 4 – US 2 (distributional) | Phase 2 (Integrated into Phase 3 via T018) |
| 5 – US 3 (significance + conformal) | Phases 3 & 4 (needs coverage & PIT/CRPS outputs) |
| 6 – Edge‑case tests | After the corresponding model implementations (T015, T018) |
| 7 – Documentation | After all result files are generated |

---  

*All tasks marked `[P]` can run in parallel as long as their file dependencies are respected.*