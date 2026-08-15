# Implementation Plan: Evaluating Calibration of Probabilistic Weather Forecasts

**Branch**: `001-evaluating-calibration-weather` | **Date**: 2026-07-14 | **Spec**: `specs/001-evaluating-calibration-weather/spec.md`
**Input**: Feature specification from `/specs/001-evaluating-calibration-weather/spec.md`

## Summary
This project implements a rigorous pipeline to evaluate and recalibrate probabilistic weather forecasts from the SubseasonalRodeo dataset. The technical approach involves downloading the dataset, aligning GFS ensemble forecasts with ground-truth observations, and computing baseline calibration metrics (Brier score, CRPS). It then applies two recalibration methods: Isotonic Regression (non-parametric) and a Bayesian Hierarchical Logistic Regression (parametric, with lead-time decay priors). The plan ensures strict adherence to the project constitution regarding reproducibility, data hygiene, and meteorological calibration integrity, while managing computational constraints on GitHub Actions (CPU-first) with a Kaggle GPU escape hatch for the Bayesian inference if Variational Inference fails diagnostics.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `pymc`, `arviz`, `properscoring`, `matplotlib`, `seaborn`, `requests`, `tqdm`, `statsmodels`
**Storage**: Local filesystem (`data/`, `results/`) for intermediate and final artifacts; no persistent database.
**Testing**: `pytest` (unit tests for metric calculations, integration tests for pipeline phases).
**Target Platform**: Linux (GitHub Actions Free Tier: multi-core CPU, ~7GB RAM). GPU escape hatch via Kaggle for PyMC sampling if CPU time exceeds limits or ADVI diagnostics fail.
**Project Type**: Data Science Pipeline / Statistical Analysis Library
**Performance Goals**: 
- **CPU-Path Success**: Complete baseline, isotonic, and data processing within ≤ 30 minutes.
- **Full-Path Success (with GPU offload)**: Complete entire pipeline including Bayesian sampling within ≤ 6 hours.
- Bayesian sampling limited to ≤ 500 draws (or equivalent ADVI iterations) to ensure convergence within the time budget.
**Constraints**: 
- CPU-first execution; GPU only for PyMC sampling if CPU fails or is too slow (auto-offload).
- No modification of raw data; all transformations create new files with checksums.
- Strict handling of missing data (drop or flag) and sparse events (fallback logic).
- All comparisons must use Diebold-Mariano (HAC-corrected) or Wilcoxon tests as specified; block bootstrapping for sensitivity analysis.
- **Dataset Constraint**: If SubseasonalRodeo is unavailable or schema-mismatched, the pipeline halts with "Dataset Unavailable" or "Schema Mismatch" (no fallback to incompatible datasets).
- **Dataset Size Contingency**: If the downloaded dataset exceeds available memory or disk capacity, the pipeline switches to streaming mode or a fixed-seed random sample (e.g., [deferred]) with a logged warning about power limitations.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Reproducibility**: The plan enforces pinned dependencies (`requirements.txt`), random seed setting (global `numpy` and `pymc` seeds), and canonical dataset fetching (via `wget` or verified Hugging Face URLs). All scripts are runnable end-to-end.
- **II. Verified Accuracy**: The plan enforces that the pipeline halts if the dataset source is unverified or schema-mismatched. No assumed URLs are used; if the verified source is missing, the project stops.
- **III. Data Hygiene**: The pipeline will compute and record SHA-256 checksums for all downloaded files in `state/`. Raw data is immutable; derived datasets (aligned, train/test splits) are written to new files.
- **IV. Single Source of Truth**: All metrics in `results/` CSVs are generated programmatically. The `quickstart.md` will reference these exact file paths. No hand-typed numbers will appear in the paper.
- **V. Versioning Discipline**: Artifacts will be tagged with content hashes. The plan includes a step to update the project state file upon successful completion.
- **VI. Meteorological Calibration Integrity**: **Explicitly mapped to Tasks T004, T007, and T010.** The implementation MUST iterate over `variables` (precipitation, temperature) AND `lead_times` as separate strata. **Every metric calculation task (T004, T007, T010) MUST explicitly state iteration over both dimensions** to ensure metrics are not aggregated inappropriately.
- **VII. Probabilistic Forecasting Rigor**: Metrics will be limited to Brier score, CRPS, and PIT histograms. Reliability diagrams will be kernel-smoothed. The plan explicitly avoids misinterpretation of Brier scores.

