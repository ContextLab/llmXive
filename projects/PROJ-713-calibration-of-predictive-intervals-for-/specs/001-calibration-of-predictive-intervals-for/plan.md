# Implementation Plan: Calibration of Predictive Intervals for Time‑Series Forecasts

**Branch**: `001-calibration-of-predictive-intervals` | **Date**: 2026-10-12 | **Spec**: `specs/001-calibration-of-predictive-intervals/spec.md`  
**Input**: Feature specification from `/specs/001-calibration-of-predictive-intervals/spec.md`

## 0 – Project Setup & Governance

| Task | Description | Notes |
|------|-------------|-------|
| **T001a** | Create `code/` directory (writable, idempotent) | Ensured by repository scaffold. |
| **T001b** | Create `tests/` directory (writable, idempotent) |  |
| **T001c** | Create `data/raw/` directory (writable, idempotent) |  |
| **T001d** | Create `data/processed/` directory (writable, idempotent) |  |
| **T001e** | Create `results/` directory (writable, idempotent) |  |
| **T000a** | **Verified‑Dataset‑Check** – abort if required URLs are not listed in the verified‑datasets block. | Blocks execution early if datasets are not verified. |
| **T040** | **Governance Gate** – external amendment process for the Constitution (if ever needed). Not a code dependency; execution proceeds regardless. | Marked as *Governance* (outside the computational DAG). |

## 1 – Data Acquisition & Verification

| Task | Description |
|------|-------------|
| **T000** | Download M4 and UCI Electricity archives from canonical URLs (listed in `code/config.yaml`). |
| **T009** | Compute SHA‑256 checksums for each downloaded file and verify against known values (recorded in `state/dataset_hashes.yaml`). |
| **T010** | Extract archives (e.g., unzip) into `data/raw/` preserving original folder structure. |
| **T011** | Stream series using `datasets.load_dataset(..., streaming=True)` or custom HTTP streaming; no full‑dataset load into RAM. |

## 2 – Sampling & Splitting

| Task | Description |
|------|-------------|
| **T012** | Stratified sampling of a sufficiently large set of series (balanced across frequencies for M4 and load‑profile types for UCI). |
| **T013** | Train‑test split: first [deferred] → training, last [deferred] → test; record split metadata in `data/processed/split_metadata.json`. |
| **T014** | Standardize training values to zero mean / unit variance; apply same parameters to test set. |

## 3 – Model Training (Baseline)

| Task | Description |
|------|-------------|
| **T015** | Fit ARIMA (`statsmodels.tsa.arima.model.ARIMA`, order (1,1,1)). |
| **T016** | Fit Prophet (`prophet.Prophet`, default seasonalities, `uncertainty_samples=1000`). |
| **T017** | Fit LSTM (PyTorch CPU, 1 hidden layer, 32 units, max 50 epochs, early stopping patience = 5). |
| **T018** | **Edge‑Case Handling** – For series with constant variance or LSTM numerical instability: log `series_id` to `results/skipped_series.log` and **skip** them for primary metric computation. If LSTM produces `NaN/Inf` intervals, retry up to 2 times with reduced learning rate; after failure, log and skip. No fallback model replaces the primary LSTM result. |

## 4 – Predictive Interval Generation

| Task | Description |
|------|-------------|
| **T019** | ARIMA: generate 0.80 and 0.95 intervals via conditional variance (Gaussian assumption). |
| **T020** | Prophet: generate intervals from `uncertainty_samples` (empirical quantiles). |
| **T021** | LSTM: obtain point forecasts; compute residuals on training set; assume Gaussian residuals to form intervals. If residuals are non‑Gaussian (Shapiro‑Wilk p < 0.05), **log a warning** and still use Gaussian approximation (for logging only). |

## 5 – Metric Computation

| Task | Description |
|------|-------------|
| **T022** | Empirical coverage for nominal levels 0.80 & 0.95. |
| **T023** | Compute PIT values; **primary** uniformity test = Kolmogorov–Smirnov (KS) (satisfies Constitution VI). **Secondary** diagnostic = Ljung‑Box test (reported but not a primary decision criterion). |
| **T024** | Compute CRPS using `properscoring.crps_ensemble`. |
| **T025** | Write `results/coverage.csv`, `results/distributional_metrics.csv`. |

