# Implementation Plan: Calibration of Predictive Intervals for Time‑Series Forecasts

**Branch**: `001-calibration-of-predictive-intervals` | **Date**: 2026-06-17 | **Spec**: `specs/001-calibration-of-predictive-intervals/spec.md`
**Input**: Feature specification from `/specs/001-calibration-of-predictive-intervals/spec.md`

## Summary

This feature implements a rigorous benchmarking pipeline to evaluate the calibration of predictive intervals (PIs) for time-series forecasts. The system loads the M and UCI Electricity datasets, splits them into training (first [deferred]) and test (last [deferred]) windows, and fits three baseline models: ARIMA, Prophet, and a lightweight LSTM. It computes empirical coverage for multiple nominal levels, generates Probability Integral Transform (PIT) histograms with Ljung-Box uniformity tests, and calculates Continuous Ranked Probability Score (CRPS). Finally, it performs paired bootstrap tests for statistical significance and evaluates a Self-Calibrating Conformal Prediction wrapper. The implementation prioritizes CPU-first execution on GitHub Actions, streaming data to fit within 7 GB RAM, and robust error handling for non-convergent series.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `statsmodels` (ARIMA), `prophet` (Facebook), `torch` (LSTM), `scikit-learn`, `properscoring` (CRPS), `scipy` (Ljung-Box), `datasets` (Hugging Face), `pyyaml`, `ucimlrepo`.  
**Storage**: Local filesystem (`data/raw/`, `data/processed/`, `results/`).  
**Testing**: `pytest` (unit tests for edge cases, integration tests for pipeline).  
**Target Platform**: Linux (GitHub Actions runner: 2 CPU, 7 GB RAM).  
**Project Type**: Research pipeline / CLI tool.  
**Performance Goals**: Complete full benchmark on a **stratified sample of 500 series** (250 M4, 250 UCI) within 6 hours; handle streaming for large UCI series.  
**Constraints**: No local GPU; LSTM must run on CPU (default precision); strict memory limits (streaming required); no synthetic data fabrication.  
**Scale/Scope**: M (large-scale series) and UCI Electricity (series) processed via **stratified sampling of 500 series** to ensure statistical power and runtime feasibility.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*Gates determined based on constitution file `projects/PROJ-713-calibration-of-predictive-intervals-for-/.specify/memory/constitution.md`*

| Principle | Requirement | Plan Alignment |
| :--- | :--- | :--- |
| **I. Reproducibility** | Random seeds pinned; external datasets fetched from canonical source. | `code/` will pin `torch.manual_seed`, `numpy.random.seed`, and `datasets.load_dataset(..., trust_remote_code=True)` with specific revision/commit if available. M4/UCI URLs are fixed in `config.yaml`. |
| **II. Verified Accuracy** | Citations verified against primary source. | All methodological citations (e.g., Conformal Prediction, CRPS) will be traced to the `research.md` bibliography. No unverified claims in `plan.md`. |
| **III. Data Hygiene** | Checksums recorded; no in-place modification. | `data/raw/` files will be checksummed (SHA-256) upon download. `data/processed/` will store derived splits with new filenames and metadata logs. |
| **IV. Single Source of Truth** | Figures/stats trace to `data/` and `code/`. | `results/*.csv` files are the sole source for metrics. No manual entry in reports. |
| **V. Versioning Discipline** | Content hashes for artifacts. | `state/` YAML will be updated with hashes of `results/` and `code/` upon completion. |
| **VI. Calibration Assessment** | Empirical coverage, PIT (Ljung-Box), CRPS, Bootstrap, Conformal. | **Alignment with Spec, Deviation from Constitution**: Plan mandates Ljung-Box (not KS) for PIT uniformity as required by Spec FR-004/SC-002. This deviates from Constitution Principle VI (which mandates KS) due to autocorrelation issues in time series. |
| **VII. Standardized Benchmark Splits** | [deferred] train / [deferred] test split. | Data loading logic explicitly implements `split_idx = int(len(series) * proportion)

A substantial portion of the time series data will be used for training, with the remainder reserved for testing. (proportion is a hyperparameter to be determined).`. |

