# Feature Specification: Statistical Analysis of Sentiment Drift in Social Media During Economic Recessions

**Feature Branch**: `001-sentiment-drift`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "Statistical Analysis of Sentiment Drift in Social Media During Economic Recessions"

## User Scenarios & Testing *(mandatory)*

<!--
  IMPORTANT: User stories should be PRIORITIZED as user journeys ordered by importance.
  Each user story/journey must be INDEPENDENTLY TESTABLE - meaning if you implement just ONE of them,
  you should still have a viable MVP (Minimum Viable Product) that delivers value.
  
  Assign priorities (P1, P2, P3, etc.) to each story, where P1 is the most critical.
  Think of each story as a standalone slice of functionality that can be:
  - Developed independently
  - Tested independently
  - Deployed independently
  - Demonstrated to users independently
-->

### User Story 1 - Data Acquisition and Alignment (Priority: P1)

The researcher MUST be able to download historical sentiment scores from social media datasets and macroeconomic indicators from official sources, then align them to a common monthly frequency.

**Why this priority**: Without aligned time-series data, no statistical analysis can occur. This is the foundational data layer required for all subsequent modeling.

**Independent Test**: Can be fully tested by running the data ingestion script and verifying the existence of a single merged CSV file with monthly timestamps and no missing values.

**Acceptance Scenarios**:

1. **Given** valid API access to FRED and HuggingFace datasets, **When** the ingestion script runs, **Then** GDP, unemployment, and sentiment data are merged on a monthly timestamp.
2. **Given** missing values in the raw time series, **When** linear interpolation preprocessing is applied, **Then** the Pearson correlation coefficient between original and interpolated series remains ≥ 0.95.
3. **Given** raw sentiment ratios, **When** aggregation is performed, **Then** a 30-day rolling average is computed to reduce noise.

---

### User Story 2 - Statistical Modeling and Causal Inference (Priority: P2)

The researcher MUST be able to execute stationarity tests and Granger causality tests to determine if sentiment predicts economic variables.

**Why this priority**: This addresses the core research question regarding lead/lag relationships. It is the analytical core of the feature.

**Independent Test**: Can be fully tested by running the modeling notebook and verifying that p-values for Granger causality are output for all variable pairs.

**Acceptance Scenarios**:

1. **Given** aligned time-series data, **When** the ADF test is run, **Then** non-stationary series are differenced until I(0) stationarity is achieved.
2. **Given** stationary series, **When** the VAR model is fit, **Then** optimal lag length is selected via Akaike Information Criterion (AIC).
3. **Given** fitted VAR model, **When** Granger causality test is executed, **Then** F-test p-values are recorded for sentiment predicting GDP and unemployment.

---

### User Story 3 - Visualization and Robustness Reporting (Priority: P3)

The researcher MUST be able to visualize the temporal relationships and validate results through bootstrapping across held-out recession periods.

**Why this priority**: Visualization communicates findings, and bootstrapping ensures robustness. This completes the research deliverable but depends on P1 and P2.

**Independent Test**: Can be fully tested by generating the final report artifacts and verifying that confidence intervals are calculated for key statistics.

**Acceptance Scenarios**:

1. **Given** model results, **When** plots are generated, **Then** time-series charts include shading for recession periods (e.g., 2008, 2020).
2. **Given** test statistics, **When** bootstrap validation runs on configurable iterations, **Then** confidence intervals are calculated for held-out recession periods.
3. **Given** VAR model results, **When** impulse response functions MAY be generated (optional for MVP), **Then** sentiment shock trajectories are visualized over a multi‑week horizon.
4. **Given** final analysis, **When** the notebook is archived, **Then** all dataset URLs and DOIs are documented in the metadata.

---

### Edge Cases

<!--
  ACTION REQUIRED: The content in this section represents placeholders.
  Fill them out with the right edge cases.
-->

- **FRED API incomplete data**: System MUST handle partial quarterly GDP data by flagging affected periods and applying documented interpolation or exclusion. (Technical requirement supporting User Story 1; see FR-008)
- **Non-stationary after differencing**: System MUST detect when series remain non-stationary after first differencing and log diagnostic output for researcher review. (Technical requirement supporting User Story 2; see FR-009)
- **Insufficient sentiment volume**: System MUST detect weeks/months with sentiment sample size below configurable threshold and flag these periods as low-confidence. (Technical requirement supporting User Story 1; see FR-010)

