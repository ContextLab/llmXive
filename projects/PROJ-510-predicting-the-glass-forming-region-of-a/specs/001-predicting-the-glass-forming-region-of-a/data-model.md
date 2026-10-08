# Data Model: Predicting the Glass Forming Region of Alloy Systems with Machine Learning

## Overview
The project manipulates three core entity types that are persisted as CSV/JSON files. All artifacts are validated against schemas located in `contracts/`.

---

## Entity Definitions

| Entity | Description | Primary Fields | File(s) |
|--------|-------------|----------------|---------|
| **AlloyRecord** | One ternary alloy entry after filtering. | `composition` (str, e.g. "Fe_0.5Ni_0.3Cr_0.2")<br>`critical_cooling_rate` (float, K/s)<br>`mixing_enthalpy` (float, eV/atom)<br>`atomic_size_mismatch` (float, Å)<br>`electronegativity_variance` (float) | `data/processed/processed_alloys.csv` |
| **ModelMetrics** | Results of training, CV, and test evaluation. | `fold_scores` (list[float])<br>`mean_rmse` (float)<br>`std_rmse` (float)<br>`test_rmse` (float)<br>`dummy_rmse` (float)<br>`p_value` (float)<br>`feature_importance` (dict)<br>`permutation_p_values` (dict)<br>`oob_score` (float)<br>`learning_curve_slope` (float) | `data/models/cv_metrics.json` |
| **SensitivityReport** | Performance across CCR thresholds. | `thresholds` (list[int]) – a set of representative threshold values spanning low, medium, and high levels.<br>`rmse_at_thresholds` (list[float])<br>`rmse_variance` (float)<br>`collinearity_flags` (list[object])<br>`stability_status` (str, PASS/FAIL)<br>`top_2_features_valid` (bool) | `data/reports/sensitivity_report.json` |
| **FeatureImportance** | Permutation importance ranking. | `feature_name` (str)<br>`importance_mean` (float)<br>`importance_std` (float)<br>`p_value` (float) | `data/reports/feature_importance.csv` |

---

## Schema Files

### `contracts/processed_alloys.schema.yaml`
```yaml
$schema: "https://json-schema.org/draft/2020-12/schema"
title: "Processed Alloys"
type: object
required:
  - path
  - sha256
  - columns
  - row_count
properties:
  path:
    type: string
    const: "data/processed/processed_alloys.csv"
  sha256:
    type: string
    description: "SHA‑256 checksum of the CSV file."
  columns:
    type: array
    items:
      type: string
    enum:
      - composition
      - critical_cooling_rate
      - mixing_enthalpy
      - atomic_size_mismatch
      - electronegativity_variance
      - source_label
  row_count:
    type: integer
    minimum: 500
    description: "Number of rows after filtering; must be ≥ 500 to satisfy FR‑001."
additionalProperties: false
```

### `contracts/features.schema.yaml`
```yaml
$schema: "https://json-schema.org/draft/2020-12/schema"
title: "Alloy Feature Record"
type: object
required:
  - composition
  - critical_cooling_rate
  - mixing_enthalpy
  - atomic_size_mismatch
  - electronegativity_variance
properties:
  composition:
    type: string
    description: "Ternary composition expressed as Element1_x1Element2_x2Element3_x3"
  critical_cooling_rate:
    type: number
    description: "Measured critical cooling rate in Kelvin per second (K/s)"
    minimum: 0
  mixing_enthalpy:
    type: number
    description: "Mixing enthalpy (eV/atom) computed from OQMD elemental formation energies"
  atomic_size_mismatch:
    type: number
    description: "Root‑mean‑square deviation of atomic radii (Å) across the three elements"
  electronegativity_variance:
    type: number
    description: "Variance of Pauling electronegativity values across the three elements"
additionalProperties: false
```