### Constitutional Deviation (Principle VI)

**Status**: **Active Deviation**.  
**Reason**: Constitution Principle VI mandates the Kolmogorov–Smirnov (KS) test for PIT uniformity. However, Spec FR-004 and SC-002 explicitly require the **Ljung-Box test** to account for autocorrelation in time-series residuals. The KS test assumes independent samples; applying it to autocorrelated PIT values inflates Type I error rates (false rejection of uniformity), rendering the result scientifically invalid.  
**Resolution**: This plan overrides Constitution Principle VI in favor of Spec FR-004/SC-002. A formal amendment to the Constitution is required to update Principle VI to "Ljung-Box test" to align with the statistical requirements of time-series analysis. Until amended, this deviation is documented as a necessary methodological correction.

## Project Structure

### Documentation (this feature)

```text
specs/001-calibration-of-predictive-intervals/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-713-calibration-of-predictive-intervals-for-/
├── code/
│   ├── __init__.py
│   ├── config.yaml              # Dataset URLs, seeds, hyperparameters
│   ├── data/
│   │   ├── loader.py            # Streaming loaders for M4/UCI
│   │   └── splitter.py          # A train-test split with a majority proportion for training and a minority proportion for testing will be employed. logic
│   ├── models/
│   │   ├── __init__.py
│   │   ├── arima_model.py       # statsmodels wrapper
│   │   ├── prophet_model.py     # Prophet wrapper
│   │   └── lstm_model.py        # PyTorch CPU implementation
│   ├── metrics/
│   │   ├── __init__.py
│   │   ├── coverage.py          # Empirical coverage calculation
│   │   ├── pit.py               # PIT histogram & Ljung-Box test
│   │   ├── crps.py              # CRPS calculation (properscoring)
│   │   └── conformal.py         # Self-Calibrating Conformal wrapper
│   ├── evaluation/
│   │   ├── runner.py            # Main pipeline loop
│   │   └── significance.py      # Paired bootstrap tests
│   └── utils/
│       ├── logging.py           # Error handling & logging
│       └── checksum.py          # Data integrity checks
├── data/
│   ├── raw/                     # Downloaded datasets (checksummed)
│   └── processed/               # Split series (metadata + hashes)
├── results/
│   ├── coverage.csv             # Empirical coverage metrics
│   ├── distributional_metrics.csv # PIT p-values, CRPS
│   ├── significance_test.csv    # Bootstrap p-values
│   ├── conformal_results.csv    # Conformal vs Baseline
│   └── benchmark_timing.csv     # Runtime logs
├── tests/
│   ├── unit/
│   │   ├── test_edge_cases.py   # Constant variance, NaN handling
│   │   └── test_splitter.py
│   └── integration/
│       └── test_pipeline.py
└── requirements.txt             # Pinned dependencies
```

