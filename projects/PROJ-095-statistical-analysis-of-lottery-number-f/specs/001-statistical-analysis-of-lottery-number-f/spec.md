# Feature Specification: Lottery Draw Integrity and Anomaly Detection

**Feature Branch**: `001-lottery-draw-integrity`  
**Created**: 2026-07-08  
**Status**: Draft  
**Input**: User description: "Statistical Analysis of Lottery Number Frequency and Player Behavior"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Draw Uniformity Analysis (Priority: P1)

The system MUST ingest historical lottery draw data (winning numbers, jackpot amounts, total sales) and calculate a "draw_uniformity_deviation" score representing the statistical deviation of the *winning numbers'* frequency distribution from a uniform distribution, specifically quantifying "birthday clustering" (numbers 1-31) and consecutive patterns.

**Why this priority**: This is the foundational capability. Without accurate data ingestion and the calculation of the core metric (draw uniformity), no subsequent analysis of jackpot correlation or anomaly detection is possible. It delivers the primary data artifact required for the research question regarding lottery machine fairness.

**Independent Test**: Can be fully tested by running the ingestion script against a static, known CSV dataset and verifying the calculated `draw_uniformity_deviation` matches a manually computed reference value for that specific draw.

**Acceptance Scenarios**:

1. **Given** a CSV file containing 100 historical draws with winning numbers and jackpot sizes, **When** the ingestion script processes the file, **Then** the system outputs a JSON object where each draw includes a calculated `draw_uniformity_deviation` (Chi-Square statistic) and a boolean flag `is_majority_birthday` if the `birthday_cluster_ratio` (fraction of numbers in 1-31) > 0.5.
2. **Given** a draw where all winning numbers are >31 (e.g., 32-45), **When** the uniformity calculation runs, **Then** the `birthday_cluster_ratio` is recorded as 0.0, and the total `draw_uniformity_deviation` reflects only consecutive pattern deviations.

---

### User Story 2 - Jackpot Correlation and Anomaly Detection (Priority: P2)

The system MUST compute the statistical correlation (Spearman/Pearson) between jackpot magnitude and the calculated `draw_uniformity_deviation` scores, noting that confounding by Quick Pick proportion cannot be empirically controlled due to data limitations.

**Why this priority**: This directly answers the research question regarding the relationship between reward magnitude and draw anomalies. It builds upon the P1 data artifact to produce the primary research finding.

**Independent Test**: Can be tested by providing a pre-processed dataset with known correlations and verifying the system outputs the correct correlation coefficient and p-value within a tolerance of 0.001.

**Acceptance Scenarios**:

1. **Given** a dataset segmented into "Small," "Medium," and "Large" jackpot tiers, **When** the correlation analysis runs, **Then** the system outputs a correlation coefficient (r) and p-value for the relationship between `jackpot_amount` and `draw_uniformity_deviation`, with a metadata flag `control_variable_note` stating "Quick Pick rate unobservable; no control applied".
2. **Given** a scenario where a jackpot tier has < 5 draws, **When** the analysis runs, **Then** the system flags the result with a warning that the sample size is insufficient for reliable correlation, but still outputs the calculated coefficient.

---

### User Story 3 - Robustness Validation and Sensitivity Analysis (Priority: P3)

The system MUST perform bootstrapping (1000 iterations) to generate confidence intervals for effect sizes and execute a sensitivity analysis sweeping the "birthday clustering" threshold (e.g., 50%, 60%, 70%) to ensure results are not artifacts of arbitrary cutoffs.

**Why this priority**: This ensures the scientific validity and reproducibility of the findings. It addresses methodological concerns regarding multiplicity and threshold justification, which are critical for the methodology panel.

**Independent Test**: Can be tested by running the validation script on a small subset of data and verifying that the confidence intervals and sensitivity report are generated within the 6-hour time limit and contain no null values.

**Acceptance Scenarios**:

1. **Given** a completed correlation analysis, **When** the bootstrapping module executes, **Then** the system outputs a 95% confidence interval for the correlation coefficient that does not include zero if the p-value is <0.05.
2. **Given** a default birthday threshold of 60%, **When** the sensitivity analysis runs with thresholds {50%, 60%, 70%}, **Then** the system outputs a table showing the variation in the headline correlation coefficient across these three thresholds.

### Edge Cases

