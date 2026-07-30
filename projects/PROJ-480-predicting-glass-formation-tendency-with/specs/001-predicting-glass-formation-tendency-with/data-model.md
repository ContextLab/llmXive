# Data Model: Predicting Glass Formation Tendency

## Overview

This document defines the data structures used throughout the pipeline, from raw ingestion to model output. All data is stored in CSV/Parquet format under `data/` and validated against the schemas in `contracts/`.

## Entities

### CompositionRecord

Represents a single alloy sample.

| Field | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `composition` | `str` | Chemical formula (e.g., "Zr50Cu40Al10") | Raw Data |
| `target_type` | `str` | "regression" ($D_c$) or "classification" (binary) | Detected |
| `target_value` | `float` | Critical casting thickness ($D_c$) or binary label (0/1) | Raw Data |
| `atomic_size_mismatch` | `float` | $\delta$ (atomic size mismatch) | Computed |
| `mixing_enthalpy` | `float` | $\Delta H_{mix}$ (kJ/mol) | Computed |
| `electronegativity_diff` | `float` | $\Delta \chi$ (Pauling) | Computed |
| `entropy_mixing` | `float` | $\Delta S_{mix}$ (J/mol-K) | Computed (Optional) |
| `cooling_rate` | `float` | Cooling rate (K/s) | Raw Data (Optional) |
| `is_valid` | `bool` | True if all descriptors computed successfully | Pipeline |

### DescriptorSet

A collection of computed thermodynamic properties for a composition.
*Note: This is a logical grouping; data is stored flat in `CompositionRecord`.*

### ModelArtifact

The trained model and its metadata.

| Field | Type | Description |
| :--- | :--- | :--- |
| `model_type` | `str` | "XGBRegressor" or "XGBClassifier" |
| `hyperparameters` | `dict` | JSON-serializable model params |
| `feature_importances` | `dict` | Map of feature name to importance score |
| `metrics` | `dict` | R², AUC, RMSE, Accuracy, etc. |
| `vif_scores` | `dict` | Variance Inflation Factor for top features |
| `report_disclaimer` | `str` | The mandatory associational disclaimer text |

## Data Flow

1.  **Raw Data**: Downloaded CSVs from public sources (Matbench, UCI).
2.  **Preprocessed Data**: CSV with computed descriptors. Dropped rows (missing elements) are logged.
3.  **Training Data**: Split into Train/Test (80/20) or used for Group K-Fold CV.
4.  **Model Output**: Pickled model file + JSON metrics file.

## Constraints

- **Missing Values**: No null values allowed in primary predictors (`atomic_size_mismatch`, `mixing_enthalpy`, `electronegativity_diff`). Rows with nulls are dropped.
- **Target Variable**: Must be either continuous ($D_c$) or binary (0/1).
- **Sample Size**: Minimum 30 samples required for training.
- **Cooling Rate**: If available, it is used for confounding control. If missing, a warning is logged.