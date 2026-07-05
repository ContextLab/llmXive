# Feature Specification: Statistical Analysis of Publicly Available Stack Overflow Question Tags

**Feature Branch**: `001-stat-so-tag-trends`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Statistical Analysis of Publicly Available Stack Overflow Question Tags"

## User Scenarios & Testing

### User Story 1 - Quantify Technology Growth and Decline Trajectories (Priority: P1)

A researcher needs to identify which programming language tags show statistically significant growth or decline between 2015 and 2023 to determine emerging versus declining technologies.

**Why this priority**: This is the core research objective. Without quantifying trends, the project cannot answer the primary research question regarding technology adoption curves.

**Independent Test**: Can be fully tested by running the Mann-Kendall test on the top 50 tags (filtered for data sufficiency) and verifying the output contains a list of tags with p-values < 0.05 classified as "Growth," "Decline," or "Stable," AND verifying a correlation coefficient ≥ 0.7 with an external metric (GitHub stars).

**Acceptance Scenarios**:

1. **Given** the preprocessed monthly tag frequency data for 2015-2023, **When** the Mann-Kendall test is applied to the top 50 most frequent tags (that have ≥12 months of data), **Then** the system outputs a classification for each tag (Growth/Decline/Stable) with a corresponding p-value.
2. **Given** a specific tag known to be declining (e.g., "silverlight"), **When** the analysis runs, **Then** the tag is correctly classified as "Decline" with a p-value < 0.05.
3. **Given** a tag with no clear trend, **When** the analysis runs, **Then** the tag is classified as "Stable" or fails to meet the significance threshold (p ≥ 0.05).

---

### User Story 2 - Visualize Time Series Decomposition and Seasonality (Priority: P2)

A data analyst needs to visualize the decomposition of tag frequency time series to identify seasonal patterns correlating with major framework releases or conference cycles.

**Why this priority**: Visual validation is essential for interpreting the statistical results and understanding the context of the trends (e.g., distinguishing seasonal spikes from structural growth).

**Independent Test**: Can be fully tested by generating a time series plot for a specific tag (e.g., "react") that includes the observed data, trend component, seasonal component, and residual, with confidence intervals, and verifying the residuals show no significant autocorrelation (p > 0.05 in Ljung-Box test).

**Acceptance Scenarios**:

1. **Given** the monthly frequency data for a single tag, **When** the time series decomposition is performed, **Then** the output includes a plot with four panels: Observed, Trend, Seasonal, and Residual.
2. **Given** the decomposition results, **When** the seasonal component is analyzed, **Then** peaks in the seasonal component align with events in the `data/events/reference_calendar.json` (derived from SO Developer Survey and official release logs) within a ±1 month window.
3. **Given** the trend component, **When** compared to the raw data, **Then** the trend line smooths out short-term noise while preserving the long-term direction of the data, and residuals pass the Ljung-Box test for independence (p > 0.05).

---

### User Story 3 - Cluster Technologies via Co-occurrence Analysis (Priority: P3)

A community researcher needs to identify clusters of related technologies based on how frequently they appear together on the same Stack Overflow posts.

**Why this priority**: This provides secondary insight into the ecosystem structure (e.g., "JavaScript ecosystem" vs. "Python data science ecosystem") but is not required to answer the primary growth/decline question.

**Independent Test**: Can be tested by computing the Pearson correlation matrix for tag pairs, running hierarchical clustering, and validating that intra-cluster correlation is significantly higher than inter-cluster correlation (p < 0.05) AND that clusters align with the "Tech Stack" categories in the Stack Overflow Developer Survey.

**Acceptance Scenarios**:

1. **Given** the post-tag co-occurrence matrix, **When** Pearson correlation is calculated for all tag pairs, **Then** the system produces a correlation matrix where related tags (e.g., "python" and "pandas") have a correlation coefficient > 0.6.
2. **Given** the correlation matrix, **When** hierarchical clustering is applied, **Then** the resulting clusters exhibit an average intra-cluster correlation coefficient ≥ 0.65, which is statistically significantly higher than the average inter-cluster correlation (p < 0.05, two-sample t-test).
3. **Given** a specific technology cluster, **When** the members are listed, **Then** the cluster matches a "Tech Stack" category defined in the Stack Overflow Developer Survey taxonomy (e.g., "Web Development", "Data Science") with ≥ 80% overlap.

---

### Edge Cases