- **Missing Data**: What happens when a historical draw record lacks the `total_sales` figure? The system MUST log a warning, exclude that specific draw from any sales-dependent analysis (if applicable), but include it in the raw frequency analysis if winning numbers are present.
- **Zero Variance**: How does the system handle a jackpot tier with only a single draw? The system MUST flag this segment as "Insufficient Data for Correlation" and exclude it from the regression analysis to prevent division-by-zero errors or spurious correlations.
- **Extreme Outliers**: How does the system handle a record-breaking jackpot that is 10x the historical mean? The system MUST perform the analysis both with and without this outlier and report the difference in correlation strength in the final output.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download and parse historical lottery CSV data from specified public APIs (e.g., California Lottery, UK National Lottery) into a structured internal format (See US-1).
- **FR-002**: System MUST calculate a `draw_uniformity_deviation` score for each draw based on the Chi-Square deviation of observed winning number frequencies from a uniform distribution, specifically quantifying "birthday clustering" (numbers 1-31) and consecutive patterns (See US-1).
- **FR-003**: System MUST use explicit Quick Pick rates ONLY if provided by the source API; if not provided, the system MUST mark the `quick_pick_rate` as `NA` and explicitly NOT derive it from sales volume or prize variance (See US-2).
- **FR-004**: System MUST compute the Spearman or Pearson correlation coefficient between `jackpot_amount` and `draw_uniformity_deviation` without controlling for Quick Pick proportion, and append a metadata note explaining the absence of this control variable (See US-2).
- **FR-005**: System MUST execute a bootstrapping procedure (1000 iterations) to generate 95% confidence intervals for all reported effect sizes (See US-3).
- **FR-006**: System MUST perform a sensitivity analysis on the "birthday clustering" threshold by sweeping values {0.50, 0.60, 0.70} and reporting the resulting variance in correlation coefficients (See US-3).
- **FR-007**: System MUST apply Bonferroni correction for multiple comparisons when testing multiple bias patterns (birthday, consecutive, multiples) to control family-wise error rate (See US-3).

### Key Entities

- **DrawRecord**: Represents a single lottery event. Attributes: `draw_date`, `winning_numbers` (list), `jackpot_amount`, `total_sales`, `draw_uniformity_deviation`, `birthday_cluster_ratio`, `quick_pick_rate` (nullable).
- **BiasMetric**: Represents a specific deviation pattern. Attributes: `metric_type` (e.g., "birthday_clustering"), `threshold_value`, `observed_frequency`, `expected_frequency`.
- **CorrelationResult**: Represents the statistical outcome. Attributes: `correlation_coefficient`, `p_value`, `confidence_interval_lower`, `confidence_interval_upper`, `n_samples`, `control_variable_note`.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values to the implementation phase.

- **SC-001**: The `draw_uniformity_deviation` calculation is measured against a manually computed reference value for a known draw to ensure algorithmic accuracy (See FR-002, US-1).
- **SC-002**: The correlation coefficient between jackpot magnitude and `draw_uniformity_deviation` is measured against an alpha threshold of 0.05 to determine statistical significance (p < 0.05) (See FR-004, US-2).
- **SC-003**: The stability of the correlation result is measured against a sensitivity sweep of the clustering threshold (0.50, 0.60, 0.70) to ensure the finding is not an artifact of the chosen cutoff (See FR-006, US-3).
- **SC-004**: The 95% confidence interval width is measured against the absolute effect size to ensure precision, specifically requiring CI width ≤ 0.2 × |correlation_coefficient| (See FR-005, US-3).
- **SC-005**: The system MUST output the Bonferroni-corrected alpha and adjusted p-values for each test, ensuring the correction mechanism is active and visible in the final report (See FR-007, US-3).

## Assumptions

- **Data Availability**: It is assumed that public lottery APIs or archived CSV files contain `total_sales` volume for at least 80% of historical draws; for draws missing this data, the analysis proceeds with available fields only.
- **Observational Nature**: The analysis assumes an observational design; therefore, all findings regarding jackpot size and draw anomalies will be framed as **associational** correlations, not causal effects, as no random assignment of jackpot sizes occurs.
- **Compute Constraints**: The entire analysis (ingestion, calculation, bootstrapping) is assumed to fit within the GitHub Actions free-tier limits (2 CPU, ~7 GB RAM, 6 hours) by processing data in chunks or sampling if the full historical dataset exceeds 500MB.
- **Threshold Justification**: The "birthday clustering" threshold is set to 60% (absolute majority of numbers in 1-31) based on the community standard for defining "majority" bias in similar behavioral studies; this value is subject to the sensitivity analysis defined in FR-006.
- **Data Limitation**: The dataset is assumed to contain the necessary variables (winning numbers, sales volume, jackpot amount). However, explicit Quick Pick rates are rarely available. Therefore, the analysis is strictly limited to "Draw Integrity" (winning number distribution) and cannot empirically control for player selection behavior (Quick Pick vs. manual) as this data is unobservable from public sources.
- **Scope Boundary**: The study scope is limited to analyzing the uniformity of *winning numbers* (machine fairness) rather than *player selections* (behavior), as the latter requires proprietary ticket data not available in public archives. If the specific state lottery source provides `total_sales` only for recent years, the temporal scope of the study is strictly limited to the range where `total_sales` is available (≥ 80% coverage required for sales-dependent checks), and the analysis will explicitly report the `data_coverage_start_date` and `data_coverage_end_date` in the final output (See US-1).