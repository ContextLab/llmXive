# Feature Specification: Evaluating Calibration of Probabilistic Weather Forecasts

**Feature Branch**: `001-evaluating-calibration-weather`
**Created**: 2026-06-22
**Status**: Draft
**Input**: User description: "Evaluating Calibration of Probabilistic Weather Forecasts"

## User Scenarios & Testing

### User Story 1 - Baseline Calibration Assessment (Priority: P1)

The researcher needs to download the SubseasonalRodeo dataset, align NOAA GFS ensemble forecasts with ground-truth observations, and compute baseline calibration metrics (Brier score, CRPS, reliability diagrams) to quantify existing mis-calibration without any post-processing.

**Why this priority**: This establishes the ground truth for the project. Without a rigorous baseline measurement of the raw model's performance, any claim of improvement via recalibration is scientifically invalid. This is the minimum viable research step.

**Independent Test**: The pipeline executes successfully on the GitHub Actions runner, downloading the dataset, performing alignment, and outputting a `results_baseline.csv` file containing Brier scores and CRPS for all lead times, plus a `reliability_diagram_raw.png`. The test passes if:
1. The file exists and contains non-null values for all requested metrics.
2. The system detects a missing `probability_value` field and halts execution immediately with exit code 1 and log message "Data Availability Gate Failed" (if applicable).

**Acceptance Scenarios**:

1. **Given** the SubseasonalRodeo dataset is accessible via the verified URL `, **When** the pipeline runs the download and alignment script, **Then** the system produces a clean, aligned dataset where forecast probabilities and observations match by grid point, lead time, and date.
2. **Given** the aligned dataset, **When** the baseline metrics module runs, **Then** the system calculates the Brier score and CRPS for each lead time and variable, storing them in a structured CSV with no missing values.
3. **Given** the aligned dataset, **When** the reliability diagram generator runs, **Then** the system outputs a kernel-smoothed reliability diagram (PNG) that visually maps forecast probability bins against observed frequencies.

---

### User Story 2 - Isotonic Recalibration (Priority: P2)

The researcher needs to apply isotonic regression to the baseline forecasts using a blocked/expanding window validation scheme (train on full years 1 to N, test on year N+1) to correct systematic biases and measure the improvement in calibration metrics compared to the raw baseline.

**Why this priority**: This implements the first proposed intervention. It tests whether a non-parametric, monotonic method (isotonic regression) can effectively remove bias in the probability estimates, serving as a robust baseline for the more complex Bayesian method.

**Independent Test**: The pipeline runs the isotonic regression module on the training split (train on years 1-N, test on year N+1), applies the fitted model to the held-out test split (year N+1), and outputs a `results_isotonic.csv` and `reliability_diagram_isotonic.png`. The test passes if:
1. The new Brier score is lower than the baseline (or the Diebold-Mariano p-value < 0.05 with alternative hypothesis: Baseline > Isotonic, OR the absolute difference ≤ 0.005 (0.5 percentage points)).
2. The reliability diagram shows reduced deviation from the diagonal.
3. The system correctly selects the statistical test (DM-HAC or Block Bootstrap) based on the Shapiro-Wilk normality check (per lead time and variable) and executes it.
4. The sensitivity analysis runs (60/40, 80/20 splits) complete and are logged, with results stable within 5% (relative difference in mean Brier score) of the 70/30 baseline.

**Acceptance Scenarios**:

1. **Given** the baseline metrics and the training split (years 1-N), **When** the isotonic regression model is fitted, **Then** the system produces a monotonic mapping function for each lead time and variable that preserves the rank order of forecasts.
2. **Given** the fitted model and the test split (year N+1), **When** the recalibrated probabilities are generated, **Then** the system computes new Brier scores and CRPS, demonstrating a reduction in error relative to the baseline metrics.
3. **Given** the recalibrated probabilities, **When** the reliability diagram is regenerated, **Then** the plotted points lie closer to the 45-degree line of perfect calibration compared to the raw forecast diagram.

---

### User Story 3 - Bayesian Hierarchical Recalibration (Priority: P3)

The researcher needs to implement a Bayesian hierarchical logistic regression model that shares information across lead times to recalibrate forecasts, specifically targeting improvements in sparse event categories (e.g., heavy precipitation) and comparing its performance against isotonic regression. The model MUST use a structured prior that respects the physics of forecast degradation (e.g., lead-time decay) and include a sensitivity analysis to decouple prior influence from data signal, including a 'Flat Prior' control.

**Why this priority**: This explores the advanced method proposed in the idea. While computationally heavier, it offers potential gains in data-sparse regimes by borrowing strength across lead times. It is P3 because the isotonic method is the primary "simple" solution, and this is an enhancement.

**Independent Test**: The pipeline executes the Bayesian model (using PyMC or statsmodels) with short MCMC chains (initial 2000 draws, 4 chains) on the training split, applies the posterior predictive probabilities to the test split, and outputs `results_bayesian.csv`. The test passes if:
1. The model converges (R-hat ≤ 1.05 AND Effective Sample Size > 400 for all group-level parameters and hyperparameters) within 60 minutes.
2. If convergence fails or time exceeds 60 minutes, the system MUST fallback to isotonic results, generate `results_fallback.csv` (containing isotonic results labeled as 'isotonic'), and log the status as "Unconverged" or "Timeout". `results_bayesian.csv` is NOT generated in this case.
3. The Brier score is within 1% (relative reduction of the isotonic Brier score) of isotonic regression (or Diebold-Mariano p-value < 0.05 with alternative: Isotonic > Bayesian).
4. The prior sensitivity analysis (varying prior strength, including a 'Flat Prior' control) is executed and logged, and the physics-informed prior demonstrates a lower Brier score than the flat prior to validate the improvement claim.

**Acceptance Scenarios**:

1. **Given** the training data and a hierarchical model structure with a lead-time decay prior, **When** the MCMC sampler runs, **Then** the system completes the sampling within the 60-minute limit and reports convergence diagnostics (R-hat, ESS) for all group-level parameters.
2. **Given** the posterior distributions, **When** predictions are generated for the test set, **Then** the system produces recalibrated probabilities that account for lead-time correlations, specifically improving performance on rare events compared to the isotonic method (if validated against the flat prior).
3. **Given** the Bayesian results, **When** the metrics are computed, **Then** the system outputs a comparison table showing Brier score and CRPS improvements relative to both the raw baseline and the isotonic method.

---

### Edge Cases

- **What happens when the dataset download fails or is incomplete?** The pipeline must detect a non-zero exit code from `wget` or a corrupted file checksum, stop execution, and log a clear error message "Dataset acquisition failed" rather than proceeding with partial data.
- **How does the system handle grid points with zero observed events?** For lead times/variables where the observation count is zero (perfectly dry), the Brier score calculation must handle division-by-zero or empty bin scenarios gracefully, returning `NaN` or `0.0` with a warning, rather than crashing the script.
- **What happens if MCMC chains fail to converge?** If the Bayesian model fails to converge (R-hat > 1.05 or ESS < 400) after the maximum iterations or exceeds 60 minutes, the system MUST flag the result as "Unconverged" or "Timeout" in the log and generate `results_fallback.csv` (containing isotonic results labeled as 'isotonic') instead of `results_bayesian.csv`, rather than halting the entire pipeline.
- **What happens if the dataset lacks probability fields?** If the primary dataset lacks the required probability fields (e.g., `probability_value`), the system MUST halt execution immediately with a "Data Availability Gate Failed" error (exit code 1), as fallback to binary data is not supported for Brier/CRPS calculation.
- **How does the system handle lead times with extremely sparse data?** For lead times with very few data points (e.g., < 100 samples), the isotonic regression might overfit; the system must enforce a minimum sample size threshold or fallback to the raw forecast for those specific bins.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download the SubseasonalRodeo dataset (a moderate-sized archive) via `wget` from the verified URL ` and verify file integrity before processing. **CRITICAL**: The system MUST implement a "Data Availability Gate" that checks for the presence of `probability_value` fields in the dataset. If these fields are missing, the system MUST halt execution immediately with exit code 1 and log "Data Availability Gate Failed". (See US-1)
- **FR-002**: System MUST align forecast probabilities with observations by grid point, lead time, and date, discarding any records with missing values in either field. (See US-1)
- **FR-003**: System MUST compute Brier scores, Continuous Ranked Probability Scores (CRPS), and generate kernel-smoothed reliability diagrams for raw forecasts. (See US-1)
- **FR-004**: System MUST fit an isotonic regression model on a blocked validation split (train on full years 1 to N, test on year N+1) for each lead time and variable. The system MUST ALSO execute and log results for sensitivity analysis runs (60/40, 80/20 splits) to ensure robustness against non-stationarity. (See US-2)
- **FR-005**: System MUST implement a Bayesian hierarchical logistic regression model that shares information across lead times using a structured prior modeling lead-time decay, and generates posterior predictive probabilities. The system MUST perform a "Prior Sensitivity Analysis" by varying the prior strength (e.g., weak, medium, strong decay) AND include a "Flat Prior" (non-physics-informed) control run to decouple prior influence from data signal. The system MUST enforce a configurable timeout; if exceeded, or if R-hat > 1.05 or ESS < 400, it MUST fallback to isotonic results and generate `results_fallback.csv` (labeled 'isotonic') instead of `results_bayesian.csv`. The system MUST use a minimum of 2000 draws per chain (4 chains) to ensure stable convergence. (See US-3)
- **FR-006**: System MUST perform the Diebold-Mariano test (α=0.05, one-sided, alternative: Method A > Method B) with Heteroskedasticity and Autocorrelation Consistent (HAC) estimators to compare Brier scores and CRPS between the baseline and each recalibrated method. The test MUST be applied to the time-series of daily forecast errors for each lead time separately (NOT aggregated means). If the normality assumption of differences is violated (Shapiro-Wilk, p < 0.05, per lead time and variable), the system MUST automatically switch to a Block Bootstrap method (block length = 7 days) to preserve autocorrelation. These tests MUST be applied separately for each lead time and variable. For sensitivity analysis runs, the system MUST use bootstrapped confidence intervals instead of paired tests, and MUST NOT run DM tests across different splits. (See US-2, US-3)
- **FR-007**: System MUST output all results (metrics, diagrams, convergence diagnostics) to a single `results` directory with standardized filenames. `results_baseline.csv` and `results_isotonic.csv` MUST always be generated. `results_bayesian.csv` MUST be generated ONLY if the model converges (R-hat ≤ 1.05, ESS > 400). If the model fails to converge or times out, the system MUST generate `results_fallback.csv` containing the isotonic results labeled with method='isotonic' and status='fallback'. (See US-1, US-2, US-3)
- **FR-008**: System MUST complete the entire pipeline within 6 hours of GitHub Actions runtime. The Isotonic step must complete within ≤ 30 minutes, and the Bayesian step (including fallback) within ≤ 60 minutes. (See US-1, US-2, US-3)

