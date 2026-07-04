# Feature Specification: Investigating the Correlation Between Gut Microbiome Composition and Sleep Quality

**Feature Branch**: `001-gene-regulation`
**Created**: 2023-10-27
**Status**: Draft
**Input**: User description: "Investigating the Correlation Between Gut Microbiome Composition and Sleep Quality Using Public Datasets"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1)

**As a** research analyst, **I want** to automatically download, filter, and merge the American Gut Project microbiome data with sleep metadata, excluding samples with antibiotic use in the last 3 months or missing sleep data, **so that** I have a clean, analysis-ready dataset.

**Why this priority**: Without a validated, clean dataset, no statistical analysis can occur. This is the foundational step that determines the feasibility of the entire study.

**Independent Test**: The pipeline can be tested by running the ingestion script and verifying that the output CSV contains only rows where `antibiotic_use_last_3m` is false/null and `sleep_efficiency` and `sleep_duration_hours` are not null, and that the total row count matches the expected filtered size from the source.

**Acceptance Scenarios**:
1. **Given** raw OTU tables and metadata from American Gut Project, **When** the ingestion script runs, **Then** samples with reported antibiotic use in the last 3 months are excluded from the final dataset.
2. **Given** the merged dataset, **When** the script checks for sleep variables, **Then** any sample lacking a valid `sleep_efficiency` or `sleep_duration_hours` (for the 7 days prior to sample collection) is removed.
3. **Given** the final dataset, **When** the user inspects the schema, **Then** it contains alpha-diversity columns (Shannon, Simpson, Observed OTUs), sleep metric columns, and covariates (age, BMI) without missing values in these specific fields.

---

### User Story 2 - Statistical Correlation Analysis (Priority: P2)

**As a** researcher, **I want** to compute Spearman rank correlations between alpha-diversity indices (Shannon, Simpson, Observed OTUs) and sleep quality metrics, applying Benjamini-Hochberg correction for multiple comparisons, **so that** I can identify statistically significant associations while controlling for false discoveries.

**Why this priority**: This is the core scientific inquiry. It directly addresses the research question and provides the primary evidence for the gut-brain axis hypothesis. The analysis is strictly limited to alpha-diversity indices (approx. 3 metrics) vs. sleep metrics (approx. 2-3 variables) to ensure statistical power and manage multiple comparison correction.

**Independent Test**: The analysis script can be tested on a small, synthetic dataset with known correlation coefficients to verify that the calculated Spearman r-values and adjusted p-values match expected mathematical results.

**Acceptance Scenarios**:
1. **Given** the cleaned dataset, **When** the correlation analysis runs, **Then** Spearman correlation coefficients and raw p-values are calculated for every pair of alpha-diversity metric (Shannon, Simpson, Observed OTUs) and sleep variable.
2. **Given** the set of raw p-values, **When** the Benjamini-Hochberg procedure is applied, **Then** adjusted p-values (q-values) are generated and stored.
3. **Given** the analysis results, **When** the null hypothesis is tested at α = 0.05, **Then** only associations with q-value < 0.05 are flagged as statistically significant.
4. **Given** the analysis results, **When** the user inspects the output, **Then** the 'Observed OTUs' index is explicitly included in the correlation table alongside Shannon and Simpson.

---

### User Story 3 - Visualization and Reporting (Priority: P3)

**As a** stakeholder, **I want** to generate scatterplots with regression lines and boxplots by sleep quartiles for significant correlations, **so that** I can visually interpret the strength and direction of the relationships.

**Why this priority**: Visualizations are essential for communicating findings and validating the statistical output, but they are secondary to the computation of the statistics themselves.

**Independent Test**: The visualization module can be tested by generating a plot file and verifying that the output image file exists, contains the correct axis labels, and displays the regression line for the specified variable pair.

**Acceptance Scenarios**:
1. **Given** a significant correlation result, **When** the report generation script runs, **Then** a scatterplot with a regression line is saved to the output directory.
2. **Given** the sleep efficiency variable, **When** the script runs, **Then** a boxplot grouping samples by sleep quartile (Q1-Q4) is generated.
3. **Given** the full analysis, **When** the final report is compiled, **Then** it includes a summary table of all correlations with their r-values, p-values, and adjusted q-values.

### Edge Cases

- What happens if the American Gut Project dataset is unavailable or the API rate-limits the download? (System should retry 3 times with exponential backoff, then fail gracefully with a clear error message).
- How does the system handle samples where BMI is missing but other data is present? (Exclude these samples from the multivariate analysis but include them in univariate diversity checks if valid).
- What if no correlations survive the Benjamini-Hochberg correction? (The system must still generate a report explicitly stating "No significant associations found" rather than crashing or returning empty results).

