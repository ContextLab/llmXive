# Implementation Plan: Statistical Analysis of Flight Delay Distributions

**Branch**: `001-flight-delay-distributions` | **Date**: 2024-05-22 | **Spec**: `specs/001-flight-delay-distributions/spec.md`
**Input**: Feature specification from `specs/001-flight-delay-distributions/spec.md`

## Summary

This feature implements a statistical analysis pipeline to determine if flight delay times follow heavy-tailed distributions. The system downloads Bureau of Transportation Statistics (BTS) On-Time Performance data, preprocesses it to handle zero-inflation and anomalies, fits five parametric distributions (Exponential, Gamma, Log-Normal, Weibull, Pareto), and performs rigorous heavy-tail diagnostics (Hill estimator, log-log survival plots, Vuong tests). The output includes a comparative ranking of models, tail index estimates, and visual diagnostics, all constrained to run on a CPU-only CI environment with ≤7 GB RAM. The methodology strictly adheres to Clauset et al. standards for power-law testing, utilizing bootstrap-based Goodness-of-Fit (GoF) tests rather than arbitrary R² thresholds.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scipy`, `matplotlib`, `seaborn`, `pyyaml`, `statsmodels`  
**Storage**: Local filesystem (CSV/Parquet input, JSON/CSV/Plots output)  
**Testing**: `pytest`  
**Target Platform**: Linux (GitHub Actions Free Tier)  
**Project Type**: Computational Research Pipeline  
**Performance Goals**: Complete full analysis within 6 hours; peak memory ≤ 6.5 GB.  
**Constraints**: No GPU usage; no external API calls beyond verified dataset sources; strict handling of memory limits (fail gracefully if exceeded).  
**Scale/Scope**: Single year of US commercial flight data (large-scale records, requiring chunked processing or memory-mapping).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Strategy | Status |
| :--- | :--- | :--- |
| **I. Reproducibility** | All random seeds pinned in `code/`. Data fetched from canonical BTS endpoint (verified in research.md). Environment pinned in `requirements.txt`. | **Compliant** |
| **II. Verified Accuracy** | Citations in `research.md` restricted to the "Verified datasets" block. The BTS endpoint is explicitly designated as the verified source for the full year. | **Compliant** |
| **III. Data Hygiene** | Raw data checksums recorded in `state/`. Transformations produce new files (e.g., `cleaned_delays.csv`). No in-place edits. | **Compliant** |
| **IV. Single Source of Truth** | All figures/stats trace to `data/` rows and `code/` blocks. No hand-typed numbers in paper. | **Compliant** |
| **V. Versioning Discipline** | Artifacts hashed; `updated_at` timestamps managed by agent. | **Compliant** |
| **VI. Statistical Model Transparency** | Full parameter estimates, GOF stats (AIC, BIC, KS, AD), and diagnostics (QQ-plots, tail overlays, Bootstrap GoF p-values) stored in `code/` and referenced. | **Compliant** |
| **VII. Source Authenticity** | BTS data sourced from the official BTS endpoint (verified). Checksums recorded. | **Compliant** |

## Project Structure

### Documentation (this feature)

```text
specs/001-flight-delay-distributions/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── tail-index-estimate.schema.yaml
│   ├── fitted_model.schema.yaml
│   └── delay_record.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── config.py            # Paths, seeds, thresholds
├── data_loader.py       # BTS download, chunking, filtering
├── preprocessing.py     # Zero-inflation, anomaly flags, memory checks
├── models.py            # Distribution fitting (MLE), GOF metrics
├── diagnostics.py       # Hill estimator, x_min selection, tail plots, Bootstrap GoF
├── visualization.py     # Log-log, QQ-plots, histograms
├── utils.py             # Memory monitoring, error handling
└── main.py              # Orchestration script

tests/
├── contract/
│   └── test_schemas.py
├── integration/
│   └── test_pipeline.py
└── unit/
    ├── test_preprocessing.py
    └── test_models.py

