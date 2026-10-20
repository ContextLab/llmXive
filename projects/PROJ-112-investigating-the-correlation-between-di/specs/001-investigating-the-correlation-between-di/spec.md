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

### US-2 - Compositional Transformation and Correlation Analysis (Priority: P2)

**Description**: The system MUST apply centered log‑ratio (CLR) transformation to taxon abundance data for correlation analysis, and MUST compute associations between fiber intake and each taxon’s CLR‑transformed abundance using a linear model (MaAsLin2 or equivalent) that adjusts for covariates (age, BMI, antibiotic use). The analysis will include Benjamini‑Hochberg FDR correction across all tests.

**Why this priority**: This step directly addresses the primary research question (association between fiber and microbiome composition) while handling the compositional nature of microbiome data correctly and controlling for confounding variables.

**Independent Test**: Can be fully tested by running the correlation analysis on a small synthetic dataset with known associations and covariates, verifying that the output matches expected coefficients and corrected p‑values.

**Acceptance Scenarios**:

1. **Given** a CLR‑transformed taxon abundance matrix, fiber intake vector, and covariate table, **When** the association analysis runs, **Then** a table of effect sizes (beta coefficients), raw p‑values, and adjusted q‑values is produced for all taxa.
2. **Given** the raw p‑values from the association test, **When** FDR correction is applied, **Then** the adjusted q‑values are correctly calculated using the Benjamini‑Hochberg method.
3. **Given** a taxon with a known true effect size in the synthetic test data, **When** the analysis runs, **Then** the reported effect size is within ±0.05 of the true value.

---

### US-3 - Differential Abundance and Cross‑Cohort Validation (Priority: P3)

**Description**: The system MUST perform differential abundance testing between high‑fiber (samples with fiber intake ≥ 75th percentile, i.e., top [deferred] of the distribution) and low‑fiber (samples with fiber intake ≤ 25th percentile, i.e., bottom [deferred] of the distribution) groups using both ANCOM‑II and DESeq2, then evaluate replication status of significant findings in the second dataset for cross‑cohort validation. The system MUST also report absolute median fiber intake (g/day) for these groups in each cohort to enable cross‑cohort comparability.

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
- What if one dataset has significantly fewer samples than the other? → The system will report the sample‑size disparity in the final summary but will not enforce a mandatory power analysis.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download and parse 16S rRNA amplicon tables and metadata from the American Gut Project and UK Biobank (See US-1).
- **FR-002**: System MUST filter samples with <5,000 reads and exclude implausible fiber intake values (>200 g/day) (See US-1).
- **FR-003**: System MUST apply centered log‑ratio (CLR) transformation to taxon abundance data for correlation analysis (See US-2).
- **FR-004**: System MUST compute associations between fiber intake and taxon abundances using MaAsLin2 (or equivalent linear model) adjusting for covariates; MaAsLin2 will handle compositional aspects internally (no prior CLR) (See US-2).
- **FR-005**: System MUST apply Benjamini‑Hochberg FDR correction across all association tests (See US-2).
- **FR-006**: System MUST perform differential abundance testing using both ANCOM‑II and DESeq2 methods, outputting results as TSV files with columns: taxon, method, q‑value, effect_size, direction (See US-3).
- **FR-007**: System MUST evaluate replication status of significant findings in a second independent cohort and flag non‑replicable taxa (See US-3).
- **FR-008**: System MUST output summary tables of significant taxa with effect sizes, confidence intervals, and q‑values (See US-2, US-3).
- **FR-009**: System MUST report absolute median fiber intake (g/day) for high‑fiber and low‑fiber groups in each cohort (See US-3).

### Key Entities

- **Sample**: Represents an individual participant with attributes including fiber intake (g/day), taxon abundances, and covariates (age, sex, BMI, antibiotic use).
- **Taxon**: Represents a bacterial taxon (e.g., genus, species) with attributes including relative abundance and CLR‑transformed value.
- **Covariate**: Represents confounding variables (age, sex, BMI, antibiotic use, sequencing batch) used in multivariable models.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: System reports beta coefficients (or equivalent effect sizes) and raw p‑values for each taxon association (See US-2).
- **SC-002**: Adjusted q‑values from Benjamini‑Hochberg correction are reported; taxa with q < 0.05 are considered significant (See US-3).
- **SC-003**: System calculates and reports cross‑cohort replication rate as a percentage with two decimal places (See US-3).
- **SC-006**: Unified dataset produced after ingestion contains ≥ 1,000 samples total across both cohorts and passes all quality filters (See US-1).

## Assumptions

- The American Gut Project and UK Biobank datasets contain self‑reported dietary fiber intake (grams/day) and 16S rRNA amplicon sequencing data with sufficient depth (≥5,000 reads) for analysis.
- Self‑reported dietary fiber intake is subject to measurement error, but the magnitude of bias is comparable across cohorts and does not invalidate the association analysis.
- The compositional nature of microbiome data requires CLR transformation for correlation analysis; a small pseudocount is acceptable for zero‑inflated taxa.
- The expected effect size (beta coefficient) is detectable with the available sample sizes in both cohorts after FDR correction.
- The analysis can be completed within a reasonable compute budget on a CPU‑only GitHub Actions runner with ≤7 GB RAM and no GPU acceleration.
- ANCOM‑II and DESeq2 are available as CPU‑tractable implementations (e.g., via R packages or Python wrappers) without requiring large memory or GPU resources.
- The Benjamini‑Hochberg FDR correction method is appropriate for controlling false discoveries across the number of taxa tested (typically hundreds to thousands).
- Covariates (age, sex, BMI, antibiotic use) are available in both datasets and can be harmonized for multivariable adjustment.
- MaAsLin2 (or equivalent) is available and capable of handling the dataset size and covariate structure.
- **Quartile definition justification**: Using the top and bottom [deferred] of fiber intake aligns with the original research question to contrast extreme dietary exposures while retaining sufficient sample size for statistical power.