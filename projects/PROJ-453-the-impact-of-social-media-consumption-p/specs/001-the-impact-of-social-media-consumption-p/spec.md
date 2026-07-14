# Feature Specification: The Impact of Social Media Consumption Patterns on Cognitive Flexibility

**Feature Branch**: `001-social-media-cognitive-flexibility`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "Does frequent task-switching between social media platforms predict reduced performance on cognitive flexibility measures?"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Variable Extraction (Priority: P1)

The system must successfully download, parse, and extract the specific predictor and outcome variables from the designated public survey datasets (e.g., AddHealth, HILDA, ESS) without requiring manual intervention or external API keys beyond standard public access.

**Why this priority**: This is the foundational step. Without a clean, reproducible pipeline to extract the "platform-switching index" and "cognitive flexibility scores," no analysis can occur. It is the minimum viable data product.

**Independent Test**: The pipeline can be run against a mock or subset of the target dataset; if it outputs a CSV containing the required columns (switching_index, cognitive_score, age, total_time) without errors, the story is complete.

**Acceptance Scenarios**:
1. **Given** a public URL for the AddHealth Wave IV dataset is configured, **When** the ingestion script executes, **Then** the script downloads the raw files and outputs a cleaned CSV with 500+ rows containing the `switching_index` and `cognitive_flexibility_score` columns.
2. **Given** the target dataset lacks a direct "app switching frequency" variable, **When** the script runs, **Then** it successfully computes the proxy `switching_index` using the formula `(number_of_platforms) × (self_reported_switching_frequency)` and logs the derivation method.
3. **Given** the dataset contains missing values on the primary outcome variable, **When** the script runs, **Then** it automatically excludes rows with missing outcomes and reports the exclusion count (e.g., "Excluded 12 rows due to missing WCST data").

---

### User Story 2 - Associational Analysis and Model Fitting (Priority: P2)

The system must fit a multiple linear regression model to test the relationship between the switching index and cognitive flexibility, controlling for age and total screen time, and output the statistical summary (coefficients, p-values, R²) in a reproducible format.

**Why this priority**: This delivers the core research answer. It transforms raw data into the specific statistical evidence required to validate the hypothesis, adhering to the "associational" framing for observational data.

**Independent Test**: The analysis script runs on the extracted CSV and produces a JSON report containing the regression coefficients and p-values; the output can be verified against a known small sample manually.

**Acceptance Scenarios**:
1. **Given** a cleaned dataset with valid predictor and outcome variables, **When** the regression model is fitted, **Then** the output includes the standardized beta coefficient for `switching_index` and its p-value, explicitly labeled as an associational estimate.
2. **Given** the model includes an interaction term (`switching_index × age`), **When** the model is fitted, **Then** the output includes the interaction coefficient and a p-value indicating whether age moderates the relationship.
3. **Given** multiple hypothesis tests are performed (e.g., testing switching index vs. platform count), **When** the analysis completes, **Then** the output includes a corrected p-value (e.g., Bonferroni or FDR) to account for multiplicity.

---

### User Story 3 - Sensitivity Analysis and Visualization (Priority: P3)

The system must perform a sensitivity analysis on the switching index definition (sweeping thresholds) and generate publication-ready visualizations (scatter plots with regression lines) to support the findings.

**Why this priority**: This ensures the methodological robustness of the results. It demonstrates that the findings are not artifacts of a specific arbitrary cutoff and provides the visual evidence needed for the final report.

**Independent Test**: The script generates PDF/PNG files containing the regression plot and a sensitivity table; the visualizations can be inspected to confirm the regression line and confidence intervals are plotted correctly.

**Acceptance Scenarios**:
1. **Given** the primary regression result, **When** the sensitivity analysis runs, **Then** it re-runs the model using alternative operationalizations (e.g., `platform_count` alone, `switching_frequency` alone) and outputs a table comparing the beta coefficients across these definitions.
2. **Given** the regression results, **When** the visualization script executes, **Then** it generates a scatter plot with `switching_index` on the X-axis, `cognitive_score` on the Y-axis, and a fitted regression line with 95% confidence intervals.
3. **Given** the interaction term is significant, **When** the visualization script executes, **Then** it generates a stratified plot showing the regression lines for at least two distinct age groups (e.g., <30 and >30).

---

### Edge Cases

