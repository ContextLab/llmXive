# Data Model: Predicting Plant Defense Compound Production

## Overview

This document defines the data schemas for the pipeline, ensuring type safety and structural integrity across the download, preprocessing, and modeling stages. All data artifacts must conform to these schemas to pass contract tests.

## Entity Definitions

### 1. ExpressionMatrix
**Description**: Normalized gene expression values (TPM/FPKM) for defense‑pathway genes.  
**Source**: `data/processed/expression_matrix.csv`  
**Dimensions**: Rows = Gene IDs, Columns = Sample IDs.

| Column Name | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `gene_id` | string | Unique gene identifier (e.g., AT1G01010) | Primary Key, Non‑null |
| `species` | string | Species name (*Arabidopsis* or *Solanum*) | Enum: ['Arabidopsis', 'Solanum'] |
| `pathway` | string | KEGG pathway name | Enum: ['Terpenoid', 'Alkaloid', 'Phenylpropanoid'] |
| `sample_001` | float | Expression value for sample 001 | ≥ 0.0, No NaN |
| `sample_002` | float | Expression value for sample 002 | ≥ 0.0, No NaN |
| … | float | … | … |

### 2. MetaboliteMatrix
**Description**: Log‑transformed concentrations of defense metabolites.  
**Source**: `data/processed/metabolite_matrix.csv`  
**Dimensions**: Rows = Metabolite IDs, Columns = Sample IDs.

| Column Name | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `metabolite_id` | string | Unique metabolite identifier | Primary Key, Non‑null |
| `compound_class` | string | Chemical class | Enum: ['Terpenoid', 'Alkaloid', 'Phenylpropanoid'] |
| `sample_001` | float | Log‑concentration for sample 001 | Real number, No NaN |
| `sample_002` | float | Log‑concentration for sample 002 | Real number, No NaN |
| … | float | … | … |

### 3. PairedSampleIndex
**Description**: A mapping of sample IDs that exist in both matrices.  
**Source**: `data/processed/paired_samples.csv`

| Column Name | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `sample_id` | string | Unique biological sample ID | Primary Key |
| `expression_source` | string | GEO Accession ID | Non‑null |
| `metabolite_source` | string | Metabolomics Workbench Study ID | Non‑null |
| `pairing_confidence` | string | Confidence level | Enum: ['exact', 'inferred'] |

### 4. ModelOutput
**Description**: Results from the Ridge Regression and permutation tests.  
**Source**: `outputs/metrics/model_results.json`

| Field | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `metabolite_id` | string | Target metabolite | Non‑null |
| `rmse_mean` | float | Mean RMSE across CV folds | ≥ 0.0 |
| `rmse_std` | float | Std dev of RMSE | ≥ 0.0 |
| `pearson_r` | float | Mean Pearson correlation | [-1.0, 1.0] |
| `p_value_raw` | float | Raw permutation p‑value | [0.0, 1.0] |
| `p_value_corrected` | float | Bonferroni‑corrected p‑value | [0.0, 1.0] |
| `is_significant` | boolean | True if corrected p < 0.05 | Boolean |

## Data Flow

1. **Raw Download**: `data/raw/` contains unmodified files from GEO and Metabolomics Workbench.  
2. **Preprocessing**:  
   - Pairing logic creates `PairedSampleIndex`.  
   - Filtering creates `ExpressionMatrix` and `MetaboliteMatrix`.  
   - Retention audit logs ensure ≥ 75 % of known defense pathway genes are kept (SC‑006).  
3. **Modeling**:  
   - Input: `ExpressionMatrix` (columns subset to paired samples).  
   - Input: `MetaboliteMatrix` (columns subset to paired samples).  
   - Output: `ModelOutput` (metrics) and serialized model artifacts (`outputs/models/`).  

--- End of Data Model ---