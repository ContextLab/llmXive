# Data Model: Predicting the Glass Forming Region of Alloy Systems with Machine Learning

## Entity Definitions

### AlloyRecord
Represents a single ternary alloy entry after feature engineering.

| Attribute | Type | Description | Source/Calculation |
|-----------|------|-------------|--------------------|
| `composition` | string | Alloy formula (e.g., "Zr50Cu30Ni20") | Raw Data |
| `element_a` | string | First element symbol | Parsed |
| `element_b` | string | Second element symbol | Parsed |
| `element_c` | string | Third element symbol | Parsed |
| `fraction_a` | float | Atomic fraction of A | Parsed |
| `fraction_b` | float | Atomic fraction of B | Parsed |
| `fraction_c` | float | Atomic fraction of C | Parsed |
| `critical_cooling_rate` | float | Target variable (K/s) | Raw Data (MatsSci-Glass) |
| `mixing_enthalpy` | float | Thermodynamic descriptor (kJ/mol) | Calculated |
| `atomic_size_mismatch` | float | Thermodynamic descriptor (dimensionless) | Calculated |
| `electronegativity_variance` | float | Thermodynamic descriptor (dimensionless) | Calculated |
| `source_label` | string | Source identifier | Raw Data |

### ModelMetrics
Output of the training and validation process.

| Attribute | Type | Description |
|-----------|------|-------------|
| `fold_scores` | list[float] | RMSE for each of the 5 folds |
| `mean_rmse` | float | Average RMSE across folds |
| `test_rmse` | float | RMSE on the held-out test set |
| `feature_importance_ranking` | list[tuple] | (feature_name, importance_score) sorted descending |
| `null_model_rmse` | float | RMSE of the dummy regressor (mean prediction) |
| `p_value_null` | float | P-value from permutation test comparing model to null |

### SensitivityReport
Output of the threshold and collinearity analysis.

| Attribute | Type | Description |
|-----------|------|-------------|
| `threshold_values` | list[float] | Swept thresholds (e.g., [50, 100, 150]) |
| `rmse_variance` | float | Variance of RMSE across thresholds |
| `collinearity_flags` | list[tuple] | (feature1, feature2, correlation) for |r| > 0.8 |
| `stability_check` | bool | True if model re-run (excluding collinear) yields similar RMSE |

## Data Flow

1.  **Ingestion**: Raw CSV (MatsSci-Glass) -> `data/raw/matsci_glass.csv` (checksummed).
2.  **Cleaning**: Filter for ternary alloys, drop rows with missing CCR or elemental data -> `data/processed/cleaned_alloys.csv`.
3.  **Feature Engineering**: Apply thermodynamic formulas -> `data/processed/featurized_alloys.csv`.
4.  **Modeling**: Train/Validate -> `data/outputs/model_metrics.json`.
5.  **Analysis**: Sensitivity/Importance -> `data/outputs/sensitivity_report.json`.

## Constraints

- **Missing Data**: Rows with missing `critical_cooling_rate` or elemental data are excluded.
- **Zero Enthalpy**: Treated as valid (0.0).
- **Collinearity**: If |r| > 0.8, one feature is excluded for stability check; both are reported in the flag.