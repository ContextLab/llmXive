# Data Model: Unveiling Hidden Correlations Between Processing Parameters and Mechanical Properties in Additively Manufactured Alloys

## Overview
This document defines the data schemas, transformations, and model artifacts required for the feature. It ensures the "Single Source of Truth" (Constitution Principle IV) and "Data Hygiene" (Constitution Principle III).

## Data Entities

### 1. Raw Dataset Record
A single row from the input CSV.
- **Source**: User-provided CSV or verified HuggingFace dataset.
- **Constraints**: Must contain at least 50 rows.
- **Required Columns**: `laser_power`, `scan_speed`, `layer_thickness`, `yield_strength`.
- **Optional Columns**: `ductility`, `fatigue_life`, `alloy_type`, `porosity`.

### 2. Processed Dataset Record
Output of `preprocess.py`.
- **Transformation**:
  - Missing values: Imputed with column median.
  - Numeric features: Min-Max Normalized to a standardized unit interval.
  - Categorical features: One-Hot Encoded (e.g., `is_Ti-6Al-4V`).
  - Zero-variance columns: Removed.
  - **Collinearity Handling**: If VIF > 5, `laser_power` and `scan_speed` are replaced by `energy_density` (Power/Speed).
- **Output Format**: CSV.

### 3. Model Artifact
Serialized GPR model.
- **Format**: `pickle` or `joblib`.
- **Contents**:
  - Trained hyperparameters (`theta`, `sigma_f`, `l`).
  - Training data reference (or path).
  - Performance metrics (R², RMSE).
- **Location**: `code/models/gpr_model.joblib`.

### 4. Results Artifact
JSON file containing metrics and analysis.
- **Fields**:
  - `r2_score`: float.
  - `rmse`: float.
  - `rmse_percentage_of_range`: float.
  - `mae`: float.
  - `high_uncertainty_percentage`: float (percentage of test points with σ > 2× median σ).
  - `permutation_importance`: dict (feature name -> score).
  - `runtime_seconds`: float (total runtime).
  - `baseline_r2`: float (R² of linear baseline).
  - `null_result_flag`: boolean (True if GPR not significantly better than baseline).

### 5. Uncertainty Flags Artifact
JSON file listing high-uncertainty regions.
- **Fields**:
  - `regions`: list of objects with `x`, `y`, `sigma` values.
  - `threshold`: float (2× median σ).

## Transformation Pipeline

1.  **Ingestion**: Load raw CSV. Validate columns.
2.  **Validation**: Check for N >= 50. Check for required columns.
3.  **Source Independence Check**: Verify `source_independence_log.txt` exists if data is user-provided.
4.  **Cleaning**:
    - Identify missing values.
    - Impute with median.
    - Detect zero-variance columns -> Remove.
5.  **Collinearity Check**: Calculate VIF. If VIF > 5, construct `energy_density`.
6.  **Encoding**:
    - One-hot encode `alloy_type`.
    - Drop original categorical column.
7.  **Normalization**:
    - Min-Max scale numeric features to [0, 1].
8.  **Split**:
    - Train/Test split (80/20) with `random_state=42`.
9.  **Modeling**:
    - Train GPR on Train set (or Sparse GPR if N>500).
    - Train Linear Baseline on Train set.
    - Predict on Test set.
10. **Evaluation**:
    - Calculate metrics.
    - Calculate uncertainty (σ).
    - Identify high-uncertainty regions and write to `uncertainty_flags.json`.

## Schema Definitions

See `contracts/dataset.schema.yaml` and `contracts/model_output.schema.yaml` for strict validation rules.
