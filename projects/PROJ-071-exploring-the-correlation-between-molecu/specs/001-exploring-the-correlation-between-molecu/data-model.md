# Data Model: Exploring the Correlation Between Molecular Complexity and Degradation Rates in Pharmaceuticals

## 1. Overview
This document defines the data structures used for ingestion, processing, and analysis. All data is stored in CSV or Parquet formats within the `data/` directory.

## 2. Core Entities

### 2.1 Molecule
Represents a pharmaceutical compound.
- **smiles**: `string` (Canonical SMILES)
- **molecular_weight**: `float` (g/mol)
- **tps_a**: `float` (Topological Polar Surface Area, Å²)
- **rotatable_bonds**: `int`
- **aromatic_rings**: `int`
- **wiener_index**: `float`
- **zagreb_index**: `float`
- **is_fda_approved**: `boolean`
- **calculation_status**: `string` ("valid", "failed", "skipped")
- **failure_reason**: `string` (if status != "valid")

### 2.2 DegradationRecord
Represents experimental stability data.
- **drug_id**: `string` (Unique identifier, e.g., DrugBank ID)
- **half_life_hours**: `float` (Standardized to hours)
- **rate_constant_k**: `float` (Optional, original unit)
- **ph**: `float` (Optional)
- **temperature_celsius**: `float` (Optional)
- **source_dataset**: `string` (e.g., "Synthyra", "DrugBank")
- **normalization_status**: `string` ("normalized", "unnormalized", "missing_conditions")
- **is_valid**: `boolean`

### 2.3 AnalysisResult
Aggregated statistical output.
- **feature_name**: `string`
- **correlation_pearson**: `float`
- **correlation_spearman**: `float`
- **p_value_pearson**: `float`
- **p_value_spearman**: `float`
- **regression_coefficient**: `float` (from MLR)
- **lasso_coefficient**: `float`
- **cv_r2_score**: `float`
- **p_value_model**: `float`

## 3. Data Flow

1.  **Raw Ingestion**: Downloaded Parquet/JSONL files stored in `data/raw/`.
2.  **Merged Dataset**: `data/processed/merged_drugs.csv` containing `smiles`, `degradation` columns.
3.  **Processed Dataset**: `data/processed/final_analysis.csv` with calculated descriptors and standardized half-lives.
4.  **Output**: `data/processed/results.json` (summary statistics) and `data/processed/plots/` (images).

## 4. Constraints
- **SMILES**: Must be canonicalized.
- **Missing Data**: Rows with missing `half_life_hours` or invalid `smiles` are excluded.
- **Units**: All time units converted to hours. All temperatures to Celsius.
