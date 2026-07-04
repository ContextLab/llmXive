# Feature Specification: Investigating the Correlation Between Gut Microbiome Composition and Sleep Quality

**Feature Branch**: `001-gene-regulation`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Investigating the Correlation Between Gut Microbiome Composition and Sleep Quality Using Public Datasets"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Ingestion and Pre-processing (Priority: P1)

The research pipeline MUST successfully download, filter, and merge raw 16S rRNA OTU count tables from the American Gut Project with sleep metadata, excluding samples with recent antibiotic use or missing sleep data, to produce a clean analysis-ready dataset.

**Why this priority**: Without a clean, merged dataset, no statistical analysis can occur. This is the foundational step that ensures data quality and validity before any hypothesis testing.

**Independent Test**: Can be fully tested by running the ingestion script and verifying the output DataFrame contains a sample size sufficient to achieve statistical power ≥0.8 for the expected effect size (or a minimum of n ≥30 samples) with non-null alpha-diversity and sleep metrics, and zero samples with `antibiotic_use_last_3mo == True`.

**Acceptance Scenarios**:

1. **Given** a raw OTU count table and metadata file from American Gut, **When** the ingestion script runs, **Then** samples with `antibiotic_use_last_3mo == True` or missing sleep data are removed, resulting in a filtered dataset.
2. **Given** the filtered dataset, **When** alpha-diversity indices (Shannon, Simpson) are computed, **Then** every sample in the output DataFrame has a valid numerical value for `shannon_index`, `simpson_index`, and at least one sleep metric.
3. **Given** the merged dataset, **When** the script completes, **Then** the output file `analysis_data.csv` is generated.

---

### User Story 2 - Statistical Correlation Analysis (Priority: P2)

The research pipeline MUST compute Spearman rank correlations between alpha-diversity indices and sleep metrics (efficiency, duration), apply Benjamini-Hochberg correction for multiple comparisons, and output a summary table of correlation coefficients and adjusted p-values. Additionally, the pipeline MUST perform taxon-level correlation analysis between individual OTUs/ASVs and sleep metrics.

**Why this priority**: This directly addresses the research question. It transforms the cleaned data into statistical evidence regarding the gut-sleep relationship at both community and taxon levels.

**Independent Test**: Can be fully tested by executing the analysis script on the `analysis_data.csv` and verifying the output `correlation_results.csv` contains rows for Shannon and Simpson indices, and a separate section or table containing taxon-level correlations, with `p_adjusted` values calculated via Benjamini-Hochberg.

**Acceptance Scenarios**:

1. **Given** the `analysis_data.csv` with ≥30 valid samples, **When** the correlation script runs, **Then** a Spearman correlation coefficient (`r`) and unadjusted p-value are calculated for each diversity metric against `sleep_efficiency` and `sleep_duration`.
2. **Given** the unadjusted p-values, **When** the Benjamini-Hochberg correction is applied, **Then** the output `correlation_results.csv` contains an `p_adjusted` column where values are sorted by rank and adjusted accordingly.
3. **Given** the taxon-level data, **When** the script runs, **Then** correlations are computed for all available OTUs/ASVs against sleep metrics, resulting in thousands of tests.
4. **Given** the final results, **When** the script completes, **Then** the system logs whether any `p_adjusted < 0.05` to indicate statistical significance.

---

### User Story 3 - Visualization and Reporting (Priority: P3)

The research pipeline MUST generate scatter plots with regression lines for significant correlations and boxplots comparing diversity across sleep quartiles, saving them as PNG files in the `results/` directory.

**Why this priority**: Visualizations are essential for interpreting the statistical findings and communicating results to the scientific community.

**Independent Test**: Can be fully tested by running the visualization script and verifying that `results/scatter_shannon_sleep.png` and `results/boxplot_diversity_sleep_quartile.png` exist, have a file size >0 bytes, and contain valid PNG headers.

**Acceptance Scenarios**:

1. **Given** the `correlation_results.csv` with at least one significant correlation, **When** the visualization script runs, **Then** a scatter plot with a regression line is generated for that metric.
2. **Given** the `analysis_data.csv`, **When** the script runs, **Then** sleep efficiency is binned into quartiles, and a boxplot showing diversity distribution per quartile is generated.
3. **Given** the generated plots, **When** the script finishes, **Then** all PNG files are saved to the `results/` directory with filenames matching the metric names.

---

### Edge Cases

