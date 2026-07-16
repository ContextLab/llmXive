# Feature Specification: Assessing Statistical Significance of Observed Correlations in Public Databases

**Feature Branch**: `001-assess-correlation-significance`  
**Created**: 2026-06-25  
**Status**: Draft  
**Input**: User description: "Assessing Statistical Significance of Observed Correlations in Public Databases"

## User Scenarios & Testing

### User Story 1 - Core Permutation Null Model Generation (Priority: P1)

The system must be able to ingest a multivariate dataset, compute observed network statistics (mean absolute correlation, density, etc.), and generate an empirical null distribution for each statistic by performing a sufficient number of random permutations of the data while preserving marginal distributions.

**Why this priority**: This is the foundational statistical engine. Without a valid null distribution generated via permutation, no significance testing can occur. This is the minimal viable product (MVP) for the research question: distinguishing signal from noise.

**Independent Test**: Can be fully tested by running the pipeline on a single dataset (e.g., *Wine*) and verifying that the output includes a histogram of null values and the observed value, with the observed value falling outside the 95% confidence interval (central 95%) of the null distribution if the data is synthetic with known structure.

**Acceptance Scenarios**:

1. **Given** a CSV file with ≥20 continuous variables, **When** the system executes the permutation engine with N=2,000, **Then** the system outputs four distinct null distribution arrays (one per statistic) and the four corresponding observed statistic values.
2. **Given** a synthetic dataset with a known block-diagonal covariance structure, **When** the system runs the permutation test, **Then** the observed network density must fall in the top [deferred] of the null distribution (p < 0.05), confirming the method detects true signal.
3. **Given** a dataset with shuffled columns (no true correlation), **When** the system runs the test, **Then** the observed network density must fall within the central [deferred] of the null distribution (p > 0.05), confirming the method does not generate false positives.

---

### User Story 2 - Multiple Testing Correction and Significance Reporting (Priority: P2)

The system must apply the Benjamini-Yekutieli (BY) procedure to the empirical p-values generated across all datasets and all four network statistics to control the False Discovery Rate at a predefined significance level under dependence, and produce a summary table of significant findings.

**Why this priority**: The research question explicitly addresses "multiple‑testing effects" across many datasets and statistics. Reporting raw p-values without correction would lead to inflated false positives, invalidating the study's conclusions. This is the critical step for statistical validity.

**Independent Test**: Can be tested by feeding the system a set of p-values where the ground truth of significance is known (simulated), and verifying that the BY-corrected q-values correctly identify the true positives while controlling the expected proportion of false discoveries under dependence.

**Acceptance Scenarios**:

1. **Given** a list of raw empirical p-values from 6 datasets × 4 statistics (24 total tests), **When** the system applies the BY procedure, **Then** the output must include a table listing each test, its raw p-value, its adjusted q-value, and a boolean flag indicating significance at α=0.05.
2. **Given** a scenario where 20 of 24 tests are truly null and 4 are true signals, **When** the system runs the correction, **Then** the number of false discoveries among the reported significant results must be ≤ 5% of the total reported discoveries (on average).
3. **Given** the requirement to frame findings as associational, **When** the system generates the summary report, **Then** the report must explicitly state that significant results indicate "non-random association" rather than "causal effect."

---

### User Story 3 - Threshold Sensitivity Analysis and Visualization (Priority: P3)

The system must perform a sensitivity analysis on the correlation threshold (|r| > 0.3) by sweeping it across {0.1, 0.2, 0.3, 0.4, 0.5} and reporting how the network density and significance rates vary, alongside generating visualizations (heatmaps, histograms) for the primary threshold.

**Why this priority**: The choice of |r| > 0.3 is a community-standard default but arbitrary. The methodology panel requires explicit justification and sensitivity analysis to ensure results are robust to this decision. This ensures the findings are not artifacts of a specific cutoff choice. The sweep set of candidate values is confirmed to be feasible within the runtime limit.

**Independent Test**: Can be tested by running the analysis on a single dataset with multiple thresholds and verifying that the output includes a sensitivity plot or table showing the variation in "significant" counts and density metrics across the swept thresholds.

**Acceptance Scenarios**:

1. **Given** a dataset and the primary threshold |r| > 0.3, **When** the sensitivity analysis is triggered, **Then** the system must re-run the permutation and significance test for thresholds in {0.1, 0.2, 0.3, 0.4, 0.5} and output a summary table of the results.
2. **Given** the output of the sensitivity analysis, **When** a user reviews the table, **Then** they must be able to see the change in the number of significant statistics (e.g., "Significant at 0.3: 4/24; Significant at 0.4: 2/24") to assess robustness.
3. **Given** the primary analysis results, **When** the system generates visualizations, **Then** it must produce a heatmap of the observed correlation matrix and a histogram of the null distribution with the observed value overlaid for at least one representative dataset.

---

### Edge Cases

