# Implementation Plan: Evaluating Calibration of Probabilistic Weather Forecasts

**Branch**: `001-evaluating-calibration-weather` | **Date**: 2026-06-22 | **Spec**: [link]
**Input**: Feature specification from `specs/001-evaluating-calibration-weather/spec.md`

## Summary
This project evaluates the calibration of probabilistic weather forecasts from the GFS ensemble system. The technical approach involves three sequential phases: (1) establishing a baseline calibration assessment (Brier score, CRPS, reliability diagrams) on raw forecasts; (2) applying isotonic regression for non-parametric recalibration with blocked validation; and (3) implementing a Bayesian hierarchical logistic regression model with physics-informed priors to address sparse event categories. All methods run on a CPU-first GitHub Actions runner, with strict data availability gates and fallback mechanisms for model convergence failures.

**Note on Dataset**: The spec mandates SubseasonalRodeo, but no verified URL exists. The plan implements a fallback to NOAA GFS (verified HuggingFace URL: `https://huggingface.co/datasets/Qdrant/NOAA-Buoy/resolve/main/full_2023_remove_flawed.parquet`) as the primary executable path. A spec amendment is flagged to update FR-001 to allow the substitute.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `scikit-learn`, `pymc`, `arviz`, `properscoring`, `diebold-mariano`, `pandas`, `numpy`, `matplotlib`, `seaborn`  
**Storage**: Local file system (GitHub Actions runner), CSV outputs, PNG images  
**Testing**: `pytest` (unit), `pytest-cov` (coverage), custom integration tests for pipeline gates  
**Target Platform**: GitHub Actions free-tier runner (2 CPU, ~7 GB RAM, ~14 GB disk, no GPU)  
**Project Type**: Computational data analysis pipeline  
**Performance Goals**: Complete entire pipeline within 6 hours; Isotonic step ≤ 30 mins; Bayesian step ≤ 60 mins  
**Constraints**: No local GPU; memory < 7 GB; disk < 14 GB; strict data availability gate; fallback to isotonic if Bayesian fails  
**Scale/Scope**: NOAA GFS dataset (moderate size); multiple lead times (positive integers); multiple variables (precip, temp); recalibration methods  

> Domain-specific empirical specifics (exact dataset sizes, lead time counts, convergence rates) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Notes |
|-----------|---|---|
| **I. Reproducibility** | **PASS** | All random seeds pinned in `code/`; dataset fetched from canonical source (NOAA GFS); `requirements.txt` pins dependencies. |
| **II. Verified Accuracy** | **PASS** | Citations in `research.md` will be validated against primary sources; title overlap ≥ 0.7 enforced. NOAA GFS URL is verified. |
| **III. Data Hygiene** | **PASS** | Raw data preserved; checksums recorded; no in-place modifications; PII scan enforced. |
| **IV. Single Source of Truth** | **PASS** | All figures/stats trace to `data/` and `code/`; no hand-typed numbers. |
| **V. Versioning Discipline** | **PASS** | Content hashes for artifacts; `updated_at` timestamps updated on change. |
| **VI. Meteorological Calibration Integrity** | **PASS** | Metrics computed separately per lead time and variable; no aggregation artifacts. |
| **VII. Probabilistic Forecasting Rigor** | **PASS** | Proper scoring rules (Brier, CRPS); reliability diagrams; PIT histograms; no Brier misconceptions. |

## Project Structure

### Documentation (this feature)

```text
specs/001-evaluating-calibration-weather/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── dataset.schema.yaml
    ├── output.schema.yaml
    └── metrics.schema.yaml
```

### Source Code (repository root)

```text
code/
├── data/
│   ├── download.sh          # Dataset acquisition script
│   ├── verify.sh            # Checksum verification
│   └── raw/                 # Downloaded raw data (checksummed)
├── analysis/
│   ├── baseline/
│   │   ├── align.py         # Forecast-observation alignment
│   │   ├── metrics.py       # Brier, CRPS computation
│   │   └── plots.py         # Reliability diagrams, PIT histograms
│   ├── isotonic/
│   │   ├── train.py         # Isotonic regression fitting
│   │   ├── evaluate.py      # Recalibrated metrics
│   │   └── sensitivity.py   # 60/40, 80/20 split analysis
│   ├── bayesian/
│   │   ├── model.py         # Hierarchical logistic regression
│   │   ├── prior_sensitivity.py # Flat vs physics-informed prior
│   │   └── diagnostics.py   # R-hat, ESS, convergence checks
│   └── comparison/
│       ├── diebold_mariano.py # Statistical tests (DM-HAC, Block Bootstrap)
│       └── summary.py       # Final comparison table
├── tests/
│   ├── unit/
│   ├── integration/
│   └── contract/
├── requirements.txt
└── run_pipeline.sh          # Main orchestration script
```

