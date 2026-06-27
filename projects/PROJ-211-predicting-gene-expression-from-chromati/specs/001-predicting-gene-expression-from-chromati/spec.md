# Feature Specification: Predicting Gene Expression from Chromatin Accessibility in Human Cells

**Feature Branch**: `001-gene-regulation`  
**Created**: 2024-01-15  
**Status**: Draft  
**Input**: User description: "To what extent can bulk chromatin accessibility profiles (DNase-seq/ATAC-seq) predict steady-state gene expression levels (RNA-seq) across diverse human cell types using interpretable regression models?"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Download and preprocess paired multiomic data from ENCODE (Priority: P1)

The researcher MUST be able to download paired RNA-seq and DNase-seq/ATAC-seq count data for at least 5 human cell lines from the ENCODE portal, preprocess the accessibility signal within ±50kb windows of each gene's transcription start site (TSS), and filter genes with zero expression in all samples.

**Why this priority**: This is the foundational data pipeline. Without valid input data, no downstream modeling or analysis can occur. This is the minimum viable product for any multiomic regression study.

**Independent Test**: Can be fully tested by verifying that the pipeline produces a matrix of accessibility features (rows=genes, columns=peaks) and a matrix of expression values (rows=genes, columns=samples) with matching gene identifiers, and that both matrices fit within 7GB RAM.

**Acceptance Scenarios**:

1. **Given** the ENCODE portal is accessible, **When** the pipeline queries for 5 cell lines (GM12878, K562, and 3 others), **Then** the system downloads paired RNA-seq and DNase-seq/ATAC-seq count files for each cell line
2. **Given** raw accessibility signal files exist, **When** the pipeline aggregates signal within ±50kb windows of each TSS using bedtools, **Then** a feature matrix is produced with dimensions ≤10,000 peaks × 5 cell lines
3. **Given** expression matrices exist, **When** the pipeline filters genes with zero expression in all samples, **Then** at least 10,000 genes remain for downstream analysis

---

### User Story 2 - Train and validate interpretable regression models (Priority: P2)

The researcher MUST be able to train Elastic Net regression models for each cell line using accessibility features to predict log-transformed expression values, perform 5-fold cross-validation per cell line, and calculate Pearson correlation coefficients between predicted and actual expression.

**Why this priority**: This delivers the core scientific analysis. The model performance directly addresses the research question about predictability of expression from accessibility.

**Independent Test**: Can be fully tested by verifying that each cell line produces a trained model object, cross-validation scores, and a correlation matrix with p-values for all genes.

**Acceptance Scenarios**:

1. **Given** preprocessed feature and expression matrices exist, **When** the system trains Elastic Net regression with α=0.5 and λ selected via cross-validation, **Then** a model is produced for each cell line with R² ≥ 0.5 for housekeeping genes
2. **Given** trained models exist, **When** the system performs 5-fold cross-validation, **Then** each fold produces a correlation coefficient and the mean correlation is recorded
3. **Given** predictions are generated, **When** Pearson correlation is calculated between predicted and actual expression, **Then** p-values are computed and Bonferroni-corrected for multiple testing across genes

---

### User Story 3 - Analyze feature importance and report regulatory insights (Priority: P3)

The researcher MUST be able to extract feature importance scores from the trained models, identify accessible regions near the TSS as primary predictors, and generate a report comparing model performance across cell types and gene categories.

**Why this priority**: This provides the interpretability component that distinguishes this work from black-box deep learning approaches, supporting the research goal of understanding the regulatory code.

**Independent Test**: Can be fully tested by verifying that feature importance rankings are produced, TSS-proximal regions appear in the top 100 important features, and a summary report documents performance differences between housekeeping and cell-type-specific genes.

**Acceptance Scenarios**:

1. **Given** trained Elastic Net models exist, **When** the system extracts non-zero coefficient features, **Then** a ranked list of the top 100 most important peaks is produced for each cell line
2. **Given** feature importance rankings exist, **When** the system maps peaks to genomic coordinates, **Then** at least 50% of top 100 features fall within ±10kb of a TSS
3. **Given** correlation results exist, **When** the system compares housekeeping vs. cell-type-specific genes, **Then** a performance gap of ≥0.2 R² is documented if the data supports it

