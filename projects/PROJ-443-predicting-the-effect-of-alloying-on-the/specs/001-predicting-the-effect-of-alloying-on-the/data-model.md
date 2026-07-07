# Data Model: Predicting the Effect of Alloying on the Elastic Modulus of High-Entropy Alloys

## 1. Overview

This document defines the data structures used in the pipeline, from raw API responses to processed datasets and model outputs. All data is stored in `data/` (raw) and `data/processed/` (derived).

## 2. Raw Data Schema

### 2.1 API Response (Materials Project / OQMD)
*Source: `data/raw/`*
- **Format**: JSON (API) or CSV (OQMD fallback).
- **Key Fields**:
 - `material_id`: Unique identifier.
 - `composition`: String or dict (e.g., "FeCoNiCrMn" or `{"Fe": 0.2, "Co": 0.2,...}`).
 - `elastic_constants`: Dict of $C_{11}, C_{12}, C_{44}$.
 - `bulk_modulus`: Calculated $B_{observed}$.

### 2.2 Source Metadata
*File: `data/source_metadata.yaml`*
- **Purpose**: Record API versions, query parameters, and timestamps (Constitution Principle VI).
- **Structure**:
 ```yaml
 fetch_timestamp: "2024-05-21T12:00:00Z"
 sources:
 - name: "Materials Project"
 api_version: "v2"
 query_params: {"elements": ">=5", "elastic": true}
 - name: "OQMD"
 url: "..."
 checksums:
 raw_data: "sha256:..."
 ```

## 3. Processed Data Schema

### 3.1 HEA Sample (Processed)
*File: `data/processed/hea_samples_ilr.parquet`*
- **Format**: Parquet (efficient storage).
- **Rows**: Individual HEA samples.
- **Columns**:
 - `sample_id`: Unique string (e.g., "CrMnFeCoNi_001").
 - `elements`: String (e.g., "CrMnFeCoNi").
 - `composition_ilr`: List of float (ILR-transformed composition).
 - `descriptors`: Dict or expanded columns (Entropy, Radius_Variance, etc.).
 - *Note*: Miedema-derived features are **excluded** if target is residual.
 - `bulk_modulus_observed`: Float.
 - `bulk_modulus_miedema`: Float.
 - `target_residual`: Float ($B_{obs} - B_{Miedema}$).
 - `residual_descriptor_correlation`: Float (Pearson |r| between residuals and key descriptors).
 - `validation_status`: String ("Success: Descriptors capture alloying effects" or "Note: Weak residual signal").
 - `metadata`: Dict (source, crystal structure).

### 3.2 Feature Engineering Rules
1. **Normalization**: Composition percentages must sum to 1.0.
2. **ILR**: Applied to composition vector to break closure.
3. **Descriptor Exclusion**: If `target_residual` is used, `mixing_enthalpy_miedema` is removed from predictors.
4. **Correlation Validation**: Calculate correlation between `target_residual` and descriptors.
 - If $|r| \ge 0.1$: Set `validation_status` to "Success: Descriptors capture alloying effects".
 - If $|r| < 0.1$: Set `validation_status` to "Note: Weak residual signal".

## 4. Model Output Schema

### 4.1 Metrics Record
*File: `results/metrics.yaml`*
- **Structure**:
 ```yaml
 models:
 - name: "RandomForest"
 metrics:
 r2: 0.XX
 rmse: 0.XX
 mae: 0.XX
 r2_ci: [lower, upper] # 95% CI from bootstrap
 p_value_null: 0.XX
 significant: true/false
 hyperparams: {...}
 - name: "GradientBoosting"
...
 - name: "ElasticNet"
...
 comparisons:
 fdr_corrected_p_values: {...}
 sensitivity:
 thresholds:
 - 0.25: {type1_error: 0.XX}
 - 0.30: {type1_error: 0.XX}
 - 0.35: {type1_error: 0.XX}
 residual_validation:
 correlation_threshold: 0.1
 status: "Success: Descriptors capture alloying effects"
 correlation_value: 0.XX
 ```

### 4.2 Interpretability Output
*File: `results/interpretability/shap_values.npy`*
- **Format**: Numpy array (samples x features).
- **Purpose**: SHAP values for feature importance.

## 5. Data Flow Diagram

1. **Fetch**: API/CSV $\to$ `data/raw/` (JSON/CSV).
2. **Validate**: Check sample count ($\ge 500$). Halt if fail.
3. **Preprocess**: Normalize $\to$ ILR $\to$ Calculate Descriptors $\to$ **Calculate Residual Correlation** $\to$ `data/processed/hea_samples_ilr.parquet`.
4. **Train**: Split $\to$ Train RF/GB/EN $\to$ `models/`.
5. **Evaluate**: Bootstrap $\to$ FDR $\to$ Sensitivity $\to$ `results/metrics.yaml`.
6. **Report**: Generate PDF/Markdown with SHAP, Parity Plots, and residual validation status.