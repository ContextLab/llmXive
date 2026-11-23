# Data Model: Predicting the Impact of Composition on the Band Gap of Perovskite Materials

## Overview
The pipeline yields three core artefact families that constitute the project's data model:

1. **Raw DFT data** – untouched parquet files (or CSV) downloaded from the Materials Project API or a Zenodo mirror.
2. **Processed perovskite feature table** – a CSV containing the original formulas, filtered DFT band gaps, all computed compositional descriptors, and a `source` identifier indicating whether the row originated from the Materials Project API (`materials_project`) or the Zenodo mirror (`zenodo_mirror`).
3. **Model artefacts & evaluation summary** – serialized scikit‑learn models, scaler parameters, and a JSON file summarizing every metric, statistical test, and audit flag.

All artefacts are immutable; any new version receives a SHA‑256 hash suffix and is recorded in `state/projects/.../artifact_hashes`.

## Schema Definitions

### 1. `data/processed/perovskite_features.csv`
| Column | Type | Description | Required |
|--------|------|-------------|----------|
| `formula` | string | ABX₃ stoichiometric chemical formula (e.g., `CsPbI3`). Must match regex `^[A-Z][a-z]?[A-Z][a-z]?[A-Z][a-z]?\\d*$`. | ✔ |
| `dft_band_gap_eV` | float | DFT‑calculated band gap (eV). Must satisfy `0 < value < 6`. | ✔ |
| `mean_electronegativity` | float | Mean Pauling electronegativity of constituent elements. | ✔ |
| `var_electronegativity` | float | Variance of electronegativity across elements. | ✔ |
| `mean_atomic_radius` | float | Mean atomic radius (pm). | ✔ |
| `var_atomic_radius` | float | Variance of atomic radius. | ✔ |
| `mean_ionization_energy` | float | Mean first ionization energy (eV). | ✔ |
| `var_ionization_energy` | float | Variance of ionization energy. | ✔ |
| `oxidation_state_variance` | float | Variance of the most‑common oxidation states per element. | ✔ |
| `goldschmidt_tolerance_factor` | float | Goldschmidt tolerance factor (unitless). | ✔ |
| `octahedral_factor` | float | Octahedral factor (unitless). | ✔ |
| `lead_free` | boolean | `True` if the formula contains no `Pb`; otherwise `False`. | ✔ |
| `source` | string | Identifier of the original raw dataset (`materials_project`, `zenodo_mirror`, `dft23-full`, `dftest61523`, `dftest61623`). | ✔ |
| `checksum` | string | SHA‑256 hash of the original raw row (audit). Must match pattern `^[a-f0-9]{64}$`. | ✔ |

All numeric columns contain the *raw* (pre‑standardized) values; standardization parameters are stored separately (`models/scaler.pkl`).

### 2. `models/` artefacts
| File | Type | Description |
|------|------|-------------|
| `rf_best.pkl` | binary (pickle) | Trained `RandomForestRegressor` with optimal hyper‑parameters. |
| `gb_best.pkl` | binary (pickle) | Trained `GradientBoostingRegressor` with optimal hyper‑parameters. |
| `scaler.pkl` | binary (pickle) | `StandardScaler` fitted on the training descriptor matrix. |
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
| `baseline_rmse` | float | RMSE of the mean‑baseline predictor. |
| `pvalue_rf_vs_baseline` | float | Bonferroni‑adjusted bootstrap paired p‑value. |
| `pvalue_gb_vs_baseline` | float | Bonferroni‑adjusted bootstrap paired p‑value. |
| `pvalue_rf_vs_gb` | float | Bonferroni‑adjusted bootstrap paired p‑value. |
| `spearman_rho` | float | Spearman rank correlation on NREL experimental set. |
| `spearman_pvalue` | string | Numeric p‑value or `"insufficient sample size"` (FR‑011). |
| `spearman_power` | float | Observed power of the Spearman test (added for methodology). |
| `false_negative_rates` | object | Mapping `{ "0.30": float, "0.35": float, "0.40": float }`. |
| `top5_r2_ratio` | float | Ratio `R²_top5 / R²_full` (must be ≥ 0.80). |
| `audit` | object | Counts of logged warnings: `{ "missing_elements": int, "metallic_entries": int }`. |

All fields are mandatory; downstream contract tests will validate presence and type.