# Implementation Plan: Evaluating Calibration of Probabilistic Weather Forecasts

**Branch**: `001-evaluating-calibration-weather` | **Date**: 2026-07-14 | **Spec**: `specs/001-evaluating-calibration-of-probabilistic/spec.md`

## Summary

This project implements a rigorous pipeline to evaluate and recalibrate probabilistic weather forecasts. The technical approach involves downloading the dataset (strictly from verified sources), enforcing a strict "Data Availability Gate" to verify the presence of `probability_value` fields (FR-001), and computing baseline calibration metrics. It applies two recalibration methods: Isotonic Regression (P2) and a Bayesian Hierarchical Logistic Regression (P3). The pipeline includes mandatory sensitivity analyses, enforces computational fallbacks, and uses robust statistical comparisons (Diebold-Mariano with HAC or Bootstrap).

**CRITICAL DATA STATUS**: The primary dataset "SubseasonalRodeo" currently lacks a verified URL in the project's "Verified datasets" block. This plan is **BLOCKED** until a verified source is provided or an alternative from the verified list (e.g., NOAA parquet) is confirmed to contain the required schema. The pipeline will halt immediately if the dataset cannot be fetched from a verified source.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `pymc` (v5+), `arviz`, `properscoring`, `diebold-mariano` (or `statsmodels` equivalent), `requests`, `tqdm`.  
**Storage**: Local file system (GitHub Actions runner); data streamed or downloaded to `data/` directory.  
**Testing**: `pytest` (unit tests for metric calculation, integration tests for pipeline flow).  
**Target Platform**: Linux (GitHub Actions Free Runner: 2 CPU, 7GB RAM).  
**Project Type**: Data Science Pipeline / Research Code.  
**Performance Goals**: Baseline/Isotonic < 30 mins; Bayesian < 60 mins (with hard timeout fallback).  
**Constraints**: No local GPU; CPU-first execution with automatic Kaggle GPU offload for Bayesian steps if CUDA detected. Memory < 7GB.  
**Scale/Scope**: Moderate-sized dataset; processing by lead time and variable.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Status | Verification |
| :--- | :--- | :--- |
| **I. Reproducibility** | PASS | All random seeds pinned in `code/`. Dataset download URL/ID fixed (pending verification). `requirements.txt` pins versions. |
| **II. Verified Accuracy** | **BLOCKED** | **CRITICAL**: The primary dataset "SubseasonalRodeo" is NOT in the "Verified datasets" block. The plan cannot proceed until a verified URL is provided or an alternative is selected. No unverified URLs will be used. |
| **III. Data Hygiene** | PASS | Data downloaded to `data/raw/` with checksum verification (if source verified). Derivations written to `data/processed/`. No in-place edits. |
| **IV. Single Source of Truth** | PASS | All metrics in `results/*.csv` trace to specific code blocks. No hand-typed numbers in `paper/`. |
| **V. Versioning Discipline** | PASS | Artifact hashes tracked in state file. Plan version 1.0.0. |
| **VI. Meteorological Calibration Integrity** | PASS | Metrics computed separately for each lead time and variable (precip/temp) as required. |
| **VII. Probabilistic Forecasting Rigor** | PASS | Brier, CRPS, PIT histograms used. No counter-intuitive Brier interpretations. |

## Project Structure

### Documentation (this feature)

```text
specs/001-evaluating-calibration-weather/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   └── results.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-763-evaluating-calibration-of-probabilistic-/
├── data/
│   ├── raw/                 # Downloaded files (checksummed)
│   └── processed/           # Aligned CSV/Parquet, train/test splits
├── code/
│   ├── requirements.txt     # Pinned dependencies
│   ├── __init__.py
│   ├── download.py          # FR-001: Download + Data Availability Gate
│   ├── align.py             # FR-002: Alignment logic
│   ├── metrics.py           # FR-003: Brier, CRPS, Reliability Diagrams
│   ├── isotonic.py          # FR-004: Isotonic Regression + Sensitivity
│   ├── bayesian.py          # FR-005: Hierarchical Model + Timeout/Sensitivity
│   ├── compare.py           # FR-006: Diebold-Mariano + Bootstrap
│   └── main.py              # Orchestration
├── results/
│   ├── results_baseline.csv
│   ├── results_isotonic.csv
│   ├── results_bayesian.csv
│   └── figures/             # PNG diagrams
└── tests/
    ├── unit/
    └── integration/
```

