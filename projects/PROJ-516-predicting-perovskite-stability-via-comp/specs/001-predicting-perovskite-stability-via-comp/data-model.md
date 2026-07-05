# Data Model: Predicting Perovskite Stability via Compositional Fingerprints

## Entity Definitions

### PerovskiteEntry
A single record representing a perovskite composition and its thermal stability.

| Attribute | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `formula` | string | Chemical formula (e.g., "FAPbI3") | Raw Data |
| `source_db` | string | "NREL", "MaterialsProject", or "Literature" | Raw Data |
| `T_d` | float | Decomposition temperature (°C) | Raw Data (TGA) |
| `T_d_uncertainty` | float | Measurement uncertainty (°C) | Raw Data (default 10.0) |
| `family` | string | "lead-halide", "tin-halide", "double", "other" | Derived (via formula parsing) |
| `instrument_type` | string | "TGA", "DSC", etc. | Raw Data (Filtering) |

### CompositionalDescriptor
A feature vector derived from a `PerovskiteEntry`.

| Attribute | Type | Description | Formula/Logic |
| :--- | :--- | :--- | :--- |
| `formula` | string | Reference to source entry | |
| `atomic_fraction_A` | float | Fraction of A-site elements | $\sum f_A$ |
| `atomic_fraction_B` | float | Fraction of B-site elements | $\sum f_B$ |
| `atomic_fraction_X` | float | Fraction of X-site elements | $\sum f_X$ |
| `weighted_ionic_radius` | float | Mean ionic radius | $\sum f_i r_i$ |
| `weighted_electronegativity` | float | Mean electronegativity | $\sum f_i \chi_i$ |
| `weighted_formation_enthalpy` | float | Mean formation enthalpy | $\sum f_i \Delta H_f$ |
| `weighted_ionization_energy` | float | Mean first ionization energy | $\sum f_i I_i$ (FR-002) |
| `variance_ionic_radius` | float | Variance of ionic radius | $\text{Var}(r)$ |
| `variance_electronegativity` | float | Variance of electronegativity | $\text{Var}(\chi)$ |
| `variance_ionization_energy` | float | Variance of ionization energy | $\text{Var}(I)$ |
| `vif_score` | float | Variance Inflation Factor | Computed via `statsmodels` |
| `is_excluded` | boolean | Flag for exclusion (missing data) | Logic: `missing_count >= 2` |

### ModelRun
A record of a training experiment.

| Attribute | Type | Description |
| :--- | :--- | :--- |
| `model_type` | string | "RandomForest", "GradientBoosting", "ElasticNet" |
| `hyperparams` | json | Dictionary of hyperparameters |
| `cv_r2_mean` | float | Mean R² across folds |
| `cv_rmse_mean` | float | Mean RMSE across folds |
| `cv_mae_mean` | float | Mean MAE across folds |
| `feature_importance` | json | Map of feature name to importance score |
| `runtime_seconds` | float | Execution time |

## Data Flow

1. **Raw Data** (JSON) → `data/raw/` (Checksummed).
2. **Ingestion Script** → Filters for $T_d$ (experimental TGA), computes `CompositionalDescriptor` using `pymatgen` for family assignment.
3. **Processed Data** → `data/processed/descriptors.csv` (Checksummed).
4. **Training Script** → Reads processed data, trains models, outputs `ModelRun` records.
5. **Validation Script** → Reads `ModelRun`, computes SHAP, external metrics.
6. **State Manager** → Updates `state/...yaml` with hashes of processed artifacts.

## Constraints

- **Missing Values**: Entries with ≥2 missing descriptors are excluded.
- **Collinearity**: Descriptors with VIF > 5 trigger automatic removal of the highest VIF feature or switch to Elastic Net.
- **Schema Compliance**: All derived data must match the `contracts/descriptor.schema.yaml`.
- **Family Assignment**: Deterministic via `pymatgen` parsing. If B-site has two distinct elements, family = 'double'.