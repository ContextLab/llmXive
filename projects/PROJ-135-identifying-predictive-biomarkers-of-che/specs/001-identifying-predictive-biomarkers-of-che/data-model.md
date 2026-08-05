# Data Model: Identifying Predictive Biomarkers of Chemotherapy Response in Public Cancer Datasets

## 1. Conceptual Overview

The data model supports a pipeline that ingests heterogeneous transcriptomic data, harmonizes it, identifies biomarkers, and trains predictive models. Key entities include `Sample`, `GenePanel`, and `Model`.

## 2. Entity Definitions

### 2.1 Sample
Represents a patient tumor specimen.
- **sample_id**: Unique identifier (string).
- **tumor_type**: Cancer type (string, e.g., "BRCA", "LUAD").
- **response_label**: Binary (0=Non-responder, 1=Responder).
- **expression_vector**: Dictionary or array of gene expression values. **Note**: While the pipeline uses streaming internally to load data efficiently, the `expression_vector` in this entity represents the **final, fully materialized** vector for the sample in memory. Streaming is an internal optimization for the loading function, not a property of the `Sample` entity itself.
- **set_type**: "discovery" (for DE) or "training" (for model fitting).
- **source**: "TCGA" or "GEO".
- **dataset_id**: Original accession number (e.g., "GSE25055").
- **proxy_flag**: Boolean, true if `response_label` was derived from survival data (prognostic proxy).

### 2.2 GenePanel
Represents the meta-analyzed biomarker set.
- **gene_symbol**: HGNC symbol (string).
- **meta_p_value**: Combined p-value from REML method (float).
- **log2FC_mean**: Mean log2 fold change across tumor types (float).
- **selected**: Boolean flag indicating inclusion in final panel.
- **panel_rank**: Integer rank based on meta_p_value.

### 2.3 Model
Represents the trained elastic-net predictor.
- **cancer_type**: The tumor type the model is trained on (or "pan-cancer").
- **alpha**: Elastic-net mixing parameter (float).
- **lambda**: Regularization parameter (float).
- **coefficients**: Dictionary of gene -> coefficient.
- **cross_val_auc**: Internal CV AUC (float).
- **external_auc**: AUC on external validation (float).
- **validation_type**: "LOO" or "NestedCV" or "ExternalOnly".

## 3. Data Flow & Transformations

1.  **Raw Data**:
    - TCGA: HTSeq-Counts (raw counts), Clinical JSON.
    - GEO: Expression Matrix (RMA/MAS5), Clinical Metadata.
2.  **Harmonized Data**:
    - All genes mapped to HGNC.
    - Low-expression genes filtered (CPM < 1 in >80% samples).
    - Normalized via DESeq2 VST.
3.  **Discovery Data**:
    - Split into Discovery Set (DE) and Training Set (Model).
4.  **Processed Data**:
    - `data/processed/harmonized_counts.csv` (VST values).
    - `results/meta_analysis/gene_panel.csv`.
    - `results/models/final_model.pkl`.

## 4. Storage & Integrity

- **Raw Data**: Stored in `data/raw/`. Checksums recorded in `state/...yaml`.
- **Processed Data**: Stored in `data/processed/`. Immutable after creation.
- **Artifacts**: All intermediate files (e.g., `vst_matrix.csv`) are versioned with content hashes.
