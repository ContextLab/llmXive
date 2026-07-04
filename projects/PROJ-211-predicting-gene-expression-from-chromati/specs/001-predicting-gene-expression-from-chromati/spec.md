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

The researcher MUST be able to train Elastic Net regression models for each cell line using accessibility features to predict log-transformed expression values, perform cross-validation with multiple folds per cell line, and calculate Pearson correlation coefficients between predicted and actual expression.

**Why this priority**: This delivers the core scientific analysis. The model performance directly addresses the research question about predictability of expression from accessibility.

**Independent Test**: Can be fully tested by verifying that each cell line produces a trained model object, cross-validation scores, and a correlation matrix with p-values for all genes.

**Acceptance Scenarios**:

1. **Given** preprocessed feature and expression matrices exist, **When** the system trains Elastic Net regression with α=0.5 and λ selected via cross-validation, **Then** the system reports the R² value for housekeeping genes for each cell line
2. **Given** trained models exist, **When** the system performs 5-fold cross-validation, **Then** each fold produces a correlation coefficient and the mean correlation is recorded
3. **Given** predictions are generated, **When** Pearson correlation is calculated between predicted and actual expression, **Then** p-values are computed and Bonferroni-corrected for multiple testing across genes

---

### User Story 3 - Analyze feature importance and report regulatory insights (Priority: P3)

The researcher MUST be able to extract feature importance scores from the trained models, identify accessible regions near the TSS as primary predictors, and generate a report comparing model performance across cell types and gene categories.

**Why this priority**: This provides the interpretability component that distinguishes this work from black-box deep learning approaches, supporting the research goal of understanding the regulatory code.

**Independent Test**: Can be fully tested by verifying that feature importance rankings are produced, TSS-proximal regions appear in the top 100 important features, and a summary report documents performance differences between housekeeping and cell-type-specific genes.

**Acceptance Scenarios**:

1. **Given** trained Elastic Net models exist, **When** the system extracts non-zero coefficient features, **Then** a ranked list of the most important peaks is produced for each cell line
2. **Given** feature importance rankings exist, **When** the system maps peaks to genomic coordinates, **Then** at least 50% of top 100 features fall within ±10kb of a TSS
3. **Given** correlation results exist, **When** the system compares housekeeping vs. cell-type-specific genes, **Then** the system reports the performance gap (ΔR²) between the two gene sets

---

### Edge Cases

- What happens when ENCODE data for a requested cell line is unavailable or incomplete? The system MUST retry up to 3 failed attempts with 60-second intervals before marking the cell line as unavailable and proceeding with remaining data.
- How does the system handle genes with extremely low expression values (near zero on log scale)? The system MUST add a pseudocount before log transformation to avoid undefined values.
- What happens when peak accessibility data contains missing values? The system MUST impute missing values using median imputation across samples for each peak.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download paired RNA-seq and DNase-seq/ATAC-seq count data for ≥5 human cell lines from ENCODE portal (See US-1)
- **FR-002**: System MUST aggregate accessibility signal within ±50kb windows of each gene's TSS using bedtools (See US-1)
- **FR-003**: System MUST filter genes with zero expression in all samples, retaining ≥10,000 genes for analysis (See US-1)
- **FR-004**: System MUST train Elastic Net regression models (α=0.5) for each cell line using scikit-learn (See US-2)
- **FR-005**: System MUST perform k-fold cross-validation, with k representing a reasonable number of folds. per cell line and record mean correlation coefficient (See US-2)
- **FR-006**: System MUST apply Bonferroni correction for multiple testing across all genes when calculating p-values (See US-2)
- **FR-007**: System MUST extract non-zero coefficient features and rank by absolute coefficient magnitude (See US-3)
- **FR-008**: System MUST map peak coordinates to genomic location relative to nearest TSS (See US-3)
- **FR-009**: System MUST calculate and report the R² value for the set of housekeeping genes for each cell line (See US-2)
- **FR-010**: System MUST calculate and report the performance gap (ΔR²) between housekeeping and cell‑type‑specific genes (See US-3)
- **FR-011**: System MUST select the top [deferred] most variable accessibility peaks across samples based on variance (See US-1)
- **FR-012**: System MUST define housekeeping genes as the 500 genes with the lowest coefficient of variation (CV ≤ 0.2) across all cell lines (See US-2)
- **FR-013**: System MUST define cell‑type‑specific genes as the 500 genes with the highest expression variance (variance > 0.5) across cell lines (See US-3)
- **FR-014**: System MUST perform external validation by training on a subset of cell lines and testing on a held‑out cell line., reporting the R² for the held‑out line (See US-2)

