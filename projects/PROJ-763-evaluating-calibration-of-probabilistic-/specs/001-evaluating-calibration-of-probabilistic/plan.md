# Implementation Plan: Evaluating Calibration of Probabilistic Weather Forecasts

**Branch**: `001-evaluating-calibration-weather` | **Date**: 2026-06-22 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-evaluating-calibration-weather/spec.md`

## Summary

This project implements a rigorous statistical pipeline to evaluate and recalibrate probabilistic weather forecasts. The primary requirement is to quantify mis-calibration in raw NOAA GFS ensemble forecasts using Brier scores, CRPS, and reliability diagrams, then apply two post-processing methods: non-parametric Isotonic Regression and a Bayesian Hierarchical Logistic Regression model. The technical approach prioritizes CPU feasibility on GitHub Actions by streaming data, using quantized or small-scale MCMC, and enforcing strict fallback mechanisms.

**Critical Data Note**: The plan explicitly addresses the lack of a verified public dataset with `probability_value` fields. If no such dataset is found, the pipeline halts with a "Data Unavailability Report" or revises the scope to binary event calibration (if `ensemble_members` are available to derive probabilities).

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `pandas`, `numpy`, `scikit-learn` (isotonic), `pymc` (Bayesian), `properscoring` (CRPS/Brier), `arviz` (diagnostics), `diebold-mariano` (statistical testing), `matplotlib`, `seaborn`.
**Storage**: Local filesystem (GitHub Actions ephemeral storage); data streamed from Hugging Face.
**Testing**: `pytest` (unit tests for metric calculation, integration tests for pipeline flow).
**Target Platform**: Linux (GitHub Actions Free Runner).
**Project Type**: Data Science Pipeline / Statistical Research Tool.
**Performance Goals**: Full pipeline ≤ 6 hours; Isotonic step ≤ 30 mins; Bayesian step ≤ 60 mins (with timeout fallback).
**Constraints**: No local GPU; strict memory limit (~7GB); no external API calls requiring credentials; all data must be downloadable via programmatic means.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Implementation Detail |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | `requirements.txt` pins all versions. Random seeds set globally. Data fetched from canonical sources. |
| **II. Verified Accuracy** | **PASS** | All citations restricted to verified sources. No invented URLs. |
| **III. Data Hygiene** | **PASS** | Data downloaded to `data/raw/` with checksum verification. Derivations written to `data/processed/`. |
| **IV. Single Source of Truth** | **PASS** | All results generated programmatically. No hand-typed numbers. |
| **V. Versioning Discipline** | **PASS** | Artifact hashes recorded in state file. |
| **VI. Meteorological Calibration Integrity** | **PASS** | Metrics computed **separately** for each `lead_time` and `variable`. |
| **VII. Probabilistic Forecasting Rigor** | **PASS** | Proper scoring rules used. Reliability diagrams and PIT histograms generated. |

## Project Structure

### Documentation (this feature)

```text
specs/001-evaluating-calibration-weather/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/
    ├── dataset.schema.yaml
    ├── metrics.schema.yaml
    └── recalibrator_model.schema.yaml
```

### Source Code (repository root)

```text
src/
├── data/
│   ├── download.py          # Handles HF download, checksum, Data Availability Gate
│   ├── align.py             # Joins forecast/obs by grid/lead/date
│   ├── autocorr.py          # Calculates effective autocorrelation length
│   └── loaders.py           # Streaming loaders for large datasets
├── models/
│   ├── isotonic.py          # Isotonic regression fitting/prediction
│   ├── bayesian.py          # PyMC hierarchical model definition
│   └── calibration.py       # Recalibration logic
├── metrics/
│   ├── scoring.py           # Brier, CRPS, PIT calculation
│   ├── diagrams.py          # Reliability diagram generation
│   └── tests.py             # Diebold-Mariano, Shapiro-Wilk, Wilcoxon
├── pipeline/
│   ├── run_baseline.py
│   ├── run_isotonic.py
│   └── run_bayesian.py
├── utils/
│   ├── config.py            # Paths, seeds, timeouts
│   └── logging.py           # Structured logging
└── main.py                  # Orchestrator

tests/
├── contract/                # Schema validation tests
├── integration/             # End-to-end pipeline tests
└── unit/                    # Metric calculation unit tests

