# Data Model: Predicting the Yield Strength of Steel Alloys

## Overview

This document defines the data structures, transformations, and schemas used throughout the project. It ensures that the input data, engineered features, and model outputs conform to the specifications required for reproducibility and validation.

## Entities

### 1. SteelSample (Raw Input)
Represents a single alloy instance from the source data.

| Field | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `sample_id` | str | Unique identifier | Source metadata |
| `composition_C` | float | Carbon content (%) | Source |
| `composition_Mn` | float | Manganese content (%) | Source |
| `composition_Cr` | float | Chromium content (%) | Source |
| `composition_Ni` | float | Nickel content (%) | Source |
| `temp_tempering` | float | Tempering temperature (°C) | Source |
| `cooling_rate` | float | Cooling rate (°C/s) | Source |
| `holding_time` | float | Holding time (s) | Source |
| `heat_treatment_type` | str | Category (e.g., "quenching") | Source |
| `yield_strength` | float | Measured yield strength (MPa) | Source |
| `missing_flags` | dict | Boolean flags for missing values | Derived |

### 2. ProcessedSample (Engineered)
The result of the preprocessing and feature engineering pipeline.

| Field | Type | Description | Derivation |
| :--- | :--- | :--- | :--- |
| `sample_id` | str | Unique identifier | Copied |
| `comp_C` | float | Normalized Carbon (0-1) | MinMaxScaler |
| `comp_Mn` | float | Normalized Manganese (0-1) | MinMaxScaler |
| `comp_Cr` | float | Normalized Chromium (0-1) | MinMaxScaler |
| `comp_Ni` | float | Normalized Nickel (0-1) | MinMaxScaler |
| `temp_norm` | float | Normalized Temperature (0-1) | MinMaxScaler |
| `cooling_norm` | float | Normalized Cooling Rate (0-1) | MinMaxScaler |
| `time_norm` | float | Normalized Holding Time (0-1) | MinMaxScaler |
| `type_quench` | int | One-hot: Quenching (0/1) | OneHotEncoder |
| `type_temper` | int | One-hot: Tempering (0/1) | OneHotEncoder |
| `ratio_C_Mn` | float | C / Mn | Derived |
| `ratio_Cr_Ni` | float | Cr / Ni | Derived |
| `inter_C_cool_ortho` | float | Orthogonalized (C × Cooling) via GAM (k=5, cubic) | Non-Linear Orthogonalization |
| `inter_Cr_time_ortho` | float | Orthogonalized (Cr × Time) via GAM (k=5, cubic) | Non-Linear Orthogonalization |
| `inter_C_cool_raw` | float | Raw (C × Cooling) | Derived (for comparison) |
| `yield_strength` | float | Target (MPa) | Copied (filtered) |

## Transformation Pipeline

1. **Ingestion**: Load raw CSV/JSONL. Drop rows with `null` `yield_strength`.
2. **Normalization**: Apply MinMaxScaler to continuous thermal and composition features.
3. **Encoding**: One-hot encode `heat_treatment_type`.
4. **Ratio Generation**: Compute `C/Mn` and `Cr/Ni`. Handle division by zero (add epsilon).
5. **Interaction Generation**: Compute raw products (e.g., `comp_C * cooling_norm`).
6. **Non-Linear Orthogonalization**:
   - For each interaction $I = A \times B$:
   - Fit a **GAM model** with splines (**k=5, cubic**): $I \sim \text{GAM}(A, B)$.
   - Extract residuals: $I_{ortho} = I - \hat{I}$.
   - Replace $I$ with $I_{ortho}$.
7. **Validation**: Assert no nulls in target; assert all features finite.

## Data Constraints

- **Max Rows**: [deferred] (to fit 6 GB RAM).
- **Target**: `yield_strength` must be non-null.
- **Features**: All continuous features must be in [0, 1] or orthogonalized residuals.
- **Categorical**: Must be binary (0/1) after encoding.
- **Memory**: Peak RAM usage must not exceed 6 GB.

## Output Artifacts

- **`data/processed/engineered_dataset.parquet`**: The final dataset for modeling.
- **`data/results/model_metrics.json`**: R², MAE, p-values, SHAP values.
- **`data/results/pdp_plots/`**: Directory containing PDP images.

## Stability Analysis Constraints

- **Minimum Feature Count**: For stability metrics (Kuncheva index), a minimum of 5 features must be selected at each threshold. If fewer than 5 are selected, the metric is not computed, and the result is flagged as 'insufficient_data'.