### Key Entities

- **Forecast Record**: Represents a single ensemble forecast instance, containing attributes: `grid_id`, `lead_time`, `forecast_date`, `probability_value` (continuous probability, required for Brier/CRPS), `raw_ensemble_mean`.
- **Observation Record**: Represents the ground truth event, containing attributes: `grid_id`, `observation_date`, `event_occurred` (binary), `event_value` (continuous for temp/rain).
- **Calibration Metric**: Represents a computed statistic, containing attributes: `metric_name` (Brier, CRPS), `lead_time`, `method` (raw, isotonic, bayesian, bayesian_fallback), `value`, `confidence_interval`.
- **Recalibrator Model**: Represents a fitted post-processing function, containing attributes: `method_type`, `lead_time`, `parameters` (coefficients or isotonic knots), `training_sample_size`.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The reduction in Brier score for the isotonic method is measured against the baseline Brier score; the Diebold-Mariano test (one-sided, alternative: Baseline > Isotonic) applied to the time-series of daily errors for each lead time yields p < 0.05, OR the bootstrapped 95% CI (moving block bootstrap, block length = 7 days) of the mean difference across lead times excludes 0. (See US-2)
- **SC-002**: The reduction in CRPS for the Bayesian method is measured against the isotonic method's CRPS; the relative reduction must be ≥ 1% (calculated as (Isotonic - Bayesian) / Isotonic, mean across all lead times and variables) OR the Diebold-Mariano p-value < 0.05 (alternative: Isotonic > Bayesian). (See US-3)
- **SC-003**: The slope of the reliability diagram (calibration slope) is measured against the ideal value of 1.0; the absolute deviation from 1.0 must be ≤ 0.05 for recalibrated methods, and strictly less than the baseline deviation. The slope is calculated via linear regression on probability bins (0.0-0.1,..., 0.9-1.0). (See US-1, US-2, US-3)
- **SC-004**: The PIT (Probability Integral Transform) histogram flatness is measured against a uniform distribution; the Kolmogorov-Smirnov p-value must be > 0.05 for recalibrated methods, and higher than the baseline p-value. The PIT histogram is generated using equal-width bins. (See US-1, US-2, US-3)
- **SC-005**: The convergence of the Bayesian model is measured against the R-hat statistic and Effective Sample Size (ESS); an R-hat value ≤ 1.05 AND ESS > 400 for all group-level parameters and hyperparameters confirms the validity of the posterior inference. If the 60-minute limit is exceeded, the status is "Timeout" and the result is marked as a fallback. (See US-3)
- **SC-006**: The difference in Brier score between the physics-informed prior and the flat prior control must be logged, and the physics-informed prior must demonstrate a lower Brier score than the flat prior to validate the improvement claim. (See US-3)
- **SC-007**: The pipeline MUST exit with code 1 and log the message "Data Availability Gate Failed" if the `probability_value` field is missing, verifying the hard stop condition. (See US-1)
- **SC-008**: The system MUST log the normality test result (Shapiro-Wilk p-value) and the selected test method (DM-HAC or Block Bootstrap) for every lead time, verifying the statistical test selection logic. (See US-2, US-3)
- **SC-009**: The validation split MUST prevent data leakage, verified by ensuring no observation date in the test set precedes any training date in the training set. (See US-2)

