# Feature Specification: Statistical Analysis of Sentiment Drift in Social Media During Economic Recessions

**Feature Branch**: `001-sentiment-drift`
**Created**: 2024-05-21
**Status**: Draft
**Input**: User description: "Statistical Analysis of Sentiment Drift in Social Media During Economic Recessions"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Acquisition, Alignment, and Preprocessing (Priority: P1)

The researcher MUST be able to ingest historical sentiment scores from social media datasets and macroeconomic indicators from official sources, align them to a common quarterly frequency, and handle missing data via documented interpolation.

**Why this priority**: Without aligned, clean time-series data, no statistical analysis can occur. This is the foundational data layer required for all subsequent modeling and is the primary bottleneck for reproducibility.

**Independent Test**: Can be fully tested by running the data ingestion script and verifying the existence of a single merged CSV file with quarterly timestamps, no missing values (or documented interpolation), and valid sentiment polarity ratios.

**Acceptance Scenarios**:

1. **Given** valid API access to FRED and HuggingFace datasets, **When** the ingestion script runs, **Then** GDP, unemployment, and sentiment data are merged on a quarterly timestamp.
2. **Given** raw daily sentiment data, **When** aggregation is performed, **Then** a quarterly average is computed to match the frequency of GDP and unemployment data, and low-confidence prediction periods (confidence <0.7) are flagged. Weeks with sentiment sample size below a sufficient threshold are excluded from the quarterly average calculation..
3. **Given** quarterly GDP and unemployment data with missing values, **When** linear interpolation is applied, **Then** the missing rate per series (defined as the percentage of total time-points in the series that lack a valid value) is ≤5%, and periods exceeding this threshold are flagged and excluded.

---

### User Story 2 - Statistical Modeling, Stationarity Testing, and Causal Inference (Priority: P2)

The researcher MUST be able to execute stationarity tests, select optimal lags, and run Granger causality tests to determine if sentiment predicts economic variables or vice versa.

**Why this priority**: This addresses the core research question regarding lead/lag relationships. It is the analytical core of the feature and directly answers the "does sentiment lead or lag?" hypothesis.

**Independent Test**: Can be fully tested by running the modeling notebook and verifying that p-values for Granger causality, ADF test statistics, and optimal lag orders are output for all variable pairs.

**Acceptance Scenarios**:

1. **Given** aligned quarterly time-series data, **When** the Augmented Dickey-Fuller (ADF) test is run, **Then** non-stationary series are differenced until I(0) stationarity is achieved or a fallback transformation (log/Box-Cox) is applied.
2. **Given** stationary series, **When** the Vector Autoregression (VAR) model is fit, **Then** the optimal lag length is selected via Akaike Information Criterion (AIC) and documented.
3. **Given** fitted VAR model, **When** Granger causality test is executed, **Then** F-test p-values are recorded for the relationship "Sentiment → GDP/Unemployment" and "GDP/Unemployment → Sentiment".
4. **Given** non-stationary series, **When** the Johansen cointegration test is run, **Then** the system selects the cointegration rank based on the trace statistic; if the trace and max-eigenvalue statistics conflict (e.g., trace suggests rank 2, max-eigen suggests rank 1), the system prioritizes the trace statistic unless the max-eigenvalue statistic exceeds the critical value by >10%, in which case the lag order is re-evaluated. If cointegration is detected, a VECM is used instead of a standard VAR.

---

### User Story 3 - Visualization, Robustness Validation, and Reporting (Priority: P3)

The researcher MUST be able to visualize the temporal relationships with recession shading and validate results through bootstrapping and sensitivity analysis on interpolation thresholds.

**Why this priority**: Visualization communicates findings, while bootstrapping and sensitivity analysis ensure the results are not artifacts of specific data handling choices. This completes the research deliverable.

**Independent Test**: Can be fully tested by generating the final report artifacts and verifying that confidence intervals are calculated, recession periods are shaded, and sensitivity analysis results are included.

**Acceptance Scenarios**:

1. **Given** model results, **When** plots are generated, **Then** time-series charts include shading for NBER-dated recession periods (e.g., recent historical downturns) sourced from the NBER Business Cycle Dating Committee.
2. **Given** test statistics, **When** Moving Block Bootstrap (MBB) validation runs with a minimum of 1,000 iterations (block length = 4 weeks) and a convergence check (CI width stabilizes within 1% for 3 consecutive runs), **Then** confidence intervals are calculated, and the consistency metric (CI width ≤20% of the original OLS coefficient) is verified, and the system reports a pass/fail status based on the CI width criterion.
3. **Given** the baseline analysis, **When** sensitivity analysis is performed, **Then** a small to moderate proportion of data is randomly masked and re-interpolated, and the resulting shift in p-values or causal direction is reported.

---

### User Story 4 - Sensitivity Analysis and Methodological Validity (Priority: P3)

The researcher MUST be able to execute a sensitivity analysis to validate the robustness of the causal inference against data perturbations and masking proportions.

**Why this priority**: This ensures the methodological validity of the findings by testing how sensitive the results are to data masking and interpolation choices, addressing the risk of spurious causality.

**Independent Test**: Can be fully tested by running the sensitivity analysis script and verifying that p-value shifts are calculated and reported for the specified masking range.

**Acceptance Scenarios**:

1. **Given** the baseline model, **When** the sensitivity analysis runs, **Then** the system masks a low percentage of the data points randomly and re-interpolates.
2. **Given** the masked datasets, **When** the model is re-run, **Then** the system calculates the absolute difference in p-values between the baseline and each masked run.
3. **Given** the calculated p-value shifts, **When** the results are reported, **Then** The system confirms that the absolute p-value shift remains within an acceptable threshold for any of the masking proportions..

---

### Edge Cases

