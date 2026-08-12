# Data Model: Identifying Predictive Biomarkers of Chemotherapy Response in Public Cancer Datasets

## Entities

### Sample
Represents a patient tumor specimen.
-   `sample_id`: Unique identifier (string).
-   `tumor_type`: Cancer type (string, e.g., "BRCA", "LUAD").
-   `response_label`: Binary label (0=Non-responder, 1=Responder).
-   `expression_vector`: Array of gene expression values (float64).
-   `set_type`: "discovery" or "training" (string).
-   `dataset_source`: "TCGA" or "GEO" (string).

### GenePanel
Represents the meta-analyzed biomarker set.
-   `gene_symbol`: HGNC gene symbol (string).
-   `meta_p_value`: Combined p-value from Stouffer's method (float).
-   `log2FC_mean`: Mean log2 fold change across studies (float).
-   `selected`: Boolean flag indicating inclusion in final panel.
-   `tumor_types`: List of tumor types where gene was significant (list of strings).

### Model
Represents the trained elastic-net predictor.
-   `cancer_type`: Tumor type for which model was trained (string).
-   `alpha`: Elastic-net mixing parameter (float).
-   `lambda`: Regularization parameter (float).
-   `coefficients`: Dictionary of gene_symbol -> coefficient (dict).
-   `cross_val_auc`: Mean AUC from nested CV (float).
-   `validation_auc`: AUC on external validation set (float).

## Data Flow

1.  **Raw Data**: Downloaded to `data/raw/` (TCGA `.h5`, GEO `.zip`).
2.  **Harmonized**: Gene IDs mapped to HGNC; low-expression filtered.
3.  **Normalized**: VST transformation applied; batch correction (ComBat).
4.  **Split**: Discovery (for DE) and Training (for modeling) sets created.
5.  **DE Results**: Significant genes identified per tumor type.
6.  **Meta-Analysis**: Genes intersected/unioned; p-values combined.
7.  **Model Training**: Elastic-net trained on training set.
8.  **Validation**: Model evaluated on LOO and external GEO data.
9.  **Output**: `results/summary.md`, `results/meta_analysis/gene_panel.json`, `results/models/*.pkl`.

## Constraints

-   **Gene Coverage**: ≥95% of genes must be harmonized to HGNC.
-   **Expression Filter**: Genes with CPM < 1 in >80% of samples removed.
-   **Sample Size**: Minimum 50 responders and 50 non-responders per tumor type (or report limitation).
-   **Panel Size**: ≤50 genes (fallback to union if intersection empty).
-   **Memory**: All intermediate matrices must fit in ≤7GB RAM (streaming/sampling used).