data/
├── raw/                 # Downloaded BTS files (checksummed)
├── processed/           # Cleaned CSVs, subsets (zeros excluded)
└── results/             # JSON reports, plots, stability curves
```

**Structure Decision**: Single project structure selected to maintain tight coupling between data loading, processing, and analysis. The `code/` directory contains modular scripts for each stage of the pipeline, ensuring testability and reproducibility.

## Phase Breakdown

### Phase 0: Data Acquisition & Pre-processing (FR-001, FR-002, US-1)
1.  **Download**: Fetch BTS data for the specified year from the **official BTS endpoint** (designated as the verified source). Handle network errors gracefully (retry with backoff). If the full-year data is not available or the download fails permanently, **fail immediately** with exit code 1 and message "Data Availability Error: Full year data not found." No silent fallback to test samples.
2.  **Memory Check**: Estimate memory usage; if > 6.5 GB, abort with clear error.
3.  **Clean**: Filter for US commercial flights. Compute `total_delay = ArrDelay + DepDelay`. Treat missing as 0. Remove negatives.
4.  **Flagging**: Mark `is_anomaly` (>1440 min) and `is_data_error` (>10,000 min). Exclude errors from primary analysis but keep for sensitivity.
5.  **Sensitivity**: Create subset excluding zeros for tail fitting.
6.  **Output**: `cleaned_delays.csv`, `summary_report.json` (initial).
7.  **Retention Rate Calculation**: Calculate `retention_rate = valid_records / total_downloaded`. Report in `summary_report.json`.
8.  **Retention Gate**: **Hard Check**: If `retention_rate < 0.95`, halt pipeline with exit code 1 and message "Retention Rate Failure: < 95%". This is a pre-condition for Phase 1.

### Phase 1: Model Fitting & Evaluation (FR-003, FR-004, FR-009, US-2)
1.  **Fit (Full Data)**: Apply MLE for Exponential, Gamma, Log-Normal, Weibull, Pareto on the full cleaned dataset (excluding data errors) to get initial rankings.
2.  **Fit (Tail Subset)**: For the **Vuong Test**, refit **ALL** candidate distributions **exclusively** on the tail subset (x >= x_min).
    *   *Note*: Pareto fitting is restricted to `delay >= x_min`.
    *   *Note*: Short-tail models (Exponential, Gamma) are refitted on the tail subset to ensure likelihood comparability.
3.  **Metrics**: Compute AIC, BIC, KS, AD for all models on the tail subset.
4.  **Select Best**: Identify the best heavy-tail and best short-tail model based on **tail-AIC** (lowest AIC on the tail subset).
5.  **Vuong Test**: Perform Vuong test comparing the best heavy-tail candidate vs. best short-tail candidate using the **tail subset likelihoods**. Report p-value.
6.  **Component Comparison**: KS test and histograms for sum vs. components. Explicitly report the **p-value** in the output JSON.
7.  **Output**: `model_comparison.json`, `vuong_test_results.json`, `component_comparison.json`.

### Phase 2: Heavy-Tail Diagnostics (FR-005, FR-006, FR-010, FR-011, FR-014, FR-015, US-3)
1.  **Threshold (x_min)**: Estimate `x_min` via KS minimization on the tail subset.
    *   **Bootstrap Uncertainty**: Perform a sufficient number of bootstrap iterations to estimate the uncertainty of `x_min`.. Report confidence intervals (2.5th/97.5th percentiles).
2.  **Hill Estimator**: Compute tail index on top `k` records.
    *   *Constraint*: **Explicitly enforce** `k/n <= 0.1` during the stability analysis.
    *   *Method*: Minimize variance of alpha estimates over sliding window `w=10`.
    *   *Output*: Save full stability curve (variance vs k) as CSV; report summary stats (min_k, max_k, variance_min) in JSON.
3.  **Visuals**: Generate log-log survival plot (with R² calculation for visualization only) and QQ-plots.
4.  **Bootstrap GoF Test (Validation Gate)**:
    *   Perform a formal Goodness-of-Fit test using the **Bootstrap Method** (Clauset et al.).
    *   Generate a set of synthetic datasets from the fitted model.
    *   Compute KS statistic for each synthetic dataset.
    *   Compare the empirical KS to the synthetic distribution to derive a **p-value**.
    *   **Rejection Rule**: Reject the model if `p < 0.1`. **Do not use R² as a pass/fail gate.**
5.  **Tail KS Test**: Perform KS test on the tail subset using the **bootstrapped p-value correction** for the data-driven threshold (generate a representative set of synthetic datasets, estimate x_min for each, fit model, compute KS, compare empirical KS to this distribution).
6.  **Log-Normal Discrimination**:
    *   Calculate the **curvature statistic** of the Hill plot.
    *   Simulate multiple Log-Normal datasets with similar parameters.
    *   Calculate curvature for each simulated dataset.
    *   Compare empirical curvature to the null distribution.
    *   **Rejection Rule**: If the empirical curvature is not significantly different from the Log-Normal null (p > 0.05), the hypothesis of a pure Power-Law is rejected in favor of a Log-Normal heavy tail.
7.  **Validation**: If the best model fails the Bootstrap GoF test or Log-Normal Discrimination, flag the next best candidate and report the failure reason.
8.  **Output**: `tail_diagnostics.json`, `plots/` directory, `stability_curve.csv`.

### Phase 3: Reporting & Schema Generation (FR-016, SC-001..SC-011)
1.  **Schema**: Generate `TailIndexEstimate` JSON schema (saved as a YAML file).
2.  **Report**: Compile final summary with all metrics, p-values, and visual references.
3.  **Causal Framing**:
    *   Add `causality_disclaimer` field to the summary JSON: "Findings are associational only; data is observational."
    *   Add `causality_flag: true` to all model comparison tables.
    *   Ensure plot captions include "Associational Analysis" text.
4.  **Validation Checks**:
    *   **SC-001**: Verify `retention_rate >= 0.95` (already enforced in Phase 0).
    *   **SC-005**: Measure `total_runtime_seconds`. If > 3600, set `sc_005_result: "FAIL"`, else `"PASS"`. Include this in the summary JSON.
    *   **SC-009**: Ensure `stability_range` (min_k, max_k, variance_min) is reported.
    *   **SC-011**: Ensure `tail_ks_pvalue` is reported.
5.  **Output**: `summary_report.json` (final), `contracts/` updated.

## Compute Feasibility Strategy
-   **Memory**: Use `pandas` with `dtype` optimization (e.g., `float32`, `category` for carriers). Implement **Streaming Analysis**:
    -   Data is processed in chunks for histogram generation and initial filtering.
    -   For the final fitted dataset, use **memory-mapped arrays (memmap)** to avoid loading the entire ~M row dataset into RAM at once.
    -   If the filtered dataset still exceeds 6.5 GB, the pipeline will process the tail estimation in chunks or use a subsample for the Hill estimator (with a note on reduced power), but will not crash.
-   **CPU**: All `scipy` and `numpy` operations are CPU-bound. No GPU libraries used.
-   **Time**: MLE fitting for multiple distributions on a large-scale dataset is computationally intensive. We will limit the Hill estimator stability search to a small window and use vectorized operations. A hard timeout of 3500 seconds is implemented in `main.py`. If exceeded, the pipeline logs a warning and exits with `sc_005_result: "FAIL"`.
