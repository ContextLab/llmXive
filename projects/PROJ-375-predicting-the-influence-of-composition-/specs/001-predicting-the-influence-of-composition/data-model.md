# Data Model: Predicting the Influence of Composition on the Thermal Expansion of Metallic Glasses

## Overview
The pipeline operates on a single canonical table of processed alloy entries (metallic glasses). All downstream artifacts (models, metrics, feature‑importance tables) reference rows from this table via the stable `material_id`.

## Entity Definitions

### AlloyEntry
| Field | Type | Description |
|-------|------|-------------|
| `material_id` | string | Unique Materials Project identifier, e.g., `"mp-12345"`. |
| `composition` | string | Stoichiometric formula, e.g., `"Zr50Cu40Al10"`. |
| `cte` | number | Coefficient of thermal expansion (1/K). |
| `weighted_mean_atomic_radius` | number | Σ fraction × atomic radius (pm). |
| `electronegativity_variance` | number | Weighted variance of Pauling electronegativity. |
| `vec` | number | Valence electron concentration (e⁻/atom). |
| `atomic_size_coefficient_of_variation` | number | Standard deviation of atomic radii divided by the weighted mean radius (σ/μ). |
| `source_method` | string | `"DFT"` or `"Experimental"` as reported by the source. |
| `checksum` | string | SHA‑256 checksum of the raw JSON record. |
| `vif_score` | number | optional | VIF computed for each descriptor (if computed). |
| `thermal_history_flag` | boolean | optional | True if non‑standard thermal‑history metadata is present. |
| `alloy_family` | string | Sorted, comma‑separated list of constituent element symbols; used for GroupKFold stratification. |

### ModelPerformance
| Field | Type | Description |
|-------|------|-------------|
| `model_type` | string | `"linear_regression"`, `"random_forest"` or `"baseline_linear"`. |
| `r2_test` | number | Coefficient of determination on the held‑out test set. |
| `mae_test` | number | Mean Absolute Error (K⁻¹) on the test set. |
| `rmse_test` | number | Root Mean Squared Error (K⁻¹) on the test set. |
| `p_value` | number | nullable | Permutation‑test p‑value; `null` if observed R² < 0.3. |
| `null_result_flag` | boolean | True if the observed R² is below the significance threshold (R² < 0.3). |
| `runtime_seconds` | number | Wall‑clock time spent during training and evaluation. |
| `memory_peak_mb` | number | Peak RAM usage (MB). |

### FeatureImportance
| Field | Type | Description |
|-------|------|-------------|
| `model_type` | string | `"random_forest"` or `"linear_regression"` (coefficients). |
| `feature_name` | string | Name of the compositional descriptor. |
| `importance_score` | number | Normalised importance (RF) or absolute standardized coefficient (LR). |
| `rank` | integer | 1 = most important. |
| `pearson_corr` | number | Pearson correlation between feature and CTE (training data). |
| `abs_corr_rank` | integer | Rank of `|pearson_corr|`. |
| `spearman_rho` | number | nullable | Spearman ρ between importance rank and absolute‑correlation rank. |
| `kendall_tau` | number | nullable | Kendall‑τ between the two rankings. |

## Relationships
- Each `ModelPerformance` entry corresponds to a model trained on the full `AlloyEntry` table (post‑cleaning).  
- `FeatureImportance` rows are linked to the same `model_type`.  
- All files are version‑controlled; the `checksum` column guarantees reproducibility (Constitution Principle III).

---
