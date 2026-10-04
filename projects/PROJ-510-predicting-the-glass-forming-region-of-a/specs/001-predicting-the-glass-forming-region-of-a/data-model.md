# Data Model: Predicting the Glass Forming Region

## Data Entities

### 1. AlloyRecord (Processed)
Represents a single ternary alloy entry with engineered features.
- **Attributes**:
  - `composition`: String (e.g., "Zr50Cu30Al20")
  - `elements`: List[str] (e.g., ["Zr", "Cu", "Al"])
  - `fractions`: List[float] (e.g., [0.5, 0.3, 0.2])
  - `critical_cooling_rate`: Float (Target, K/s)
  - `mixing_enthalpy`: Float (kJ/mol)
  - `atomic_size_mismatch`: Float (dimensionless)
  - `electronegativity_variance`: Float (dimensionless)
  - `source_label`: String (e.g., "Zenodo", "Figshare")
  - `exclusion_reason`: String (if filtered out, null otherwise)

### 2. ModelMetrics
Output of the training pipeline.
- **Attributes**:
  - `fold_scores`: List[float] (RMSE for each of 5 folds)
  - `mean_rmse`: Float
  - `std_rmse`: Float
  - `test_rmse`: Float (Held-out set)
  - `dummy_rmse`: Float (Baseline)
  - `p_value`: Float (From two-sided t-test vs dummy)
  - `oob_score`: Float (Out-of-bag score)
  - `learning_curve_slope`: Float (Slope of learning curve)
  - `feature_importance`: Dict[str, float]
  - `permutation_p_values`: Dict[str, float]

### 3. SensitivityReport
Output of the threshold/collinearity analysis.
- **Attributes**:
  - `threshold_values`: List[float] (50, 100, 150)
  - `rmse_at_thresholds`: List[float]
  - `collinearity_flags`: List[Dict] (feature pairs, correlation)
  - `stability_status`: String ("PASS" if variance < 5% of mean, else "FAIL")
  - `top_2_features_valid`: Boolean (True if top-2 have p < 0.05)

## Data Flow

1.  **Raw Input**: `data/raw/bmg_ccr.csv` (Downloaded from Zenodo/Figshare).
2.  **Filtering**: Rows with missing `critical_cooling_rate` or non-ternary compositions are excluded. Logs written to `data/logs/exclusion_log.txt`.
3.  **Feature Engineering**: `features.py` computes descriptors. Output: `data/processed/processed_alloys.csv`.
4.  **Modeling**: `train.py` consumes processed CSV. Output: `data/models/random_forest_model.pkl`, `data/models/cv_metrics.json`.
5.  **Analysis**: `analyze.py` consumes model and metrics. Output: `data/models/sensitivity_report.json`.

## Integrity Constraints

- **No Missing Values**: `critical_cooling_rate` must be non-null for inclusion.
- **Ternary Only**: Exactly 3 elements per composition.
- **Positive CCR**: `critical_cooling_rate` > 0.
- **Checksum**: `data/processed/processed_alloys.csv` must match stored SHA-256 in `data/logs/ingestion_hash.txt`.