- **FRED API incomplete data**: System MUST handle partial quarterly GDP data by flagging affected periods and applying linear interpolation to maintain quarterly alignment.
- **Non-stationary after differencing**: System MUST detect when series remain non-stationary after first differencing and log diagnostic output for researcher review, triggering fallback transformations.
- **Insufficient sentiment volume**: System MUST detect quarters with sentiment sample size below a sufficient threshold and flag these periods as low-confidence to prevent noise injection.
- **Collinearity of predictors**: If GDP and unemployment rates are highly correlated, the system MUST log a collinearity diagnostic (e.g., Variance Inflation Factor) and frame results as a joint relationship rather than independent effects.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download sentiment scores from HuggingFace Datasets (specifically `snap-cornell/twitter-roberta-base-sentiment-dataset`) aggregated to quarterly time series. (See US-1)
- **FR-002**: System MUST download economic indicators (GDP growth, unemployment rate, consumer confidence) from the FRED API via the `fred-macroeconomics` dataset (IDs: `FRED/GDP`, `FRED/UNRATE`) and align them to quarterly frequency using linear interpolation for missing values. (See US-1)
- **FR-003**: System MUST apply Augmented Dickey-Fuller (ADF) tests to verify stationarity of all input series (on quarterly data) and document p-values and test statistics. (See US-2)
- **FR-004**: System MUST conduct Granger causality tests (F-test) to determine predictive relationships between sentiment and economic variables, reporting p-values and F-statistics. (See US-2)
- **FR-005**: System MUST generate time-series visualizations with NBER recession period annotations (sourced from `) and cross-correlation heatmaps. (See US-3)
- **FR-006**: System MUST validate results using out-of-sample held-out recession periods (specifically masking the NBER recession dates) and Moving Block Bootstrap (MBB) confidence intervals (minimum 1,000 iterations, block length=4 weeks, convergence check: CI width stabilizes within 1% for 3 consecutive runs). (See US-3)
- **FR-007**: System MUST output analysis artifacts in a reproducible Jupyter Notebook format with embedded code, outputs, and narrative text, including `block_length` and `masking_proportion` attributes in the final JSON/CSV output. (See US-3)
- **FR-008**: System MUST handle FRED API incomplete data by flagging affected periods and applying linear interpolation to ensure ≥95% continuous quarterly alignment. (See US-1)
- **FR-009**: System MUST detect non-stationary series after first differencing, log diagnostic output, and apply fallback transformations (log, Box-Cox) if necessary. (See US-2)
- **FR-010**: System MUST flag sentiment data periods with sample size below a sufficient threshold as low-confidence and exclude them from primary analysis if they exceed a significant proportion of the dataset. (See US-1)
- **FR-011**: System MUST log the specific imputation method (forward-fill or interpolation) used for each variable and the percentage of data affected. (See US-1)
- **FR-012**: System MUST calculate and report the absolute p-value shift between the baseline model and each sensitivity analysis run ([deferred], [deferred], [deferred] masking). (See US-4)
- **FR-013**: System MUST select the cointegration rank based on the Johansen trace statistic, with a conflict resolution rule for trace vs. max-eigenvalue statistics. (See US-2)
- **FR-014**: System MUST validate the detected sentiment drift against an external economic event timeline (e.g., NBER recession start/end dates) to ensure scientific validity. (See US-3)

### Key Entities *(include if feature involves data)*

- **TimeSeries**: Represents aligned quarterly data points containing sentiment polarity (positive/negative/neutral ratios), GDP growth rate, and unemployment rate.
- **ModelResult**: Represents statistical output including p-values, lag lengths, F-statistics, confidence intervals, `block_length`, and `masking_proportion` for Granger causality and VAR/VECM models.
- **RecessionPeriod**: Represents time boundaries of known economic downturns (e.g., NBER dates) used for validation and visualization shading.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Statistical significance is measured against the standard p-value threshold (<0.05) for Granger causality tests to determine causal precedence. (Validates FR-004, See US-2)
- **SC-002**: Data completeness is measured against the requirement for continuous quarterly time-series alignment without manual intervention, ensuring ≥95% coverage. (Validates FR-001, FR-002, FR-008, See US-1)
- **SC-003**: Reproducibility is measured against the successful execution of the analysis notebook from raw data to final visualization on a standard CPU-only environment. (Validates FR-007, See US-3)
- **SC-004**: Robustness is measured against the consistency of results across Moving Block Bootstrap resamples. Consistency is quantified as: (a) the width of the bootstrap confidence interval for key statistics must be ≤20% of the original OLS coefficient, (b) the interval must contain the original point estimate, and (c) the coefficient of variation (CV) of the bootstrap distribution must be <0.1. (Validates FR-006, See US-3)
- **SC-005**: Output quality is measured against the inclusion of recession shading in all time-series plots and the documentation of all dataset URLs and DOIs in the metadata. (Validates FR-005, FR-007, See US-3)
- **SC-006**: Methodological validity is measured by the successful application of sensitivity analysis where [deferred] to [deferred] of data is randomly masked and re-interpolated, with reported shifts in p-values within a negligible absolute difference. (Validates FR-012, US-4, See US-4)

## Assumptions

- Users have valid API access credentials for the FRED API and can access HuggingFace Datasets without rate-limiting restrictions during the analysis window.
- Historical data exists in sufficient quantity to cover the global financial crisis and the 2020 COVID-19 recession periods, providing adequate statistical power for Granger causality tests.
- The computational environment is CPU-only (no GPU), with sufficient RAM and disk space to process the sampled dataset and run a minimum of 1,000 bootstrap iterations within a fixed time limit.
- Social media sentiment scores derived from the specified pre-trained model are sufficiently accurate for macroeconomic correlation, and the model's confidence scores are reliable indicators of prediction quality.
- Linear interpolation is an acceptable method for handling missing values in quarterly macroeconomic variables, provided the missing rate remains ≤5% per series.
- The MVP scope focuses on major recession periods as default validation sets, but the system is designed to support configurable recession period selection.
- Impulse response functions are standard visualization practice for VAR model results but are considered optional for MVP completion if computational resources are constrained.
- The analysis treats the relationship as associational; causal claims are framed strictly within the limits of observational data and Granger causality definitions.