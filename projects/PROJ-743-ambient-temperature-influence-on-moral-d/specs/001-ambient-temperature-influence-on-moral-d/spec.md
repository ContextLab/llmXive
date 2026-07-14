# Feature Specification: Ambient Temperature Influence on Moral Decision Speed

**Feature Branch**: `001-ambient-temp-moral-speed`  
**Created**: 2026-06-21  
**Status**: Draft  
**Input**: User description: "Ambient Temperature Influence on Moral Decision Speed"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Temperature Matching (Priority: P1)

The system must ingest the Moral Machine dataset and successfully match each response record with historical ambient temperature data from ERA5 Reanalysis based on geographic coordinates and timestamps.

**Why this priority**: This is the foundational data layer. Without accurate temperature variables linked to specific moral decisions, no statistical analysis can occur. It is the prerequisite for all subsequent modeling.

**Independent Test**: Can be fully tested by running the ingestion script on a small, known subset of the Moral Machine data and verifying that every output record contains a valid temperature value within a reasonable geographic range and that no records are dropped due to missing location data.

**Acceptance Scenarios**:

1. **Given** a valid Moral Machine CSV file and access to ERA5 Reanalysis data, **When** the ingestion script runs, **Then** the percentage of original records successfully matched with ERA5 temperature data is measured against the total number of records with valid location data.
2. **Given** a record with ambiguous location data (e.g., missing latitude/longitude), **When** the script processes the record, **Then** the record is flagged in a `data_quality_log` and excluded from the primary analysis dataset.
3. **Given** a record where the timestamp falls outside the available ERA5 coverage period, **When** the script processes the record, **Then** the record is excluded and logged with the reason "ERA5 coverage gap".

---

### User Story 2 - Mixed-Effects Regression Modeling (Priority: P2)

The system must fit a linear mixed-effects model (with log-transformed response times) or a Generalized Linear Mixed Model (GLMM) to quantify the association between ambient temperature and moral decision response time, controlling for participant ID, cultural region, dilemma complexity, and response type.

**Why this priority**: This addresses the core research question. It transforms the raw data into a statistical estimate of the temperature effect, directly testing the hypothesis while accounting for the non-normal distribution of reaction times and potential confounds.

**Independent Test**: Can be fully tested by running the modeling script on the pre-processed dataset and verifying that the model converges, produces a coefficient for `temperature_celsius`, and reports a p-value for the fixed effect.

**Acceptance Scenarios**:

1. **Given** the merged dataset with temperature and response time, **When** the regression model is fitted, **Then** the output includes a fixed-effect coefficient for `temperature_celsius` with a standard error and p-value.
2. **Given** the model output, **When** the likelihood-ratio test is performed against a null model (without temperature), **Then** the test statistic and p-value are recorded in the results log.
3. **Given** the fitted model, **When** residuals are analyzed, **Then** diagnostic plots (QQ-plot, residual vs. fitted) are generated to assess normality and homoscedasticity assumptions of the transformed data.

---

### User Story 3 - Robustness and Sensitivity Analysis (Priority: P3)

The system must execute robustness checks, including alternative temperature metrics (e.g., 3-hour moving average), sensitivity analysis on temperature thresholds, and a specific analysis for the indoor/outdoor confound, to ensure the findings are not artifacts of specific data choices.

**Why this priority**: This validates the reliability of the P2 results. It ensures the observed effect is robust to minor variations in data processing, modeling assumptions, and the validity of the temperature proxy.

**Independent Test**: Can be fully tested by running the robustness script and verifying that it produces a summary table comparing the primary model results with alternative specifications.

**Acceptance Scenarios**:

1. **Given** the primary model results, **When** the robustness script runs, **Then** it generates a comparison table showing the temperature coefficient and p-value for at least two alternative temperature metrics (e.g., raw hourly vs. 3-hour moving average).
2. **Given** a decision cutoff for temperature outliers, **When** the sensitivity analysis runs, **Then** it sweeps the cutoff threshold over a range of standard deviations and reports how the headline temperature coefficient varies.
3. **Given** the full analysis pipeline, **When** it completes, **Then** all generated figures (scatter plots, conditional effect plots) are saved to the `results/` directory in a standard format (e.g., PNG).

---

### Edge Cases

- What happens when the ERA5 grid cell nearest to a Moral Machine response location is >100km away? (System MUST flag this as a "low confidence match" and log the reason "distance > 100km" in the data quality log, then exclude the record).
- How does the system handle response times that are physically impossible (e.g., <100ms or >10,000ms)? (System MUST apply a hard filter to remove these outliers before modeling).
- What happens if the temperature data contains missing values for a specific hour? (System should interpolate linearly or use the nearest available hourly reading, but only if the gap is ≤2 hours; otherwise, exclude the record).

## Requirements

### Functional Requirements