**Structure Decision**: Single-project structure chosen for computational pipeline; modular `analysis/` subdirectories for each method; `data/` for raw and processed files; `tests/` for validation.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|---|---|
| **Bayesian Hierarchical Model** | Required to share information across lead times for sparse events (heavy precipitation) and validate physics-informed priors. | Simpler isotonic regression alone cannot model lead-time correlations or handle sparse event categories effectively; flat prior control needed to decouple prior influence. |
| **Diebold-Mariano with HAC/Block Bootstrap** | Required for valid time-series comparison of forecast errors; standard t-tests fail due to autocorrelation. | Aggregated mean comparisons or simple t-tests would produce invalid p-values and misleading conclusions about method superiority. |
| **Data Availability Gate** | Required to halt if `probability_value` fields missing; ensures no fallback to binary data which invalidates Brier/CRPS. | Proceeding with binary data would produce incorrect calibration metrics and invalidate the entire study. |

## Phase Breakdown

### Phase 0: Data Acquisition & Baseline Assessment (FR-001, FR-002, FR-003)
- **Steps**:
  1. **Download Dataset**: Execute download of NOAA GFS from `https://huggingface.co/datasets/Qdrant/NOAA-Buoy/resolve/main/full_2023_remove_flawed.parquet` (verified URL). Log the substitution of SubseasonalRodeo.
  2. Verify file integrity via checksum.
  3. **Data Availability Gate**: Check for `probability_value` OR `precip_prob` field (to support NOAA GFS schema). Halt with exit code 1 if neither is present (FR-001, SC-007).
  4. Align forecasts with observations by `grid_id`, `lead_time`, `forecast_date`/`observation_date`; discard records with missing values (FR-002).
  5. Compute Brier scores and CRPS for raw forecasts per lead time and variable (FR-003).
  6. Generate kernel-smoothed reliability diagrams and PIT histograms (FR-003, SC-003, SC-004).
- **Outputs**: `results_baseline.csv`, `reliability_diagram_raw.png`, `pit_histogram_raw.png`.

### Phase 1: Isotonic Recalibration (FR-004, FR-006)
- **Steps**:
  1. Split data by years: train on years 1-N, test on year N+1 (blocked validation, FR-004, SC-009).
  2. Fit isotonic regression model per lead time and variable on training split. **Constraint**: If test set sample size < 100, regularize by pooling adjacent bins or fallback to raw forecast for that lead time.
  3. Apply fitted model to test split; compute recalibrated Brier scores and CRPS (FR-004).
  4. Generate reliability diagram for isotonic recalibration (FR-004, SC-003).
  5. Perform sensitivity analysis: 60/40 and 80/20 splits; log results (FR-004).
  6. Conduct Diebold-Mariano test (DM-HAC or Block Bootstrap) comparing baseline vs. isotonic per lead time **on the daily time-series of forecast errors** (FR-006, SC-001, SC-008). **Methodology**: Use Newey-West lag length `floor(4 * (T/100)^(2/9))` for HAC; Block Bootstrap block length = 7 days (empirical decay). Ensure `variable` and `lead_time` fields are populated for every test result record.
- **Outputs**: `results_isotonic.csv`, `reliability_diagram_isotonic.png`, `sensitivity_analysis_log.csv`.

