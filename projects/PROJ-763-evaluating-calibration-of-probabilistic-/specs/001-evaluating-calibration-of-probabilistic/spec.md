# Feature Specification: Evaluating Calibration of Probabilistic Weather Forecasts

**Feature Branch**: `001-evaluating-calibration-weather`  
**Created**: 2026-06-22  
**Status**: Draft  
**Input**: User description: "Evaluating Calibration of Probabilistic Weather Forecasts"

## User Scenarios & Testing

### User Story 1 - Baseline Calibration Assessment (Priority: P1)

The researcher needs to download the SubseasonalRodeo dataset, align NOAA GFS ensemble forecasts with ground-truth observations, and compute baseline calibration metrics (Brier score, CRPS, reliability diagrams) to quantify existing mis-calibration without any post-processing.

**Why this priority**: This establishes the ground truth for the project. Without a rigorous baseline measurement of the raw model's performance, any claim of improvement via recalibration is scientifically invalid. This is the minimum viable research step.

**Independent Test**: The pipeline executes successfully on the GitHub Actions runner, downloading the dataset, performing alignment, and outputting a `results_baseline.csv` file containing Brier scores and CRPS for all lead times, plus a `reliability_diagram_raw.png`. The test passes if the file exists and contains non-null values for all requested metrics.

**Acceptance Scenarios**:

1. **Given** the SubseasonalRodeo dataset is accessible via `wget`, **When** the pipeline runs the download and alignment script, **Then** the system produces a clean, aligned dataset where forecast probabilities and observations match by grid point, lead time, and date.
2. **Given** the aligned dataset, **When** the baseline metrics module runs, **Then** the system calculates the Brier score and CRPS for each lead time and variable, storing them in a structured CSV with no missing values.
3. **Given** the aligned dataset, **When** the reliability diagram generator runs, **Then** the system outputs a kernel-smoothed reliability diagram (PNG) that visually maps forecast probability bins against observed frequencies.

---

### User Story 2 - Isotonic Recalibration (Priority: P2)

The researcher needs to apply isotonic regression to the baseline forecasts using a 70/30 train-test split to correct systematic biases and measure the improvement in calibration metrics compared to the raw baseline.

**Why this priority**: This implements the first proposed intervention. It tests whether a non-parametric, monotonic method (isotonic regression) can effectively remove bias in the probability estimates, serving as a robust baseline for the more complex Bayesian method.

**Independent Test**: The pipeline runs the isotonic regression module on the training split, applies the fitted model to the held-out test split, and outputs a `results_isotonic.csv` and `reliability_diagram_isotonic.png`. The test passes if the new Brier score is lower than the baseline (or within statistical noise) and the reliability diagram shows reduced deviation from the diagonal.

**Acceptance Scenarios**:

1. **Given** the baseline metrics and the training split, **When** the isotonic regression model is fitted, **Then** the system produces a monotonic mapping function for each lead time and variable that preserves the rank order of forecasts.
2. **Given** the fitted model and the test split, **When** the recalibrated probabilities are generated, **Then** the system computes new Brier scores and CRPS, demonstrating a reduction in error relative to the baseline metrics.
3. **Given** the recalibrated probabilities, **When** the reliability diagram is regenerated, **Then** the plotted points lie closer to the 45-degree line of perfect calibration compared to the raw forecast diagram.

---

### User Story 3 - Bayesian Hierarchical Recalibration (Priority: P3)

The researcher needs to implement a Bayesian hierarchical logistic regression model that shares information across lead times to recalibrate forecasts, specifically targeting improvements in sparse event categories (e.g., heavy precipitation) and comparing its performance against isotonic regression.

**Why this priority**: This explores the advanced method proposed in the idea. While computationally heavier, it offers potential gains in data-sparse regimes by borrowing strength across lead times. It is P3 because the isotonic method is the primary "simple" solution, and this is an enhancement.

**Independent Test**: The pipeline executes the Bayesian model (using PyMC or statsmodels) with short MCMC chains (500 draws, 2 chains) on the training split, applies the posterior predictive probabilities to the test split, and outputs `results_bayesian.csv`. The test passes if the model converges (R-hat < 1.1) and produces a Brier score that is comparable to or better than isotonic regression.

**Acceptance Scenarios**:

1. **Given** the training data and a hierarchical model structure, **When** the MCMC sampler runs, **Then** the system completes the sampling within the 6-hour CI limit and reports convergence diagnostics (R-hat, effective sample size) for all parameters.
2. **Given** the posterior distributions, **When** predictions are generated for the test set, **Then** the system produces recalibrated probabilities that account for lead-time correlations, specifically improving performance on rare events compared to the isotonic method.
3. **Given** the Bayesian results, **When** the metrics are computed, **Then** the system outputs a comparison table showing Brier score and CRPS improvements relative to both the raw baseline and the isotonic method.

---

### Edge Cases