**Structure Decision**: Single project structure selected. `code/` contains modular scripts for each functional requirement. `data/` separates raw vs. processed. `results/` is the single source of truth for metrics.

## Phase Execution Order

1.  **Phase 0 (Data Acquisition)**: `download.py` runs.
    -   **Step 1**: Fetch data ONLY from a verified URL (if available) or halt with "Data Source Not Verified".
    -   **Step 2**: Verify file integrity (checksum).
    -   **Step 3 (Data Availability Gate)**: Load dataset and verify presence of `probability_value` fields.
    -   **HALT CONDITION**: If `probability_value` is missing, **HALT immediately** with error "Data Availability Gate Failed". Do not proceed to alignment.

2.  **Phase 1 (Alignment)**: `align.py` merges forecasts and observations by grid/lead/date. Outputs `processed_data.parquet`.
    -   Discards records with missing values in either field.

3.  **Phase 2 (Baseline)**: `metrics.py` computes Brier/CRPS for raw data. Generates `results_baseline.csv` and `reliability_diagram_raw.png`.
    -   Computes metrics separately for each lead time and variable.

4.  **Phase 3 (Isotonic)**: `isotonic.py` fits models on training split.
    -   **Blocking Strategy**: **Train on full historical years (e.g., 2017-2021), Test on the final full year (2022)**. This ensures seasonal cycles are respected and prevents data leakage.
    -   **Sensitivity**: Runs repeated with 60/40 and 80/20 splits (using the same temporal boundary logic: train on years 1-N, test on N+1).
    -   Generates `results_isotonic.csv`.

5.  **Phase 4 (Bayesian)**: `bayesian.py` runs MCMC.
    -   **Configuration**: **4 chains** (mandatory for all runs, including sensitivity and control models), **minimum 2000 draws** (raised from 500 to ensure stability).
    -   **Convergence**: R-hat ≤ 1.05 AND Effective Sample Size (ESS) > 200 per parameter.
    -   **Dynamic Adjustment**: If ESS or R-hat targets are not met, the sampler will **extend draws** up to a maximum timeout (60 mins).
    -   **Prior Sensitivity**: Includes a **"Flat Prior"** control model (weakly informative, no decay assumption) to decouple prior influence from data signal.
    -   **Fallback**: If timeout exceeded or convergence fails (R-hat > 1.05 or ESS < 200), **fallback to Isotonic results** and log status as "Timeout" or "Unconverged".
    -   Generates `results_bayesian.csv`.

6.  **Phase 5 (Comparison)**: `compare.py` compares methods.
    -   **Test Input**: Uses the **time series of individual forecast errors** (daily/weekly loss differentials) for each lead time. **NOT** aggregated means.
    -   **Primary Test**: Diebold-Mariano (DM) with HAC estimators.
    -   **Non-Normal Handling**: If normality fails, use **Bootstrap** (preserving time-series structure) instead of Wilcoxon (which assumes i.i.d. and is invalid for autocorrelated errors).
    -   **Scope**: DM tests are run *within* a single fixed test set. Sensitivity splits use bootstrapped CIs for meta-analysis.
    -   Outputs final comparison table.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Bayesian Hierarchical Model** | Required by Spec (US-3) to borrow strength across lead times for sparse events. | A simple isotonic model cannot capture lead-time decay correlations or improve performance on rare events as effectively. |
| **Strict Data Availability Gate** | Required by FR-001 to prevent silent failure on missing probability fields. | Standard file integrity checks do not verify schema content; proceeding without probability fields makes Brier/CRPS impossible. |
| **Automatic Test Switching (to Bootstrap)** | Required to handle non-normal, autocorrelated error distributions. | Wilcoxon assumes i.i.d. and is invalid for autocorrelated forecast errors. Bootstrap preserves time-series structure. |
| **4 Chains Mandatory** | Required for robust R-hat estimation. | 2 chains are insufficient for reliable convergence diagnostics in hierarchical models. |
| **Minimum 2000 Draws** | Required to ensure stable R-hat and ESS for the hierarchical model with structured priors. | 500 draws are insufficient for complex hierarchical models, risking false convergence signals. |