# Feature Specification: The Impact of Social Media "Doomscrolling" on Anticipatory Anxiety

**Feature Branch**: `001-doomscrolling-anxiety`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "How does the aggregate volume of negative news consumption on social media relate to population-level anticipatory anxiety during periods of global uncertainty?"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Acquisition (Priority: P1)

The system MUST retrieve historical time-series data for negative news sentiment tone and anticipatory anxiety search trends from external public APIs.

**Why this priority**: Without raw data, no analysis can occur. This is the foundational step for the entire research pipeline.

**Independent Test**: Can be fully tested by executing the data fetch script and verifying the output CSV files contain non-empty rows for the target date range.

**Acceptance Scenarios**:

1. **Given** valid API credentials and a target date range (e.g., 2020-01-01 to 2023-12-31), **When** the fetch script runs, **Then** a local CSV file containing daily negative news sentiment tone metrics is generated.
2. **Given** valid API credentials and a target date range, **When** the fetch script runs, **Then** a local CSV file containing daily anxiety-related search volume metrics is generated.
3. **Given** a failed API request, **When** the retry logic triggers (max 3 attempts), **Then** the script logs the error and exits with a non-zero status code.

---

### User Story 2 - Data Preprocessing (Priority: P2)

The system MUST clean, normalize, and align the retrieved time-series data to a consistent daily temporal resolution for analysis.

**Why this priority**: Raw data often contains missing values, different scales, and misaligned timestamps which invalidate statistical tests. Daily resolution is required to support lag-based causality testing.

**Independent Test**: Can be fully tested by running the preprocessing script on the raw CSVs and verifying the output contains no missing values and aligned daily timestamps.

**Acceptance Scenarios**:

1. **Given** two time-series CSVs with different start dates, **When** the alignment process runs, **Then** the output dataset contains only timestamps present in both series (intersection).
2. **Given** missing data points in a time-series, **When** the imputation process runs, **Then** missing values are filled using forward-fill (last observation carried forward) and the dataset has 0 nulls.
3. **Given** raw search volume scores, **When** normalization runs, **Then** all series are converted to z-scores with a mean of 0 and standard deviation of 1.

---

### User Story 3 - Statistical Analysis & Reporting (Priority: P3)

The system MUST compute correlation coefficients, perform causality tests, and generate visualizations to summarize the relationship between news sentiment and anxiety.

**Why this priority**: This delivers the core research insight and allows stakeholders to evaluate the hypothesis.

**Independent Test**: Can be fully tested by executing the analysis script and verifying the output reports contain correlation values, p-values, and plot images.

**Acceptance Scenarios**:

1. **Given** aligned daily time-series data, **When** the correlation analysis runs, **Then** a Pearson and Spearman correlation coefficient is calculated with a p-value reported.
2. **Given** aligned daily time-series data, **When** the Granger causality test runs, **Then** a p-value indicating predictive power is reported for lags of 1, 2, and 3 days.
3. **Given** analysis results, **When** the report generation runs, **Then** a PDF or HTML report containing lag plots and correlation heatmaps is produced.

---

### Edge Cases

- What happens when the GDELT API returns zero events for a specific day? (Handled by forward-fill interpolation in preprocessing).
- How does the system handle Google Trends keyword volatility (e.g., a term becoming too broad)? (Handled by explicit keyword list validation before fetch).
- What happens if the time-series length is too short for Granger causality (minimum N < 20)? (Script must exit with error "Insufficient data for Granger causality").

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST fetch negative news sentiment tone from GDELT Project using the `AVGTONE` metric. Note: GDELT `AVGTONE` measures the average sentiment tone of global news articles (range -100 to +100), not direct social media consumption volume. This is used as a proxy for the *intensity* of negative news exposure driving doomscrolling behavior, as direct public API access to granular social media consumption volume is unavailable. The research question is explicitly framed around the impact of negative news sentiment. See GDELT methodology documentation on AVGTONE. (See US-1)
- **FR-002**: System MUST normalize all time-series data to z-scores and align timestamps to DAILY intervals before analysis (See US-2)
- **FR-003**: System MUST compute Pearson and Spearman correlation coefficients between negative news sentiment tone and anxiety indicators with p-value output (See US-3)
- **FR-004**: System MUST perform Granger causality tests at multiple lags, framing results as associational predictive relationships rather than causal effects (See US-3)
- **FR-005**: System MUST conduct a sensitivity analysis sweeping the lag window ∈ {1, 2, 3} days and report how the significance rate (p < 0.05) varies across these thresholds (See US-3)
- **FR-006**: System MUST execute the entire analysis pipeline on a CPU-only environment without GPU/CUDA dependencies and within ≤ 6 hours (See US-3)

### Key Entities

- **TimeSeriesRecord**: Represents a single day's aggregated value for a specific metric (news tone or search trend), containing `date`, `value`, and `source`.
- **AnalysisResult**: Represents the output of a statistical test, containing `metric`, `coefficient`, `p_value`, `lag`, and `significance_flag`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Data completeness is measured against the target date range, requiring ≥ 95% of days to have valid values after forward-fill imputation (See US-1)
- **SC-002**: Statistical validity is measured against the standard alpha level corrected for multiple comparisons (Bonferroni), requiring p < 0.0167 (0.05/3) for at least one lag window in the primary Granger causality test (See US-3)
- **SC-003**: Compute feasibility is measured against the CI runner limits, requiring total job runtime ≤ 6 hours on a 2-core CPU runner (See US-3)

## Assumptions

- GDELT Project API provides accessible historical data for the `AVGTONE` metric without authentication barriers for the required time range.
- Google Trends search volume data for keywords like "anticipatory anxiety" and "worry about future" is available at daily granularity for the target period.
- The analysis environment is restricted to CPU resources (no GPU/CUDA) with limited RAM available for the Python runtime.
- The relationship between news sentiment and anxiety is observational; no causal claims will be made regardless of statistical significance due to lack of randomization.
- Forward-fill imputation is sufficient for handling missing daily data points in the time-series without introducing significant bias, and is preferred over linear interpolation to preserve stationarity.
- The standard alpha level (corrected for multiple comparisons) is appropriate for initial hypothesis testing..