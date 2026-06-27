# Feature Specification: Investigating the Relationship Between Gut Microbiome Composition and Resting-State EEG Alpha Power

**Feature Branch**: `001-gut-microbiome-eeg-alpha`  
**Created**: 2024-01-15  
**Status**: Draft  
**Input**: User description: "Investigating the Relationship Between Gut Microbiome Composition and Resting-State EEG Alpha Power"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1)

The research pipeline must acquire 16S rRNA sequencing data from the American Gut Project and resting-state EEG recordings from OpenNeuro dataset ds000248, then preprocess both modalities for downstream analysis.

**Why this priority**: Without validated input data in proper format, no statistical analysis can proceed. This is the foundational dependency for all subsequent research steps.

**Independent Test**: Can be fully tested by verifying that (1) microbiome data loads with ≥100 samples containing genus-level taxonomic abundances, and (2) EEG data loads with ≥50 subjects containing raw .edf/.bdf files with resting-state epochs.

**Acceptance Scenarios**:

1. **Given** the American Gut Project data source is accessible, **When** the pipeline downloads and processes 16S rRNA data with QIIME2, **Then** the output contains ≥100 samples with genus-level taxonomic abundances and demographic metadata (age, sex, BMI, diet category).
2. **Given** the OpenNeuro ds000248 repository is accessible, **When** the pipeline downloads and preprocesses EEG data with MNE-Python, **Then** the output contains ≥50 subjects with bandpass-filtered (0.5–45 Hz) resting-state epochs after ICA artifact removal.
3. **Given** both datasets are preprocessed, **When** the pipeline attempts to merge by demographic matching, **Then** it reports the count of overlapping subjects and flags any insufficient overlap (<20 subjects) for review.

---

### User Story 2 - Statistical Analysis and Association Testing (Priority: P1)

The pipeline must compute alpha power (8–12 Hz) from EEG epochs, apply CLR transformation to microbiome data, and test associations between taxa abundances and alpha power using Spearman correlation with appropriate corrections.

**Why this priority**: This is the core research question—establishing whether gut microbiome composition correlates with neural oscillatory activity. Without valid statistical associations, the research question cannot be answered.

**Independent Test**: Can be fully tested by running the correlation analysis on a sample dataset and verifying that (1) CLR-transformed abundances are computed correctly, (2) Spearman's rho is calculated for each taxon, and (3) FDR correction is applied to p-values.

**Acceptance Scenarios**:

1. **Given** preprocessed EEG and microbiome data, **When** the pipeline computes alpha power using Welch's method, **Then** each subject has a single alpha power estimate (averaged across 2-minute epochs) with units in μV²/Hz.
2. **Given** CLR-transformed taxa abundances, **When** the pipeline runs Spearman correlation against alpha power for the top 20 most abundant taxa, **Then** it outputs correlation coefficients (rho), uncorrected p-values, and Benjamini-Hochberg FDR-corrected q-values (q<0.1 threshold).
3. **Given** the correlation results, **When** the pipeline runs permutation testing (1000 iterations), **Then** it generates a null distribution of correlation coefficients and validates whether observed correlations exceed the 95th percentile of the null.

---

### User Story 3 - Results Visualization and Reporting (Priority: P2)

The pipeline must generate publication-ready visualizations showing correlation relationships, effect sizes, and alpha power distributions stratified by abundance groups.

**Why this priority**: Visual outputs enable interpretation and dissemination of findings but are not required for the core statistical validation. This supports research communication.

**Independent Test**: Can be fully tested by verifying that (1) correlation heatmap is generated, (2) scatter plots with regression lines exist for significant taxa, and (3) stratified alpha power distributions are produced.

**Acceptance Scenarios**:

1. **Given** correlation results with p<0.05 (FDR-corrected), **When** the pipeline generates visualization outputs, **Then** it produces a correlation heatmap showing the top 20 taxa versus alpha power with significance indicators.
2. **Given** significant taxa (q<0.1), **When** the pipeline creates scatter plots, **Then** each plot shows alpha power versus CLR-transformed abundance with regression line, R² value, and 95% confidence interval.
3. **Given** the full dataset, **When** the pipeline stratifies subjects by high/low abundance groups (median split), **Then** it generates alpha power distribution plots (histograms or boxplots) for each group with sample sizes labeled.

---

### Edge Cases

