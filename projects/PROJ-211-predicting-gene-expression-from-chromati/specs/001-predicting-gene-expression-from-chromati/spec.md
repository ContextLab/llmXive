# Specification: Predicting Gene Expression from Chromatin Accessibility in Human Cells

## 1. Overview

### 1.1 Purpose
This project investigates the extent to which bulk chromatin accessibility profiles (DNase-seq/ATAC-seq) can predict steady-state gene expression levels (RNA-seq) across multiple human cell lines. The goal is to build interpretable regression models that quantify the relationship between regulatory element accessibility and transcriptional output.

### 1.2 Scope
- **Data Sources**: ENCODE Consortium (RNA-seq and DNase-seq/ATAC-seq for ≥5 human cell lines).
- **Cell Lines**: GM12878, K562, HMEC, IMR90, HepG2 (subject to data availability).
- **Modeling**: Elastic Net regression with cross-validation.
- **Interpretation**: Feature importance analysis, TSS proximity mapping, and performance comparison across gene categories (housekeeping vs. cell-type-specific).

### 1.3 Limitations
- **Bulk vs. Single-Cell**: This project uses bulk profiles, which average over cellular heterogeneity. Predictions represent a "first-order approximation" of gene regulation and do not capture single-cell dynamics or causal mechanisms.
- **Correlation vs. Causation**: The models identify statistical associations between accessibility and expression, not causal regulatory links.
- **Genomic Context**: Analysis is limited to ±50kb windows around Transcription Start Sites (TSS). Distal enhancers outside this range are not explicitly modeled.

## 2. User Stories

### US1: Download and Preprocess Paired Multiomic Data
**As a** researcher,
**I want** to download and preprocess paired RNA-seq and DNase-seq/ATAC-seq data for multiple human cell lines,
**So that** I can build a dataset of accessibility features and expression values for modeling.

**Acceptance Criteria**:
- Data downloaded from ENCODE for at least 5 cell lines.
- Accessibility signal aggregated within ±50kb of TSS.
- Genes with zero expression in all samples are filtered.
- Data fits within 7GB RAM.

### US2: Train and Validate Interpretable Regression Models
**As a** researcher,
**I want** to train Elastic Net models and perform cross-validation,
**So that** I can quantify the predictive power of chromatin accessibility on gene expression.

**Acceptance Criteria**:
- Elastic Net models trained for each cell line (α=0.5, λ via CV).
- 5-fold cross-validation performed.
- Pearson correlation and R² calculated.
- P-values corrected for multiple testing (Bonferroni).

### US3: Analyze Feature Importance and Report Regulatory Insights
**As a** researcher,
**I want** to analyze feature importance and map peaks to TSS,
**So that** I can understand which regulatory regions drive expression and compare performance across gene categories.

**Acceptance Criteria**:
- Top features ranked by coefficient magnitude.
- Percentage of top features within ±10kb of TSS reported.
- Performance gap (ΔR²) between housekeeping and cell-type-specific genes calculated.

## 3. Functional Requirements

- **FR-001**: Download paired RNA-seq and DNase-seq/ATAC-seq count data from ENCODE.
- **FR-002**: Aggregate accessibility signal within ±50kb of TSS.
- **FR-003**: Filter genes with zero expression in all samples.
- **FR-004**: Apply log pseudocount transformation (log(counts + 1)).
- **FR-005**: Impute missing values using median imputation per peak.
- **FR-006**: Apply Bonferroni correction to p-values.
- **FR-007**: Extract and rank non-zero coefficient features.
- **FR-008**: Map peak coordinates to genomic location relative to nearest TSS.
- **FR-009**: Calculate R² for housekeeping genes.
- **FR-010**: Calculate performance gap between gene categories.
- **FR-011**: Generate summary report of regulatory insights.

## 4. Non-Functional Requirements

- **SC-001**: Models must be interpretable (Elastic Net).
- **SC-002**: Pipeline must run on CPU only (no GPU/CUDA).
- **SC-003**: At least 80% of top-100 features must be within ±10kb of TSS (expected biological prior).
- **SC-004**: Performance gap analysis must be reproducible.
- **SC-005**: Resource Constraints:
 - **Compute**: Several CPU cores.
 - **Memory**: Sufficient RAM to process data in memory (target <7GB).
 - **Runtime**: Maximum 6 hours for full pipeline execution.
- **SC-006**: External validation must be performed (train on subset, test on held-out cell line).

## 5. Data Models

### 5.1 Input Data
- **RNA-seq Counts**: Matrix of gene expression counts (genes x samples).
- **DNase-seq/ATAC-seq Peaks**: BED file of accessible regions (chrom, start, end, score).
- **Gene Coordinates**: BED file of gene TSS locations (chrom, start, end, gene_id).

### 5.2 Processed Data
- **Feature Matrix**: Matrix of aggregated accessibility signals (peaks x samples).
- **Target Vector**: Vector of log-transformed gene expression values.
- **Model Artifacts**: Serialized Elastic Net models and cross-validation scores.

## 6. Implementation Plan

### Phase 1: Setup
- Initialize project structure.
- Configure dependencies and linting.

### Phase 2: Foundational
- Define data schema contracts.
- Implement synthetic data generator (for CI).
- Implement utility functions (logging, checksumming).

### Phase 3: User Story 1 (MVP)
- Implement ENCODE download logic.
- Implement data preprocessing pipeline.
- Validate pipeline with synthetic data.

### Phase 4: User Story 2
- Implement Elastic Net training.
- Implement cross-validation loop.
- Calculate correlations and p-values.

### Phase 5: User Story 3
- Implement feature importance extraction.
- Implement TSS mapping and proximity analysis.
- Generate regulatory insights report.

### Phase 6: Research & Documentation
- Address reviewer concerns.
- Document limitations and findings.

## 7. References

- ENCODE Consortium: https://www.encodeproject.org/
- Elastic Net: Zou, H., & Hastie, T. (2005). Regularization and variable selection via the elastic net.
- Bonferroni Correction: Bonferroni, C. E. (1936). Teoria statistica delle classi e calcolo delle probabilità.