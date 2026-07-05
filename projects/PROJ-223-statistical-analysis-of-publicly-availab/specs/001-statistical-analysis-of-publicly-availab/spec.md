# Feature Specification: Statistical Analysis of Publicly Available Traffic Accident Data

**Feature Branch**: `001-traffic-weather-severity`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "Statistical Analysis of Publicly Available Traffic Accident Data"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Merging (Priority: P1)

As a researcher, I need to download the FARS crash dataset and the corresponding NOAA ISD (Integrated Surface Database) weather data, then merge them based on location and time, so that I have a single unified dataset containing both accident outcomes and environmental conditions.

**Why this priority**: Without a merged dataset containing both predictors (weather) and outcomes (severity), no statistical analysis can be performed. This is the foundational step for the entire research question.

**Independent Test**: Can be fully tested by running the ingestion script and verifying that the output CSV contains non-null values for `severity`, `precipitation`, `visibility`, `temperature`, and control variables for a deterministic sample of [deferred] randomly selected records (seed=42).

**Acceptance Scenarios**:

1. **Given** the FARS and NOAA ISD datasets are accessible via public URLs, **When** the ingestion script executes, **Then** a merged CSV file is generated with ≥85% of records having valid weather data for the accident timestamp and location.
2. **Given** a record exists in FARS but no matching weather station data within the defined proximity radius, **When** the merge logic runs, **Then** that record is either flagged for exclusion or imputed based on the nearest station, and the exclusion count is logged.

---

### User Story 2 - Ordinal Logistic Regression Modeling (Priority: P2)

As a researcher, I need to fit an Ordinal Logistic Regression (Cumulative Link Model) where accident severity (Property/Injury/Fatality) is the outcome and weather conditions (precipitation, visibility, temperature) are predictors, while controlling for temporal and infrastructural variables, so that I can quantify the statistical influence of weather on severity.

**Why this priority**: This directly addresses the core research question. It transforms the raw merged data into the primary statistical evidence required to answer "How do specific weather conditions influence traffic accident severity?"

**Independent Test**: Can be fully tested by running the modeling script and verifying that the output includes a coefficients table with odds ratios for all weather predictors, a model fit statistic (e.g., AIC/BIC), and a Brant test p-value > 0.05 indicating the proportional odds assumption holds.

**Acceptance Scenarios**:

1. **Given** the merged dataset is loaded and severity is encoded as an ordinal variable (0, 1, 2), **When** the Cumulative Link Model is fitted with weather and control variables, **Then** the model converges successfully within 60 seconds on the CPU runner without memory errors.
2. **Given** the model is fitted, **When** the coefficients are extracted, **Then** the odds ratios for precipitation and low visibility are reported with confidence intervals.

---

### User Story 3 - Model Diagnostics and Visualization (Priority: P3)

As a researcher, I need to generate diagnostic plots (VIF for multicollinearity, coefficient plots) and a sensitivity analysis for any decision thresholds used, so that I can validate the methodological soundness and interpretability of the findings.

**Why this priority**: This ensures the results are methodologically defensible (addressing collinearity and threshold justification) and provides the visual evidence required for the final report.

**Independent Test**: Can be fully tested by running the diagnostics script and verifying that the output includes a VIF table (all values < 5.0), a coefficient plot image, and a sensitivity analysis table showing how odds ratios shift when the precipitation threshold is swept.

**Acceptance Scenarios**:

1. **Given** the fitted model, **When** the VIF diagnostic runs, **Then** the output confirms no predictor has a VIF > 5.0, or if it does, the report flags it as a limitation.
2. **Given** a precipitation threshold is defined (e.g., >0.01 inches), **When** the sensitivity analysis runs, **Then** the output reports odds ratios for representative thresholds to demonstrate stability.

---

### Edge Cases

