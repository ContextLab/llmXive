# Feature Specification: Statistical Analysis of Flight Delay Distributions

**Feature Branch**: `001-flight-delay-distributions`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Do flight delay times follow heavy‑tailed probability distributions, and if so, which parametric models (e.g., exponential, gamma, log‑normal, Pareto) best capture the observed tails compared to conventional short‑tailed models?"

## User Scenarios & Testing

### User Story 1 - Data Acquisition and Pre-processing (Priority: P1)

The system MUST successfully retrieve the Bureau of Transportation Statistics (BTS) On-Time Performance CSV data for a specified recent year (e.g., 2022), load it into memory, and produce a clean dataset of total delay minutes ready for statistical analysis. The system MUST handle the full year's data without fallback to partial or test datasets. If memory limits are exceeded, the pipeline MUST fail gracefully with a clear error message rather than switching to a subset. The system MUST also perform a sensitivity analysis excluding zero-delay records for tail fitting.

**Why this priority**: Without a clean, valid dataset containing the target variable (delay minutes), no statistical modeling, fitting, or hypothesis testing can occur. This is the foundational block of the research pipeline.

**Independent Test**: The pipeline can be run in isolation to download, parse, and filter the BTS data, outputting a summary report (e.g., "Loaded N valid records, mean delay X minutes, retention rate Y%") without performing any distribution fitting. The test suite explicitly validates that the acceptance criteria for US-1 are met, including the retention rate calculation and zero-exclusion sensitivity analysis.

**Acceptance Scenarios**:

1. **Given** a valid BTS CSV URL for 2022, **When** the pipeline executes the download and load step, **Then** the system retrieves the file and parses it into a DataFrame without crashing due to network or format errors.
2. **Given** the raw loaded data, **When** the pre-processing filter runs, **Then** negative delay values are removed, missing values are treated as 0 (with a flag for zero-inflation analysis), and only commercial U.S. flights are retained, resulting in a final dataset where `min(delay) >= 0`.
3. **Given** a dataset with >100,000 records, **When** the pre-processing completes, **Then** the resulting dataset fits within the 7 GB RAM limit of the CI runner, with peak memory usage measured to be ≤ 6.5 GB as reported by the runner's resource monitor. If this limit is exceeded, the system MUST terminate with a non-zero exit code and the message "Memory limit exceeded: full dataset cannot be loaded."
4. **Given** the full dataset, **When** the retention analysis runs, **Then** the system calculates and reports the retention rate (valid records / total downloaded) in the summary output.
5. **Given** the full dataset, **When** the zero-inflation sensitivity analysis runs, **Then** the system produces a separate subset excluding records with delay = 0 to assess the impact on tail index estimation.
6. **Given** the full dataset, **When** the anomaly check runs, **Then** records with delay > 1440 minutes are flagged in a new column `is_anomaly` (boolean) and logged to stderr. Additionally, records with delay > 10,000 minutes (suspected data entry errors) are flagged in a separate column `is_data_error` (boolean) and excluded from the primary analysis subset, with a sensitivity analysis run performed on the subset excluding these error records to assess their impact on the tail index.

---

### User Story 2 - Parametric Model Fitting and Goodness-of-Fit Evaluation (Priority: P2)

The system MUST fit multiple candidate parametric distributions (Exponential, Gamma, Log-Normal, Weibull, Pareto) to the cleaned delay data and compute goodness-of-fit metrics (AIC, BIC, KS, AD) for each model to determine statistical performance. The system MUST estimate a tail threshold (x_min) before fitting the Pareto distribution. The system MUST perform a Vuong test to statistically compare the best heavy-tailed candidate against the best short-tailed candidate.

**Why this priority**: This is the core analytical engine. It directly addresses the research question by quantifying how well different theoretical models match the empirical data. Without this, the "heavy-tail" hypothesis cannot be tested.

