# Data Model: Predicting the Yield Strength of BCC Steels from Density Functional Theory

## 1. Entity Overview
| Entity | Description | Primary Key |
|--------|-------------|-------------|
| **ExperimentalRecord** | Raw experimental entry (composition + optional yield strength). | `formula` |
| **DFTRecord** | DFT elastic constants fetched from Materials Project. | `material_id` |
| **UnifiedRecord** | Merged, filtered row used for modeling. | `formula` |

## 2. Schema Definitions

### 2.1 `dataset.schema.yaml` (merged dataset)
```yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "Unified BCC Steel Dataset Schema"
description: "Schema for the merged dataset containing experimental yield strength and DFT descriptors."
type: "object"
properties:
  formula:
    type: "string"
    description: "Chemical formula of the alloy (e.g., Fe0.95Cr0.05)."
  yield_strength_MPa:
    type: "number"
    description: "Experimental yield strength in MPa."
    minimum: 0
  shear_modulus_GPa:
    type: "number"
    description: "DFT Shear Modulus in GPa."
    minimum: 0
  bulk_modulus_GPa:
    type: "number"
    description: "DFT Bulk Modulus in GPa."
    minimum: 0
  space_group:
    type: "integer"
    description: "Crystal space group number (must correspond to the BCC structure)."
    enum:
      - 229
  element_fractions:
    type: "object"
    description: "Map of elemental fractions."
    additionalProperties:
      type: "number"
      minimum: 0
      maximum: 1
  uncertainty_flag:
    type: "boolean"
    description: "True if the original yield strength was a range."
  # Optional experimental covariates (may be absent)
  testing_temperature_C:
    type: "number"
    description: "Testing temperature in Celsius."
  strain_rate_s^-1:
    type: "number"
    description: "Strain rate during the test (1/s)."
  heat_treatment:
    type: "string"
    description: "Heat‑treatment descriptor (e.g., 'annealed')."
required:
  - formula
  - yield_strength_MPa
  - shear_modulus_GPa
  - bulk_modulus_GPa
  - space_group
  - element_fractions
  - uncertainty_flag
additionalProperties: false
```

### 2.2 `output.schema.yaml` (final results)
```yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "Model Output Schema"
description: "Schema for the final metrics and analysis results."
type: "object"
properties:
  metrics:
    type: "object"
    description: "Performance metrics for both models."
    properties:
      r2_rf:
        type: "number"
        description: "R-squared for the Random Forest with DFT features."
      mae_rf:
        type: "number"
        description: "Mean Absolute Error for the Random Forest with DFT features."
      r2_baseline:
        type: "number"
        description: "R-squared for the composition-only baseline."
      mae_baseline:
        type: "number"
        description: "Mean Absolute Error for the composition-only baseline."
      p_value:
        type: "number"
        description: "P-value from the paired **t-test** (not Wilcoxon)."
      power:
        type: "number"
        description: "Statistical power (1 - β) of the test."
      null_hypothesis:
        type: "string"
        description: "Statement of the null hypothesis."
    required:
      - r2_rf
      - mae_rf
      - r2_baseline
      - mae_baseline
      - p_value
      - power
      - null_hypothesis
  correlation_analysis:
    type: "object"
    description: "Pearson correlation between shear modulus and yield strength."
    properties:
      r_value:
        type: "number"
      p_value:
        type: "number"
      confidence_interval_95:
        type: "array"
        items:
          type: "number"
    required:
      - r_value
      - p_value
      - confidence_interval_95
  feature_importance:
    type: "object"
    description: "Top‑5 SHAP features and permutation importance statistics."
    properties:
      top_5_shap:
        type: "array"
        description: "Top 5 features by mean absolute SHAP value."
        items:
          type: "object"
          properties:
            feature:
              type: "string"
            importance:
              type: "number"
          required:
            - feature
            - importance
      permutation_std:
        type: "array"
        description: "Standard deviation of permutation importance across 10 bootstraps."
        items:
          type: "object"
          properties:
            feature:
              type: "string"
            std_dev:
              type: "number"
          required:
            - feature
            - std_dev
    required:
      - top_5_shap
      - permutation_std
  stability_analysis:
    type: "object"
    description: "Bootstrap stability metrics."
    properties:
      sample_sizes:
        type: "array"
        description: "Sample sizes tested (full dataset with replacement)."
        items:
          type: "integer"
      std_dev_dft_descriptors:
        type: "array"
        description: "Standard deviation of importance for DFT descriptors."
        items:
          type: "number"
      is_stable:
        type: "boolean"
        description: "True if std_dev < 0.05 for key DFT descriptors."
    required:
      - sample_sizes
      - std_dev_dft_descriptors
      - is_stable
  multicollinearity:
    type: "object"
    description: "Variance Inflation Factor (VIF) scores for features."
    properties:
      vif_scores:
        type: "object"
        additionalProperties:
          type: "number"
        description: "VIF score for each feature."
      max_vif:
        type: "number"
        description: "Maximum VIF observed."
    required:
      - vif_scores
      - max_vif
  data_validation:
    type: "object"
    description: "Data validation results."
    properties:
      row_count:
        type: "integer"
        description: "Total number of valid rows in the merged dataset."
      min_threshold_met:
        type: "boolean"
        description: "True if row_count ≥ 20."
    required:
      - row_count
      - min_threshold_met
required:
  - metrics
  - correlation_analysis
  - feature_importance
  - stability_analysis
  - multicollinearity
  - data_validation
additionalProperties: false
```

## 3. Data Flow Diagram (Logical)
1. **Raw download** → `data/raw/experimental.csv` (experimental)  
2. **API query** → per‑formula JSON files in `data/raw/dft/`  
3. **Merge & filter** → `data/intermediate/merged.csv` (validated against `dataset.schema.yaml`)  
4. **Feature engineering** → `data/processed/features.npy` (numpy array)  
5. **Model training & evaluation** → `data/results/output.json` (validated against `output.schema.yaml`)  
6. **Plots** → `data/results/plots/` (PNG files referenced only in the paper).

---

