# Feature Specification: The Impact of Aggregate Negative News Publication Volume on Anticipatory Anxiety

**Feature Branch**: `001-news-volume-anxiety`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "How does the aggregate volume of negative news consumption on social media relate to population-level anticipatory anxiety during periods of global uncertainty?"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Acquisition (Priority: P1)

The system MUST retrieve historical time-series data for aggregate negative news publication volume from the GDELT Project and anxiety-related search trends from Google Trends. Note: This study uses general news publication volume as a proxy for 'news exposure' because social media consumption data is not available at the required population scale and granularity.

**Why this priority**: Without raw data, no analysis can occur. This is the foundational step for the entire research pipeline.

**Independent Test**: Can be fully tested by executing the data fetch script and verifying the output CSV files contain non-empty rows for the target date range.

**Acceptance Scenarios**:

1. **Given** valid API credentials and a target date range (e.g., 2020-01-01 to 2023-12-31), **When** the fetch script runs, **Then** a local CSV file containing daily negative news publication volume metrics (GDELT EventCount) is generated.
2. **Given** valid API credentials and a target date range, **When** the fetch script runs, **Then** a local CSV file containing daily anxiety-related search volume metrics is generated.
3. **Given** a failed API request, **When** the retry logic triggers (max 3 attempts), **Then** the script logs the error and exits with a non-zero status code.

---

### User Story 2 - Data Preprocessing (Priority: P2)

The system MUST clean, normalize, and align the retrieved time-series data to a consistent daily temporal resolution, ensuring stationarity before analysis.

**Why this priority**: Raw data often contains missing values, different scales, and misaligned timestamps which invalidate statistical tests. Additionally, non-stationary time-series can lead to spurious regression results.

**Independent Test**: Can be tested by running the preprocessing script on the raw CSVs and verifying the output contains no missing values, aligned timestamps, and passes stationarity checks (or is differenced).

**Acceptance Scenarios**:

1. **Given** two time-series CSVs with different start dates, **When** the alignment process runs, **Then** the output dataset contains only timestamps present in both series (intersection), preserving zero-event days as valid zeros.
2. **Given** missing data points (nulls) in a time-series, **When** the interpolation process runs, **Then** missing values are filled using linear interpolation, while zero-event counts are preserved as valid data points.
3. **Given** raw time-series data, **When** preprocessing runs, **Then** the Augmented Dickey-Fuller (ADF) test is performed; if non-stationary (p ≥ 0.05), the series is differenced until stationary, then normalized to z-scores (mean=0, std=1).

---

### User Story 3 - Statistical Analysis & Reporting (Priority: P3)

The system MUST compute correlation coefficients, perform causality tests with a wide lag window, conduct sensitivity analysis, and generate visualizations to summarize the relationship between news volume and anxiety.

**Why this priority**: This delivers the core research insight and allows stakeholders to evaluate the hypothesis with appropriate statistical rigor.

**Independent Test**: Can be fully tested by executing the analysis script and verifying the output reports contain correlation values, p-values (with correction), and plot images.

**Acceptance Scenarios**:

1. **Given** aligned, stationary time-series data, **When** the correlation analysis runs, **Then** a Pearson and Spearman correlation coefficient is calculated with a p-value reported.
2. **Given** aligned, stationary time-series data, **When** the Granger causality test runs, **Then** a p-value indicating predictive power is reported for lags of 1, 2, 3, 7, and 14 days.
3. **Given** analysis results, **When** the sensitivity analysis runs, **Then** the significance rate (p < 0.05 after Bonferroni correction) is reported across the swept lag windows {1, 2, 3, 7, 14}.
4. **Given** analysis results, **When** the report generation runs, **Then** a PDF or HTML report containing lag plots, correlation heatmaps, and sensitivity analysis summaries is produced.

---

### Edge Cases

- What happens when the GDELT API returns zero events for a specific day? (Handled as a valid zero value, NOT interpolated; only null/missing values are interpolated).
- How does the system handle Google Trends keyword volatility (e.g., a term becoming too broad)? (Handled by explicit keyword list validation before fetch).
- What happens if the time-series length is too short for Granger causality (minimum N < 20)? (Script must exit with error "Insufficient data for Granger causality").
- What happens if the data is non-stationary? (System applies differencing until the ADF test p < 0.05 before proceeding).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST fetch aggregate negative news publication volume from GDELT Project using the `EventCount` metric (count of events with negative sentiment), explicitly acknowledging this as a proxy for 'news exposure' rather than direct 'social media consumption' due to data availability constraints. The analysis will frame the relationship as 'news volume impact' while noting 'social media amplification' as a confounding variable. (See US-1)
- **FR-002**: System MUST align timestamps to daily intervals, perform stationarity testing (ADF), apply differencing if non-stationary (p ≥ 0.05), and then normalize to z-scores (See US-2)
- **FR-003**: System MUST compute Pearson and Spearman correlation coefficients between negative news volume and anxiety indicators with p-value output (See US-3)
- **FR-004**: System MUST perform Granger causality tests at varying lags to capture anticipatory dynamics, framing results as associational predictive relationships rather than causal effects. The wider lag window (up to 14 days) is justified by the hypothesis that anticipatory anxiety may build over weeks. (See US-3)
- **FR-005**: System MUST conduct a sensitivity analysis sweeping the lag window ∈ {, 2, 3, 7, 14} days and report how the significance rate (p < 0.05) varies across these thresholds (See US-3)
- **FR-006**: System MUST execute the entire analysis pipeline on a CPU-only environment without GPU/CUDA dependencies and within ≤ 6 hours (See US-3)

### Key Entities

- **TimeSeriesRecord**: Represents a single day's aggregated value for a specific metric (news volume or search trend), containing `date`, `value`, and `source`.
- **AnalysisResult**: Represents the output of a statistical test, containing `metric`, `coefficient`, `p_value`, `lag`, `significance_flag`, and `stationarity_status`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Data completeness is measured against the target date range, requiring ≥ 95% of days to have valid values after interpolation (See US-1)
- **SC-002**: Statistical validity is measured against the Bonferroni-corrected alpha level (α = 0.05 / 5 = 0.01), requiring p < 0.01 for at least one lag window in the primary Granger causality test (See US-3)
- **SC-003**: Compute feasibility is measured against the CI runner limits, requiring total job runtime ≤ 6 hours on a 2-core CPU runner (See US-3)

## Assumptions

- GDELT Project API provides accessible historical data for the `EventCount` metric without authentication barriers for the required time range.
- Google Trends search volume data for keywords like "anticipatory anxiety" and "worry about future" is available at daily granularity for the target period.
- The analysis environment is restricted to CPU resources (no GPU/CUDA) with limited RAM available for the Python runtime.
- The relationship between news volume and anxiety is observational; no causal claims will be made regardless of statistical significance due to lack of randomization.
- Linear interpolation is sufficient for handling missing daily data points in the time-series without introducing significant bias, provided zero-event days are preserved.
- The standard alpha level of 0.05, corrected via Bonferroni for 5 lag windows (α=0.01), is appropriate for hypothesis testing.