**Independent Test**: The analysis can be run on a static, pre-processed CSV file (mock data) to verify that all five distributions are fitted, parameters are estimated via Maximum Likelihood, the four metrics (AIC, BIC, KS, AD) are calculated, and the Vuong test is performed for non-nested comparisons. The test suite explicitly validates that the acceptance criteria for US-2 are met, including the Vuong test and tail threshold estimation.

**Acceptance Scenarios**:

1. **Given** a cleaned dataset of delay minutes, **When** the fitting routine executes, **Then** the system estimates parameters for at least 5 distinct distributions (Exponential, Gamma, Log-Normal, Weibull, Pareto) using Maximum Likelihood Estimation (MLE). For Pareto, fitting is restricted to the tail region where `delay >= x_min`.
2. **Given** the fitted models, **When** the evaluation step runs, **Then** the system outputs a comparison table containing AIC, BIC, KS statistic, and Anderson-Darling statistic for every fitted model.
3. **Given** the evaluation results, **When** the system identifies the best model, **Then** it correctly selects the model with the lowest AIC/BIC score as the primary candidate, subject to tail diagnostic validation.
4. **Given** the fitted models, **When** the Vuong test executes, **Then** the system compares the best heavy-tailed candidate against the best short-tailed candidate and reports the p-value.
5. **Given** the sum distribution and individual components (ArrDelay, DepDelay), **When** the comparison step runs, **Then** the system generates side-by-side histograms and reports the Kolmogorov-Smirnov test p-value comparing the distributions.

---

### User Story 3 - Heavy-Tail Diagnostics and Visualization (Priority: P3)

The system MUST perform specific heavy-tail diagnostics (Hill estimator on the top k records, where k is selected via stability analysis within the constraint k/n ≤ 0.1, and x_min is estimated via KS minimization) and generate visualizations (log-log survival plot, QQ-plots) to visually and numerically confirm the tail behavior of the best-fit model. The system MUST reject a model selected by bulk metrics if it fails tail diagnostics.

**Why this priority**: While P2 determines the "best fit" numerically, P3 provides the specific evidence required to distinguish "heavy-tailed" from "short-tailed" behavior, which is the specific hypothesis of the research. This validates the *nature* of the distribution, not just its fit.

**Independent Test**: The system can generate the log-log survival plot, Hill estimator output, and tail KS test results for a provided dataset, producing a visual confirmation of linearity (indicating power-law behavior) or curvature (indicating exponential decay). The test suite explicitly validates that the acceptance criteria for US-3 are met, including the tail KS test and R² calculation.

**Acceptance Scenarios**:

1. **Given** the top k records (where k is determined by minimizing the variance of alpha estimates over a sliding window of size w=10, constrained to k/n ≤ 0.1), **When** the Hill estimator is applied, **Then** the system outputs a tail index estimate with a confidence interval and reports the selected k value.
2. **Given** the full dataset and the best-fit model, **When** the visualization routine runs, **Then** it generates a log-log survival plot where the empirical data and the fitted Pareto line are overlaid.
3. **Given** the fitted models, **When** the QQ-plot generation runs, **Then** it produces a plot comparing empirical quantiles against theoretical quantiles for the top-performing model.
4. **Given** the tail subset (x >= x_min), **When** the tail KS test runs, **Then** the system reports the p-value for the goodness-of-fit of the heavy-tailed model against the empirical tail data.
5. **Given** the AIC-selected model, **When** the validation logic runs, **Then** the system rejects the model if the log-log plot is non-linear (R² < 0.95) or the Hill index is unstable, and flags the next best candidate.

---

### Edge Cases

- **What happens when** the downloaded BTS data contains zero valid records (e.g., due to a year selection error or API change)?
  - *Handling*: The pipeline MUST fail gracefully with a clear error message: "No valid delay records found for the specified year," and exit with a non-zero code, preventing downstream statistical errors.
- **How does the system handle** extreme outliers where delay minutes exceed 10,000 (e.g., data entry errors)?
 - *Handling*: The pre-processing step MUST flag values > 10,000 minutes as data errors in the metadata (column `is_data_error`) and exclude them from the primary analysis. A specific sensitivity analysis run MUST be performed excluding these error records to assess their impact on the tail index. Values between extended durations (e.g., on the order of a full day) and [deferred] minutes are flagged as anomalies. (`is_anomaly`), logged to stderr, and retained in the dataset for the primary analysis, but a separate sensitivity analysis excluding these anomalies must also be performed.