- What happens if the American Gut Project dataset is unavailable or the download fails? (The research question is not specified in the passage. The method is not specified in the passage. References are not specified in the passage. The system must implement a retry mechanism with a backoff strategy, then fail gracefully with an error log.).
- How does the system handle samples with zero OTU counts (empty samples)? (System must exclude them during alpha-diversity calculation to avoid `NaN` results).
- What if the merged dataset has <30 samples after filtering? (System must halt analysis and log a warning: "Sample size insufficient for robust correlation; power < 0.8").

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download and parse 16S rRNA OTU count tables and metadata from the American Gut Project public repository, excluding samples with `antibiotic_use_last_3mo == True` or missing sleep data. (See US-1)
- **FR-002**: System MUST compute alpha-diversity indices (Shannon, Simpson) using the `scikit-bio` library on the filtered count tables. (See US-1)
- **FR-003**: System MUST merge the computed diversity metrics with sleep quality variables (sleep efficiency, duration) into a single analysis DataFrame. (See US-1)
- **FR-004**: System MUST perform Spearman rank correlation tests between each diversity metric and sleep variables (efficiency, duration), applying Benjamini-Hochberg correction to p-values. (See US-2)
- **FR-005**: System MUST generate scatter plots with regression lines and boxplots by sleep quartile using `seaborn` or `matplotlib`, saving outputs to `results/`. (See US-3)
- **FR-006**: System MUST generate a `requirements.txt` file documenting all Python dependencies and their versions used in the analysis pipeline. (See US-1)
- **FR-007**: System MUST perform Spearman rank correlation tests between individual OTUs/ASVs and sleep variables (efficiency, duration), applying Benjamini-Hochberg correction to p-values. (See US-2)
- **FR-008**: System MUST adjust for known confounders (age, BMI, diet, medication) using partial correlation or stratified analysis where data is available. (See US-2)
- **FR-009**: System MUST implement a fallback mechanism to use proxy sleep variables (e.g., self-reported sleep quality score) if the primary `sleep_efficiency` variable is missing from the dataset. (See US-1)

### Non-Functional Requirements

- **NFR-001**: The entire analysis pipeline MUST complete execution within 6 hours on a standard CPU-only environment with a maximum memory footprint of ≤7 GB RAM.

### Key Entities

- **Sample**: A unique biological specimen identified by a Sample ID, containing attributes for OTU counts, antibiotic history, and sleep metrics.
- **DiversityMetric**: A derived value representing microbial diversity (Shannon, Simpson) associated with a specific Sample.
- **SleepMetric**: A derived value representing sleep quality (efficiency, duration) associated with a specific Sample.
- **Taxon**: A specific bacterial classification (OTU/ASV) associated with a specific Sample, containing count data.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The statistical validity of the findings is measured against the requirement to apply Benjamini-Hochberg correction for multiple comparisons to control the false discovery rate. (See FR-004, FR-007)
- **SC-002**: The data quality is measured against the requirement to exclude all samples with recent antibiotic use or missing sleep metadata prior to analysis. (See FR-001)
- **SC-003**: The reproducibility of the results is measured against the requirement to document all code and environment dependencies in a `requirements.txt` file. (See FR-006)
- **SC-004**: The sensitivity of the threshold (p < 0.05) is measured by performing a sensitivity analysis sweeping the significance cutoff over a range of conventional thresholds and reporting the count of significant findings for each cutoff value in a summary table. (See FR-004)

## Assumptions

- The American Gut Project public repository contains a pre-processed 16S rRNA OTU count table and metadata file with `antibiotic_use_last_3mo` and sleep-related survey questions (e.g., hours slept, sleep efficiency) for the same sample IDs, or sufficient proxy variables exist.
- The relationship between gut microbiome diversity and sleep quality is observational; therefore, findings will be framed as associational rather than causal, as no random assignment is present in the dataset.
- The `scikit-bio` and `pandas` libraries can process the dataset using streaming/chunking techniques to stay within the 7 GB RAM limit of the GitHub Actions runner.
- The Benjamini-Hochberg correction is the appropriate method for controlling false discovery rate given the number of hypothesis tests (including the thousands of taxon-level tests).
- No GPU or CUDA accelerators are required, as the analysis relies on classical statistical methods and CPU-tractable Python libraries.

## Risks

- **Dataset Sufficiency**: The dataset size, after filtering for antibiotic use and missing sleep data, may be insufficient (<30 samples) to perform a meaningful Spearman correlation analysis. If this occurs, the system will halt analysis as per Edge Cases.
- **Variable Availability**: Specific 'sleep efficiency' metrics may not be directly available in the public AGP release, requiring the use of proxy variables or external data linkage, which may reduce the precision of the sleep measurement.
- **Confounding**: Unmeasured confounders (e.g., specific diet details, stress levels) may bias the observed correlations despite adjustments for known variables.