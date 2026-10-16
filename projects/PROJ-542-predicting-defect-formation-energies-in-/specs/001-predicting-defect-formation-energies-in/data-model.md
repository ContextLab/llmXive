# Data Model: Predicting Defect Formation Energies in Perovskites with Machine Learning

## Overview
The project manipulates six primary data artefacts:

| Artefact | Description | Location | Format |
|----------|-------------|----------|--------|
| **Raw defect dataset** | Original perovskite compositions with DFT oxygen‑vacancy formation energies (and optional metadata). | `data/raw/materials_defects.csv` | CSV |
| **Engineered feature matrix** | 12–13 compositional descriptors (including optional tolerance factor) + target energy, one row per composition. | `data/processed/features.csv` | CSV |
| **Cross‑validation metrics** | Summary statistics (mean ± std) for each model across 5 folds. | `data/processed/cv_metrics.json` | JSON |
| **Model performance report** | JSON containing CV metrics for each model, held‑out test metrics, bootstrap CI, t‑test result, and feature‑importance list. | `data/processed/performance.json` | JSON |
| **Final figures** | Scatter plot of predictions vs. actual energies and bar chart of feature importances. | `figures/` (PNG files) | PNG |
| **Checksums** | SHA‑256 checksums for raw and derived files to ensure data hygiene. | `data/checksums/` | TXT |

## Schema Definitions

### `contracts/raw_dataset.schema.yaml`
```yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "Raw Defect Dataset"
type: object
required:
  - composition
  - defect_type
  - formation_energy
properties:
  composition:
    type: string
    description: "Perovskite formula in standard notation (e.g., 'BaTiO3')."
  defect_type:
    type: string
    enum: ["oxygen_vacancy"]
    description: "Type of defect; only 'oxygen_vacancy' is supported."
  formation_energy:
    type: number
    description: "DFT‑computed defect formation energy in eV."
  metadata:
    type: object
    description: "Optional additional fields (e.g., Materials Project ID)."
additionalProperties: false
```

### `contracts/model_performance.schema.yaml`
```yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "Model Performance Report"
type: object
required:
  - cv_metrics
  - test_metrics
  - bootstrap_ci
  - paired_ttest
  - feature_importances
properties:
  cv_metrics:
    type: object
    description: "Cross‑validation summary for each model."
    patternProperties:
      "^(RandomForest|GradientBoosting)$":
        type: object
        required:
          - rmse_mean
          - rmse_std
          - mae_mean
          - mae_std
          - r2_mean
          - r2_std
        properties:
          rmse_mean:
            type: number
          rmse_std:
            type: number
          mae_mean:
            type: number
          mae_std:
            type: number
          r2_mean:
            type: number
          r2_std:
            type: number
  test_metrics:
    type: object
    required:
      - model_name
      - rmse
      - mae
      - r2
    properties:
      model_name:
        type: string
      rmse:
        type: number
      mae:
        type: number
      r2:
        type: number
  bootstrap_ci:
    type: object
    required:
      - rmse_lower
      - rmse_upper
      - confidence
    properties:
      rmse_lower:
        type: number
      rmse_upper:
        type: number
      confidence:
        type: number
        description: "Confidence level (e.g., 0.95)."
  paired_ttest:
    type: object
    required:
      - t_statistic
      - p_value
      - alpha
    properties:
      t_statistic:
        type: number
      p_value:
        type: number
      alpha:
        type: number
        description: "Significance threshold (0.05)."
  feature_importances:
    type: array
    description: "Sorted list of descriptor importance objects."
    items:
      type: object
      required:
        - feature
        - importance
      properties:
        feature:
          type: string
          description: "Descriptor name (e.g., 'A_radius')."
        importance:
          type: number
          description: "Relative importance (normalized to sum = 1)."
additionalProperties: false
```

## Data Flow Diagram (textual)
```
raw CSV -> download.py (optional) -> checksum -> raw_dataset.schema.yaml validation
raw CSV -> featurize.py (pymatgen) -> features.csv -> raw_dataset.schema.yaml (target) + feature matrix validation
features.csv -> train.py (Stratified CV) -> cv_metrics.json
features.csv (train/test split) -> evaluate.py -> performance.json (model_performance.schema.yaml)
performance.json + figures -> pipeline.ipynb -> final report
```

---



