# Feature Specification: Statistical Discrepancies in Publicly Available Election Data

**Feature Branch**: `001-statistical-discrepancies`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Analyze statistical discrepancies between reported vote counts at different aggregation levels in publicly available US election datasets to determine if they deviate from expected random fluctuations."

## User Scenarios & Testing

### User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1)

The system must successfully download, parse, and normalize publicly available election data from specified sources (OpenElections, EAC, state-level CSVs) into a unified format, calculating discrepancies between lower-level sums (precinct) and reported higher-level totals (county/state).

**Why this priority**: Without a clean, unified dataset with calculated discrepancies, no statistical analysis can occur. This is the foundational data layer required for all subsequent research.

**Independent Test**: The pipeline can be tested by running the data ingestion script against a small, fixed sample of known CSV files and verifying that the output DataFrame contains the expected columns (precinct_sum, county_reported, discrepancy_abs, discrepancy_pct) with no nulls in critical fields.

**Acceptance Scenarios**:
1. **Given** a set of raw election CSV files from OpenElections, **When** the ingestion script is executed, **Then** the output contains a unified table where `precinct_sum` equals the sum of precinct votes and `discrepancy_pct` is calculated as `|precinct_sum - county_reported| / county_reported`.
2. **Given** a dataset with missing precinct-level data for a specific county, **When** the script processes it, **Then** the row is either imputed using the documented rule or flagged with a specific `missing_data` marker, and the script does not crash.
3. **Given** a dataset where the file format deviates slightly (e.g., different delimiter), **When** the script runs, **Then** it attempts to auto-detect the format or fails gracefully with a clear error message identifying the specific file and line number.

---

### User Story 2 - Null Model Simulation and Statistical Testing (Priority: P2)

The system must construct a Negative Binomial null model (to account for over-dispersion) and a permutation-based null model, then perform statistical tests (Anderson-Darling, Kolmogorov-Smirnov) to compare observed discrepancy distributions against these robust null models.

**Why this priority**: This is the core analytical engine that answers the research question. It transforms raw data into statistical evidence regarding whether discrepancies are random or systematic, using scientifically sound distributions rather than arbitrary assumptions.

**Independent Test**: The analysis module can be tested by feeding it a synthetic dataset with known properties (e.g., Negative Binomial distributed noise) and verifying that the p-values from the Anderson-Darling and KS tests align with the expected distribution (i.e., high p-values indicating fit to the null) within a tolerance of ±0.05, using a fixed random seed of 42.

**Acceptance Scenarios**:
1. **Given** a set of observed discrepancy values and a configured Monte Carlo iteration count (10,000), **When** the simulation runs, **Then** it generates a null distribution of discrepancies assuming a Negative Binomial fit to the data and calculates an Anderson-Darling statistic comparing observed vs. expected frequencies.
2. **Given** the observed and null distributions, **When** the Kolmogorov-Smirnov test is applied, **Then** the system outputs a D-statistic and a p-value indicating whether the distributions differ significantly.
3. **Given** an observational design where random assignment is impossible, **When** results are generated, **Then** the output explicitly frames findings as "associational" or "deviations from random expectation" rather than claiming causal mechanisms for the discrepancies.

---

### User Story 3 - Sensitivity Analysis and Visualization (Priority: P3)

The system must perform a sensitivity analysis on the discrepancy thresholds AND the underlying distributional assumptions, generating visualizations (histograms, Q-Q plots, heatmaps) to illustrate the robustness of the findings.

**Why this priority**: This ensures the results are not artifacts of arbitrary cutoffs or a single flawed model assumption. It addresses the methodological requirement for threshold and model justification.

**Independent Test**: The visualization module can be tested by running the sensitivity sweep (thresholds and models) and verifying that the output files (plots) are generated and that the sensitivity report correctly lists the variation in false-positive rates across the swept thresholds and models.

**Acceptance Scenarios**:
1. **Given** a primary discrepancy threshold of 0.5%, **When** the sensitivity analysis runs, **Then** it re-runs the anomaly detection with thresholds of {0.01%, 0.05%, 0.1%} and reports how the count of flagged jurisdictions changes.
2. **Given** the primary Negative Binomial null model, **When** the sensitivity analysis runs, **Then** it also executes the test using a permutation-based null model and reports the difference in flagged jurisdictions between the two models.
3. **Given** the full dataset, **When** the visualization script executes, **Then** it produces a histogram of observed vs. simulated discrepancies and a Q-Q plot, saving them as static image files within the 14GB disk limit.
4. **Given** a jurisdiction identified as an outlier, **When** the spatial analysis runs, **Then** it generates a simple heatmap or table listing the top 10 jurisdictions by discrepancy magnitude, using only CPU-tractable libraries (matplotlib/seaborn).

### Edge Cases

