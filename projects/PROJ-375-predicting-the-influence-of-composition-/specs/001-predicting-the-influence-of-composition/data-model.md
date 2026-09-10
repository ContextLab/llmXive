# Data Model: Predicting the Influence of Composition on the Thermal Expansion of Metallic Glasses

## Overview
The pipeline operates on a single canonical table of processed metallic‑glass entries. Downstream artifacts (models, performance metrics) reference rows from this table via a stable `material_id`.

## Entity Definitions

### MetallicGlassEntry
| Field | Type | Description |
|-------|------|-------------|
| `material_id` | string | Unique identifier from Materials Project (e.g., `"mp-12345"`). |
| `composition` | string | Stoichiometric formula (e.g., `"Zr50Cu40Al10"`). |
| `cte` | float | Coefficient of thermal expansion (1/K). |
| `weighted_mean_atomic_radius` | float | Σ fraction × atomic radius (pm). |
| `electronegativity_variance` | float | Weighted variance of Pauling electronegativity. |
| `vec` | float | Valence electron concentration (e⁻/atom). |
| `atomic_size_mismatch` | float | Weighted standard deviation of atomic radius (pm). |
| `source_method` | string | `"DFT"` or `"Experimental"` (as reported by MP). |
| `thermal_history` | string | optional | Free‑text description of any post‑synthesis heat treatment (if present). |
| `amorphous_flag` | boolean | `True` if the entry is flagged as amorphous/metallic glass. |
| `checksum` | string | SHA‑256 of the raw JSON record. |
| `vif_score` | number | optional | VIF computed for each descriptor (may be absent if VIF filtering removed the feature). |
| `thermal_history_flag` | boolean | optional | `True` if the `thermal_history` string does not match the simple `<temp>K for <time>h` pattern, indicating a potential inconsistency for sensitivity analysis. |

### ModelPerformance
| Field | Type | Description |
|-------|------|-------------|
| `model_type` | string | `"linear_regression"` or `"random_forest"` or `"baseline_linear"` . |
| `r2_test` | float | R² on held‑out test set. |
| `mae_test` | float | Mean Absolute Error (K⁻¹). |
| `rmse_test` | float | Root Mean Squared Error (K⁻¹). |
| `p_value` | float | nullable | Permutation test p‑value; null if R² < 0.3 (null result). |
| `null_result_flag` | boolean | `True` if R² < 0.3. |
| `runtime_seconds` | float | Wall‑clock time for training + evaluation. |
| `memory_peak_mb` | float | Peak resident memory usage. |

### FeatureImportance
| Field | Type | Description |
|-------|------|-------------|
| `model_type` | string | `"random_forest"` or `"linear_regression"` (coefficients). |
| `feature_name` | string | Name of the compositional descriptor. |
| `importance_score` | float | Normalized importance (RF) or absolute coefficient (LR). |
| `rank` | integer | 1 = highest importance. |
| `pearson_corr` | float | Pearson correlation between feature and CTE. |
| `abs_corr_rank` | integer | Rank of the absolute Pearson correlation. |
| `spearman_rho` | float | nullable | Spearman rank correlation between the two rankings (importance vs. absolute‑correlation). |

## Relationships
- Each `ModelPerformance` entry references a `model_type` that was trained on the **entire** `MetallicGlassEntry` table (after cleaning).  
- `FeatureImportance` rows are linked to the same `model_type`.  
- All files are version‑controlled; the checksum column guarantees reproducibility (Constitution Principle III).


## Data ?????? ?? ?? ?? ??? ... (garbled) 