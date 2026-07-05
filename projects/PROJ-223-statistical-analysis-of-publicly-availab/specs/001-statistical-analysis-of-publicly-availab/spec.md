# Feature Specification: Statistical Analysis of Publicly Available Traffic Accident Data

**Feature Branch**: `001-statistical-analysis-of-publicly-available-traffic-accident-data`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "How do specific weather conditions (precipitation, visibility, temperature) statistically influence traffic accident severity (property damage, injury, fatality) after controlling for temporal and infrastructural variables?"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Merging (Priority: P1)

The system must successfully download, clean, and merge the FARS accident dataset with the NOAA GHCN-Daily weather dataset, filtering for records where both accident severity and weather variables are present and valid.

**Why this priority**: Without a merged, clean dataset, no statistical analysis can occur. This is the foundational step that enables all subsequent modeling and insights.

**Independent Test**: Can be fully tested by verifying that the output CSV contains only rows with non-null values for severity, precipitation, visibility, temperature, and control variables, and that the output row count is less than or equal to the minimum of the input dataset row counts (representing the intersection of keys).

**Acceptance Scenarios**:
1. **Given** raw FARS and NOAA CSV files exist, **When** the ingestion script runs, **Then** the output file contains only records with complete weather and severity data, the output row count is ≤ min(input_row_count_fars, input_row_count_noaa), and a log reports the count of dropped records.
2. **Given** a record with missing visibility data, **When** the cleaning process runs, **Then** that record is excluded from the final merged dataset.
3. **Given** the merged dataset, **When** a schema validation check runs, **Then** all required columns (severity, precipitation, visibility, temperature, hour, day_of_week, road_type, vehicle_type) are present and typed correctly.

---

### User Story 2 - Ordinal Logistic Regression Modeling (Priority: P2)

The system must fit an Ordinal Logistic Regression model using `statsmodels` to quantify the relationship between weather conditions and accident severity, controlling for temporal and infrastructural variables. If the ordinal assumption is violated, the system must fall back to a Multinomial Logistic Regression model.

**Why this priority**: This is the core analytical engine that directly addresses the research question by providing the statistical evidence of weather impact.

**Independent Test**: Can be fully tested by running the model on a small, synthetic subset of the merged data and verifying that the model converges (or falls back to Multinomial Regression), returns coefficients, and produces odds ratios (or relative risk ratios) without GPU usage.

**Acceptance Scenarios**:
1. **Given** the merged dataset, **When** the regression script executes, **Then** the model converges (or successfully falls back to Multinomial Regression) and outputs a table of coefficients for all predictors (weather and controls).
2. **Given** the fitted model, **When** odds ratios (or relative risk ratios) are calculated, **Then** the output table includes the ratio and confidence intervals for precipitation, visibility, and temperature.
3. **Given** the model execution environment, **When** the script runs, **Then** it completes within the 6-hour GitHub Actions job limit on CPU-only hardware without requesting CUDA/GPU resources.

---

### User Story 3 - Model Diagnostics and Visualization (Priority: P3)

The system must perform model diagnostics (VIF for multicollinearity with Ridge fallback, Likelihood Ratio Test for fit) and generate visualizations (coefficient plots, odds ratio tables) to interpret the results.

**Why this priority**: This step validates the statistical soundness of the model and makes the results interpretable for stakeholders, ensuring the findings are trustworthy and actionable.

**Independent Test**: Can be tested by running the diagnostic script on the fitted model and verifying that VIF scores are calculated, multicollinearity remediation is applied if needed, and plots are generated as image files.

**Acceptance Scenarios**:
1. **Given** the fitted model, **When** the VIF diagnostic runs, **Then** the output reports VIF scores for all predictors. If any VIF > 5, the system automatically applies Ridge regularization and reports the regularized coefficients.
2. **Given** the fitted model, **When** the Likelihood Ratio Test runs, **Then** the output provides a p-value and McFadden's Pseudo R-squared indicating model fit adequacy.
3. **Given** the model results, **When** the visualization script runs, **Then** it generates a coefficient plot and an odds ratio table saved as image/PDF files in the output directory.