- **What happens when** the MLE optimization fails to converge for a specific distribution (e.g., Pareto on light-tailed data)?
  - *Handling*: The system MUST catch the convergence exception, record the failure for that specific model, and continue evaluating other models. The requirement is met if at least 3 models converge with finite parameters.
- **What happens when** the data contains a massive spike at zero (missing values treated as 0)?
  - *Handling*: The system MUST perform a sensitivity analysis by excluding zero-delay records for the tail fitting (Hill estimator and Pareto fitting) to ensure the heavy-tail hypothesis is not an artifact of zero-inflation.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download and parse the BTS On-Time Performance CSV for a user-specified year, filtering for commercial U.S. flights and valid delay minutes (See US-1).
- **FR-002**: System MUST compute the total delay as `ArrDelay + DepDelay`, treating missing values as 0 and removing negative values. The system MUST explicitly compare the distribution shape of the sum against the individual components by generating side-by-side histograms and reporting the Kolmogorov-Smirnov test p-value. The system MUST also perform a sensitivity analysis excluding zero-delay records for tail fitting to mitigate zero-inflation distortion (See US-1).
- **FR-003**: System MUST fit at least five parametric distributions (Exponential, Gamma, Log-Normal, Weibull, Pareto) to the delay data using Maximum Likelihood Estimation. For the Pareto distribution, fitting MUST be restricted to the tail region where `delay >= x_min` (See US-2).
- **FR-004**: System MUST calculate and report AIC, BIC, Kolmogorov-Smirnov, and Anderson-Darling statistics for every fitted model (See US-2).
- **FR-005**: System MUST estimate the tail index using the Hill estimator on the top k records, where k is determined by minimizing the variance of alpha estimates over a sliding window of size w=10, constrained to k/n ≤ 0.1, applied only to data above the estimated `x_min` threshold (See US-3).
- **FR-006**: System MUST generate a log-log survival plot and a QQ-plot comparing the empirical data against the best-fitting model (See US-3).
- **FR-007**: System MUST frame all findings as associational (not causal) since the data source is observational (See US-1).
- **FR-008**: System MUST ensure all computations complete within 6 hours on a CPU-only environment with ≤7 GB RAM (See US-1, US-2).
- **FR-009**: System MUST perform the Vuong test to statistically compare the best heavy-tailed candidate model against the best short-tailed candidate model and report the p-value (See US-2).
- **FR-010**: System MUST perform a Kolmogorov-Smirnov goodness-of-fit test specifically on the tail subset (x >= x_min) to validate the heavy-tail hypothesis (See US-3).
- **FR-011**: System MUST calculate the R² value for the log-log survival plot using Ordinary Least Squares (OLS) regression on the log-log transformed tail data points and report it (See US-3).
- **FR-012**: System MUST calculate the retention rate as `valid_records / total_downloaded` and report it in the summary output (See US-1).
- **FR-013**: System MUST define the pass/fail condition for model fitting: the requirement is met if at least 3 models converge with finite parameters (See US-2).
- **FR-014**: System MUST estimate the tail threshold `x_min` via Kolmogorov-Smirnov minimization before applying the Hill estimator or fitting the Pareto distribution (See US-3).
- **FR-015**: System MUST reject a model selected by bulk metrics (AIC/BIC) if it fails the tail diagnostic (non-linear log-log plot with R² < 0.95 or unstable Hill index) and flag the next best candidate (See US-3).
- **FR-016**: System MUST generate a JSON schema for the `TailIndexEstimate` entity and save it to the contracts directory (See US-3).

### Key Entities

