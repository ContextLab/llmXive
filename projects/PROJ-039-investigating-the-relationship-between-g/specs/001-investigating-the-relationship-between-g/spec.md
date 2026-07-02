# Feature Specification: Investigating the Relationship Between Gut Microbiome Composition and Resting-State EEG Alpha Power (Ecological Correlation)

**Feature Branch**: `001-gut-microbiome-eeg-alpha`  
**Created**: 2024-01-15  
**Status**: Draft  
**Input**: User description: "Investigating the Relationship Between Gut Microbiome Composition and Resting-State EEG Alpha Power"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Acquisition and Ecological Aggregation Pipeline (Priority: P1)

The research pipeline must acquire 16S rRNA sequencing data from the American Gut Project and resting-state EEG recordings from OpenNeuro dataset ds000248, preprocess both, and aggregate them into demographic strata for ecological correlation analysis.

**Why this priority**: Without validated input data and correct ecological aggregation, no statistical analysis can proceed. This is the foundational dependency for all subsequent research steps.

**Independent Test**: Can be fully tested by verifying that (1) microbiome data loads with ≥100 rows in the output feature matrix CSV, and (2) EEG data loads with ≥50 subjects, and (3) the pipeline successfully identifies and reports the count of valid demographic strata (groups with ≥5 subjects in both cohorts).

**Acceptance Scenarios**:

1. **Given** the American Gut Project data source is accessible, **When** the pipeline downloads and processes 16S rRNA data with QIIME2, **Then** the output contains ≥100 rows in the output feature matrix CSV with genus-level taxonomic abundances and demographic metadata (age, sex, BMI, diet category).
2. **Given** the OpenNeuro ds000248 repository is accessible, **When** the pipeline downloads and preprocesses EEG data with MNE-Python, **Then** the output contains ≥50 subjects with bandpass-filtered (0.5–45 Hz) resting-state epochs after ICA artifact removal.
3. **Given** both datasets are preprocessed, **When** the pipeline groups subjects by demographic bins (age, sex, BMI, diet) and filters for groups with ≥5 subjects in both cohorts, **Then** it reports the count of *valid strata* (groups with ≥5 subjects in both cohorts) and exits with code 0 if ≥5 valid strata exist, or code 1 if fewer than 5 valid strata exist.

---

### User Story 2 - Ecological Statistical Analysis and Association Testing (Priority: P1)

The pipeline must compute mean alpha power (8–12 Hz) and mean taxa abundances per valid demographic stratum, apply CLR transformation to the stratum-level means, and test associations between taxa abundances and alpha power using Spearman correlation with appropriate corrections.

**Why this priority**: This is the core research question—establishing whether gut microbiome composition correlates with neural oscillatory activity at the population level. Without valid statistical associations on the aggregated data, the research question cannot be answered.

**Independent Test**: Can be fully tested by running the correlation analysis on a sample dataset and verifying that (1) CLR-transformed stratum-level abundances are computed correctly, (2) Spearman's rho is calculated for each taxon using stratum means, and (3) FDR correction is applied to p-values.

**Acceptance Scenarios**:

1. **Given** preprocessed EEG and microbiome data, **When** the pipeline computes mean alpha power using Welch's method per stratum, **Then** each valid stratum has a single alpha power estimate (averaged across subjects) with units in μV²/Hz.
2. **Given** CLR-transformed stratum-level taxa abundances, **When** the pipeline runs Spearman correlation against mean alpha power for the 20 taxa with the highest mean relative abundance across the whole dataset, **Then** it outputs correlation coefficients (rho), uncorrected p-values, and Benjamini-Hochberg FDR-corrected q-values (q<0.1 threshold).
3. **Given** the correlation results, **When** the pipeline runs permutation testing (1000 iterations) on the stratum-level data, **Then** it generates a null distribution of correlation coefficients, determines if the observed correlation exceeds the 95th percentile, and outputs a boolean flag `perm_test_passed` in the results JSON.

---

### User Story 3 - Results Visualization and Reporting (Priority: P2)

The pipeline must generate publication-ready visualizations showing correlation relationships, effect sizes, and alpha power distributions stratified by abundance groups.

**Why this priority**: Visual outputs enable interpretation and dissemination of findings but are not required for the core statistical validation. This supports research communication.

**Independent Test**: Can be fully tested by verifying that (1) correlation heatmap is generated, (2) scatter plots with regression lines exist for significant taxa, and (3) stratified alpha power distributions are produced.

**Acceptance Scenarios**:

1. **Given** correlation results with p<0.05 (FDR-corrected), **When** the pipeline generates visualization outputs, **Then** it produces a correlation heatmap showing the top 20 taxa versus alpha power with significance indicators.
2. **Given** significant taxa (q<0.1), **When** the pipeline creates scatter plots, **Then** each plot shows mean alpha power versus CLR-transformed mean abundance with regression line, R² value, and 95% confidence interval.
3. **Given** the full dataset, **When** the pipeline stratifies subjects by high/low abundance groups (median split), **Then** it generates alpha power distribution plots (histograms or boxplots) for each group with sample sizes labeled.

---

### Edge Cases

