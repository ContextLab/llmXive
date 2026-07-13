# Feature Specification: Investigating the Relationship Between Gut Microbiome Composition and Mental Health in Public Datasets

**Feature Branch**: `001-gut-microbiome-mental-health`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Investigating the Relationship Between Gut Microbiome Composition and Mental Health in Public Datasets"

## User Scenarios & Testing

### User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1)

The system must successfully download, merge, and preprocess the American Gut Project (AGP) microbiome data (16S rRNA) and associated mental health metadata, filtering for valid samples and handling missing values to create a clean analysis-ready dataset.

**Why this priority**: Without a clean, merged dataset containing both microbiome features and mental health scores, no statistical analysis can be performed. This is the foundational block for the entire research project.

**Independent Test**: The pipeline can be tested by running the data ingestion script and verifying that the output CSV contains ≥ 100 valid rows where both microbiome diversity metrics and mental health scores are present, with no missing values in the key predictor/outcome columns.

**Acceptance Scenarios**:

1. **Given** the AGP study ID (10317) is provided, **When** the ingestion script executes, **Then** the system downloads the OTU/ASV table and metadata, merges them on sample ID, and outputs a unified CSV file.
2. **Given** a merged dataset with missing mental health scores, **When** the preprocessing step runs, **Then** samples with missing PHQ-9 or GAD-7 scores are filtered out, and the system logs the exclusion rate.
3. **Given** the raw OTU table, **When** rarefaction and low-abundance filtering are applied, **Then** the output table contains only taxa with ≥ 0.1% prevalence and equal sequencing depth across all samples. If rarefaction results in >20% sample loss, the system must apply variance-stabilizing transformation (VST) instead and log the fallback.

---

### User Story 2 - Statistical Association Analysis (Priority: P2)

The system must calculate alpha and beta diversity metrics, perform partial correlation analyses between diversity/taxa and mental health scores, and execute PERMANOVA tests (with covariate adjustment) to determine if microbiome composition differs significantly between mental health groups.

**Why this priority**: This is the core scientific inquiry. It directly addresses the research question by quantifying the relationship between the gut microbiome and mental health indicators.

**Independent Test**: The analysis module can be tested by running it on the preprocessed dataset and verifying that it outputs a results table containing partial correlation coefficients, p-values, and effect sizes for the specified mental health variables.

**Acceptance Scenarios**:

1. **Given** a preprocessed dataset, **When** the correlation analysis runs, **Then** the system calculates partial Spearman correlations between alpha diversity (Shannon/Simpson) and PHQ-9/GAD-7 scores, adjusting for age and BMI as covariates (if data is present).
2. **Given** a preprocessed dataset, **When** the PERMANOVA test runs, **Then** the system tests for significant differences in beta diversity (Bray-Curtis) between high-depression (PHQ-9 ≥ 10, clinically defined) and low-depression groups, using distance matrix residualization to adjust for age and BMI covariates.
3. **Given** multiple hypothesis tests across taxa, **When** the analysis completes, **Then** the system applies Benjamini-Hochberg correction and reports adjusted p-values (q-values) for all tested taxa.

---

### User Story 3 - Visualization and Reporting (Priority: P3)

The system must generate publication-ready visualizations (PCoA plots, heatmaps) and a summary report highlighting significant associations, including effect directions and statistical significance.

**Why this priority**: Visualizations and reports are essential for interpreting results and communicating findings to the scientific community. While the analysis can run without them, the value of the research is not realized without clear output.

**Independent Test**: The reporting module can be tested by executing the visualization script and verifying that output image files (PNG/SVG) and a summary text file are generated, containing the expected plots and key statistical findings.

**Acceptance Scenarios**:

1. **Given** the statistical analysis results, **When** the visualization script runs, **Then** it generates a PCoA plot colored by mental health status (high vs. low depression) with ellipses indicating group centroids.
2. **Given** significant taxa associations, **When** the heatmap is generated, **Then** it displays the top associated taxa with color intensity proportional to the correlation coefficient.
3. **Given** the full analysis results, **When** the summary report is generated, **Then** it lists all significant associations (q < 0.05) with their direction (positive/negative) and effect size.

---

### User Story 4 - Validation on Independent Cohort (Priority: P3)

If an independent cohort (e.g., UK Biobank, MetaHIT) is accessible, the system must validate the direction of effect for significant taxa found in the primary analysis to assess reproducibility.

**Why this priority**: Validation on independent data is a critical step for establishing the robustness of findings, though it is conditional on data availability.

**Independent Test**: The validation module can be tested by running it on a secondary dataset and verifying that it outputs a comparison table showing effect direction matches for significant taxa.

**Acceptance Scenarios**:

1. **Given** a secondary dataset is accessible, **When** the validation script runs, **Then** the system calculates correlations for the top significant taxa from the primary analysis and reports the direction of effect.
2. **Given** a secondary dataset is not accessible, **When** the validation script runs, **Then** the system logs a skip message and proceeds without validation.

---

### Edge Cases

- What happens when the public dataset API is temporarily unavailable or rate-limited? The system must implement a retry mechanism (a bounded number of attempts with exponential backoff) before failing gracefully.
- How does the system handle samples with zero sequencing depth after rarefaction? These samples must be excluded from analysis, and the exclusion count must be logged.
- What if the mental health metadata contains non-numeric or out-of-range values (e.g., PHQ-9 score > 27)? These samples must be flagged and excluded, with a warning logged.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download the American Gut Project (AGP) 16S rRNA sequencing data (Study ID: 10317) and associated metadata via the Qiita API or public portal. (See US-1)
- **FR-002**: System MUST preprocess the OTU/ASV table by rarefying to equal sequencing depth and filtering taxa with < 0.1% prevalence. If rarefaction results in >20% sample loss, the system MUST apply variance-stabilizing transformation (VST) instead. (See US-1)
- **FR-003**: System MUST calculate alpha diversity (Shannon, Simpson) and beta diversity (Bray-Curtis, UniFrac) metrics for all valid samples. (See US-2)
- **FR-004**: System MUST perform partial Spearman correlation analysis between diversity metrics/taxa abundance and mental health scores (PHQ-9, GAD-7), adjusting for age and BMI as covariates IF covariate data is present. (See US-2)
- **FR-005**: System MUST apply Benjamini-Hochberg correction for multiple hypothesis testing across all taxa and report adjusted p-values (q-values). (See US-2)
- **FR-006**: System MUST generate a PCoA plot colored by mental health status and a heatmap of top-associated taxa. (See US-3)
- **FR-007**: System MUST output a summary report listing all significant associations (q < 0.05) with effect direction and magnitude. (See US-3)
- **FR-008**: System MUST validate effect direction of significant taxa on an independent cohort IF accessible. (See US-4)

### Key Entities

- **MicrobiomeSample**: Represents a single subject's microbiome profile, containing OTU/ASV counts, alpha diversity metrics, and beta diversity coordinates.
- **MentalHealthRecord**: Represents a subject's mental health assessment, containing PHQ-9 score, GAD-7 score, age, BMI, and diet information (categorical, one-hot encoded).
- **AssociationResult**: Represents a statistical finding, containing the tested variable (taxon/diversity), correlation coefficient, p-value, adjusted p-value, and effect direction.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The number of valid samples retained after preprocessing is measured against the initial download count to ensure ≥ 80% data retention (if data quality permits). (See US-1)
- **SC-002**: The number of taxa with statistically significant association (q < 0.05) is measured against a pass threshold of 'at least one taxon' OR 'p-value distribution deviates from uniform (Kolmogorov-Smirnov p < 0.05)'. (See US-2)
- **SC-003**: The consistency of effect direction for significant taxa across independent cohorts (if accessible) is measured against a threshold of 'direction matches in ≥ 80% of significant taxa'. (See US-4)
- **SC-004**: The computational runtime of the full analysis pipeline is measured against a specific threshold of ≤ 4 hours. (See US-1)
- **SC-005**: The covariate adjustment logic is verified by comparing adjusted vs. unadjusted p-values for a subset of taxa; the system MUST report that at least one taxon shows a p-value change > 0.01 when adjustment is applied. (See US-2)

## Assumptions

- The American Gut Project (AGP) public dataset (Study ID: 10317) contains both 16S rRNA sequencing data and valid mental health questionnaire responses (PHQ-9, GAD-7) for a sufficient number of overlapping samples.
- The public API or download method for AGP data does not require authentication or paid access.
- The analysis will be performed on a CPU-only environment (GitHub Actions free tier) with ≤ 7 GB RAM, requiring data sampling if the full dataset exceeds memory limits.
- The mental health scores in the metadata are self-reported and valid for correlation analysis, despite potential confounding factors not captured in the dataset.
- The Benjamini-Hochberg correction is appropriate for controlling the false discovery rate across the tested taxa, given the exploratory nature of the study.
- No GPU acceleration is required for the statistical analyses (correlation, PERMANOVA, diversity calculations) as they are computationally lightweight.
- The dataset contains necessary covariates (age, BMI, diet); if missing, the analysis will proceed without adjustment or with available proxies.
- The analysis will not claim causal relationships, as the study design is observational; findings will be framed as associational.
- Independent cohorts (UK Biobank, MetaHIT) may or may not be accessible; validation is conditional.