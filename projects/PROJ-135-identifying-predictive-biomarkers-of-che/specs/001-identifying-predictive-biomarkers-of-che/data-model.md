# Data Model: Identifying Predictive Biomarkers of Chemotherapy Response

## Overview

This document defines the data structures, schemas, and transformations used in the pipeline. All data flows from `data/raw/` (immutable) to `data/processed/` (derived) to `results/` (final outputs).

## Entity Definitions

### 1. Sample
Represents a patient specimen.
- **Attributes**:
  - `sample_id`: Unique string identifier.
  - `tumor_type`: String (e.g., "BRCA", "LUAD").
  - `response_label`: Binary (1 = Responder, 0 = Non-Responder).
  - `expression_vector`: Dictionary or array mapping HGNC symbols to VST values.
  - `batch_corrected`: Boolean (True if Quantile Normalization applied).
  - `source`: String ("TCGA" or "GEO").
  - `dataset_id`: String (e.g., "GSE25055").

### 2. GenePanel
Represents the meta-analyzed biomarker set.
- **Attributes**:
  - `gene_symbol`: String (HGNC).
  - `meta_p_value`: Float (combined p-value from Stouffer's).
  - `log2FC_mean`: Float (mean log2 fold change across tumor types).
  - `selected`: Boolean (True if in final panel).
  - `rank`: Integer (1 = most significant).
  - `selection_method`: String ("intersection" or "union_fallback").

### 3. Model
Represents the trained elastic-net predictor.
- **Attributes**:
  - `model_id`: String.
  - `cancer_type`: String (or "Pan-Cancer" for pooled model).
  - `alpha`: Float (mixing parameter).
  - `lambda`: Float (regularization strength).
  - `coefficients`: Dictionary (gene_symbol -> weight).
  - `cross_val_auc`: Float (internal CV performance).
  - `external_auc`: Float (external validation performance).
  - `calibration_error`: Float (max deviation).

## Data Flow

```mermaid
graph TD
    A[TCGA Raw Counts] --> B[Harmonize IDs]
    C[GEO Raw Data] --> B
    B --> D[Filter Low Expr]
    D --> E[VST Normalization (RNA-seq) / Log2 (Microarray)]
    E --> F[Quantile Normalization (Cross-Platform)]
    F --> G[Nested CV: Feature Selection (DE) inside Inner Loop]
    G --> H[Meta-Analysis (Gene Ranking)]
    H --> I[Gene Panel Selection]
    F --> J[Model Training (Pooled Data)]
    I --> J
    J --> K[Nested CV]
    K --> L[External Validation]
    L --> M[Results: AUC, Calibration]
```

## File Formats

### Input: Raw Data
- **TCGA**: `.h5` or `.csv` (counts matrix, clinical metadata).
- **GEO**: `.txt` or `.csv` (expression matrix, phenotype data).

### Intermediate: Processed Data
- **Expression Matrix**: `.npy` (NumPy array) or `.parquet` (Pandas DataFrame).
  - Rows: Samples.
  - Columns: HGNC Gene Symbols.
  - Values: VST-normalized (RNA-seq) or Quantile-normalized (Microarray) expression.
- **Metadata**: `.json` (Sample info, set splits).

### Output: Results
- **DE Results**: `.csv` (Gene, log2FC, p-value, adj_p-value).
- **Meta Analysis**: `.csv` (Gene, meta_p, log2FC_mean, selection_method).
- **Model**: `.pkl` (Pickled sklearn model) + `.json` (Hyperparameters).
- **Summary**: `.md` (Human-readable report).

## Schema Constraints

- **Gene Symbols**: Must be valid HGNC symbols (uppercase, no special characters).
- **Response Labels**: Must be binary (0 or 1).
- **Missing Data**: Genes with >20% missing values in a tumor type are excluded.
- **Class Imbalance**: If responder ratio < 20%, class weights are applied.
- **Batch Correction**: The `batch_corrected` flag must be set to `true` for all processed data used in modeling.

## Data Hygiene & Versioning

- **Checksums**: All files in `data/` are checksummed (SHA-256) and recorded in `state/`. **Raw data checksums are generated immediately upon download.**
- **Immutability**: Raw data is never modified. Derivations create new files.
- **Traceability**: Every result in `results/` references the specific `data/` file and `code/` script used to generate it.