## Requirements

### Functional Requirements

- **FR-001**: System MUST download and parse pre-processed 16S rRNA OTU count tables and metadata from the American Gut Project public repository at ` (or the current stable public URL for the dataset) (See US-1).
- **FR-002**: System MUST filter samples to exclude those where the `antibiotic_use_last_3m` field is true (indicating use in the last 3 months) and those lacking valid `sleep_efficiency` or `sleep_duration_hours` (for the 7 days prior to sample collection) (See US-1).
- **FR-003**: System MUST compute alpha-diversity indices (Shannon, Simpson, Observed OTUs) using `scikit-bio` or `vegan` on the filtered count tables, ensuring the computation completes within 6 hours on a 2-core runner (See US-2).
- **FR-004**: System MUST perform Spearman rank correlation tests between each alpha-diversity index (Shannon, Simpson, Observed OTUs) and sleep variables. Additionally, the system MUST flag any correlation with |r| > 0.3 as a "moderate correlation" for reporting purposes, while noting that Spearman detects only monotonic trends (See US-2).
- **FR-005**: System MUST apply Benjamini-Hochberg correction to p-values to control for false discovery rate across the set of alpha-diversity vs. sleep metric comparisons (See US-2).
- **FR-006**: System MUST generate scatterplots with regression lines and boxplots by sleep quality quartile for significant findings (See US-3).
- **FR-007**: System MUST execute the entire analysis pipeline within 7 GB RAM and 6 hours on a GitHub Actions ubuntu-latest runner (2 vCPUs) (See US-2).

### Key Entities

- **MicrobiomeSample**: Represents a single participant's gut flora data, containing OTU counts, alpha-diversity indices, and metadata (age, BMI, antibiotic status).
- **SleepMetric**: Represents self-reported sleep data, containing duration, efficiency, and latency.
- **CorrelationResult**: Represents the statistical output of a single test, containing r-value, p-value, adjusted q-value, and significance flag.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values to the implementation/research phase.

- **SC-001**: The proportion of samples excluded due to antibiotic use or missing sleep data is measured against the total initial sample size (raw downloaded dataset row count) to ensure data quality (See US-1).
- **SC-002**: The correlation strength (|r|) and statistical significance (q-value < 0.05) of alpha-diversity metrics vs. sleep efficiency are measured against the biological benchmark for moderate correlation (|r| > 0.3) to identify meaningful associations (See US-2).
- **SC-003**: The false discovery rate of the correlation tests is measured against the Benjamini-Hochberg adjusted p-values to ensure multiplicity control (See US-2).
- **SC-004**: The computational resource usage (RAM and CPU time) is measured against the GitHub Actions free-tier limits (7 GB RAM, 6 hours) to ensure feasibility (See US-2).
- **SC-005**: The reproducibility of the pipeline is measured by the successful re-execution of the script on a clean runner environment with identical output, verified by SHA-256 hash comparison of the output CSV and plot files (See US-1).

## Assumptions

- The American Gut Project public repository contains a sufficient number of adult samples with both 16S rRNA data and self-reported sleep questions to achieve statistical power (if the dataset is too small, the study will be underpowered, but the pipeline will still run).
- The "American Gut Project" data source contains the specific variable "sleep efficiency" or "hours slept" in its metadata; if not, the analysis will be limited to the available sleep-related variables found in the dataset.
- The relationship between gut microbiome diversity and sleep quality is observational; therefore, all findings will be framed as associational, not causal, as no random assignment exists in the public dataset.
- The `scikit-bio` or `vegan` packages can compute alpha-diversity indices on the full dataset within the 6-hour time limit on a CPU-only runner without requiring GPU acceleration.
- The Benjamini-Hochberg correction is the appropriate method for multiple comparison control in this context, rather than Bonferroni, due to the large number of taxa comparisons (though this analysis is limited to alpha-diversity).
- The pipeline is designed to handle datasets exceeding 7 GB RAM via chunked processing; the system does not assume the raw dataset fits in memory.
- A correlation magnitude of |r| > 0.3 is defined as "moderate correlation" for reporting purposes, consistent with the Idea's expected results, but is not used as a hard filter for data inclusion or exclusion.
- The sleep metadata window (7 days prior to sample collection) aligns with the physiological recovery period of the microbiome after potential antibiotic exposure.