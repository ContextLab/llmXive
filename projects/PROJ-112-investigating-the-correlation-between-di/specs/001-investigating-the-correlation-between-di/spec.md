# Feature Specification: Investigating the Correlation Between Dietary Fiber Intake and Gut Microbiome Composition

**Feature Branch**: `001-gene-regulation`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "Investigating the Correlation Between Dietary Fiber Intake and Gut Microbiome Composition Using Publicly Available Data"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Harmonization (Priority: P1)

**Description**: The system MUST download 16S rRNA amplicon tables and metadata from the American Gut Project and UK Biobank, extract self-reported dietary fiber intake, and harmonize units while filtering out implausible values (e.g., >200 g/day) and low-sequencing-depth samples (<5,000 reads).

**Why this priority**: Without clean, harmonized data, no statistical analysis can proceed. This is the foundational step that enables all downstream correlation and differential abundance testing.

**Independent Test**: Can be fully tested by verifying that the pipeline successfully downloads both datasets, filters samples correctly, and outputs a unified CSV/TSV file with consistent column names and units.

**Acceptance Scenarios**:

1. **Given** raw American Gut Project and UK Biobank data files exist, **When** the ingestion script runs, **Then** a unified dataset is produced containing only samples with ≥5,000 reads and fiber intake values between 0–200 g/day.
2. **Given** a sample with missing fiber intake data, **When** the preprocessing step runs, **Then** that sample is excluded from the final analysis dataset.
3. **Given** conflicting unit formats (e.g., mg/day vs. g/day) across datasets, **When** the harmonization step runs, **Then** all fiber values are converted to a consistent unit (g/day) before output.

---

### User Story 2 - Compositional Transformation and Correlation Analysis (Priority: P2)

**Description**: The system MUST apply centered log-ratio (CLR) transformation to taxon abundance data and compute associations between fiber intake and each taxon’s CLR-transformed abundance using MaAsLin2 (or equivalent linear model) to adjust for covariates (age, BMI, antibiotic use), with Benjamini-Hochberg FDR correction applied across all tests.

**Why this priority**: This step directly addresses the primary research question (association between fiber and microbiome composition) and must handle the compositional nature of microbiome data correctly while controlling for confounding variables.

**Independent Test**: Can be fully tested by running the correlation analysis on a small synthetic dataset with known associations and covariates, verifying that the output matches expected coefficients and corrected p-values.

**Acceptance Scenarios**:

1. **Given** a CLR-transformed taxon abundance matrix, fiber intake vector, and covariate table, **When** the association analysis runs, **Then** a table of effect sizes, raw p-values, and adjusted q-values is produced for all taxa.
2. **Given** the raw p-values from the association test, **When** FDR correction is applied, **Then** the adjusted q-values are correctly calculated using the Benjamini-Hochberg method.
3. **Given** a taxon with a known true effect size in the synthetic test data, **When** the analysis runs, **Then** the reported effect size is within ±0.05 of the true value.

---

### User Story 3 - Differential Abundance and Cross-Cohort Validation (Priority: P3)

**Description**: The system MUST perform differential abundance testing between high-fiber (top [deferred], 75th percentile) and low-fiber (bottom [deferred], 25th percentile) groups using both ANCOM-II and DESeq2, then evaluate replication status of significant findings in the second dataset for cross-cohort validation. The system MUST also report absolute median fiber intake for these groups in each cohort to enable cross-cohort comparability.

**Why this priority**: This step provides robustness by using multiple methods and validates findings across independent cohorts, increasing confidence in the results.

**Independent Test**: Can be fully tested by running the differential abundance pipeline on both datasets independently and verifying that the output format is correct and replication status is accurately flagged.

**Acceptance Scenarios**:

1. **Given** the high-fiber and low-fiber group assignments (top/bottom quartiles), **When** ANCOM-II and DESeq2 run, **Then** two separate TSV files are produced containing taxa, method, q-value, effect_size, and direction, filtered for q < 0.05.
2. **Given** significant taxa from the American Gut Project analysis (sorted by ascending adjusted q-value), **When** the same analysis is run on UK Biobank data, **Then** at least 50% of the top 10 taxa (by q-value) show consistent directionality (same sign of effect size) in both cohorts.
3. **Given** a taxon identified as significant in only one cohort, **When** the cross-cohort validation step runs, **Then** it is flagged as 'non-replicable' in the final output table.
4. **Given** the high/low fiber groups in each cohort, **When** the summary step runs, **Then** the absolute median fiber intake (g/day) for each group is reported in the final summary table.