- What happens when a dataset contains < 20 variables? (The system should skip the dataset or raise a specific warning, as the network statistics may be unstable).
- How does the system handle datasets with missing values? (The system must impute or drop rows to ensure the permutation preserves the marginal distribution correctly; dropping is preferred for simplicity).
- What if the permutation count (2,000) results in a p-value of exactly 0 or 1? (The system must handle edge cases in p-value calculation, e.g., using (r+1)/(n+1) to avoid 0/1).
- How does the system handle datasets with constant variables (zero variance)? (The system must detect and exclude these variables prior to correlation calculation to avoid division by zero).

## Requirements

### Functional Requirements

- **FR-001**: System MUST download and load 6 specific multivariate datasets from the UCI Machine Learning Repository (Wine, Abalone, Breast Cancer Wisconsin, Student Performance, Air Quality, Concrete Compressive Strength) containing ≥20 continuous variables; if a dataset has <20 continuous variables, it is excluded from the analysis. (See US-1)
- **FR-002**: System MUST compute Pearson and Spearman correlation matrices for each dataset using `scipy.stats` and construct an undirected weighted graph by thresholding absolute Pearson correlations at |r| > 0.3. (See US-1)
- **FR-003**: System MUST perform a sufficient number of random permutations per dataset, preserving marginal distributions, to generate empirical null distributions for mean absolute correlation, edge density, maximum absolute correlation, and average clustering coefficient. (See US-1)
- **FR-004**: System MUST calculate two-sided empirical p-values and apply the Benjamini-Yekutieli procedure across all tests (multiple datasets × 4 statistics) to control the False Discovery Rate at 0.05 under dependence. (See US-2)
- **FR-005**: System MUST execute a sensitivity analysis by sweeping the correlation threshold over a range of low to moderate values and report the variation in network density and significance counts. (See US-3)
- **FR-006**: System MUST generate visualizations including heatmaps of observed vs. null correlation matrices and histograms of null distributions with observed values overlaid. (See US-3)
- **FR-007**: System MUST frame all significant findings as "associational" evidence of non-random structure, explicitly avoiding causal language in the output report. (See US-2)
- **FR-008**: System MUST handle datasets with missing values by dropping rows with any missing data prior to analysis to ensure valid permutation logic. (See Edge Cases)
- **FR-009**: System MUST validate the permutation null model by testing a synthetic dataset with known independence (identity covariance) and confirming that the observed statistics fall within the central [deferred] of the null distribution (p > 0.05) for at least 95% of runs. (See US-1)

### Key Entities

- **Dataset**: A multivariate collection of continuous variables (e.g., from UCI) used as the input for analysis.
- **Network Statistics**: A set of four metrics (mean absolute correlation, density, max correlation, clustering coefficient) derived from the correlation matrix.
- **Null Distribution**: An empirical distribution of a network statistic generated from [deferred] permuted versions of the original data.
- **Significance Result**: A structured record containing the raw p-value, BY-adjusted q-value, and a binary significance flag for a specific dataset-statistic pair.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values to the implementation/research phase.

- **SC-001**: The proportion of synthetic datasets with known independence (true null) correctly identified as non-significant (p > 0.05) is measured against the ground truth of the synthetic generation process, with a required pass rate of ≥ 95%. (See US-1)
- **SC-002**: The system must output q-values calculated via the Benjamini-Yekutieli procedure; in synthetic tests with known signals, the system must detect ≥ 90% of true positives. (See US-2)
- **SC-003**: The stability of the "significant" count is measured against the variation in the correlation threshold sweep (|r| ∈ {0.1, 0.2, 0.3, 0.4, 0.5}) to assess robustness. (See US-3)
- **SC-004**: The total runtime of the full pipeline (datasets × a substantial number of permutations) is measured against the time limit of the GitHub Actions free-tier runner. (See US-1)

## Assumptions

- **Dataset Variable Availability**: It is assumed that the 6 selected UCI datasets contain ≥20 continuous variables suitable for correlation analysis; if a dataset has fewer, it will be excluded from the analysis.
- **Permutation Validity**: It is assumed that permuting each variable independently preserves the marginal distribution sufficiently to generate a valid null hypothesis for network statistics, provided the strategy is validated for specific metrics (see FR-009); note that for non-linear metrics like clustering, the null distribution is empirically derived and may require larger permutation counts for stability.
- **Threshold Justification**: The threshold |r| > 0.3 is assumed to be a defensible community standard for "moderate" correlation in exploratory network analysis; the sensitivity analysis will verify if results hold for adjacent values.
- **Compute Constraints**: It is assumed that the permutation count and dataset scope will complete within a reasonable time limit on a multi-CPU, sufficient RAM runner..; if not, the permutation count will be reduced as a fallback.
- **Methodological Framing**: It is assumed that the datasets are observational (no random assignment), so all findings must be framed as associational, not causal.
- **Measurement Validity**: It is assumed that Pearson and Spearman correlations are valid measures of linear and monotonic relationships for the continuous variables in these repositories.
- **Predictor Collinearity**: It is assumed that the network statistics (e.g., density and mean correlation) are treated as a joint set of dependent measures, and the Benjamini-Yekutieli procedure accounts for the multiplicity of these inter-dependent tests.