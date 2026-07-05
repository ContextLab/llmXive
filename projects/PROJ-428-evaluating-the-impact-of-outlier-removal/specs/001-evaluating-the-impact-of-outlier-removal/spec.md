# Feature Specification: Evaluating the Impact of Outlier Removal Methods on Variance Estimation

**Feature Branch**: `001-evaluating-outlier-removal-impact`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Evaluating the Impact of Outlier Removal Methods on Variance Estimation"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Generate Contaminated Dataset and Compute Baseline Metrics (Priority: P1)

The researcher needs to generate synthetic clean distributions (e.g., Normal, LogNormal), simulate outlier contamination at varying rates, and compute baseline variance estimates to establish ground truth for comparison.

**Why this priority**: This is the foundational step; without valid contaminated data and a known ground truth (synthetic), no removal strategies can be evaluated. It delivers the core dataset required for all subsequent analysis.

**Independent Test**: Can be fully tested by executing the data generation script and verifying that the output files contain the expected number of rows (original + injected outliers) and that variance calculations match manual checks on a small subset against the known synthetic parameters.

**Acceptance Scenarios**:

1. **Given** a list of 5 public datasets from the UCI repository, **When** the system downloads and processes them, **Then** the system MUST output 5 clean CSV files with identified continuous variables and their baseline variance values.
2. **Given** a synthetically generated clean dataset with known variance, **When** the system injects outliers at [deferred], [deferred], [deferred], and [deferred] contamination rates, **Then** the resulting dataset MUST contain the specified percentage of rows modified with extreme values, and the calculated variance MUST be significantly higher than the baseline.
3. **Given** a dataset with multiple continuous variables, **When** the system processes it, **Then** the system MUST identify and isolate all continuous variables, skipping categorical or non-numeric columns, and output a summary report listing the variable names and their baseline variances.

---

### User Story 2 - Apply Outlier Removal Strategies and Calculate Bias/MSE (Priority: P2)

The researcher needs to apply three distinct outlier removal methods (IQR filtering, Winsorization, Trimmed Variance) to the contaminated datasets and calculate the bias and Mean Squared Error (MSE) of the resulting variance estimates against the known ground truth.

**Why this priority**: This implements the core experimental intervention. It allows the researcher to see how each method performs individually, which is necessary before comparing them.

**Independent Test**: Can be fully tested by running the removal pipeline on a single simulated dataset and verifying that the output contains three distinct sets of variance estimates (one per method) and that the calculated bias/MSE values are finite numbers.

**Acceptance Scenarios**:

1. **Given** a contaminated dataset and the IQR removal rule (1.5× IQR), **When** the system applies the filter, **Then** the system MUST output a cleaned dataset where all values outside the [Q1 - 1.5×IQR, Q3 + 1.5×IQR] range are removed, and the new variance MUST be calculated.
2. **Given** a contaminated dataset and Winsorization parameters (5th/95th percentiles), **When** the system applies the transformation, **Then** the system MUST cap all values below the 5th percentile to the 5th percentile value and all values above the 95th percentile to the 95th percentile value, then calculate the variance.
3. **Given** a contaminated dataset and a [deferred] trim parameter, **When** the system applies the trimmed variance logic to variance estimation, **Then** the system MUST remove the lowest [deferred] and highest [deferred] of values, recalculate the variance of the remaining sample, and report the bias relative to the true variance.

---

### User Story 3 - Perform Statistical Comparison and Generate Visualizations (Priority: P3)

The researcher needs to run Monte Carlo replicates (sufficient per condition), perform Repeated Measures ANOVA (or Friedman test) with Bonferroni correction to compare methods, and generate interaction plots showing performance across contamination levels and distribution types.

**Why this priority**: This synthesizes the experimental results into actionable insights and statistical significance, fulfilling the research question's requirement for "systematic empirical guidance."

**Independent Test**: Can be fully tested by running the analysis script on the aggregated results and verifying that the output includes a statistical summary table with p-values (corrected) and a set of interaction plots.

**Acceptance Scenarios**:

1. **Given** the aggregated bias and MSE results from 100 Monte Carlo replicates for each method/condition, **When** the system performs Repeated Measures ANOVA, **Then** the system MUST output a p-value for the difference between methods and apply Bonferroni correction for the number of pairwise comparisons performed.
2. **Given** the performance metrics across 5 distribution types and 4 contamination levels, **When** the system generates visualizations, **Then** the system MUST produce an interaction plot where the X-axis is contamination level, lines represent methods, and Y-axis is MSE, with separate facets for distribution types.
3. **Given** the requirement to compare multiple hypotheses, **When** the system calculates significance, **Then** the system MUST explicitly state the family-wise error rate control method used (Bonferroni) and report the adjusted alpha threshold (e.g., 0.05 / number of comparisons).