---

### Edge Cases

- What happens when a dataset contains zero-inflated taxa that cannot be log-transformed? → The system MUST apply a small pseudocount, defaulting to 1, before CLR transformation and document this in the output.
- How does the system handle missing covariate data (e.g., BMI, antibiotic use)? → Samples with >20% missing covariate data MUST be excluded; others are imputed using median/mode per covariate.
- What if one dataset has significantly fewer samples than the other? → The system MUST perform power analysis and report calculated power and margin of error. This is required to distinguish true null effects from underpowered results in smaller cohorts.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download and parse 16S rRNA amplicon tables and metadata from American Gut Project and UK Biobank (See US-1).
- **FR-002**: System MUST filter samples with <5,000 reads and exclude implausible fiber intake values (>200 g/day) (See US-1).
- **FR-003**: System MUST apply centered log-ratio (CLR) transformation to taxon abundance data (See US-2).
- **FR-004**: System MUST compute associations between fiber intake and CLR-transformed taxon abundances using MaAsLin2 (or equivalent linear model) adjusting for covariates (See US-2).
- **FR-005**: System MUST apply Benjamini-Hochberg FDR correction across all association tests (See US-2).
- **FR-006**: System MUST perform differential abundance testing using both ANCOM-II and DESeq2 methods, outputting results as TSV files with columns: taxon, method, q-value, effect_size, direction (See US-3).
- **FR-007**: System MUST evaluate replication status of significant findings in a second independent cohort and flag non-replicable taxa (See US-3).
- **FR-008**: System MUST output summary tables of significant taxa with effect sizes, confidence intervals, and q-values (See US-2, US-3).
- **FR-009**: System MUST report absolute median fiber intake (g/day) for high-fiber and low-fiber groups in each cohort (See US-3).

### Key Entities

- **Sample**: Represents an individual participant with attributes including fiber intake (g/day), taxon abundances, and covariates (age, sex, BMI, antibiotic use).
- **Taxon**: Represents a bacterial taxon (e.g., genus, species) with attributes including relative abundance and CLR-transformed value.
- **Covariate**: Represents confounding variables (age, sex, BMI, antibiotic use, sequencing batch) used in multivariable models.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: System reports Spearman ρ (or equivalent effect size) with 3 decimal places and includes standard error (See US-2).
- **SC-002**: False discovery rate (q-value) is measured against the threshold of 0.05 for differential abundance testing (See US-3).
- **SC-003**: System calculates and reports cross-cohort replication rate with 2 decimal places (See US-3).
- **SC-004**: Computational feasibility is measured against the constraint of ≤6 hours runtime on a CPU-only GitHub Actions runner (See Assumptions).
- **SC-005**: System reports calculated statistical power and margin of error for the smaller cohort (See Edge Cases).

## Assumptions

- The American Gut Project and UK Biobank datasets contain self-reported dietary fiber intake (grams/day) and 16S rRNA amplicon sequencing data with sufficient depth (≥5,000 reads) for analysis.
- Self-reported dietary fiber intake is subject to measurement error, but the magnitude of bias is comparable across cohorts and does not invalidate the association analysis.
- The compositional nature of microbiome data requires CLR transformation, and a small pseudocount, defaulting to 1, is acceptable for zero-inflated taxa.
- The expected effect size (Spearman ρ ≈ small to moderate magnitude) is detectable with the available sample sizes in both cohorts after FDR correction.
- The analysis can be completed within 6 hours on a CPU-only GitHub Actions runner with ≤7 GB RAM and no GPU acceleration.
- ANCOM-II and DESeq2 are available as CPU-tractable implementations (e.g., via R packages or Python wrappers) without requiring large memory or GPU resources.
- The Benjamini-Hochberg FDR correction method is appropriate for controlling false discoveries across the number of taxa tested (typically hundreds to thousands).
- Covariates (age, sex, BMI, antibiotic use) are available in both datasets and can be harmonized for multivariable adjustment.
- MaAsLin2 (or equivalent) is available and capable of handling the dataset size and covariate structure.