### Key Entities

- **Cell Line**: Biological sample identifier (e.g., GM12878, K562) with associated RNA-seq and DNase-seq/ATAC-seq data
- **Gene**: Genomic feature with expression value (log-transformed counts) and associated accessibility peaks
- **Peak**: Genomic region with accessibility measurement (DNase-seq/ATAC-seq signal) mapped relative to gene TSS
- **Model**: Elastic Net regression object trained on accessibility features to predict expression

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: R² for housekeeping genes is calculated and reported for each cell line (See US-2)
- **SC-002**: Model generalization is measured against 5-fold cross-validation scores to assess overfitting risk (See US-2)
- **SC-003**: Percentage of the top‑100 important features that fall within ±10 kb of a TSS is calculated and reported (See US-3)
- **SC-004**: Statistical significance is measured against Bonferroni‑corrected p‑values to control family‑wise error rate (See US-2)
- **SC-005**: Computational feasibility is measured against A limited number of CPU cores, sufficient RAM, and a runtime limit were imposed on each experiment.

The research question is: How does the choice of activation function impact the performance of deep neural networks on image classification tasks?

The method is: We will train convolutional neural networks with ReLU, Sigmoid, and Tanh activation functions on the CIFAR-10 dataset and compare their accuracy and training time.

References: [], (Krizhevsky et al., 2009) (See US-1)
- **SC-006**: External validation R² on the held‑out cell line is calculated and reported (See US-2)

## Assumptions

- ENCODE portal contains paired RNA-seq and DNase-seq/ATAC-seq data for at least 5 common human cell lines (GM12878, K562, HMEC, IMR90, HepG2) with ≥3 biological replicates per cell line
- All required variables for the analysis (accessibility peaks, gene expression values, TSS coordinates) are present in the ENCODE dataset; ENCODE does not provide pre‑computed peak‑to‑gene linkages, therefore the pipeline will implement a deterministic ±50 kb windowing algorithm to construct these links. This windowing approach is the standard community practice for bulk multiomic integration when single‑cell co‑assay data is unavailable.
- The analysis is observational (no random assignment), so all findings will be framed as associational rather than causal
- Housekeeping genes are defined as the 500 genes with the lowest coefficient of variation (CV ≤ 0.2) across all cell lines
- Cell‑type‑specific genes are defined as the 500 genes with the highest expression variance (variance > 0.5) across cell lines
- The most variable peaks, as determined by variance across samples, are selected for further analysis. ()

Research question: How do patterns of genomic variation relate to phenotypic diversity?
Method: We will employ a genome-wide association study (GWAS) to identify genomic regions associated with variation in key phenotypic traits. to satisfy the RAM constraint
- Elastic Net with α=0.5 is used as the default regularization balance between L1 and L2 penalties
- Bonferroni correction is applied at α=0.05 significance threshold for multiple testing across all genes
- No GPU/CUDA accelerators are available; all computation runs on a limited number of CPU cores with default precision
- Gene expression values are log‑transformed using log₂(counts + 1) to handle zero counts and normalize distribution
- Peak accessibility signal is aggregated as sum of reads within the ±50 kb window using bedtools coverage
- The allocated runtime budget allows for complete pipeline execution including data download, preprocessing, model training, and validation