- What happens when the demographic matching yields <20 overlapping subjects between American Gut Project and OpenNeuro ds000248? → The pipeline MUST flag this as a power limitation and recommend alternative strategies (e.g., single-dataset analysis or additional data sources).
- How does the system handle missing demographic covariates (e.g., BMI not reported for a subject)? → The pipeline MUST either exclude the subject from covariate-adjusted models or impute using median value with a documented flag.
- What happens when the permutation test shows observed correlations within the null distribution? → The pipeline MUST report null results explicitly (no significant associations) and flag for potential type-II error due to sample size.
- How does the system handle taxa with zero abundance in many samples (sparse compositional data)? → The pipeline MUST apply a pseudocount (e.g., 0.5) before CLR transformation to avoid log(0) errors.
- What happens when alpha power computation yields NaN/Inf values for certain epochs? → The pipeline MUST filter invalid epochs and proceed only if ≥80% of epochs remain valid per subject.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download and process 16S rRNA sequencing data from the American Gut Project to genus-level taxonomic abundances with ≥100 samples (See US-1)
- **FR-002**: System MUST download and preprocess resting-state EEG data from OpenNeuro ds000248 with bandpass filtering (0.5–45 Hz) and ICA artifact removal (See US-1)
- **FR-003**: System MUST merge datasets by demographic matching (age, sex, BMI, diet) and report overlapping subject count (See US-1)
- **FR-004**: System MUST apply centered log-ratio (CLR) transformation to microbiome data with pseudocount=0.5 to handle zeros (See US-2)
- **FR-005**: System MUST compute alpha power (8–12 Hz) using Welch's method and average across 2-minute epochs per subject (See US-2)
- **FR-006**: System MUST perform Spearman correlation between top 20 taxa and alpha power with Benjamini-Hochberg FDR correction (q<0.1) (See US-2)
- **FR-007**: System MUST run permutation testing (1000 iterations) to validate statistical significance against null distribution (See US-2)
- **FR-008**: System MUST generate correlation heatmap, scatter plots with regression lines, and stratified alpha power distributions (See US-3)
- **FR-009**: System MUST frame all findings as associational (not causal) since this is an observational design with no random assignment (See US-2)
- **FR-010**: System MUST include collinearity diagnostics when multiple taxa predictors are tested simultaneously (See US-2)

### Key Entities

- **Subject**: Individual participant with linked microbiome and EEG measurements; key attributes include subject ID, age, sex, BMI, diet category
- **Taxon**: Bacterial genus-level classification; key attributes include genus name, CLR-transformed abundance, correlation coefficient with alpha power
- **Alpha Power**: Neural oscillatory measure; key attributes include subject ID, power value (μV²/Hz), frequency band (8–12 Hz), epoch count
- **Correlation Result**: Statistical association output; key attributes include taxon name, Spearman's rho, uncorrected p-value, FDR-corrected q-value, significance flag

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Overlapping subject count is measured against the minimum threshold of 20 subjects required for adequate statistical power (See US-1)
- **SC-002**: Number of significant taxa associations (q<0.1) is measured against the expected baseline of ≥1 taxon based on prior gut-brain association studies (See US-2)
- **SC-003**: Permutation test validation rate is measured against the 95th percentile null distribution threshold to confirm observed correlations exceed random chance (See US-2)
- **SC-004**: FDR correction coverage is measured against the requirement that all 20 taxa tests receive Benjamini-Hochberg adjustment (See US-2)
- **SC-005**: Visualization completeness is measured against the requirement for correlation heatmap, ≥1 scatter plot, and ≥1 stratified distribution plot (See US-3)

## Assumptions

- The American Gut Project and OpenNeuro ds000248 datasets contain overlapping demographic variables (age, sex, BMI, diet category) enabling subject matching; [NEEDS CLARIFICATION: does the American Gut Project dataset contain individual subject IDs that can be matched to OpenNeuro ds000248 subjects, or are these independent datasets with no subject overlap?]
- The American Gut Project contains individual-level microbiome data (not aggregated) with sufficient sample size to enable correlation analysis with EEG data
- Resting-state EEG recordings in OpenNeuro ds000248 include ≥2 minutes of artifact-free resting-state data per subject suitable for alpha power computation
- The total combined dataset size (microbiome + EEG) will fit within 7 GB RAM and 14 GB disk on GitHub Actions free-tier runner
- The analysis will complete within 6 hours on a CPU-only runner (2 cores, ~7 GB RAM) without requiring GPU acceleration
- Validated instruments are used for demographic and dietary variables (American Gut Project uses standardized questionnaires)
- The top 20 most abundant taxa represent sufficient coverage of the microbiome for exploratory association testing
- A pseudocount of 0.5 is appropriate for CLR transformation of sparse microbiome data (community-standard practice)
- The Benjamini-Hochberg FDR correction with q<0.1 threshold is justified as a balance between type-I and type-II error control for exploratory research
- Permutation testing with 1000 iterations provides adequate null distribution resolution for p-value estimation
- All statistical findings must be framed as associational (not causal) since this is an observational study without random assignment