---

### Edge Cases

- What happens when a dataset contains no continuous variables? (System MUST skip the dataset and log a warning).
- How does the system handle a distribution where the IQR is zero (all values identical)? (System MUST detect this and skip the IQR filter for that variable or apply a fallback to standard deviation).
- What happens if the Monte Carlo simulation exceeds the 6-hour runner limit? (System MUST implement a checkpoint/restart mechanism or reduce the replicate count to a minimum of 50 if time is critical, logging the reduction).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download at least 5 public datasets from the UCI Machine Learning Repository and identify univariate continuous variables for analysis (See US-1).
- **FR-002**: System MUST simulate outlier contamination by injecting extreme values at [deferred], [deferred], [deferred], and [deferred] rates into the identified continuous variables (See US-1).
- **FR-003**: System MUST implement three distinct outlier removal methods: IQR filtering (1.5× rule), Winsorization (5th/95th percentiles), and [deferred] Trimmed Variance (See US-2).
- **FR-004**: System MUST calculate the bias (mean difference from true variance) and Mean Squared Error (MSE) for each removal method against the known ground truth variance (See US-2).
- **FR-005**: System MUST perform 100 Monte Carlo replicates per condition (method × contamination level × distribution type) to ensure statistical stability, or 50 if time-constrained per Edge Cases (See US-3).
- **FR-006**: System MUST apply Bonferroni correction for multiple comparisons when testing the difference in MSE between the three removal methods using a Repeated Measures ANOVA (See US-3).
- **FR-007**: System MUST generate interaction plots visualizing MSE across contamination levels and distribution types for all three methods (See US-3).

### Key Entities

- **Dataset**: Represents a public dataset from UCI, containing attributes like name, source URL, and identified continuous variables.
- **ContaminationProfile**: Represents a specific experimental condition defined by contamination rate (0-20%) and distribution type.
- **RemovalMethod**: Represents the strategy applied (IQR, Winsorization, Trimmed) and its specific parameters.
- **EstimationResult**: Represents the outcome of a single replicate, containing the calculated variance, bias, and MSE.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The absolute bias of variance estimates is measured against the known true variance of the synthetic uncontaminated data for each method (See US-2).
- **SC-002**: The Mean Squared Error (MSE) of variance estimates is measured against the known true variance of the synthetic uncontaminated data to rank method performance (See US-2).
- **SC-003**: The statistical significance of performance differences between methods is measured against the Bonferroni-corrected alpha threshold (standard significance level divided by the number of comparisons) (See US-3).
- **SC-004**: The stability of results is measured by the standard deviation of MSE across multiple Monte Carlo replicates for each condition. (See US-3).
- **SC-005**: The computational feasibility is measured by the total execution time, which must be ≤ 6 hours on a GitHub Actions free-tier runner (2 CPU, 7GB RAM) (See Assumptions).

## Assumptions

- The UCI Machine Learning Repository datasets are accessible via direct HTTP/HTTPS links without requiring authentication or API keys.
- The "true variance" is calculated from a *synthetically generated* clean distribution (e.g., Normal, LogNormal) used as the ground truth for the simulation, not the raw UCI data, to ensure an unbiased baseline.
- The standard community threshold for IQR filtering is a multiplier of the interquartile range, as established in prior literature [cite].; no sensitivity analysis is required for this specific rule as it is a fixed definition, but the *effect* of the rule is tested against other methods.
- Percentiles at the extremes of the distribution are the standard community thresholds for Winsorization.; the [deferred] trim is the standard for Trimmed Variance.
- The simulation of outliers involves injecting values from a heavy-tailed distribution (e.g., Cauchy or extreme values from the same distribution scaled by a large factor) to ensure they are statistically distinct.
- The analysis is observational in nature regarding the *method performance*; findings will be framed as "Method A performs better than Method B under Condition X" (associational) rather than "Method A causes lower error" (causal), as the method is the intervention but the data generation is simulated.
- The dataset variables are independent; no collinearity diagnostics are required between variables as the analysis focuses on univariate variance estimation.
- The GitHub Actions free-tier runner (standard CPU and RAM allocation) is sufficient to process the selected datasets and a sufficient number of Monte Carlo replicates within the 6-hour limit; if not, the replicate count will be reduced to a lower feasible number.
- No GPU acceleration is available or required; all calculations will use standard CPU-based Python libraries (numpy, pandas, scipy).