# Feature Specification: Investigating the Correlation Between Dietary Fiber Intake and Gut Microbiome Composition

**Feature Branch**: `001-gene-regulation`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "Investigating the Correlation Between Dietary Fiber Intake and Gut Microbiome Composition Using Publicly Available Data"

## User Scenarios & Testing

### US-1 - Data Ingestion and Harmonization (Priority: P1)

**Description**: The system MUST download 16S rRNA amplicon tables and metadata from the American Gut Project and UK Biobank, extract self‑reported dietary fiber intake, and harmonize units while filtering out implausible values (e.g., >200 g/day) and low‑sequencing‑depth samples (<5,000 reads).

**Why this priority**: Without clean, harmonized data, no statistical analysis can proceed. This is the foundational step that enables all downstream correlation and differential abundance testing.

**Independent Test**: Can be fully tested by verifying that the pipeline successfully downloads both datasets, filters samples correctly, and outputs a unified CSV/TSV file with consistent column names and units.

**Acceptance Scenarios**:

1. **Given** raw American Gut Project and UK Biobank data files exist, **When** the ingestion script runs, **Then** a unified dataset is produced containing only samples with ≥5,000 reads and fiber intake values between 0–200 g/day.
2. **Given** a sample with missing fiber intake data, **When** the preprocessing step runs, **Then** that sample is excluded from the final analysis dataset.
3. **Given** conflicting unit formats (e.g., mg/day vs. g/day) across datasets, **When** the harmonization step runs, **Then** all fiber values are converted to a consistent unit (g/day) before output.

---

### US-2 - Compositional Transformation, Correlation, and Association Analysis (Priority: P2)

**Description**: The system MUST (1) apply a centered log‑ratio (CLR) transformation to taxon abundance data, (2) compute Spearman rank‑correlation between fiber intake and each CLR‑transformed taxon, (3) perform linear‑model association testing using MaAsLin2 (or an equivalent) on the CLR‑transformed data while adjusting for covariates (age, BMI, antibiotic use), and (4) apply Benjamini‑Hochberg FDR correction across all tests. Additionally, the system MUST run a measurement‑error simulation to quantify bias introduced by self‑reported fiber intake.

**Why this priority**: This step directly addresses the primary research question (association between fiber and microbiome composition) while handling compositional data correctly, providing both non‑parametric (Spearman) and multivariate (MaAsLin2) perspectives, and assessing robustness to measurement error.

**Independent Test**: Can be fully tested by running the pipeline on a small synthetic dataset with known associations, covariates, and introduced measurement error, verifying that (a) CLR transformation succeeds, (b) Spearman rho values match expectations, (c) MaAsLin2 coefficients are within ±0.05 of true values, (d) FDR‑adjusted q‑values are correct, and (e) the bias simulation reports the expected attenuation.

**Acceptance Scenarios**:

1. **Given** a CLR‑transformed taxon abundance matrix, fiber intake vector, and covariate table, **When** the Spearman correlation step runs, **Then** a table of rho, raw p‑values, and BH‑adjusted q‑values is produced for all taxa.
2. **Given** the same inputs, **When** the MaAsLin2 association step runs, **Then** a table of beta coefficients, raw p‑values, and BH‑adjusted q‑values is produced for all taxa.
3. **Given** the raw p‑values from either analysis, **When** FDR correction is applied, **Then** the adjusted q‑values are correctly calculated using the Benjamini‑Hochberg method.
4. **Given** a taxon with a known true effect size in the synthetic test data, **When** the MaAsLin2 analysis runs, **Then** the reported effect size is within ±0.05 of the true value.
5. **Given** synthetic data with injected measurement error in fiber intake, **When** the measurement‑error simulation runs, **Then** the bias (difference between estimated and true effect) is reported and falls within the expected range (≤ 10 % relative error).

---

### US-3 - Differential Abundance and Cross‑Cohort Validation (Priority: P3)

**Description**: The system MUST perform differential abundance testing between high‑fiber (samples with fiber intake ≥ 75th percentile) and low‑fiber (samples with fiber intake ≤ 25th percentile) groups using both ANCOM‑II and DESeq2, then evaluate replication status of significant findings in the second dataset for cross‑cohort validation. The system MUST also report absolute median fiber intake (g/day) for these groups in each cohort to enable cross‑cohort comparability.

**Why this priority**: This step provides robustness by using multiple methods and validates findings across independent cohorts, increasing confidence in the results.

**Independent Test**: Can be fully tested by running the differential abundance pipeline on both datasets independently and verifying that the output format is correct and replication status is accurately flagged.

**Acceptance Scenarios**:

1. **Given** the high‑fiber and low‑fiber group assignments (top/bottom quartiles), **When** ANCOM‑II and DESeq2 run, **Then** two separate TSV files are produced containing taxa, method, q‑value, effect_size, and direction, filtered for q < 0.05.
2. **Given** significant taxa from the American Gut Project analysis (sorted by ascending adjusted q‑value), **When** the same analysis is run on UK Biobank data, **Then** at least 50 % of the top taxa (by q‑value) show consistent directionality (same sign of effect size) in both cohorts.
3. **Given** a taxon identified as significant in only one cohort, **When** the cross‑cohort validation step runs, **Then** it is flagged as ‘non‑replicable’ in the final output table.
4. **Given** the high/low fiber groups in each cohort, **When** the summary step runs, **Then** the absolute median fiber intake (g/day) for each group is reported in the final summary table.

---

### Edge Cases