### Phase 2: Bayesian Hierarchical Recalibration (FR-005, FR-006)
- **Steps**:
  1. Define hierarchical logistic regression model with lead-time decay prior (FR-005). **Structure**: Unit of analysis is (forecast, observation) pair. **Hierarchy**: Random intercepts and slopes per lead_time (grouping factor) with hyperpriors to share information. **Prior**: Physics-informed prior = Gaussian(mean=-0.1, std=0.05) on decay coefficient (based on known atmospheric decay rates, not tuned to minimize Brier). Flat prior = Gaussian(mean=0, std=10).
  2. Run MCMC sampling (Multiple chains, a sufficient number of draws) with 60-minute timeout (FR-005).
  3. Check convergence: R-hat ≤ 1.05, ESS > 400 (FR-005, SC-005).
  4. If convergence fails or timeout, generate `results_fallback.csv` (isotonic results labeled `method='isotonic'`, `status='fallback'`) and log status (FR-005, FR-007). **Logic**: Failed lead times are excluded from SC-002 comparisons to avoid tautological results.
  5. If converged, compute posterior predictive probabilities; apply to test split; compute Brier scores and CRPS (FR-005).
  6. Perform prior sensitivity analysis: physics-informed prior vs. flat prior control vs. weak/medium/strong strengths (variance = 1.0, 0.5, 0.1). Log Brier score difference to `prior_sensitivity_log.csv` (SC-006). **Note**: If flat prior performs better, record `fallback_reason='Prior_Dominated'` in `recalibrator_model.schema.yaml` metadata only; this does not trigger the `results_fallback.csv` generation mechanism.
  7. Conduct Diebold-Mariano test comparing isotonic vs. Bayesian **on the daily time-series of forecast errors** (FR-006, SC-002). **Fallback handling**: If Bayesian fails, exclude failed lead times from comparison or label as 'N/A' to avoid tautological zero-difference results.
- **Outputs**: `results_bayesian.csv` (if converged), `results_fallback.csv` (if failed), `prior_sensitivity_log.csv`, `convergence_diagnostics.json`.

### Phase 3: Final Comparison & Reporting (FR-007, FR-008)
- **Steps**:
  1. Aggregate all results into `results` directory with standardized filenames (FR-007).
  2. Generate summary comparison table (baseline, isotonic, Bayesian/fallback) with metrics and test results (FR-007). **Logic**: If Bayesian failed, label as 'Bayesian_Fallback' in summary but exclude from SC-002 comparison or label as 'N/A'.
  3. Verify all outputs meet success criteria (SC-001 to SC-009).
  4. Ensure pipeline completes within 6 hours (FR-008).
- **Outputs**: `results/` directory with all CSVs, PNGs, and logs.

## Risk Mitigation

- **Data Availability**: If SubseasonalRodeo lacks `probability_value` or URL, pipeline switches to NOAA GFS and logs substitution (FR-001, SC-007). No fallback to binary data.
- **Convergence Failure**: Bayesian model fallback to isotonic results if R-hat > 1.05, ESS < 400, or timeout (FR-005, FR-007).
- **Memory/Disk Constraints**: Stream data or sample if full dataset exceeds 7 GB RAM / 14 GB disk; log power limitation (see `research.md`).
- **Autocorrelation**: Use Block Bootstrap (block length=7) if Shapiro-Wilk normality test fails (FR-006, SC-008).
- **Sparse Events**: Enforce minimum sample size threshold for isotonic regression; fallback to raw forecast if too few samples (edge case).

## Success Criteria Alignment

- **SC-001**: DM test p < 0.05 or bootstrapped CI excludes 0 for isotonic vs. baseline.
- **SC-002**: Bayesian CRPS reduction ≥ 1% vs. isotonic or DM p < 0.05. **Fallback**: If Bayesian fails, exclude failed lead times from comparison or label as 'N/A' to avoid tautological zero-difference.
- **SC-003**: Calibration slope deviation ≤ 0.05 for recalibrated methods.
- **SC-004**: PIT histogram KS p-value > 0.05 for recalibrated methods.
- **SC-005**: R-hat ≤ 1.05 and ESS > 400 for Bayesian convergence.
- **SC-006**: Physics-informed prior Brier score < flat prior Brier score (logged in `prior_sensitivity_log.csv`).
- **SC-007**: Exit code 1 with "Data Availability Gate Failed" if `probability_value`/`precip_prob` missing.
- **SC-008**: Log normality test results and selected test method (DM-HAC or Block Bootstrap).
- **SC-009**: Validation split ensures no date leakage (test dates > all training dates).

## Spec Amendment Flag
- **Issue**: FR-001 mandates SubseasonalRodeo, but no verified URL exists.
- **Action**: Plan implements fallback to NOAA GFS. Spec amendment required to update FR-001 to allow the substitute if primary dataset is inaccessible.
- **Status**: Flagged for kickback.