- **Dataset Variable Mismatch**: What happens if the chosen dataset (e.g., ESS) contains no cognitive flexibility measures? The system must fail gracefully with a clear error message listing available variables and suggesting an alternative dataset.
- **Collinearity**: How does the system handle high collinearity between `total_time` and `switching_index`? The system must compute and report a Variance Inflation Factor (VIF) and flag if VIF > 5, preventing interpretation of independent effects.
- **Memory Constraints**: How does the system handle datasets that exceed the GB RAM limit of the CI runner? The system must implement chunked reading or sampling (e.g., a representative random subset) if the dataset size exceeds 5 GB, logging the sampling method.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST download and parse the specified public survey datasets (e.g., AddHealth, HILDA) using standard HTTP tools (`wget`/`curl`) without requiring authentication tokens. (See US-1)
- **FR-002**: The system MUST compute the `switching_index` as `(number_of_platforms) × (self_reported_switching_frequency)` and store it as a derived variable in the analysis dataset. (See US-1)
- **FR-003**: The system MUST fit a multiple linear regression model where the outcome is `cognitive_flexibility_score` and predictors include `switching_index`, `total_screen_time`, `age`, and `baseline_ability`. (See US-2)
- **FR-004**: The system MUST frame all reported effects as "associational" and explicitly exclude causal language (e.g., "causes," "impacts") in the final statistical summary output. (See US-2)
- **FR-005**: The system MUST perform a sensitivity analysis by re-running the regression with at least two alternative predictor definitions (e.g., `platform_count` only, `switching_frequency` only) and report the variation in coefficients. (See US-3)
- **FR-006**: The system MUST calculate and report the Variance Inflation Factor (VIF) for all predictors to diagnose multicollinearity before interpreting independent effects. (See US-2)
- **FR-007**: The system MUST apply a multiple-comparison correction (e.g., Bonferroni or Benjamini-Hochberg) if more than one hypothesis test is conducted on the same dataset. (See US-2)

### Key Entities

- **Participant**: Represents an individual survey respondent; attributes include `participant_id`, `age`, `total_screen_time`, `num_platforms`, `switching_frequency`, and `cognitive_score`.
- **RegressionModel**: Represents the fitted statistical model; attributes include `coefficients`, `p_values`, `r_squared`, `vif_scores`, and `correction_method`.
- **SensitivityRun**: Represents a specific iteration of the sensitivity analysis; attributes include `predictor_definition`, `beta_coefficient`, `p_value`, and `sample_size`.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values to the implementation phase.

- **SC-001**: The dataset extraction pipeline is measured against the requirement for reproducibility by successfully processing the full target dataset within the 6-hour CI runtime limit. (See FR-001)
- **SC-002**: The regression model's validity is measured against the methodological requirement for diagnostic checks by reporting VIF scores < 5 for all primary predictors. (See FR-006)
- **SC-003**: The robustness of the findings is measured against the sensitivity requirement by demonstrating that the sign and significance of the `switching_index` coefficient remain stable across at least two alternative operationalizations. (See FR-005)
- **SC-004**: The statistical rigor is measured against the multiplicity requirement by reporting a corrected p-value that accounts for the number of hypothesis tests performed. (See FR-007)
- **SC-005**: The output fidelity is measured against the associational framing requirement by ensuring zero instances of causal language (e.g., "causes," "leads to") in the final summary statistics. (See FR-004)

## Assumptions

- **Assumption about data availability**: It is assumed that at least one of the selected public datasets (AddHealth Wave IV, HILDA, or ESS) contains both a proxy for platform-switching frequency and a validated cognitive flexibility measure (e.g., WCST, Trail Making). If no single dataset contains both, the project will use a proxy variable or combine datasets, which may introduce measurement noise.
- **Assumption about measurement validity**: It is assumed that self-reported "frequency of app switching" is a sufficiently valid proxy for actual cognitive task-switching behavior, despite the known limitations of self-report bias.
- **Assumption about compute constraints**: It is assumed that the selected dataset(s) can be processed entirely within the 7 GB RAM and 6-hour runtime limits of the GitHub Actions free-tier runner using Python's `pandas` and `statsmodels` libraries without GPU acceleration.
- **Assumption about threshold justification**: The threshold for defining "high" vs. "low" switching behavior (if used for stratification) will be based on the median split of the sample distribution, justified as a standard exploratory technique, with sensitivity analysis performed on alternative cutpoints (e.g., 25th/75th percentiles).
- **Assumption about dataset-variable fit**: The project assumes that the "number of platforms" variable in the survey is a valid proxy for the "platform-switching frequency" construct, pending a `[NEEDS CLARIFICATION: does the specific survey item "number of platforms used" correlate with actual switching frequency?]` if the survey metadata is ambiguous.
- **Assumption about power**: It is assumed that the sample size of the available public datasets (typically N > 1000 for these surveys) is sufficient to detect a small-to-moderate effect size (r ≈ -0.2) with power ≥ 0.80 at α=0.05, given the multiple predictors.