data/
├── raw/                     # Downloaded archives (checksummed)
└── processed/               # Aligned CSV/Parquet
results/
├── results_baseline.csv
├── results_isotonic.csv
├── results_bayesian.csv
└── figures/                 # PNGs
```

## Phase Breakdown

### Phase 0: Data Acquisition, Autocorrelation Estimation & Alignment (FR-001, FR-002)
1.  **Download & Gate**: Implement `download.py` to fetch data.
    *   *Gate*: Check for `probability_value` OR `ensemble_members`.
        *   If `probability_value` exists: Proceed.
        *   If `ensemble_members` exist: Derive probabilities.
        *   If neither: Halt with error `NO_PROB_DATA` and generate `data_unavailability_report.md`.
2.  **Autocorrelation Estimation** (New): Implement `autocorr.py`.
    *   Calculate the Autocorrelation Function (ACF) of forecast errors (raw forecast - observation) for each variable.
    *   Determine `lag_95`: The first lag where ACF drops below 0.05.
    *   Compute `effective_autocorrelation_length` = `max(30, floor(2 * lag_95))`.
    *   Store this value in `data/processed/autocorr_metadata.json`.
3.  **Alignment**: Implement `align.py` to join forecasts and observations.
    *   Discard rows with missing values.
    *   Output: `data/processed/aligned_data.parquet`.

### Phase 1: Baseline Calibration Assessment (FR-003, US-1)
1.  **Metric Calculation**: Compute Brier Score and CRPS for raw forecasts.
    *   *Constraint*: Compute separately for each `lead_time` and `variable`.
2.  **Visualization**: Generate kernel-smoothed reliability diagrams (`reliability_diagram_raw.png`).
3.  **Output**: `results_baseline.csv` with columns: `metric_name`, `lead_time`, `variable`, `value`, `confidence_interval`.

### Phase 2: Isotonic Recalibration (FR-004, US-2)
1.  **Split Strategy**: Implement blocked/expanding window split using `effective_autocorrelation_length` calculated in Phase 0.
    *   Block size = `effective_autocorrelation_length`.
    *   *Sensitivity*: Run additional splits (60/40, 80/20).
2.  **Model Fitting**: Fit `IsotonicRegression` per `lead_time`/`variable`.
    *   *Constraint*: Enforce a sufficient minimum sample size per bin.
    *   *Pooling*: If `sample_size < 100`, pool adjacent lead times or seasons until `sample_size >= 100` OR all adjacent bins exhausted.
    *   *Fallback*: If global fit also `sample_size < 100`, mark model as `Insufficient_Data` and exclude from comparison.
3.  **Evaluation**: Apply to test set, compute new Brier/CRPS.
4.  **Statistical Test**:
    *   Perform Diebold-Mariano test (with HAC) comparing Baseline vs. Isotonic.
    *   *Normality Check*: If Shapiro-Wilk fails ($p < 0.05$), switch to Wilcoxon Signed-Rank test.
    *   *Recorded Test Type*: Always record 'DM' or 'Wilcoxon' in `test_type` (never 'Shapiro-Wilk_Failed').
    *   *Rank-Preserving Control*: Compare Isotonic against a 'Rank-Preserving Calibration' baseline to isolate calibration gain from rank gain.
5.  **Output**: `results_isotonic.csv`, `reliability_diagram_isotonic.png`.

### Phase 3: Bayesian Hierarchical Recalibration (FR-005, US-3)
1.  **Model Definition**: Define PyMC hierarchical logistic regression.
    *   *Structure*: `logit(p) = alpha_season[season] + beta_lead[lead] * raw_prob`.
    *   *Priors*: `alpha_season ~ Normal`, `beta_lead ~ Normal` with a hyperprior enforcing decay (negative mean).
    *   *Control*: Run a 'Flat Prior' model (no decay constraint) as a null control.
    *   *Decision Rule*: If 'Flat Prior' Brier < 'Physics Prior' Brier, flag as 'Prior_Dominated'.
2.  **Sampling**: Run MCMC with a sufficient number of draws and multiple chains, subject to a 60-minute timeout.
    *   *Convergence*: R-hat ≤ 1.05 for all parameters.
    *   *Sample Size Check*: If effective draws < 1000, label as 'Exploratory'.
    *   *Testing*: If 'Exploratory', **DO NOT** perform Diebold-Mariano test. Report descriptive metrics only.
    *   *Fallback*: If timeout or R-hat > 1.05, log status 'Unconverged' or 'Timeout'.
    *   *Zero-Valid-Samples*: If ALL runs are excluded, report 'Bayesian: Not Available' and set comparison metrics to 'N/A'.
3.  **Sensitivity**: Vary prior strength (weak, medium, strong).
4.  **Output**: `results_bayesian.csv` (always generated), `convergence_status` column.

### Phase 4: Comparative Analysis & Reporting (FR-006, FR-007)
1.  **Comparison**:
    *   Isotonic vs. Baseline: Diebold-Mariano (or Wilcoxon).
    *   Bayesian vs. Isotonic: Only if Bayesian is 'Converged' AND 'Exploratory' is False.
    *   *Bootstrap*: For sparse events, use Stratified Bootstrap (1000 iterations, stratified by `lead_time` and `season`). Only perform DM test if bootstrap IQR < 0.01.
2.  **PIT Histograms**: Generate PIT histograms for all methods.
3.  **Final Report**: Aggregate all results into a summary table.
4.  **Validation**: Ensure all CSVs have `convergence_status`, `test_type`, and no null metric values.

## Compute Feasibility Strategy

*   **CPU-First**: All data processing, Isotonic regression, and metric calculation are CPU-tractable.
*   **Bayesian Escape Hatch**: The PyMC model is the only GPU-intensive component.
    *   *Plan*: Use `target_accept=0.9`, short chains (500 draws), and `tune=500`.
    *   *Constraint*: Hard 60-minute timeout enforced via `signal` module.
    *   *Fallback*: If timeout/convergence fails, the pipeline automatically switches to Isotonic results and logs the failure, ensuring the job completes within the 6-hour runner limit.
    *   *Streaming*: Data loaded via `datasets.load_dataset(..., streaming=True)` to avoid OOM on the 7GB RAM limit.

## Risk Mitigation

*   **Data Unavailability**: The "Data Availability Gate" ensures the pipeline halts cleanly if `probability_value` is missing, preventing fabrication.
*   **MCMC Failure**: Explicit timeout and R-hat checks ensure the pipeline never hangs or produces invalid Bayesian results.
*   **Sparse Data**: Minimum sample size thresholds and pooling strategies prevent overfitting in Isotonic regression.
*   **Prior Dominance**: The 'Flat Prior' control ensures that improvements are not artifacts of the prior choice.