---

### Edge Cases

- What happens when ENCODE data for a requested cell line is unavailable or incomplete? The system MUST retry up to 3 failed attempts with 60-second intervals before marking the cell line as unavailable and proceeding with remaining data.
- How does the system handle genes with extremely low expression values (near zero on log scale)? The system MUST add a pseudocount of 1 before log transformation to avoid undefined values.
- What happens when peak accessibility data contains missing values? The system MUST impute missing values using median imputation across samples for each peak.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download paired RNA-seq and DNase-seq/ATAC-seq count data for ≥5 human cell lines from ENCODE portal (See US-1)
- **FR-002**: System MUST aggregate accessibility signal within ±50kb windows of each gene's TSS using bedtools (See US-1)
- **FR-003**: System MUST filter genes with zero expression in all samples, retaining ≥10,000 genes for analysis (See US-1)
- **FR-004**: System MUST train Elastic Net regression models (α=0.5) for each cell line using scikit-learn (See US-2)
- **FR-005**: System MUST perform 5-fold cross-validation per cell line and record mean correlation coefficient (See US-2)
- **FR-006**: System MUST apply Bonferroni correction for multiple testing across all genes when calculating p-values (See US-2)
- **FR-007**: System MUST extract non-zero coefficient features and rank by absolute coefficient magnitude (See US-3)
- **FR-008**: System MUST map peak coordinates to genomic location relative to nearest TSS (See US-3)

### Key Entities

- **Cell Line**: Biological sample identifier (e.g., GM12878, K562) with associated RNA-seq and DNase-seq/ATAC-seq data
- **Gene**: Genomic feature with expression value (log-transformed counts) and associated accessibility peaks
- **Peak**: Genomic region with accessibility measurement (DNase-seq/ATAC-seq signal) mapped relative to gene TSS
- **Model**: Elastic Net regression object trained on accessibility features to predict expression

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Prediction accuracy (R² between predicted and observed expression) is measured against the baseline expectation of R² > 0.5 for housekeeping genes (See US-2)
- **SC-002**: Model generalization is measured against 5-fold cross-validation scores to assess overfitting risk (See US-2)
- **SC-003**: Feature importance is measured against TSS proximity to verify regulatory plausibility (See US-3)
- **SC-004**: Statistical significance is measured against Bonferroni-corrected p-values to control family-wise error rate (See US-2)
- **SC-005**: Computational feasibility is measured against 2 CPU cores, 7GB RAM, and 6-hour runtime limits (See US-1)

## Assumptions

- ENCODE portal contains paired RNA-seq and DNase-seq/ATAC-seq data for at least 5 common human cell lines (GM12878, K562, HMEC, IMR90, HepG2) with ≥3 biological replicates per cell line
- All required variables for the analysis (accessibility peaks, gene expression values, TSS coordinates) are present in the ENCODE dataset; [NEEDS CLARIFICATION: does ENCODE contain the specific peak-to-gene linkages needed for ±50kb window aggregation?]
- The analysis is observational (no random assignment), so all findings will be framed as associational rather than causal
- Housekeeping genes are defined using the [deferred] most consistently expressed genes across all cell lines based on coefficient of variation < 0.2
- Cell-type-specific genes are defined as genes with expression variance > 0.5 across cell lines
- The top [deferred] most variable peaks are selected to reduce dimensionality to fit 7GB RAM constraint
- Elastic Net with α=0.5 is used as the default regularization balance between L1 and L2 penalties
- Bonferroni correction is applied at α=0.05 significance threshold for multiple testing across all genes
- No GPU/CUDA accelerators are available; all computation runs on 2 CPU cores with default precision
- Gene expression values are log-transformed using log2(counts + 1) to handle zero counts and normalize distribution
- Peak accessibility signal is aggregated as sum of reads within the ±50kb window using bedtools coverage
- The 6-hour runtime budget allows for complete pipeline execution including data download, preprocessing, model training, and validation
