# Data Model: Assessing Uncertainty Quantification Techniques for Machine‑Learning Predicted Material Properties

## 1. Overview
This document defines the data structures used throughout the pipeline, from raw ingestion to final UQ predictions and evaluation metrics. All data is stored in CSV or JSON format, with strict schema validation via YAML contracts.

## 2. Entity Definitions

### 2.1 MaterialSample
Represents a single inorganic compound from the dataset.

| Field | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `material_id` | string | Unique identifier from Materials Project | Required |
| `composition` | object | Element fractions (e.g., `{"Fe": 0.5, "O": 0.5}`) | Required |
| `structural_features` | object | Descriptors (packing, radius, etc.) | Required |
| `formation_energy` | float | Target property 1 | Required (no nulls) |
| `bulk_modulus` | float | Target property 2 | Optional |
| `band_gap` | float | Target property 3 | Optional |
| `is_stable` | boolean | Derived from formation energy threshold | Calculated |

### 2.2 UQPrediction
Output of a UQ method for a single sample.

| Field | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `material_id` | string | Reference to MaterialSample | Required |
| `method` | string | "deep_ensemble", "mc_dropout", "sparse_gp" | Enum |
| `prediction` | float | Point estimate (mean) | Required |
| `variance` | float | Predictive variance | Required |
| `lower_50` | float | Lower bound of 50% CI | Required |
| `upper_50` | float | Upper bound of 50% CI | Required |
| `lower_90` | float | Lower bound of 90% CI | Required |
| `upper_90` | float | Upper bound of 90% CI | Required |
| `uncertainty_type` | string | "aleatoric", "epistemic", or "total" | Required |

### 2.3 CalibrationMetric
Aggregated evaluation results.

| Field | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `method` | string | Method name | Required |
| `confidence_level` | float | 0.5 or 0.9 | Required |
| `ece` | float | Expected Calibration Error | Required |
| `interval_score` | float | Proper interval score | Required |
| `sharpness` | float | Mean interval width | Required |
| `coverage` | float | Empirical coverage percentage | Required |

### 2.4 ScreeningResult
Results of the downstream screening task.

| Field | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `method` | string | Method used for filtering | Required |
| `recall_target` | float | Target recall (e.g., 0.9) | Required |
| `precision` | float | Achieved precision | Required |
| `num_selected` | int | Number of candidates selected | Required |
| `num_true_stable` | int | True stable candidates in selected | Required |

## 3. Data Flow
1.  **Ingestion**: `Materials Project` -> `MaterialSample` (filtered for nulls).
2.  **Training**: `MaterialSample` -> `Baseline Model` -> `UQPrediction` (per method).
3.  **Evaluation**: `UQPrediction` + `MaterialSample` (targets) -> `CalibrationMetric`.
4.  **Screening**: `UQPrediction` -> `ScreeningResult`.

## 4. Validation Rules
- **Null Handling**: Any `MaterialSample` with null `formation_energy` is excluded and logged.
- **Range Checks**: `lower_50` < `prediction` < `upper_50`.
- **Enum Checks**: `method` must be one of the three defined techniques.
- **Consistency**: `CalibrationMetric` must exist for every method and confidence level.