- **FR-001**: System MUST ingest the Moral Machine dataset and merge it with ERA5 Reanalysis historical temperature data using geographic coordinates and timestamps as keys. (See US-1)
- **FR-002**: System MUST filter out records with temperature values outside the range of extreme cold to extreme heat. (See US-1)
- **FR-003**: System MUST fit a linear mixed-effects model with log-transformed response time as the dependent variable, ambient temperature as the fixed effect, and random intercepts for participant ID and cultural region. If log-transformation fails, a GLMM with a log-link function MUST be used. (See US-2)
- **FR-004**: System MUST include covariates for participant age (if available at aggregate country level), gender (if available at aggregate country level), dilemma complexity score (derived independently of response time from static dilemma attributes), and time-of-day in the primary regression model. (See US-2)
- **FR-005**: System MUST perform a likelihood-ratio test comparing the full model (with temperature) to a null model (without temperature) to assess statistical significance. (See US-2)
- **FR-006**: System MUST execute a sensitivity analysis that sweeps the temperature outlier threshold over a range of standard deviations and reports the variation in the temperature coefficient. (See US-3)
- **FR-007**: System MUST generate diagnostic plots for model residuals (QQ-plot and residual vs. fitted) to verify normality and homoscedasticity assumptions of the transformed data. (See US-2)
- **FR-008**: System MUST export all results, including model coefficients, p-values, and generated figures, to the `results/` directory in a reproducible format. (See US-3)
- **FR-009**: System MUST flag or exclude records where the distance to the nearest ERA5 grid point exceeds 100km and log the reason "distance > 100km". (See US-1)
- **FR-010**: System MUST filter out response times <100ms or >10,000ms before any modeling occurs. (See US-1)
- **FR-011**: System MUST control for the specific dilemma choice (e.g., "save the many" vs. "save the few") as a fixed effect or interaction term to prevent confounding, and ensure dilemma complexity is derived independently of response time. (See US-2)
- **FR-012**: System MUST perform a sensitivity analysis for the indoor/outdoor confound by stratifying the data or applying a proxy adjustment (using urban/rural classification of the coordinate) if metadata is available; if neither is available, the system MUST report the limitation and quantify the potential noise impact via robustness checks. (See US-3)
- **FR-013**: System MUST test for non-linearity in the temperature effect by including a quadratic term (temperature^2) or using a spline basis, and compare the model fit against the linear-only model. (See US-2)
- **FR-014**: System MUST validate all data sources against the project constitution's 'Verified Accuracy' principle before ingestion, rejecting any source that does not meet the hourly resolution or geographic coverage standards. (See US-1)

### Key Entities

- **Moral Response**: A single decision event containing participant ID, location coordinates, timestamp, dilemma ID, response time, and demographic data.
- **Temperature Record**: A meteorological data point containing grid ID, timestamp, latitude, longitude, and ambient temperature in Celsius.
- **Merged Dataset**: The combined entity linking Moral Responses to Temperature Records, serving as the input for statistical modeling.
- **Model Output**: The statistical result containing fixed-effect coefficients, standard errors, p-values, and random effect variances.
- **Dilemma Complexity**: A static metric derived from the number of lives at stake and the specific dilemma type, explicitly excluding response time from its calculation.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The percentage of Moral Machine records successfully matched with ERA5 temperature data is measured against the total number of records with valid location data. (See US-1)
- **SC-002**: The statistical significance of the temperature coefficient (p-value) is measured against a standard alpha threshold to determine if the association is non-zero. (See US-2)
- **SC-003**: The variation in the temperature coefficient across the sensitivity analysis thresholds is measured against the primary model coefficient to assess robustness. (See US-3)
- **SC-004**: The convergence status of the mixed-effects model is measured against the requirement of successful optimization (no convergence warnings) to ensure valid inference. (See US-2)
- **SC-005**: The distribution of model residuals is measured against the normal distribution using the Anderson-Darling test on a random [deferred] sample, requiring a p-value > 0.05 to indicate a good fit, supplemented by visual inspection of QQ-plots. (See US-2)

## Assumptions

- The Moral Machine dataset contains sufficient geographic and timestamp granularity to be matched with hourly ERA5 Reanalysis data for at least 90% of the records.
- The relationship between ambient temperature and response time may be non-linear (e.g., inverted-U), justifying the inclusion of quadratic terms or splines.
- The ERA5 Reanalysis data provides accurate hourly temperature estimates for the specific locations and times of the Moral Machine responses.
- The GitHub Actions free-tier runner (multiple CPU cores, sufficient RAM) is sufficient to process the merged dataset and fit the mixed-effects model without memory overflow or timeout, provided the dataset is sampled if necessary.
- The "dilemma complexity score" and "time-of-day" covariates are either present in the Moral Machine dataset or can be derived from the available data without introducing circularity.
- Any observed association between temperature and response time is correlational; the design does not support causal claims due to the observational nature of the data (no random assignment of temperature).
- The dataset contains all necessary variables (predictors, outcomes, covariates) for the analysis; if specific demographic data (e.g., age, gender) is missing for a significant portion of records, the model will exclude those records, potentially reducing statistical power.
- The "3-hour moving average" temperature metric is a valid proxy for the thermal environment experienced by the participant during the decision-making task.
- The micro-climate (indoor vs. outdoor) effect is either negligible or can be adjusted for using urban/rural classification; otherwise, it is treated as a source of noise that must be quantified via sensitivity analysis.