### `contracts/metrics.schema.yaml`
```yaml
$schema: "https://json-schema.org/draft/2020-12/schema"
title: "Model Metrics"
type: object
required:
  - fold_scores
  - mean_rmse
  - std_rmse
  - test_rmse
  - dummy_rmse
  - p_value
  - feature_importance
  - permutation_p_values
  - oob_score
  - learning_curve_slope
properties:
  fold_scores:
    type: array
    items:
      type: number
    minItems: 5
    maxItems: 5
    description: "RMSE for each CV fold"
  mean_rmse:
    type: number
    description: "Mean RMSE across folds"
  std_rmse:
    type: number
    description: "Standard deviation of fold scores"
  test_rmse:
    type: number
    description: "RMSE on held-out test set"
  dummy_rmse:
    type: number
    description: "RMSE of dummy baseline (mean predictor)"
  p_value:
    type: number
    minimum: 0
    maximum: 1
    description: "P-value from two-sided t-test vs dummy model"
  feature_importance:
    type: object
    additionalProperties:
      type: number
    description: "Map of feature name to importance score"
  permutation_p_values:
    type: object
    additionalProperties:
      type: number
    description: "P-values from permutation test for each feature"
  oob_score:
    type: number
    description: "Out-of-bag score for overfitting check"
  learning_curve_slope:
    type: number
    description: "Slope of learning curve for overfitting check"
additionalProperties: false
```

### `contracts/feature_importance.schema.yaml`
```yaml
$schema: "https://json-schema.org/draft/2020-12/schema"
title: "Feature Importance"
type: object
required:
  - feature_name
  - importance_mean
  - importance_std
  - p_value
properties:
  feature_name:
    type: string
    description: "Name of the thermodynamic descriptor (e.g., mixing_enthalpy)."
  importance_mean:
    type: number
    description: "Mean permutation importance score."
  importance_std:
    type: number
    description: "Standard deviation of the importance scores across permutations."
  p_value:
    type: number
    minimum: 0
    maximum: 1
    description: "Empirical p‑value from the permutation test."
additionalProperties: false
```

### `contracts/sensitivity.schema.yaml`
```yaml
$schema: "https://json-schema.org/draft/2020-12/schema"
title: "Sensitivity Report"
type: object
required:
  - thresholds
  - rmse_at_thresholds
  - rmse_variance
  - collinearity_flags
  - stability_status
  - top_2_features_valid
properties:
  thresholds:
    type: array
    items:
      type: integer
    minItems: 3
    maxItems: 3
    const: [50, 100, 150]
    description: "CCR thresholds evaluated (K/s)."
  rmse_at_thresholds:
    type: array
    items:
      type: number
    minItems: 3
    maxItems: 3
    description: "RMSE corresponding to each threshold."
  rmse_variance:
    type: number
    description: "Variance of RMSE across thresholds."
  collinearity_flags:
    type: array
    items:
      type: object
      required:
        - feature_pair
        - correlation
      properties:
        feature_pair:
          type: array
          items:
            type: string
          description: "Pair of collinear features."
        correlation:
          type: number
          description: "Correlation coefficient (>0.8)."
    description: "List of flagged collinear pairs."
  stability_status:
    type: string
    enum: ["PASS", "FAIL"]
    description: "PASS if RMSE variance < 5 % of mean RMSE."
  top_2_features_valid:
    type: boolean
    description: "True if the top‑2 features have p < 0.05."
additionalProperties: false
```

### `contracts/model_output.schema.yaml`
```yaml
$schema: "https://json-schema.org/draft/2020-12/schema"
title: "ModelOutput"
description: "Artifacts produced after training and evaluation."
type: object
properties:
  model_path:
    type: string
    const: "data/models/random_forest_model.pkl"
  cv_metrics_path:
    type: string
    const: "data/models/cv_metrics.json"
  feature_importance_path:
    type: string
    const: "data/reports/feature_importance.csv"
  sensitivity_report_path:
    type: string
    const: "data/reports/sensitivity_report.json"
  model_sha256:
    type: string
    description: "SHA‑256 checksum of the serialized model."
required:
  - model_path
  - cv_metrics_path
  - feature_importance_path
  - sensitivity_report_path
  - model_sha256
additionalProperties: false
```