## Assumptions

- **Assumption about data availability**: The SubseasonalRodeo dataset is publicly accessible via the verified URL ` and contains the necessary GFS ensemble probability fields (`probability_value`) and ground-truth observations for the required variables (precipitation and temperature) across the full time range. **If these fields are missing, the project halts (see FR-001); no fallback to binary data is supported.**
- **Assumption about computational resources**: The CPU core, sufficient RAM, and disk constraints of the GitHub Actions free tier are sufficient to process the dataset and run the MCMC chains for the Bayesian model without exceeding memory limits or the 60-minute time limit for the Bayesian step.
- **Assumption about software environment**: The `pymc`, `scikit-learn`, `properscoring`, `arviz`, and `diebold-mariano` (or equivalent) libraries are available in the standard Python environment and do not require CUDA or GPU acceleration to function correctly.
- **Assumption about statistical validity**: The observational nature of the data means that any improvements in calibration metrics are associational and descriptive of the model's performance, not causal claims about the weather system itself.
- **Assumption about threshold justification**: The 70/30 split (years 1-N vs N+1) and the 2000 MCMC draws (with dynamic adjustment for ESS) are standard defaults for this scale of data; the mandatory sensitivity analysis (60/40, 80/20) and prior strength variations (including Flat Prior) ensure robustness.
- **Assumption about variable fit**: The GFS ensemble data contains the specific probability fields required for the analysis; if a specific variable is missing, the Data Availability Gate (FR-001) will halt the project.