## Requirements *(mandatory)*

<!--
  ACTION REQUIRED: The content in this section represents placeholders.
  Fill them out with the right functional requirements.
-->

### Functional Requirements

- **FR-001**: System MUST download sentiment scores from HuggingFace Datasets aggregated to monthly time series.
- **FR-002**: System MUST download economic indicators (GDP, unemployment rate, consumer confidence) from FRED API.
- **FR-003**: System MUST apply Augmented Dickey-Fuller (ADF) tests to verify stationarity of all input series.
- **FR-004**: System MUST conduct Granger causality tests (F-test) to determine predictive relationships between sentiment and economic variables.
- **FR-005**: System MUST generate time-series visualizations with recession period annotations.
- **FR-006**: System MUST validate results using out-of-sample held-out recession periods.
- **FR-007**: System MUST output analysis artifacts in reproducible format with embedded code, outputs, and narrative text.
- **FR-008**: System MUST handle FRED API incomplete data by flagging affected periods and applying documented interpolation or exclusion. (Technical edge case requirement; supports User Story 1)
- **FR-009**: System MUST detect non-stationary series after first differencing and log diagnostic output for researcher review. (Technical edge case requirement; supports User Story 2)
- **FR-010**: System MUST flag sentiment data periods with sample size below configurable threshold as low-confidence. (Technical edge case requirement; supports User Story 1)

### Key Entities *(include if feature involves data)*

- **TimeSeries**: Represents aligned monthly data points containing sentiment polarity, GDP growth, and unemployment rates.
- **ModelResult**: Represents statistical output including p-values, lag lengths, and confidence intervals.
- **RecessionPeriod**: Represents time boundaries of known economic downturns used for validation and visualization shading.

## Success Criteria *(mandatory)*

<!--
  ACTION REQUIRED: Define measurable success criteria.
  These must be technology-agnostic and measurable.
-->

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Statistical significance is measured against the standard p-value threshold (<0.05) for Granger causality tests (validates FR-004).
- **SC-002**: Data completeness is measured against the requirement for continuous monthly time-series alignment without manual intervention (validates FR-001, FR-002).
- **SC-003**: Reproducibility is measured against the successful execution of the analysis notebook from raw data to final visualization (validates FR-007).
- **SC-004**: Robustness is measured against the consistency of results across bootstrap confidence intervals on configurable iterations. Consistency is quantified as follows: (a) the width of the [deferred] bootstrap confidence interval for each key statistic (e.g., Granger causality F‑statistic or impulse‑response magnitude) must be [deferred] of the point estimate, (b) the interval must contain the original point estimate, and (c) the coefficient of variation (CV) of the bootstrap distribution must be sufficiently low (e.g., below a conventional stability threshold). The default bootstrap configuration uses a sufficiently large number of resamples. (validates FR-006).
- **SC-005**: Output format is measured against the reproducible format specification documented in the Assumptions section (embedded code, outputs, narrative text) (validates FR-007).

## Assumptions

<!--
  ACTION REQUIRED: The content in this section represents placeholders.
  Fill them out with the right assumptions based on reasonable defaults
  chosen when the feature description did not specify certain details.
-->

- Users have valid API access credentials for the FRED API and HuggingFace Datasets.
- Historical data exists in sufficient quantity to cover the 2008 and 2020 recession periods (sufficient duration of data required for Granger causality statistical power).
- The computational environment supports configurable bootstrap iterations without timeout.
- Social media sentiment scores derived from the specified model are sufficiently accurate for macroeconomic correlation.
- Linear interpolation is an acceptable method for handling missing values in this specific context.
- Jupyter Notebook (.ipynb) format with embedded code, outputs, and narrative text is the standard format for reproducible statistical research in Python-based analysis pipelines.
- The MVP scope focuses on the 2008 Global Financial Crisis and the 2020 COVID-19 recession as default recession periods, but the system must support configurable recession period selection for future iterations.
- Impulse response functions are recommended visualization practice for VAR model results but are optional for MVP completion.