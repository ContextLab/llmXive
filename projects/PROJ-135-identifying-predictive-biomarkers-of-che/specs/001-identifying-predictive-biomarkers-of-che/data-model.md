# Data Model: Identifying Predictive Biomarkers of Chemotherapy Response

## Entities

### Sample
Represents a single patient tumor specimen.
- `sample_id` (string): Unique identifier (e.g., "TCGA-05-4244-01Z-00-DX1").
- `tumor_type` (string): Cancer type (e.g., "LUAD", "OV").
- `response_label` (integer): 1 for Responder, 0 for Non-Responder.
- `expression_vector` (list[float]): Gene expression values (normalized).
- `set_type` (string): "discovery" or "training" or "validation".
- `source` (string): "TCGA" or "GEO".

### Gene
Represents a single gene feature.
- `gene_symbol` (string): HGNC symbol (e.g., "TP53").
- `log2FC` (float): Log2 fold change from DE analysis.
- `p_value` (float): Raw p-value from DE test.
- `adj_p_value` (float): FDR-adjusted p-value.
- `meta_p_value` (float): Combined p-value from Stouffer's method.
- `selected` (boolean): True if included in final panel.

### Model
Represents a trained predictive model.
- `model_id` (string): Unique identifier.
- `cancer_type` (string): Tumor type the model was trained on.
- `alpha` (float): Elastic-net mixing parameter.
- `lambda_` (float): Regularization strength.
- `coefficients` (dict): {gene_symbol: coefficient}.
- `cross_val_auc` (float): AUC from nested CV.
- `external_auc` (float): AUC from external validation.

## Relationships

- **Sample** has **expression_vector** (1:1).
- **Gene** is used in **Model** (N:M).
- **Model** is trained on a subset of **Sample** (1:N).
- **Sample** is part of a **GenePanel** (via selection).

## Data Flow

1.  **Raw Data**: Downloaded to `data/raw/` (metadata + synthetic/real expression).
2.  **Preprocessing**: Filtered, normalized, harmonized -> `data/processed/`.
3.  **DE Analysis**: Generates `results/de_analysis/{tumor_type}.csv`.
4.  **Meta Analysis**: Generates `results/meta_analysis/panel.csv`.
5.  **Model Training**: Generates `results/models/{model_id}.pkl`.
6.  **Validation**: Generates `results/validation/summary.csv`.
