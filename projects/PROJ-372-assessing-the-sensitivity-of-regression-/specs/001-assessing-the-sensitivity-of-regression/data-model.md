# Data Model: Assessing the Sensitivity of Regression Coefficients to Dataset Subset Selection

## Overview
This document defines the data structures for ingestion, resampling, and analysis artifacts. All models are serialized to JSON/Parquet for reproducibility.

## 1. DatasetProfile

Represents the violation profile of a full dataset.

```yaml
type: object
properties:
  dataset_id:
    type: string
    description: "Unique identifier for the dataset (e.g., URL hash or name)"
  source_url:
    type: string
    description: "Verified URL of the source dataset"
  n_rows:
    type: integer
    description: "Total number of rows in the dataset"
  n_features:
    type: integer
    description: "Number of features used in OLS"
  violation_metrics:
    type: object
    properties:
      condition_number:
        type: number
        format: double
        description: "Condition number of X'X (Full Dataset)"
      breusch_pagan_statistic:
        type: number
        format: double
        description: "BP test statistic (Full Dataset)"
      breusch_pagan_p_value:
        type: number
        format: double
        description: "BP test p-value (Full Dataset)"
      mean_cooks_distance:
        type: number
        format: double
        description: "Average Cook's Distance (Full Dataset)"
  severity_classification:
    type: string
    enum: ["Low", "Medium", "High"]
    description: "Based on BP p-value thresholds"
  timestamp:
    type: string
    format: date-time
    description: "ISO 8601 timestamp of profiling"
required:
  - dataset_id
  - source_url
  - n_rows
  - n_features
  - violation_metrics
  - severity_classification
```

## 2. StabilityResult

Represents the OLS coefficient statistics for a single subset or tier aggregation.

```yaml
type: object
properties:
  dataset_id:
    type: string
  tier_percentage:
    type: integer
    enum: [10, 25, 50, 75, 90]
    description: "Sample size tier"
  subset_id:
    type: integer
    description: "Unique ID for the subset (1-200)"
  n_samples:
    type: integer
    description: "Actual number of samples in subset"
  coefficients:
    type: object
    description: "Map of feature_name -> coefficient_value"
    additionalProperties:
      type: number
      format: double
  standard_errors:
    type: object
    description: "Map of feature_name -> standard_error_value"
    additionalProperties:
      type: number
      format: double
  r_squared:
    type: number
    format: double
  subset_violation_metrics:
    type: object
    description: "Violation metrics computed PER SUBSET"
    properties:
      condition_number:
        type: number
        format: double
        description: "Condition number of X'X (Subset)"
      breusch_pagan_p_value:
        type: number
        format: double
        description: "BP test p-value (Subset)"
      mean_cooks_distance:
        type: number
        format: double
        description: "Average Cook's Distance (Subset)"
  timestamp:
    type: string
    format: date-time
required:
  - dataset_id
  - tier_percentage
  - subset_id
  - coefficients
  - standard_errors
  - subset_violation_metrics
```

## 3. MetaAnalysisResult

Aggregated results of the meta-analysis regression.

```yaml
type: object
properties:
  dataset_id:
    type: string
  feature_name:
    type: string
    description: "The specific coefficient being analyzed"
  model_summary:
    type: object
    properties:
      r_squared:
        type: number
      adj_r_squared:
        type: number
      f_statistic:
        type: number
      p_value_f:
        type: number
    required:
      - r_squared
      - f_statistic
  coefficients:
    type: object
    description: "Regression coefficients: Intercept, log(N), Subset_CondNum, Subset_BP_p, Subset_Cooks_D, Interactions, Random Effects"
    properties:
      intercept:
        type: number
      log_n_coef:
        type: number
        description: "Coefficient for log(N) (sample size control)"
      condition_number_coef:
        type: number
        description: "Coefficient for Subset_CondNum"
      bp_p_coef:
        type: number
        description: "Coefficient for Subset_BP_p"
      cooks_d_coef:
        type: number
        description: "Coefficient for Subset_Cooks_D"
      interaction_cond_bp_coef:
        type: number
        description: "Interaction term: CondNum × BP"
      interaction_cond_cooks_coef:
        type: number
        description: "Interaction term: CondNum × Cooks"
      random_intercept:
        type: number
        description: "Random intercept for Dataset ID (Full Dataset baseline)"
    required:
      - intercept
      - log_n_coef
      - condition_number_coef
      - bp_p_coef
      - cooks_d_coef
  convergence_status:
    type: string
    enum: ["Converged", "Invalid"]
    description: "Based on Bootstrap SE of SD < 5% (Invalid if not met)"
  se_of_sd:
    type: number
    format: double
    description: "Standard Error of the standard deviation (Bootstrap derived)"
  sd_of_coef:
    type: number
    format: double
    description: "Empirical standard deviation of the coefficient"
required:
  - dataset_id
  - feature_name
  - model_summary
  - coefficients
  - convergence_status
  - se_of_sd
  - sd_of_coef
```

## 4. VisualizationMetadata

Metadata for generated stability curves.

```yaml
type: object
properties:
  dataset_id:
    type: string
  feature_name:
    type: string
  curve_type:
    type: string
    enum: ["Stability Curve (SD vs Subset CondNum)", "Stability Curve (SD vs Severity)"]
  data_points:
    type: array
    description: "List of (X, Y) points for the curve"
    items:
      type: object
      properties:
        x:
          type: number
          description: "Subset Condition Number"
        y:
          type: number
          description: "Coefficient SD"
        severity:
          type: string
          description: "Severity classification based on Full Dataset"
      required:
        - x
        - y
required:
  - dataset_id
  - feature_name
  - curve_type
  - data_points
```