---

### Edge Cases

- What happens when the weather data has no records matching the accident timestamps? (System should log a warning and proceed with available data, potentially reducing sample size).
- How does the system handle extreme outliers in temperature or precipitation values? (System should apply a robust clipping or winsorization method as defined in the preprocessing step).
- What if the ordinal logistic regression fails to converge or the ordinal assumption is violated? (System should log the failure, validate the assumption, and automatically switch to Multinomial Logistic Regression as defined in FR-010).

## Requirements

### Functional Requirements

- **FR-001**: System MUST download the FARS dataset and NOAA GHCN-Daily weather data for the specified time range and locations (See US-1).
- **FR-002**: System MUST merge the datasets on timestamp and location, filtering out records with missing critical variables (See US-1).
- **FR-003**: System MUST encode accident severity as an ordinal variable (0=Property, 1=Injury, 2=Fatality) (See US-2).
- **FR-004**: System MUST fit an Ordinal Logistic Regression model using `statsmodels` with weather predictors and control variables (See US-2).
- **FR-005**: System MUST perform VIF diagnostics to check for multicollinearity among predictors (See US-3).
- **FR-006**: System MUST calculate and report odds ratios with confidence intervals for all weather predictors (See US-2).
- **FR-007**: System MUST generate a coefficient plot and an odds ratio table as visual outputs (See US-3).
- **FR-008**: System MUST execute entirely on CPU without requiring GPU or CUDA resources (See US-2).
- **FR-009**: System MUST perform a post-hoc power analysis to verify the sample size is sufficient to detect an odds ratio of 1.5 with 80% power at alpha=0.05, and report the result (See US-2).
- **FR-010**: System MUST validate the proportional odds assumption; if violated, the system MUST automatically switch to a Multinomial Logistic Regression model and report the switch (See US-2).
- **FR-011**: System MUST automatically apply L2 regularization (Ridge regression) if any predictor has a VIF > 5, and report the regularized coefficients (See US-3).

### Key Entities

- **Accident Record**: Represents a single traffic accident with attributes for severity, location, time, and vehicle type.
- **Weather Observation**: Represents a weather reading with attributes for precipitation, visibility, and temperature at a specific time and location.
- **Merged Dataset**: The combined entity containing both accident and weather data, used for analysis.
- **Regression Model**: The statistical model object containing coefficients, odds ratios, and diagnostic metrics.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Model convergence rate is measured against the requirement that the Ordinal Logistic Regression (or fallback Multinomial) must converge on the merged dataset (See US-2).
- **SC-002**: Multicollinearity is measured against the VIF threshold of 5; if exceeded, the system MUST apply Ridge regularization and report the action taken (See US-3).
- **SC-003**: Model fit is measured against the Likelihood Ratio Test p-value and McFadden's Pseudo R-squared; the system MUST report these values and flag the fit as 'adequate' or 'inadequate' based on the p-value > 0.05 convention (See US-3).
- **SC-004**: Compute resource usage is measured against the constraint of running on a 2-core, 7GB RAM CPU-only runner within 6 hours (See US-2).
- **SC-005**: Data completeness is measured against the post-hoc power analysis result, ensuring the reported power is ≥ 0.80 for an effect size of OR=1.5 (See US-2).

## Assumptions

- The FARS dataset and NOAA GHCN-Daily data are publicly accessible and can be downloaded via `wget` without authentication.
- The merged dataset will fit within the 7GB RAM and 14GB disk constraints of the GitHub Actions free-tier runner after appropriate sampling or chunking if necessary.
- The `statsmodels` library is available and compatible with the Python environment on the CI runner.
- The ordinal encoding of severity (0=Property, 1=Injury, 2=Fatality) is appropriate for the research question and aligns with standard practice in traffic safety analysis, subject to validation by FR-010.
- The weather data will have sufficient temporal and spatial resolution to match accident records without excessive interpolation or aggregation.
- The analysis will treat weather variables as fixed effects in the regression model, assuming no significant random effects from location or time that would require a mixed-effects model.