# Implementation Plan: Calibration of Predictive Intervals for Time‑Series Forecasts

**Branch**: `001-calibration-of-predictive-intervals` | **Date**: 2026-06-17 | **Spec**: `specs/001-calibration-of-predictive-intervals/spec.md`

## Summary

This feature implements a reproducible benchmarking pipeline to evaluate the calibration of predictive intervals for time-series forecasts. **Execution is conditional**: If the M4 and UCI Electricity datasets are available via their verified canonical sources, the system loads them, trains ARIMA, Prophet, and a lightweight LSTM model on a standardized A standard split (Fit/Cal/Test), and computes empirical coverage, Probability Integral Transform (PIT) histograms, and Continuous Ranked Probability Score (CRPS) metrics. It further performs paired bootstrap tests for statistical significance and applies a Self-Calibrating Conformal Prediction wrapper to assess post-hoc improvements. **If verified sources are missing, the pipeline halts immediately with error code FR-007.**

**Critical Constraint**: Per FR-007, if the required datasets (M4, UCI Electricity) are not available via verified sources, the pipeline MUST fail immediately with a descriptive error. No data substitution (e.g., UCI HAR) is permitted as it invalidates the research question's scope.

**Model Strategy**: For LSTM, the plan includes a diagnostic step (Shapiro-Wilk test) to validate the Gaussian residual assumption. If residuals are non-Gaussian, the system falls back to Empirical CDF (quantile-based) interval generation to ensure valid calibration metrics.

**Critical Constraint**: All analysis runs on CPU-only infrastructure within GitHub Actions free-tier constraints.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `statsmodels` (ARIMA), `prophet` (Prophet), `torch` (CPU-only LSTM), `properscoring` (CRPS), `scikit-learn`, `scipy` (statistical tests), `matplotlib`  
**Storage**: Local file system (`data/` for raw/processed data, `results/` for outputs)  
**Testing**: `pytest` (unit tests for metrics, integration tests for pipeline execution)  
**Target Platform**: Linux (GitHub Actions Free Runner: limited CPU, 7 GB RAM, no GPU)  
**Project Type**: Research pipeline / CLI tool  
**Performance Goals**: Complete full benchmark run on M4 (subset) and UCI Electricity (streamed) within 6 hours.  
**Constraints**: No GPU/CUDA; no large LLMs; memory footprint < 7 GB; sequential processing for multivariate data; strict reproducibility (random seeds).  
**Scale/Scope**: A large-scale collection of time series (M4) processed sequentially

The research question, method, and references remain unchanged as per the planning document requirements.; UCI Electricity processed series-by-series.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Strategy |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Random seeds pinned in `code/`. External datasets fetched via verified URLs. `requirements.txt` pins versions. |
| **II. Verified Accuracy** | **PASS** | All citations in `research.md` mapped to verified dataset URLs. **Hard Fail** if M4/UCI-Elec URLs are missing/unverified (per FR-007). |
| **III. Data Hygiene** | **PASS** | Raw data downloaded to `data/raw/` with checksums. Transformations output to `data/processed/`. No in-place edits. |
| **IV. Single Source of Truth** | **PASS** | All metrics computed by `code/` scripts; results stored in structured CSV/JSON in `results/`. No hand-typed numbers in paper. |
| **V. Versioning Discipline** | **PASS** | Content hashes tracked in `state/`. Artifact updates trigger `updated_at` timestamps. |
| **VI. Calibration Assessment** | **PASS** | Metrics (Coverage, PIT, CRPS) implemented exactly as specified. **Kolmogorov-Smirnov (KS)** test for PIT uniformity (per Constitution). **Self-Calibrating Conformal Wrapper** included and tested. |
| **VII. Standardized Benchmark Splits** | **PASS** | 72/8/20 split logic (Fit/Cal/Test) implemented in `data_loader.py`. Split boundaries recorded in `data/metadata/splits.json`. |

## Project Structure

### Documentation (this feature)

```text
specs/001-calibration-of-predictive-intervals/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── dataset.schema.yaml
    └── output.schema.yaml
```

### Source Code (repository root)

```text
projects/PROJ-713-calibration-of-predictive-intervals-for-/code/
├── __init__.py
├── config.py                # Hyperparams, seeds, paths
├── data_loader.py           # M4/UCI ingestion, 72/8/20 split, streaming
├── models/
│   ├── __init__.py
│   ├── arima_model.py       # statsmodels wrapper
│   ├── prophet_model.py     # prophet wrapper
│   └── lstm_model.py        # torch CPU-only implementation
├── metrics/
│   ├── __init__.py
│   ├── coverage.py          # Empirical coverage calc
│   ├── pit.py               # PIT histogram & KS test
│   └── crps.py              # CRPS calculation
├── calibration/
│   ├── __init__.py
│   └── conformal.py         # Self-Calibrating Conformal wrapper
├── evaluation/
│   ├── __init__.py
│   ├── bootstrap_test.py    # Paired bootstrap significance (Series-level)
│   └── runner.py            # Main orchestration loop
└── utils/
    ├── logger.py
    └── exceptions.py

tests/
├── unit/
│   └── test_metrics.py
├── integration/
│   └── test_pipeline.py
└── contract/
    └── test_schema_validation.py
```

**Structure Decision**: Single project structure selected. The research nature of the feature requires tight coupling between data loading, model training, and metric evaluation. Separation into `models`, `metrics`, and `calibration` modules ensures testability and modularity while maintaining a linear execution flow suitable for CPU-only CI.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Streaming Data Loader** | UCI Electricity is multivariate and large; loading all at once exceeds 7 GB RAM on free runners. | Loading full dataset into memory would cause OOM crashes on CI. |
| **Three Distinct Models** | Spec requires comparison of ARIMA, Prophet, and LSTM to cover classical, hybrid, and deep learning approaches. | Using only one model would fail to address the core research question of relative calibration performance. |
| **Conformal Wrapper** | Required to test post-hoc correction (US-3). | Skipping this would leave the "improvement" hypothesis untested. |
| **Bootstrap Significance** | Required for statistical rigor (US-3) beyond descriptive metrics. | Simple t-tests are invalid for time-series dependent errors; bootstrap is necessary. |
| **Hard-Fail on Missing Data** | FR-007 requires immediate failure if data is missing/unverified. | Substituting UCI HAR would invalidate the research question (different statistical properties). |
| **Conditional Interval Generation** | LSTM residuals may be non-Gaussian; standard Gaussian intervals would yield invalid calibration metrics. | Assuming Gaussian residuals without validation risks false negatives on calibration quality. |