- What happens when a dataset contains zero‑inflated taxa that cannot be log‑transformed? → The system MUST apply a small pseudocount (default = 1e‑6) before CLR transformation and document this in the output.
- How does the system handle missing covariate data (e.g., BMI, antibiotic use)? → Samples with >20 % missing covariate data MUST be excluded; remaining missing values are imputed using the median (numeric) or mode (categorical) of the respective covariate.
- What if one dataset has significantly fewer samples than the other? → The system will report the sample‑size disparity in the final summary. An a priori power analysis (FR-012) is mandatory; if the smaller cohort fails to meet the required sample size, the pipeline will issue a warning and suggest additional data collection.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download and parse 16S rRNA amplicon tables and metadata from the American Gut Project and UK Biobank (See US-1).
- **FR-002**: System MUST filter samples with <5,000 reads and exclude implausible fiber intake values (>200 g/day) (See US-1).
- **FR-003**: System MUST apply centered log‑ratio (CLR) transformation to taxon abundance data for all downstream analyses (See US-2).
- **FR-004**: System MUST compute associations between fiber intake and CLR‑transformed taxon abundances using MaAsLin2 (or equivalent linear model) adjusting for covariates; MaAsLin2 operates on the CLR‑transformed data (See US-2).
- **FR-005**: System MUST apply Benjamini‑Hochberg FDR correction across all association tests (See US-2).
- **FR-006**: System MUST perform Spearman rank‑correlation between fiber intake and each CLR‑transformed taxon, reporting rho, raw p‑values, and BH‑adjusted q‑values (See US-2).
- **FR-007**: System MUST perform differential abundance testing using both ANCOM‑II and DESeq2 methods, outputting results as TSV files with columns: taxon, method, q‑value, effect_size, direction (See US-3).
- **FR-008**: System MUST evaluate replication status of significant findings in a second independent cohort and flag non‑replicable taxa (See US-3).
- **FR-009**: System MUST output summary tables of significant taxa with effect sizes, confidence intervals, and q‑values (See US-2, US-3).
- **FR-010**: System MUST conduct a measurement‑error simulation to assess bias introduced by self‑reported fiber intake, reporting bias magnitude and direction (See US-2).
- **FR-011**: System MUST report absolute median fiber intake (g/day) for high‑fiber and low‑fiber groups in each cohort (See US-3).
- **FR-012**: System MUST perform an a priori power analysis to detect a minimum standardized effect size of β = 0.1 with 80 % power at α = 0.05 for the primary association tests, and must document the required total sample size per cohort (See US-2, Edge Cases).
- **FR-013**: System MUST issue a warning and halt downstream analyses if either cohort fails to meet the sample‑size requirement identified in FR-012.

### Key Entities

- **Sample**: Represents an individual participant with attributes including fiber intake (g/day), taxon abundances, and covariates (age, sex, BMI, antibiotic use).
- **Taxon**: Represents a bacterial taxon (e.g., genus, species) with attributes including relative abundance and CLR‑transformed value.
- **Covariate**: Represents confounding variables (age, sex, BMI, antibiotic use, sequencing batch) used in multivariable models.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: System reports beta coefficients (or equivalent effect sizes) and raw p‑values for each taxon association from MaAsLin2 (See US-2).
- **SC-002**: System reports Spearman rho, raw p‑values, and BH‑adjusted q‑values for each taxon (See US-2).
- **SC-003**: Adjusted q‑values from Benjamini‑Hochberg correction are reported; taxa with q < 0.05 are considered significant (See US-2, US-3).
- **SC-004**: System reports the a priori power analysis results, including required sample size per cohort and achieved power given the actual sample sizes (See FR-012, Edge Cases).
- **SC-005**: System reports measurement‑error simulation bias (absolute and relative) for the primary association estimates (See FR-010).
- **SC-006**: System calculates and reports cross‑cohort replication rate as a percentage with two decimal places (See US-3).
- **SC-007**: Unified dataset produced after ingestion contains ≥ 1,000 samples total across both cohorts and passes all quality filters (See US-1).

## Assumptions

- The American Gut Project and UK Biobank datasets contain self‑reported dietary fiber intake (grams/day) and 16S rRNA amplicon sequencing data with sufficient depth (≥5,000 reads) for analysis.
- Self‑reported dietary fiber intake is subject to measurement error, but the magnitude of bias is comparable across cohorts and does not invalidate the association analysis.
- The compositional nature of microbiome data requires CLR transformation for correlation and regression analyses; a small pseudocount (1e‑6) is acceptable for zero‑inflated taxa.
- The expected effect size (beta ≈ 0.1) is detectable with the sample sizes determined by the a priori power analysis (FR-012).
- The analysis can be completed within a reasonable compute budget on a CPU‑only GitHub Actions runner with ≤7 GB RAM and no GPU acceleration.
- ANCOM‑II and DESeq2 are available as CPU‑tractable implementations (e.g., via R packages or Python wrappers) without requiring large memory or GPU resources.
- The Benjamini‑Hochberg FDR correction method is appropriate for controlling false discoveries across the number of taxa tested (typically hundreds to thousands).
- Covariates (age, sex, BMI, antibiotic use) are available in both datasets and can be harmonized for multivariable adjustment.
- MaAsLin2 (or equivalent) is available and capable of handling the dataset size and covariate structure after CLR transformation.
- **Quartile definition justification**: Using the top and bottom [deferred] of fiber intake aligns with the original research question to contrast extreme dietary exposures while retaining sufficient sample size for statistical power, as confirmed by the a priori power analysis (FR-012).