- **DelayRecord**: Represents a single flight event. Key attributes: `flight_id`, `total_delay_minutes` (continuous, ≥0), `carrier`, `origin`, `destination`.
- **DistributionModel**: Represents a fitted parametric distribution. Key attributes: `name` (e.g., "Log-Normal"), `parameters` (dict of MLE estimates), `metrics` (dict of AIC, BIC, KS, AD).
- **TailIndexEstimate**: Represents the heavy-tail diagnostic result. Key attributes: `method` (Hill), `threshold_k` (number of records), `estimated_alpha` (tail index), `confidence_interval`, `stability_range`. (See FR-005, FR-010, FR-014, FR-016).

## Success Criteria

### Measurable Outcomes

- **SC-001**: The pipeline successfully processes the downloaded BTS records into a valid `DelayRecord` set without memory overflow; the retention rate (valid/total) is measured and reported and must be ≥ 95% [See US-1].
- **SC-002**: At least three distinct parametric models yield a finite AIC and BIC score, allowing for a comparative ranking [See US-2].
- **SC-003**: The Hill estimator produces a finite tail index value for the top portion of the data, enabling a heavy-tail assessment [See US-3].
- **SC-004**: The best-fitting model is identified via the lowest AIC score, and the log-log survival plot of this model yields an R² value ≥ 0.95 against the empirical tail data [See US-3].
- **SC-005**: The entire analysis (download, pre-processing, fitting, diagnostics, plotting) completes within 3600 seconds [See US-2].
- **SC-006**: The Vuong test produces a p-value comparing the heavy-tailed vs. short-tailed candidates [See US-2].
- **SC-007**: The tail KS test produces a p-value for the goodness-of-fit of the heavy-tailed model on the tail subset [See US-3].
- **SC-008**: The comparison between the sum distribution and individual components yields a KS test p-value and side-by-side histograms [See US-1].
- **SC-009**: The Hill estimator stability analysis is performed and the variance minimization results are reported [See US-3].
- **SC-010**: The Vuong test p-value is reported for the comparison of heavy-tailed vs. short-tailed models [See US-2].
- **SC-011**: The tail KS test p-value is reported for the heavy-tail model on the tail subset [See US-3].

## Assumptions

- **Assumption about data availability**: The BTS On-Time Performance CSV for the target year (e.g., 2022) is publicly accessible via the standard `transtats.bts.gov` endpoint and follows the documented schema without unexpected column renames. If the full year's data is not available, the system MUST fail; no fallback to partial or test datasets is permitted.
- **Assumption about variable fit**: The `ArrDelay` and `DepDelay` fields in the BTS dataset are sufficient to represent "total delay" for the purpose of distributional analysis; no additional covariates (e.g., weather, specific aircraft type) are required for the univariate distribution fitting.
- **Assumption about computational limits**: The dataset for a single year of U.S. commercial flights will not exceed a manageable size for RAM when loaded into a pandas DataFrame, allowing for standard in-memory processing. If it does, the pipeline is designed to fail gracefully rather than fallback to partial data.
- **Assumption about methodological constraints**: The analysis is purely observational; therefore, no causal claims about the *causes* of delays will be made, only the *shape* of the delay distribution.
- **Assumption about threshold selection**: While a fixed 5% threshold is a common heuristic, the Hill estimator requires a data-driven threshold selection via stability plots to ensure methodological soundness. A sensitivity analysis over a range of k values (constrained to k/n ≤ 0.1) will be performed to identify the stable region. The search range for the stability analysis is explicitly capped at k/n ≤ 0.1; if no stable region is found within this cap, the system reports the minimum variance found at the cap boundary.
- **Assumption about model convergence**: The `scipy.stats` MLE routines will converge for the majority of the candidate distributions on this dataset; non-convergence will be treated as a model failure rather than a system crash.
- **Assumption about zero-inflation**: Treating missing values as 0 creates a spike that distorts tail analysis; the sensitivity analysis excluding zeros is sufficient to mitigate this construct validity issue.
- **Assumption about data errors**: Values exceeding a reasonable operational threshold for the study duration are treated as data entry errors and excluded from the primary analysis.., with a specific sensitivity analysis performed to quantify their impact.