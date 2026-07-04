# Data Model: Identifying Predictive Biomarkers of Chemotherapy Response in Public Cancer Datasets

## Overview

This document defines the data structures, schemas, and transformations used in the pipeline. It ensures that all data artifacts conform to the contracts defined in `contracts/`.

## Entities

### Sample
Represents a single patient tumor specimen.
- `sample_id`: Unique identifier (string).
- `tumor_type`: Cancer type (string, e.g., "BRCA", "LUAD").
- `response_label`: Binary (0 = Non‑responder, 1 = Responder).
- `expression_vector`: Dictionary or array of gene expression values (gene_symbol → value).
- `set_type`: "discovery" or "training" (string).
- `source`: "TCGA" or "GEO" (string).

### GenePanel
Represents the meta‑analyzed biomarker set.
- `gene_symbol`: HGNC symbol (string).
- `meta_p_value`: Combined p‑value from Stouffer's method (float).
- `log2FC_mean`: Mean log2 fold change across tumor types (float).
- `selected`: Boolean (True if in final panel).
- `rank`: Integer (1‑based rank by meta_p_value).

### Model
Represents a trained elastic‑net predictor.
- `cancer_type`: The tumor type the model is trained on.
- `alpha`: Elastic‑net mixing parameter (float).
- `lambda`: Regularization parameter (float).
- `coefficients`: Dictionary of gene_symbol → coefficient.
- `cross_val_auc`: AUC from internal nested CV.
- `external_auc`: AUC from external GEO validation (if available).
- `calibration_error`: Maximum deviation across deciles (float).
- `de_long_p`: Bonferroni‑adjusted p‑value from DeLong’s test.

## Data Flow

1. **Raw Data**: Downloaded from verified URLs (TCGA CSV/H5, GEO CSV). |
2. **Harmonization**: Gene identifiers mapped to HGNC. |
3. **Filtering**: Low‑expression genes removed (CPM < 1 in > 80 % samples). |
4. **Normalization**: VST (DESeq2) applied; batch correction via ComBat‑seq or quantile matching. |
5. **Splitting**: Data split into Discovery and Training sets (FR‑013). |
6. **DE Analysis**: Performed on Discovery set only (FR‑005). |
7. **Meta‑Analysis**: Stouffer’s method applied to DE results (FR‑006). |
8. **Modeling**: Elastic‑net trained on Training set using GenePanel (FR‑007). |
9. **Validation**: Nested CV, LOO, and external GEO cohorts (FR‑008, FR‑009, FR‑011). |
10. **Reporting**: All artifacts stored under `results/` and validated against contracts.

## Constraints

- **Gene Coverage**: ≥95 % of genes must be successfully mapped to HGNC symbols. |
- **Sample Coverage**: ≥100 samples per tumor type (if available). |
- **Response Balance**: If responder ratio < 20 %, cost‑sensitive learning with class weights is applied. |
- **Memory**: All intermediate data structures must fit within 7 GB RAM.