## Project Structure

### Documentation (this feature)
```text
specs/001-evaluating-calibration-weather/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── forecast_record.schema.yaml
│   ├── observation_record.schema.yaml
│   ├── calibration_metric.schema.yaml
│   └── recalibrator_model.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)
```text
projects/PROJ-763-evaluating-calibration-of-probabilistic-/code/
├── __init__.py
├── main.py              # Entry point for pipeline execution
├── config.py            # Configuration (paths, seeds, thresholds)
├── data/
│   ├── download.py      # Dataset acquisition and checksumming
│   ├── align.py         # Forecast-Observation alignment
│   └── split.py         # Chronological train/test splitting
├── metrics/
│   ├── baseline.py      # Brier, CRPS, PIT, Reliability Diagrams
│   └── comparison.py    # Diebold-Mariano (HAC), Block Bootstrap
├── models/
│   ├── isotonic.py      # Isotonic Regression implementation
│   └── bayesian.py      # PyMC Hierarchical Logistic Regression (ADVI/MCMC)
├── utils/
│   ├── logging.py
│   └── io.py            # CSV/JSONI/O helpers
└── tests/
    ├── test_metrics.py
    └── test_alignment.py

requirements.txt
```

**Structure Decision**: Single project structure selected to minimize overhead. Modules are separated by concern (data, metrics, models) to ensure testability and adherence to the "Single Source of Truth" principle. The `main.py` orchestrates the phases in the correct order: Download -> Align -> Split -> Baseline -> Isotonic -> Bayesian -> Compare -> Output.

## Tasks

### T000: Power Analysis (Pre-Flight)
- **Goal**: Calculate minimum detectable effect size for rare events (heavy precipitation) to validate SC-001/SC-002.
- **Logic**: Compute effective sample size per lead time/variable. If power < 0.8 for the target effect size, flag results as "Underpowered".
- **Output**: `power_analysis_report.json`.

### T001: Dataset Acquisition & Verification
- **Goal**: Download SubseasonalRodeo and verify checksum.
- **Logic**: Use `wget` with checksum verification. If download fails or checksum mismatch, **HALT** with "Dataset Unavailable".
- **Output**: `data/raw_subseasonal_rodeo.tar.gz`, `state/checksums.json`.

### T001.5: Schema Verification (NEW)
- **Goal**: Validate the downloaded dataset structure against the required schema.
- **Logic**: Check for presence of `probability_value`, `event_occurred`, `grid_id`, `lead_time`. If any required field is missing or schema mismatched, **HALT** with "Schema Mismatch".
- **Output**: `state/schema_validation.json` (status: "Valid" or "Invalid").

### T002: Data Alignment
- **Goal**: Align forecasts with observations by grid point, lead time, and date.
- **Logic**: Merge on `grid_id`, `lead_time`, `date`. Drop records with missing values.
- **Output**: `data/aligned_forecasts.parquet`.

### T003: Train/Test Split
- **Goal**: A chronological split with a majority training set and a minority test set.
- **Logic**: Sort by `forecast_date`. First [deferred] for training, last [deferred] for testing.
- **Output**: `data/train_split.parquet`, `data/test_split.parquet`.

### T004: Baseline Metrics & Reliability Diagram (Raw)
- **Goal**: Compute Brier, CRPS, and generate `reliability_diagram_raw.png`.
- **Logic**: **Iterate over all variables (precipitation, temperature) AND lead_times**. Compute Brier, CRPS, and kernel-smoothed reliability diagram.
- **Note**: This task satisfies the US-1 Independent Test (Definition of Done). T012 (PIT Histogram) is Extended Scope and not required for US-1 MVP.
- **Output**: `results_baseline.csv`, `reliability_diagram_raw.png`.

### T005: Baseline PIT Histogram
- **Goal**: Generate `pit_histogram_raw.png`.
- **Logic**: Compute PIT values for raw forecasts. Plot histogram and KS statistic.
- **Output**: `pit_histogram_raw.png`.

### T006: Isotonic Regression
- **Goal**: Fit isotonic regression on training split.
- **Logic**: Iterate over `variables` AND `lead_times`. Enforce minimum sample size threshold (fallback to raw if < 100).
- **Output**: `models/isotonic_model.pkl`.

### T007: Isotonic Recalibration & Metrics
- **Goal**: Apply isotonic model to test split and compute metrics.
- **Logic**: **Iterate over all variables (precipitation, temperature) AND lead_times**. Apply model to `test_split`. Compute Brier, CRPS, reliability diagram.
- **Output**: `results_isotonic.csv`, `reliability_diagram_isotonic.png`.

### T008: Bayesian Hierarchical Model (Physics-Respecting Prior)
- **Goal**: Implement Bayesian model with lead-time decay prior.
- **Logic**: Iterate over `variables` AND `lead_times`. Implement structured prior: `beta_lead_time ~ Normal(0, sigma * exp(-alpha * lead_time))` to respect physics of forecast degradation.
- **Output**: `models/bayesian_model.pkl`.

### T009: Bayesian Sampling (ADVI First)
- **Goal**: Perform inference with ≤ 500 draws (or equivalent ADVI iterations).
- **Logic**: Use Variational Inference (ADVI) for speed. Check convergence (ELBO, R-hat approx). If diagnostics fail, switch to GPU-accelerated MCMC.
- **Output**: `results_bayesian.csv` (with convergence status).

### T010: Bayesian Recalibration & Metrics
- **Goal**: Apply Bayesian model to test split and compute metrics.
- **Logic**: **Iterate over all variables (precipitation, temperature) AND lead_times**. Apply posterior predictive to `test_split`. Compute Brier, CRPS, reliability diagram.
- **Output**: `reliability_diagram_bayesian.png`.

### T011: Bayesian PIT Histogram
- **Goal**: Generate `pit_histogram_bayesian.png`.
- **Logic**: Compute PIT values for Bayesian forecasts. Plot histogram and KS statistic.
- **Output**: `pit_histogram_bayesian.png`.

### T012: Brier Score Decomposition
- **Goal**: Decompose Brier score into Reliability, Resolution, Uncertainty.
- **Logic**: Compute components for Raw, Isotonic, and Bayesian methods to explicitly validate "calibration improvement" (Reliability component). **Extended Scope: Not required for US-1 MVP.**
- **Output**: `results_decomposition.csv`.

### T013: PIT Histogram Generation
- **Goal**: Generate `pit_histogram.png` (aggregated view).
- **Logic**: Aggregate PIT histograms across lead times/variables for final report.
- **Output**: `pit_histogram.png`.

### T014: Sensitivity Analysis (Block Bootstrap)
- **Goal**: Compute bootstrapped confidence intervals for split ratios.
- **Logic**: Use Moving Block Bootstrap (block size = 7 days) to account for temporal dependence. Vary split ratio (e.g., 80/20).
- **Output**: `results_sensitivity.csv`.

### T015: Baseline vs. Isotonic Comparison (FR-006 Compliance)
- **Goal**: Compare Baseline vs. Isotonic using Diebold-Mariano (HAC).
- **Logic**: **Iterate over all variables (precipitation, temperature) AND lead_times**. Pre-test stationarity (ADF). If non-stationary, use HLN modification. **If sensitivity_analysis_mode is True: Use Moving Block Bootstrap confidence intervals instead of paired tests.**
- **Output**: `results_comparison_isotonic.csv`.

### T016: Baseline vs. Bayesian Comparison (NEW)
- **Goal**: Compare Baseline vs. Bayesian using Diebold-Mariano (HAC).
- **Logic**: **Iterate over all variables (precipitation, temperature) AND lead_times**. Pre-test stationarity (ADF). If non-stationary, use HLN modification. **If sensitivity_analysis_mode is True: Use Moving Block Bootstrap confidence intervals instead of paired tests.**
- **Output**: `results_comparison_bayesian.csv`.

### T017: Isotonic vs. Bayesian Comparison
- **Goal**: Compare Isotonic vs. Bayesian using Diebold-Mariano (HAC).
- **Logic**: **Iterate over all variables (precipitation, temperature) AND lead_times**. Pre-test stationarity (ADF). If non-stationary, use HLN modification. **If sensitivity_analysis_mode is True: Use Moving Block Bootstrap confidence intervals instead of paired tests.**
- **Output**: `results_comparison_bayesian_vs_isotonic.csv`.

### T018: Final Results Aggregation
- **Goal**: Aggregate all results into a single summary.
- **Logic**: Combine `results_baseline.csv`, `results_isotonic.csv`, `results_bayesian.csv`, and comparison results.
- **Output**: `results/summary.csv`.

### T019: Pipeline Execution & Reporting
- **Goal**: Run the full pipeline and generate final report.
- **Logic**: Execute T000-T018 in order. Log runtime and status.
- **Output**: `pipeline_log.json`, final report.

### T020: Bayesian Prior Implementation (Physics-Respecting)
- **Goal**: Explicitly implement the structured prior for lead-time decay.
- **Logic**: Implement `beta_lead_time ~ Normal(0, sigma * exp(-alpha * lead_time))` as required by FR-005 and US-3. This ensures the prior respects the physics of forecast degradation.
- **Output**: Updated `models/bayesian_model.pkl`.

### T021: Bayesian Sampling Constraints
- **Goal**: Ensure Bayesian sampling meets runtime constraints.
- **Logic**: Limit draws to **500** (or equivalent ADVI iterations) as per Spec Assumption: Threshold Justification. Use chains. If CPU time exceeds limits, trigger GPU offload.
- **Output**: `results_bayesian.csv` with runtime logs.

### T024: Prior Sensitivity Analysis (NEW)
- **Goal**: Decouple prior influence from data signal.
- **Logic**: Run Bayesian model with varying prior strengths (weak, medium, strong decay) to ensure improvement is data-driven.
- **Output**: `results_prior_sensitivity.csv`.

### T025: Baseline vs. Bayesian Comparison (Explicit Task)
- **Goal**: Explicitly compare Baseline vs. Bayesian as required by FR-006.
- **Logic**: Implement Diebold-Mariano test for Baseline vs. Bayesian. (Note: This is now covered by T016).
- **Output**: `results_comparison_bayesian.csv`.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Bayesian Hierarchical Model | Required by US-3 and FR-005 to handle sparse events and lead-time decay physics. | A simple logistic regression per lead time would fail to share strength across lead times, violating the "Meteorological Calibration Integrity" principle for rare events. |
| Dual Statistical Tests (DM + HLN + Block Bootstrap) | Required by FR-006 to handle non-normality, non-stationarity, and temporal dependence. | A single test (e.g., t-test) or standard bootstrap would fail to meet the spec's rigorous statistical requirements for time-series data. |
| GPU Escape Hatch | Required for PyMC sampling if CPU time exceeds 6h limit (SC-005) or ADVI fails. | CPU-only sampling for complex hierarchical models often exceeds the 6h limit on free runners, leading to incomplete results. |
| Variational Inference (ADVI) | Required to meet SC-005 (30 mins) while maintaining statistical validity (R-hat). | Standard MCMC on CPU is too slow; ADVI provides a valid approximation within the time budget. |
| Schema Verification (T001.5) | Required to prevent silent failure on schema mismatches. | Without explicit schema checks, the pipeline might process incompatible data, leading to invalid results. |
| Prior Sensitivity Analysis (T024) | Required to ensure improvement is data-driven, not prior-driven. | Without this, the "improvement" might be an artifact of the prior assumption. |

## Success Criteria Re-Definition
- **SC-005 (Runtime)**: 
  - **CPU-Path**: Baseline, Isotonic, and data processing complete in ≤ 30 minutes.
  - **Full-Path (with GPU offload)**: Entire pipeline including Bayesian sampling complete in ≤ 6 hours.
  - If GPU offload is triggered, SC-005 is satisfied under the "Full-Path" definition.
  - **Note**: The 30-minute limit applies to the CPU-Path (Baseline/Isotonic). The Bayesian model requires the Full-Path (≤ 6 hours) with GPU offload.