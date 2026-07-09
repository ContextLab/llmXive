# Data Model: Predicting Plant Drought Tolerance from RSA Data

## Overview

This document defines the data structures, schemas, and relationships used in the pipeline. All data is stored in CSV or Parquet formats for reproducibility and ease of inspection.

## Entity Definitions

### 1. RootImage
Raw image file or reference to a root system.
- **Attributes**: `image_id`, `file_path`, `species_name`, `source_dataset` (NPPN/MGB3), `checksum`.

### 2. RSAMetrics
Quantitative traits extracted from `RootImage`.
- **Attributes**: `image_id`, `depth_px`, `branching_density`, `surface_area_px`, `total_length_px`, `extraction_timestamp`, `extraction_status` (success/failed).

### 3. PhysioTrait
Physiological measurements from the TRY database.
- **Attributes**: `species_name`, `stomatal_conductance`, `photosynthetic_rate`, `water_stress_level`, `measurement_condition` (stressed/optimal), `source_reference`.

### 4. MergedDataset
The joined dataset used for analysis.
- **Attributes**: `image_id`, `species_name`, `depth_px`, `branching_density`, `surface_area_px`, `stomatal_conductance`, `photosynthetic_rate`, `drought_tolerance_class` (High/Low, **only if independent proxy exists**), `phylogenetic_eigenvectors` (if PVR used).

### 5. ModelResult
Outputs from statistical models.
- **Attributes**: `model_type`, `metric_name` (e.g., "depth"), `coefficient`, `p_value`, `adjusted_p_value`, `r_squared`, `f1_score`, `vif_score`, `cross_validation_score`.

### 6. SensitivityFPR_FNR
Results of the sensitivity analysis sweep.
- **Attributes**: `threshold`, `fpr`, `fnr`, `accuracy`, `f1_score`.

## Data Flow

1. **Ingestion**: `RootImage` files downloaded from NPPN (via MGB3 verified URL).
2. **Extraction**: `extract_rsa.py` processes images -> `RSAMetrics` CSV.
3. **Enrichment**: `PhysioTrait` downloaded from TRY.
4. **Merging**: `merge_data.py` joins `RSAMetrics` and `PhysioTrait` on `species_name`.
5. **Transformation**: PCA applied to RSA metrics; PGLS/PVR applied for phylogenetic correction.
6. **Analysis**: Regression/Classification models trained; Sensitivity analysis performed.
7. **Output**: `ModelResult` artifacts and final reports.

## Constraints & Validation

- **Non-Negative Values**: RSA metrics (depth, area) must be >= 0.
- **Missing Data**: Rows with missing `stomatal_conductance` or `photosynthetic_rate` are excluded.
- **Collinearity**: If VIF > 5 for any predictor, the model output must flag this and suppress independent effect claims.
- **Phylogenetic Correction**: If PGLS fails, the `ModelResult` must include a `correction_method` field set to "PVR" or "None" with a warning.
- **Classification Conditionality**: `drought_tolerance_class` is null if no independent proxy is found.
- **Sensitivity Output**: `results/sensitivity_fpr_fnr.csv` must contain FPR and FNR columns.