- **What happens when a tag has zero frequency in a specific month?** The system must handle zero counts without crashing during log-transformation (e.g., by adding a small epsilon of 1e-9 or filtering months with zero counts for that specific tag before regression).
- **How does the system handle tags with insufficient data points?** Tags with fewer than 12 distinct months of data over the 2015-2023 period MUST be EXCLUDED from the "top 50" selection and trend analysis. The "top 50" selection is performed ONLY on the set of tags meeting this minimum data threshold.
- **What happens if the dataset is incomplete?** If the data dump lacks months between 2015 and 2023, the system must detect the gap, interpolate or flag the missing data, and adjust the time bins accordingly.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download and parse the `PostsTags` table from the Stack Overflow data dump, extracting tag names and post creation dates. (See US-1)
- **FR-002**: System MUST aggregate tag frequencies into monthly time bins spanning 2015-01-01 to 2023-12-31, normalizing tag strings to lowercase and trimmed whitespace. (See US-1)
- **FR-003**: System MUST apply the Mann-Kendall test to the top 50 most frequent tags (filtered to include only those with ≥12 months of data) to determine trend significance with a p-value threshold of < 0.05. (See US-1)
- **FR-004**: System MUST perform time series decomposition on individual tag frequency series to isolate trend, seasonal, and residual components, using a robust method (e.g., STL) if non-stationarity is detected. (See US-2)
- **FR-005**: System MUST calculate Pearson correlation coefficients for all pairs of tags appearing on the same posts and perform hierarchical clustering on the resulting matrix. (See US-3)
- **FR-006**: System MUST generate reproducible Jupyter notebooks containing all code and final visualization outputs, referencing external intermediate data files (not embedding them) to ensure separation of raw/derived data artifacts. (See US-2, US-3)
- **FR-007**: System MUST correlate the identified growth/decline trends with an external metric (GitHub stars or NPM download trends) to validate that tag frequency changes reflect actual adoption, requiring a correlation coefficient ≥ 0.7. (See US-1)
- **FR-008**: System MUST validate the semantic coherence of technology clusters against the "Tech Stack" categories in the Stack Overflow Developer Survey taxonomy. (See US-3)
- **FR-009**: System MUST perform an Augmented Dickey-Fuller (ADF) test on each time series before decomposition; if non-stationary, the system MUST apply differencing or robust decomposition and report the Ljung-Box test result for residual independence. (See US-2)

### Key Entities

- **Tag**: A normalized string representing a technology topic (e.g., "python", "react") associated with a post.
- **TimeSeries**: A sequence of monthly frequency counts for a specific tag over the 2015-2023 period.
- **Cluster**: A group of tags identified by hierarchical clustering based on high co-occurrence correlation.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The number of tags with statistically significant growth or decline trends (p < 0.05) is measured against the Mann-Kendall test output for the top 50 tags. (See US-1)
- **SC-002**: The precision of trend estimates is measured by the width of the 95% confidence interval derived from 1000 bootstrapped resamples of the monthly data. (See US-1)
- **SC-003**: The alignment of seasonal peaks with industry events is measured against the `data/events/reference_calendar.json` artifact (derived from SO Developer Survey and official release logs). (See US-2)
- **SC-004**: The coherence of technology clusters is measured by the average intra-cluster correlation coefficient, which must be ≥ 0.65 and statistically significantly higher than inter-cluster correlation (p < 0.05). (See US-3)
- **SC-005**: The computational feasibility is measured by the total execution time on a standard CPU-only runner, ensuring completion within 6 hours. (See FR-001, FR-002)
- **SC-006**: The validity of tag trends as a proxy for adoption is measured by the Pearson correlation coefficient between the SO tag trend slope and the external metric (GitHub stars/NPM downloads), requiring a value ≥ 0.7. (See US-1)

## Assumptions

- The Stack Overflow data dump available via `archive.org` or `data.stackexchange.com` contains the `PostsTags` table with sufficient coverage from 2015 to 2023.
- Tag names in the dataset are consistent enough that simple normalization (lowercase, trim) is sufficient; no complex fuzzy matching or synonym resolution is required.
- The analysis will be observational; any identified correlations between tags or trends are strictly associational and not causal.
- The dataset size (PostTags table) fits within the memory constraints of the free-tier GitHub Actions runner after sampling or efficient streaming.
- The Mann-Kendall test and Pearson correlation are appropriate non-parametric methods for this data, assuming no complex autocorrelation structures that would invalidate the independence assumption without further correction.
- If the dataset lacks a specific variable (e.g., post body text for sentiment analysis), the scope is strictly limited to tag frequency and co-occurrence metrics.
- The "top 50" tags for trend analysis are defined as the 50 tags with the highest total frequency count across the entire 2015-2023 period, **after** filtering for tags with ≥12 months of data.
- No GPU acceleration is available; all statistical computations (Mann-Kendall, bootstrapping, clustering) must be performed using CPU-only libraries (e.g., `scipy`, `scikit-learn`, `statsmodels`).
- The circularity concern (predictor and outcome derived from the same signal) is acknowledged as a limitation of the single-source methodology, mitigated by FR-007 which requires external validation against independent data sources.
- The Stack Overflow Developer Survey taxonomy and official release logs are publicly available and serve as the ground truth for semantic validation.