- **What happens when the dataset download fails or is incomplete?** The pipeline must detect a non-zero exit code from `wget` or a corrupted file checksum, stop execution, and log a clear error message "Dataset acquisition failed" rather than proceeding with partial data.
- **How does the system handle grid points with zero observed events?** For lead times/variables where the observation count is zero (perfectly dry), the Brier score calculation must handle division-by-zero or empty bin scenarios gracefully, returning `NaN` or `0.0` with a warning, rather than crashing the script.
- **What happens if MCMC chains fail to converge?** If the Bayesian model fails to converge (R-hat > 1.1) after the maximum iterations, the system must flag the result as "Unconverged" in the output CSV and proceed with the isotonic results as the fallback, rather than halting the entire pipeline.
- **How does the system handle lead times with extremely sparse data?** For lead times with very few data points (e.g., < 100 samples), the isotonic regression might overfit; the system must enforce a minimum sample size threshold or fallback to the raw forecast for those specific bins.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download the SubseasonalRodeo dataset (≈2 GB) via `wget` and verify file integrity before processing. (See US-1)
- **FR-002**: System MUST align forecast probabilities with observations by grid point, lead time, and date, discarding any records with missing values in either field. (See US-1)
- **FR-003**: System MUST compute Brier scores, Continuous Ranked Probability Scores (CRPS), and generate kernel-smoothed reliability diagrams for raw forecasts. (See US-1)
- **FR-004**: System MUST fit an isotonic regression model on a [deferred] training split and apply the transformation to the [deferred] held-out test split for each lead time and variable. (See US-2)
- **FR-005**: System MUST implement a Bayesian hierarchical logistic regression model that shares information across lead times and generates posterior predictive probabilities. (See US-3)
- **FR-006**: System MUST perform paired statistical tests (t-test, α=0.05) to compare Brier scores and CRPS between the baseline and each recalibrated method. (See US-2, US-3)
- **FR-007**: System MUST output all results (metrics, diagrams, convergence diagnostics) to a single `results` directory with standardized filenames (e.g., `results_baseline.csv`, `reliability_diagram_isotonic.png`). (See US-1, US-2, US-3)

### Key Entities

- **Forecast Record**: Represents a single ensemble forecast instance, containing attributes: `grid_id`, `lead_time`, `forecast_date`, `probability_value`, `raw_ensemble_mean`.
- **Observation Record**: Represents the ground truth event, containing attributes: `grid_id`, `observation_date`, `event_occurred` (binary), `event_value` (continuous for temp/rain).
- **Calibration Metric**: Represents a computed statistic, containing attributes: `metric_name` (Brier, CRPS), `lead_time`, `method` (raw, isotonic, bayesian), `value`, `confidence_interval`.
- **Recalibrator Model**: Represents a fitted post-processing function, containing attributes: `method_type`, `lead_time`, `parameters` (coefficients or isotonic knots), `training_sample_size`.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The reduction in Brier score for the isotonic method is measured against the baseline Brier score; a statistically significant reduction (paired t-test, p < 0.05) confirms improvement. (See US-2)
- **SC-002**: The reduction in CRPS for the Bayesian method is measured against the isotonic method's CRPS; a non-inferior or lower CRPS confirms the value of the hierarchical approach. (See US-3)
- **SC-003**: The slope of the reliability diagram (calibration slope) is measured against the ideal value of 1.0; a value closer to 1.0 for recalibrated methods than the raw baseline indicates better calibration. (See US-1, US-2, US-3)
- **SC-004**: The PIT (Probability Integral Transform) histogram flatness is measured against a uniform distribution; a flatter histogram (lower Kolmogorov-Smirnov statistic) for recalibrated methods indicates better probabilistic consistency. (See US-1, US-2, US-3)
- **SC-005**: The computational runtime of the entire pipeline is measured against the 6-hour GitHub Actions limit; completion within ≤ 30 minutes confirms CPU feasibility. (See US-1, US-2, US-3)
- **SC-006**: The convergence of the Bayesian model is measured against the R-hat statistic; an R-hat value ≤ 1.05 for all parameters confirms the validity of the posterior inference. (See US-3)

## Assumptions

- **Assumption about data availability**: The SubseasonalRodeo dataset is publicly accessible via the specified URL and contains the necessary GFS ensemble probability fields and ground-truth observations for the required variables (precipitation and temperature) across the full time range.
- **Assumption about computational resources**: The 2 CPU core, 7 GB RAM, and 14 GB disk constraints of the GitHub Actions free tier are sufficient to process the ~2 GB dataset and run the MCMC chains for the Bayesian model without exceeding memory limits or the 6-hour time limit.
- **Assumption about software environment**: The `pymc`, `scikit-learn`, `properscoring`, and `arviz` libraries are available in the standard Python environment and do not require CUDA or GPU acceleration to function correctly.
- **Assumption about statistical validity**: The observational nature of the data means that any improvements in calibration metrics are associational and descriptive of the model's performance, not causal claims about the weather system itself.
- **Assumption about threshold justification**: The 70/30 train-test split and the 500 MCMC draws are standard defaults for this scale of data; a sensitivity analysis will sweep the split ratio (e.g., 60/40, 80/20) and chain length (e.g., 300, 700) to ensure robustness.
- **Assumption about variable fit**: The GFS ensemble data contains the specific probability fields required for the analysis; if a specific variable (e.g., heavy precipitation probability) is missing or aggregated, the analysis will fall back to the available binary occurrence data.
