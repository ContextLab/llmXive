# Specification: Predicting Gene Expression from Chromatin Accessibility in Human Cells

## Project Overview
This project investigates the extent to which bulk chromatin accessibility profiles can predict steady-state gene expression levels across multiple human cell lines. We aim to build interpretable regression models that quantify the relationship between open chromatin regions (OCRs) and gene expression, while explicitly acknowledging the limitations of bulk profiling in capturing single-cell heterogeneity.

## Motivation
Gene regulation is a complex process involving the interplay of transcription factors, chromatin structure, and epigenetic modifications. While chromatin accessibility is a key indicator of regulatory potential, the precise quantitative relationship between accessibility and expression remains an active area of research. This project seeks to provide a data-driven, first-order approximation of this relationship.

## Scope
- **In Scope**:
 - Download and preprocess paired RNA-seq and DNase-seq/ATAC-seq data for ≥5 human cell lines (GM12878, K562, HMEC, IMR90, HepG2) from ENCODE.
 - Aggregate accessibility signal within ±50kb of Transcription Start Sites (TSS).
 - Train interpretable regression models (Elastic Net) to predict gene expression from accessibility features.
 - Analyze feature importance and map regulatory peaks to genomic locations.
 - Evaluate model performance across housekeeping and cell-type-specific genes.
- **Out of Scope**:
 - Single-cell resolution analysis (bulk profiles are used).
 - Causal inference of regulatory mechanisms.
 - Integration of non-accessibility features (e.g., methylation, histone marks) beyond the primary scope.
 - Real-time prediction or clinical applications.

## User Stories

### US1: Download and preprocess paired multiomic data
**As a** researcher, **I want** to download and preprocess paired RNA-seq and DNase-seq/ATAC-seq count data for multiple human cell lines, **so that** I have a clean, consistent dataset for model training.
**Acceptance Criteria**:
- Data for ≥5 cell lines is downloaded from ENCODE.
- Accessibility signal is aggregated within ±50kb of TSS.
- Genes with zero expression in all samples are filtered.
- Missing values are imputed using median imputation.
- Top N variable peaks are selected.

### US2: Train and validate interpretable regression models
**As a** researcher, **I want** to train and validate interpretable regression models (Elastic Net) for each cell line, **so that** I can quantify the predictive power of chromatin accessibility on gene expression.
**Acceptance Criteria**:
- Elastic Net models are trained for each cell line.
- Cross-validation is performed with k=5 folds.
- Pearson correlation and R² scores are calculated.
- Bonferroni correction is applied to p-values.
- External validation is performed by training on a subset of cell lines and testing on a held-out line.

### US3: Analyze feature importance and report regulatory insights
**As a** researcher, **I want** to analyze feature importance and map regulatory peaks to TSS, **so that** I can identify key regulatory regions and understand the biological insights provided by the models.
**Acceptance Criteria**:
- Non-zero coefficient features are extracted and ranked.
- Peak coordinates are mapped to genomic locations relative to TSS.
- Percentage of top features within ±10kb of TSS is calculated.
- Performance gap between housekeeping and cell-type-specific genes is reported.
- A summary report comparing model performance across cell types and gene categories is generated.

## Functional Requirements

### FR-001: ENCODE Data Download
The system shall download paired RNA-seq and DNase-seq/ATAC-seq count data for ≥5 human cell lines from the ENCODE portal.

### FR-002: Data Preprocessing
The system shall preprocess accessibility signal within ±50kb of TSS, filter genes with zero expression, and apply log pseudocount transformation.

### FR-003: Missing Value Imputation
The system shall impute missing values using median imputation per peak.

### FR-004: Variable Peak Selection
The system shall select top N variable peaks based on variance across samples.

### FR-005: Model Training
The system shall train Elastic Net models with α=0.5 and λ determined via cross-validation.

### FR-006: Statistical Correction
The system shall apply Bonferroni correction for p-values.

### FR-007: Feature Importance Extraction
The system shall extract non-zero coefficient features and rank them by absolute magnitude.

### FR-008: Peak Annotation
The system shall map peak coordinates to genomic locations relative to the nearest TSS.

### FR-009: Housekeeping Gene Analysis
The system shall calculate R² for housekeeping genes per cell line.

### FR-010: Performance Gap Analysis
The system shall calculate and report the performance gap (ΔR²) between housekeeping and cell-type-specific genes.

### FR-011: External Validation
The system shall perform external validation by training on a subset of cell lines and testing on a held-out line.

### FR-012: Report Generation
The system shall generate a summary report comparing model performance across cell types and gene categories.

### FR-013: Logging and Profiling
The system shall log memory usage and runtime to verify CPU/RAM constraints.

### FR-014: Deterministic Data Generation
The system shall include a deterministic synthetic data generator for CI validation, using seeded random number generation.

## Non-Functional Requirements

### SC-001: Computational Constraints
The system shall operate within the following resource constraints:
- **CPU**: Several CPU cores (no GPU required).
- **RAM**: ≤7GB RAM.
- **Runtime**: ≤6 hours for the full pipeline on standard hardware.

### SC-002: Reproducibility
All data generation and model training shall be reproducible using fixed random seeds.

### SC-003: TSS Proximity
The system shall calculate the percentage of top-100 features within ±10kb of TSS.

### SC-004: Performance Gap Reporting
The system shall explicitly report the performance gap between housekeeping and cell-type-specific genes.

### SC-005: Resource Thresholds
The system shall be designed to run on standard computational resources:
- **CPU**: Several CPU cores.
- **RAM**: Sufficient RAM (≤7GB).
- **Runtime**: ≤6 hours.

### SC-006: External Validation
The system shall perform external validation to assess generalizability across cell lines.

## Limitations and Caveats

### Bulk Profile Limitations
This project uses bulk chromatin accessibility profiles, which smooth over single-cell heterogeneity. As such, the results represent a "first-order approximation" of gene regulation and do not capture the full complexity of cell-type-specific regulatory mechanisms.

### Correlation vs. Causation
The models trained in this project are predictive and correlational in nature. They do not establish causal relationships between chromatin accessibility and gene expression.

### Data Availability
The quality and completeness of the results depend on the availability and quality of the ENCODE data. Missing or low-quality data may impact model performance.

## Data Sources
- **ENCODE Portal**: RNA-seq and DNase-seq/ATAC-seq data for human cell lines.
- **Synthetic Data**: Deterministically generated synthetic data for CI validation.

## Deliverables
- `data/raw/`: Raw downloaded data from ENCODE.
- `data/processed/`: Preprocessed and aggregated data.
- `data/models/`: Trained Elastic Net models.
- `logs/`: Runtime and profiling logs.
- `docs/`: Regulatory insights report and limitations documentation.
- `code/`: Python scripts for data download, preprocessing, training, and analysis.
- `tests/`: Contract, integration, and unit tests.

## Version History
- **v1.0**: Initial specification.
- **v1.1**: Added limitations and caveats regarding bulk profile limitations and correlation vs. causation.