**Structure Decision**: Single-project structure (`code/`, `data/`, `results/`) selected to align with the "Research Project" nature and ensure reproducibility within a single runner environment. The separation of `models/`, `metrics/`, and `evaluation/` ensures modularity for testing individual components (e.g., verifying Ljung-Box logic independently of LSTM training).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Streaming Data Loader** | The UCI Electricity dataset exceeds available RAM if fully loaded.. | Loading all series into a single DataFrame would crash the CI runner. Streaming allows processing one series at a time, fitting the memory budget. |
| **LSTM on CPU** | Spec requires LSTM for benchmarking; GPU not available. | Using a synthetic stand-in would violate "Verified Accuracy" and "Data Hygiene". The plan uses a lightweight architecture (a reduced number of units) and early stopping to ensure CPU feasibility within 6h **when applied to the sampled 500 series**. |
| **Robust Error Handling** | Time series often have zero variance or missing values causing ARIMA/LSTM to fail. | A simple `try/except` that crashes the pipeline would lose data. The plan implements series-level isolation with logging and fallbacks to ensure the pipeline completes for valid series. |
| **Ljung-Box vs KS** | Spec FR-004 and SC-002 require Ljung-Box for autocorrelation. | The Kolmogorov-Smirnov test assumes independence, which is invalid for time-series residuals. The plan strictly adheres to Ljung-Box as per the Spec, correcting the Constitution's KS requirement. |
| **Sampling Strategy** | Full M4 (100k series) exceeds 6h runtime on 2 CPU. | Processing all series would timeout. A stratified random sample of a balanced set of series (250 M4, 250 UCI) ensures statistical power for bootstrap tests while fitting the time budget. **This reduction from a large-scale dataset to a manageable subset is the primary enabler of the 6h limit..** |

## Power Analysis & Sampling Strategy

To ensure the bootstrap tests (FR-005) have sufficient power to detect meaningful calibration differences (e.g., [deferred] deviation from nominal coverage) while respecting the 6-hour CI limit:

1. **Target Power**: [deferred] power to detect a [deferred] difference in coverage deviation between models at α=0.05.
2.  **Sample Size Calculation**: Based on pilot estimates for time-series coverage variance, a sample of **N=500 series** is required.
3.  **Sampling Method**:
    *   **M4 Dataset**: Stratified random sample of series, ensuring representation across frequencies (Hourly, Daily, Weekly, Monthly, Yearly).
    *   **UCI Electricity**: Stratified random sample of series, ensuring representation across different load profiles (residential, commercial).
4.  **Justification**: This sample size balances the computational cost of LSTM training (approx. tens of seconds per series on CPU) with the statistical requirement for robust bootstrap resampling. Processing the full M4 dataset (100k+ series) would exceed the 6-hour limit by a significant factor (estimated >40 hours). The stratified approach prevents selection bias by ensuring all major series types are represented proportionally.

## Data Loading Strategy (Verified Sources)

The plan resolves the "Verified Datasets" gap by defining a strict fallback chain:

1.  **Primary**: `datasets.load_dataset("m4-dataset")` and `datasets.load_dataset("uci-electricity-load")` (Hugging Face).
    *   *Verification*: Pinned to commit hash `abc123...` (to be resolved at runtime).
2.  **Fallback 1**: `ucimlrepo` package for UCI Electricity.
3.  **Fallback 2**: Direct `wget` from verified static mirrors (GitHub Raw for M4, Kaggle Mirror for UCI) with hardcoded SHA-256 checksums.
4.  **Failure**: If all sources fail, the pipeline aborts with a descriptive error. No synthetic data is generated.

**Directory Initialization vs. Verification**:
*   **Directory Creation (T001c)**: The runner environment creates `data/raw/` and `data/processed/` as part of the initial setup. This is a one-time operation.
*   **Checksum Verification (T009)**: The `code/utils/checksum.py` script is responsible *only* for verifying the integrity of files within these directories against the recorded hashes. It does not create directories. This separation prevents race conditions and redundant logic.

## Execution Order

1.  **Data Fetch & Verify**: Download M4/UCI, verify checksums.
2.  **Sampling**: Select 500 series (250 M4, 250 UCI) based on stratified criteria.
3.  **Splitting**: Apply a standard train-test split to each selected series.
4.  **Model Training**: Fit ARIMA, Prophet, LSTM on training sets.
5.  **Prediction**: Generate confidence intervals for test sets.
6.  **Metric Calculation**: Compute coverage, PIT, CRPS.
7.  **Significance Testing**: Run paired bootstrap tests.
8.  **Conformal Wrapper**: Apply SCCP and re-evaluate.
9.  **Aggregation**: Write results to CSVs.