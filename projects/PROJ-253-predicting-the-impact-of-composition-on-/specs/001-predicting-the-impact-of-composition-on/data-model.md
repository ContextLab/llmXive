# Data Model: Predicting the Impact of Composition on the Band Gap of Perovskite Materials

## Overview
The pipeline produces three primary artefacts that constitute the project's data model:

1. **Raw DFT dataset** – untouched parquet files downloaded from the verified sources.
2. **Processed perovskite feature table** – CSV with one row per material, containing the original formula, filtered DFT band gap, and all computed compositional descriptors.
3. **Model artefacts & evaluation summary** – serialized scikit‑learn models, scaler parameters, and a JSON summary of all metrics.

All artefacts are immutable once written; new versions receive a SHA‑256 hash suffix.

## Schema Definitions

### 1. `processed_perovskite_features.csv`
| Column | Type | Description | Required |
|--------|------|-------------|----------|
| `formula` | string | Chemical formula (e.g., `CsPbI3`). Must match ABX₃ stoichiometry. | ✔ |
| `dft_band_gap_eV` | float | DFT‑calculated band gap (eV). Must satisfy `0 < value < 6`. | ✔ |
| `mean_electronegativity` | float | Mean Pauling electronegativity of constituent elements. | ✔ |
| `var_electronegativity` | float | Variance of electronegativity across elements. | ✔ |
| `mean_atomic_radius` | float | Mean atomic radius (pm). | ✔ |
| `var_atomic_radius` | float | Variance of atomic radius. | ✔ |
| `mean_ionization_energy` | float | Mean first ionization energy (eV). | ✔ |
| `var_ionization_energy` | float | Variance of ionization energy. | ✔ |
| `oxidation_state_variance` | float | Variance of the most‑common oxidation states per element. | ✔ |
| `goldschmidt_tolerance_factor` | float | Calculated tolerance factor (unitless). | ✔ |
| `octahedral_factor` | float | Calculated octahedral factor (unitless). | ✔ |
| `lead_free` | boolean | `True` if formula contains no `Pb`; otherwise `False`. | ✔ |
| `source` | string | Identifier of the original raw dataset (`dft23-full`, `dftest61523`, …). | ✔ |
| `checksum` | string | SHA‑256 hash of the original raw row (audit). | ✔ |

All numeric columns are standardized (zero mean, unit variance) **after** the train/validation split; the stored CSV contains the *raw* (pre‑standardized) values for reproducibility.

### 2. `model_artifacts/`
| File | Type | Description |
|------|------|-------------|
| `rf_best.pkl` | binary (pickle) | Trained `RandomForestRegressor` with optimal hyper‑parameters. |
| `gb_best.pkl` | binary (pickle) | Trained `GradientBoostingRegressor` with optimal hyper‑parameters. |
| `scaler.pkl` | binary (pickle) | `StandardScaler` fitted on training descriptors. |
| `feature_names.json` | JSON | Ordered list of descriptor column names used for training. |

### 3. `results/summary.json`
| Field | Type | Description |
|-------|------|-------------|
| `rmse_rf_test` | float | Test‑set RMSE of Random Forest. |
| `rmse_gb_test` | float | Test‑set RMSE of Gradient Boosting. |
| `mae_rf_test` | float | Test‑set MAE of Random Forest. |
| `mae_gb_test` | float | Test‑set MAE of Gradient Boosting. |
| `r2_rf_test` | float | Test‑set R² of Random Forest. |
| `r2_gb_test` | float | Test‑set R² of Gradient Boosting. |
| `baseline_rmse` | float | RMSE of mean‑baseline predictor. |
| `pvalue_rf_vs_baseline` | float | Bootstrap paired p‑value (Bonferroni‑adjusted). |
| `pvalue_gb_vs_baseline` | float | Bootstrap paired p‑value (Bonferroni‑adjusted). |
| `pvalue_rf_vs_gb` | float | Bootstrap paired p‑value (Bonferroni‑adjusted). |
| `spearman_rho` | float | Spearman rank correlation on NREL experimental set. |
| `spearman_pvalue` | string | Numeric p‑value or `"insufficient sample size"` (FR‑011). |
| `false_negative_rates` | object | Mapping from threshold (`0.30`, `0.35`, `0.40`) to FN rate (float). |
| `top5_r2_ratio` | float | `R²_top5 / R²_full` (must be ≥ 0.80). |
| `audit` | object | Counts of logged warnings (missing elements, metallic entries). |

All fields are mandatory for downstream contract validation.

---