- What happens when the demographic matching yields <5 valid strata between American Gut Project and OpenNeuro ds000248? → The pipeline MUST log the error message "ERROR: Insufficient valid strata (<5) for ecological analysis" and exit with code 1.
- How does the system handle missing demographic covariates (e.g., BMI not reported for a subject)? → The pipeline MUST either exclude the subject from covariate-adjusted models or impute using median value with a documented flag.
- What happens when the permutation test shows observed correlations within the null distribution? → The pipeline MUST report null results explicitly (perm_test_passed = false) and flag for potential type-II error due to sample size.
- How does the system handle taxa with zero abundance in many samples (sparse compositional data)? → The pipeline MUST apply a pseudocount (e.g., 0.5) before CLR transformation to avoid log(0) errors.
- What happens when alpha power computation yields NaN/Inf values for certain epochs? → The pipeline MUST filter invalid epochs and proceed only if ≥80% of epochs remain valid per subject.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download and process 16S rRNA sequencing data from the American Gut Project to genus-level taxonomic abundances with ≥100 rows in the output feature matrix CSV (See US-1)
- **FR-002**: System MUST download and preprocess resting-state EEG data from OpenNeuro ds000248 with bandpass filtering (0.5–45 Hz) and ICA artifact removal (See US-1)
- **FR-003**: System MUST aggregate group-level statistics (mean alpha power, mean taxa abundance) across matched demographic strata and report the count of valid strata (groups with ≥5 subjects in both cohorts) (See US-1)
- **FR-004**: System MUST apply centered log-ratio (CLR) transformation to stratum-level microbiome means with pseudocount=0.5 to handle zeros (See US-2)
- **FR-005**: System MUST compute mean alpha power (8–12 Hz) per stratum using Welch's method (See US-2)
- **FR-006**: System MUST perform Spearman correlation between the 20 taxa with highest mean relative abundance and mean alpha power per stratum with Benjamini-Hochberg FDR correction (q<0.1) (See US-2)
- **FR-007**: System MUST run permutation testing (1000 iterations) to validate statistical significance against null distribution and output a boolean `perm_test_passed` (See US-2)
- **FR-008**: System MUST generate correlation heatmap, scatter plots with regression lines, and stratified alpha power distributions (See US-3)
- **FR-009**: System MUST include collinearity diagnostics when multiple taxa predictors are tested simultaneously (See US-2)
- **FR-010**: System MUST include the exact string "Note: This analysis is associational only; no causal inference is made." in all generated reports and outputs (See US-2)

### Key Entities

- **Stratum**: A demographic group (defined by age, sex, BMI, diet) containing ≥5 subjects from both the American Gut Project and OpenNeuro ds000248 cohorts; key attributes include stratum ID, mean alpha power, mean taxa abundances, sample size.
- **Subject**: Individual participant with linked microbiome or EEG measurements; key attributes include subject ID, age, sex, BMI, diet category.
- **Taxon**: Bacterial genus-level classification; key attributes include genus name, CLR-transformed stratum-level abundance, correlation coefficient with alpha power.
- **Alpha Power**: Neural oscillatory measure; key attributes include stratum ID, mean power value (μV²/Hz), frequency band (8–12 Hz).
- **Correlation Result**: Statistical association output; key attributes include taxon name, Spearman's rho, uncorrected p-value, FDR-corrected q-value, significance flag.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Number of valid strata is measured against the minimum threshold of 5 strata required for adequate statistical power (See US-1)
- **SC-002**: Number of significant taxa associations is measured against the requirement that the system correctly counts and reports all taxa with q<0.1 (See US-2)
- **SC-003**: Permutation test validation rate is measured against the 95th percentile null distribution threshold to confirm observed correlations exceed random chance (See US-2)
- **SC-004**: FDR correction coverage is measured against the requirement that all 20 taxa tests receive Benjamini-Hochberg adjustment (See US-2)
- **SC-005**: Visualization completeness is measured against the requirement for correlation heatmap, ≥1 scatter plot, and ≥1 stratified distribution plot (See US-3)

## Assumptions

- The American Gut Project (AGP) and OpenNeuro ds000248 are independent datasets with NO subject overlap; AGP provides 16S rRNA sequencing data with demographic metadata but no EEG, while ds000248 provides EEG data with limited or no linked microbiome data. The pipeline MUST treat these as independent cohorts and perform analysis by aggregating group-level statistics (e.g., correlation of mean alpha power vs. mean taxa abundance across matched demographic strata) or by using the datasets to validate preprocessing pipelines separately before merging at the feature level, not the subject level.
- The analysis is explicitly an ecological correlation of group-level statistics, not an individual-level association study. This approach tests for population-level confounding patterns rather than individual gut-brain axis links.
- The American Gut Project contains individual-level microbiome data (not aggregated) with sufficient sample size to enable aggregation into demographic strata.
- Resting-state EEG recordings in OpenNeuro ds000248 include ≥2 minutes of artifact-free resting-state data per subject suitable for alpha power computation.
- The total combined dataset size (microbiome + EEG) will fit within 7 GB RAM and 14 GB disk on GitHub Actions free-tier runner.
- The analysis will complete within 6 hours on a CPU-only runner (2 cores, ~7 GB RAM) without requiring GPU acceleration.
- Validated instruments are used for demographic and dietary variables (American Gut Project uses standardized questionnaires).
- The 20 taxa with the highest mean relative abundance across the whole dataset represent sufficient coverage of the microbiome for exploratory association testing.
- A pseudocount of 0.5 is appropriate for CLR transformation of sparse microbiome data (community-standard practice).
- The Benjamini-Hochberg FDR correction with q<0.1 threshold is justified as a balance between type-I and type-II error control for exploratory research.
- Permutation testing with a sufficient number of iterations provides adequate null distribution resolution for p-value estimation.
- All statistical findings must be framed as associational (not causal) since this is an observational study without random assignment.