## 6 – Statistical Significance

| Task | Description |
|------|-------------|
| **T026** | Paired bootstrap (1000 resamples) at the *series* level for each pair of models; report p‑values (α = 0.05) in `results/significance_test.csv`. |

## 7 – Conformal Post‑hoc Calibration

| Task | Description |
|------|-------------|
| **T027** | Apply Self‑Calibrating Conformal Prediction (SCCP) wrapper to each baseline model. |
| **T028** | Re‑compute coverage, PIT, CRPS after SCCP; write `results/conformal_results.csv`. |

## 8 – Sensitivity & Bias Analysis

| Task | Description |
|------|-------------|
| **T023b** | Quantify impact of excluded series: recompute aggregate metrics including skipped series by imputing Gaussian intervals (for diagnostic purposes only) and compare to primary results. Report bias magnitude; raise a warning if bias > 1 % of the metric. |

## 9 – Aggregation & Reporting

| Task | Description |
|------|-------------|
| **T029** | Consolidate all CSVs into summary tables and generate plots (coverage bar plots, PIT histograms, CRPS boxplots). |
| **T030** | Write `results/benchmark_timing.csv` (stage runtimes) and `results/skipped_series.log`. |
| **T031** | Validate all CSV outputs against contracts (`coverage.schema.yaml`, `distributional_metrics.schema.yaml`, `significance_test.schema.yaml`, `output.schema.yaml`) using a JSON‑Schema validator. |

## 10 – Governance & Documentation

| Task | Description |
|------|-------------|
| **T040** | (Governance) Draft amendment to Constitution VI if a future decision replaces KS with Ljung‑Box. This task does **not** block any code execution; it is a separate governance gate. |

## Compute Strategy
- **CPU‑First**: All models run on CPU; LSTM is small enough for the free runner. No GPU escape hatch required.
- **Streaming** ensures memory ≤ 4 GB even for full datasets.

## Data Availability & Fallback
- **Verified‑Dataset‑Check** aborts if URLs are missing from the verified‑datasets block. No synthetic data is fabricated.
- **Extraction** step (T010) handles archive structures; the checksum step (T009) validates the whole archive before extraction.

## Edge‑Case Handling Summary
- Constant‑variance or failed LSTM series are **logged and excluded** from primary metrics.
- Fallback to Gaussian residual intervals is **only for logging**; primary results remain based on the fitted model.
- Sensitivity analysis (T023b) evaluates any bias introduced by these exclusions.

## Limitations & Risks
| Risk | Impact | Mitigation |
|------|--------|------------|
| Dataset URLs not verified | Pipeline aborts | T000a ensures early failure with clear message. |
| LSTM instability | Skipped series | Retry with reduced LR; log and skip; sensitivity analysis quantifies bias. |
| Power limitation | May miss tiny effects | Sample size (≈ 500) chosen via pilot power analysis (≥ 80 % power for ≥ 3 % differences). |
| Constitution vs Spec conflict | KS vs Ljung‑Box | KS remains primary per Constitution VI; Ljung‑Box reported as secondary. |
| Governance amendment (T040) | Potential future change | Treated as external gate; does not affect current execution. |

---  

## Constitution Check
| Principle | Requirement | Plan Alignment |
|-----------|-------------|----------------|
| **I. Reproducibility** | Fixed seeds; deterministic fetch | Seeds pinned in `code/config.yaml`; checksum verification ensures identical inputs. |
| **II. Verified Accuracy** | All citations verified | Pre‑run verification (T000a) checks dataset URLs against verified list. |
| **III. Data Hygiene** | Checksums; no in‑place mutation | `T009` records SHA‑256; transformations write new files under `data/processed/`. |
| **IV. Single Source of Truth** | Figures & stats trace to one row | Metrics written to CSVs; plots generated directly from these files. |
| **V. Versioning Discipline** | Content hashes tracked | `state/` YAML (not shown) updated with hashes after each run. |
| **VI. Calibration Assessment** | Empirical coverage, PIT (KS), CRPS, bootstrap, conformal | KS test is primary (Constitution VI); Ljung‑Box secondary; all other metrics implemented as listed. |
| **VII. Standardized Benchmark Splits** | [deferred] train / [deferred] test recorded | Implemented in `T013`; metadata saved to `data/processed/split_metadata.json`. |