- **What happens when** the accident time falls exactly between two weather station readings? (System uses linear interpolation or nearest-hour fallback).
- **How does system handle** missing severity codes (e.g., "Unknown" or "Not Reported") in the FARS dataset? (Records are excluded from the ordinal model but logged in a "missing data" summary).
- **What happens when** the dataset size exceeds 7GB RAM during the merge? (The script processes data in chunks of [deferred] rows, or dynamically adjusts to [deferred] rows if available RAM is < 4GB, and writes intermediate results to disk).

## Requirements

### Functional Requirements

- **FR-001**: System MUST download the FARS CSV dataset and the NOAA ISD (Integrated Surface Database) weather data corresponding to accident locations and times, and merge them into a single DataFrame. (See US-1)
- **FR-002**: System MUST encode accident severity as an ordinal variable (0=Property Damage, 1=Injury, 2=Fatality) using the following FARS code mapping: 0 for 'No Injury' or 'Property Damage Only', 1 for 'Injury' (Minor, Serious, Severe), and 2 for 'Fatality'. Records with non-ordinal or missing severity values MUST be excluded. (See US-2)
- **FR-003**: System MUST fit an Ordinal Logistic Regression model using `statsmodels.miscmodels.ordinal_model.OrderedModel` (Cumulative Logit) with weather predictors (precipitation amount, visibility, temperature) and control variables (hour, day of week, road type, vehicle type). (See US-2)
- **FR-004**: System MUST calculate Variance Inflation Factors (VIF) for all predictors to detect multicollinearity and report any values exceeding 5.0. (See US-3)
- **FR-005**: System MUST perform a sensitivity analysis sweeping the precipitation detection threshold over a set of low-magnitude candidate values (converting continuous precipitation to a binary flag for this specific test) and report the resulting variation in odds ratios to demonstrate robustness. (See US-3)
- **FR-006**: System MUST frame all statistical findings as associational (not causal) in the final output, given the observational nature of the data. (See US-2)

### Key Entities

- **AccidentRecord**: Represents a single traffic crash event; attributes include `severity_level`, `timestamp`, `location_lat`, `location_lon`, `road_type`, `vehicle_type`.
- **WeatherStationData**: Represents meteorological conditions at a specific location/time; attributes include `precipitation_amount`, `visibility_miles`, `temperature_f`, `station_id`.
- **MergedDataset**: The unified dataset combining `AccidentRecord` and `WeatherStationData` via spatial-temporal join.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The percentage of FARS records successfully matched with valid NOAA ISD weather data is measured against a target of ≥ 85% coverage. (See US-1)
- **SC-002**: The model convergence rate (percentage of successful fits where the algorithm converges within 50 iterations with log-likelihood change < 1e-6) is measured against a target of ≥ 95% on the sampled dataset. (See US-2)
- **SC-003**: The stability of the primary odds ratio for precipitation is measured by the maximum percentage change across the sensitivity sweep {0.01, 0.05, 0.10}, targeting a variation of < 15%. (See US-3)
- **SC-004**: The Brant test p-value for the proportional odds assumption is measured against the threshold of > 0.05 to confirm model validity. (See US-2)
- **SC-005**: The execution time of the full analysis pipeline (ingest to visualization) is measured against the constraint of ≤ 6 hours on the GitHub Actions free-tier runner. (See US-1, US-2, US-3)

## Assumptions

- The FARS dataset and NOAA ISD dataset are publicly accessible via direct download links provided in the methodology, without requiring authentication or complex API key rotation.
- The "severity" variable in FARS can be reliably mapped to the ordinal scale (0, 1, 2) using standard NHTSA coding guidelines without requiring extensive manual review of unstructured text fields.
- The weather station density in the US is sufficient to find a valid station within 50km of ≥85% of recorded accidents; records failing this proximity check are excluded rather than imputed from distant stations.
- The `statsmodels` library is available in the GitHub Actions runner environment and supports the `OrderedModel` (Cumulative Logit) without requiring GPU acceleration.
- The analysis is strictly observational; therefore, any significant correlation found between weather and severity is interpreted as an association, not a causal effect, unless randomization is explicitly introduced (which it is not).