- **What happens when** the dataset contains a county with zero reported votes (denominator zero)? **How does system handle**: The system MUST skip the relative discrepancy calculation for that record, log a warning, and exclude it from ALL analyses involving relative discrepancies or any downstream statistical tests requiring a non-zero denominator.
- **How does system handle** datasets where the precinct-level sum exceeds the county-level reported total by a margin that implies data entry error rather than clerical noise? **How does system handle**: The system flags these as "directional anomalies" and includes them in the sensitivity analysis but excludes them from the Negative Binomial-fit test if they violate the non-negative error assumption.
- **What happens when** the GitHub Actions runner runs out of memory during the 10,000 Monte Carlo iterations? **How does system handle**: The system MUST implement a chunked processing strategy (e.g., [deferred] iterations per batch) and aggregate results, ensuring the total memory footprint stays below 7 GB.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download and parse election data from OpenElections and state-level CSV sources, normalizing aggregation levels to a unified schema (See US-1).
- **FR-002**: System MUST calculate absolute and relative discrepancies between summed lower-level totals and reported higher-level totals for every jurisdiction (See US-1).
- **FR-003**: System MUST execute a Monte Carlo simulation with 10,000 iterations (seed=42) to generate a null distribution of discrepancies assuming a Negative Binomial distribution fit to the data, with a fallback to a permutation-based null model (See US-2).
- **FR-004**: System MUST perform an Anderson-Darling test and a Kolmogorov-Smirnov test to compare observed discrepancies against the simulated null distributions (See US-2).
- **FR-005**: System MUST perform a sensitivity analysis sweeping the discrepancy threshold over the set {0.01%, [deferred], [deferred]} AND comparing the Negative Binomial null model against a permutation-based null model, reporting the variation in flagged jurisdiction counts (See US-3).
- **FR-006**: System MUST generate static visualizations (histograms, Q-Q plots, and jurisdiction lists) using only CPU-tractable libraries (matplotlib, seaborn) without requiring GPU acceleration (See US-3).
- **FR-007**: System MUST explicitly frame all statistical findings as associational deviations from random expectation, avoiding causal language, given the observational nature of the data (See US-2).
- **FR-008**: System MUST handle missing data by applying documented imputation rules or flagging records, ensuring the pipeline does not crash on incomplete datasets (See US-1).
- **FR-009**: System MUST implement chunked Monte Carlo processing to ensure the total memory usage remains under 7 GB during the simulation phase (See US-3).
- **FR-010**: System MUST validate that the input dataset contains all required variables (precinct votes, county totals) before processing, raising a clear error if a variable is missing to ensure data integrity for the research question (See US-1).

### Key Entities

- **Jurisdiction**: Represents a specific geographic unit (precinct, county, state) containing vote counts at different aggregation levels. Example attributes: `county_name` (string), `state_fips` (string), `precinct_id` (string), `vote_count` (integer).
- **Discrepancy**: The calculated difference (absolute and relative) between the sum of lower-level votes and the reported higher-level total.
- **Null Model**: A simulated distribution of discrepancies generated under the hypothesis of random clerical error, implemented as either a Negative Binomial fit or a permutation-based shuffle.
- **Anomaly**: A jurisdiction where the observed discrepancy significantly deviates from the null model distribution.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The proportion of jurisdictions with discrepancies exceeding the primary 0.5% threshold is measured against the null model distribution generated by the Monte Carlo simulation (See US-2).
- **SC-002**: The goodness-of-fit p-value from the Anderson-Darling test is measured against the standard significance level (α=0.05) to determine if the observed distribution deviates from the null (See US-2).
- **SC-003**: The stability of anomaly detection is measured against the variation in flagged jurisdiction counts across the sensitivity sweep thresholds {0.01%, 0.05%, 0.1%} and across the two null models (See US-3).
- **SC-004**: The total execution time of the analysis pipeline is measured against the GitHub Actions free-tier limit of 6 hours (See US-3).
- **SC-005**: The memory footprint of the Monte Carlo simulation is measured against the 7 GB RAM limit of the runner environment (See US-3).
- **SC-006**: The correlation between predictor variables (if any) is measured against a collinearity diagnostic threshold of Variance Inflation Factor (VIF) > 5 to ensure no spurious independent effects are claimed (See US-2).

## Assumptions

- **Assumption about data availability**: Publicly available datasets (OpenElections, EAC) contain the necessary granular data (precinct-level sums and county-level reported totals) for the target election cycle; if a specific variable (e.g., specific ballot type counts) is missing, it will be excluded from the analysis rather than imputed.
- **Assumption about error model**: Clerical errors in election data entry are modeled using a Negative Binomial distribution (to account for over-dispersion) or a permutation-based shuffle, rather than a Poisson distribution, as this provides a more robust baseline for detecting systematic deviations in aggregated election data.
- **Assumption about computational constraints**: The total size of the selected election dataset (after sampling if necessary) will fit within the 14 GB disk and 7 GB RAM limits of the GitHub Actions runner, allowing the full Monte Carlo simulation to complete within 6 hours.
- **Assumption about threshold justification**: A discrepancy threshold of 0.5% is selected as the primary cutoff based on community standards for "benign noise" in election auditing, with the sensitivity analysis confirming robustness around this value.
- **Assumption about inference framing**: Since the data is observational (no random assignment of data entry pipelines), the analysis will strictly test for deviations from a random error model and will not infer causal mechanisms for the discrepancies (e.g., fraud vs. system failure).
- **Assumption about collinearity**: If multiple predictors (e.g., population density and precinct size) are used in any extended analysis, they will be checked for collinearity, and any joint relationships will be described descriptively rather than claiming independent predictive effects.