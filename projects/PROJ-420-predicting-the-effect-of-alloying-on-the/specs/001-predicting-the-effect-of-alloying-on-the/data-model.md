# Data Model: Predicting the Effect of Alloying on the Poisson's Ratio of Aluminum Alloys

## Entity Definitions

### AlloyRecord
| Field | Type | Description |
|-------|------|-------------|
| `material_id` | string | Unique identifier from the source database. |
| `formula` | string | Chemical formula (e.g., “Al95Cu5”). |
| `elemental_composition` | object | Map of element symbols to atomic fractions (Cu, Mg, Si, Zn, Mn, Al). |
| `poissons_ratio` | number (0 – 0.5) | Dimensionless target variable. |
| `youngs_modulus_gpa` | number (> 0) | Young’s modulus in GPa (unit‑normalized). |
| `measurement_method` | string (enum) | One of `"Ultrasonic"`, `"Resonant Ultrasound Spectroscopy"`, `"Static Tensile"`, `"Other"`, or `null`. |
| `source` | string (enum) | `"Materials Project"` or `"NIST MDR"` (if available). |
| `is_alloy` | boolean | `True` if composition is a continuous solid solution (variance ≥ 0.001 for at least one target element). |
| `is_independent_measurement` | boolean | `True` if `measurement_method` is in the allowed set (FR‑009). |

### ModelMetrics
| Field | Type | Description |
|-------|------|-------------|
| `cv_mae` | number | Mean Absolute Error from cross‑validation (5‑fold or LOOCV). |
| `test_mae` | number | MAE on the held‑out test set. |
| `n_samples` | integer | Total number of alloy records used after filtering. |
| `train_size` | integer | Number of training samples. |
| `test_size` | integer | Number of test samples. |
| `cv_method` | string | `"5-fold"` or `"LOOCV"`. |

### CollinearityDiagnostic
| Field | Type | Description |
|-------|------|-------------|
| `Cu_vif`, `Mg_vif`, `Si_vif`, `Zn_vif`, `Mn_vif` | number | VIF for each raw atomic fraction. |
| `max_vif` | number | Maximum VIF among the five predictors. |
| `is_flagged` | boolean | `True` if `max_vif > 5`. |
| `note` | string | Explanation that VIF is computed on raw fractions. |

### FeatureImportance
| Field | Type | Description |
|-------|------|-------------|
| `Cu_importance`, `Mg_importance`, `Si_importance`, `Zn_importance`, `Mn_importance` | number | Back‑transformed importance scores (non‑negative). |
| `ranked_elements` | array[string] | Elements ordered from highest to lowest importance. |

## Data Flow
1. **Raw**: `data/raw/mp_raw.json` (downloaded via `matminer`).  
2. **Clean**: `data/processed/alloys_clean.parquet` – filtered, unit‑normalized, Al balance added, `is_alloy` and `is_independent_measurement` flags set.  
3. **Transformed**: `data/processed/alloys_ilr.parquet` – ILR coordinates appended; VIF computed on raw fractions and stored separately.  
4. **Results**: `results/model_metrics.json`, `results/feature_importance.json`, `results/collinearity_diagnostic.json`, `results/final_report.md`.

## Constraints & Validation Rules
- **Composition Sum**: `Cu + Mg + Si + Zn + Mn + Al = 1.0 ± 1e‑6`.  
- **Major‑Element Sum**: `Cu + Mg + Si + Zn + Mn ≥ 0.95`; otherwise the record is excluded (FR‑003).  
- **Unit Consistency**: `youngs_modulus_gpa` must be in GPa; any MPa entry is converted (divide by 1000).  
- **Independence**: Records with `measurement_method` not in the allowed set are excluded (FR‑009).  
- **VIF**: Calculated on raw fractions only; values > 5 flagged.  
- **Data Hygiene**: Every file has a SHA‑256 checksum recorded in `data/checksums.json`.  

## Formula Parsing & Conversion (FR‑010)
1. Parse `formula` with `chemparse` → element counts.  
2. Compute total atom count; atomic fraction = count / total.  
3. For target elements (Cu, Mg, Si, Zn, Mn) store fractions; compute Al balance as `1 – Σ(target fractions)`.  
4. Non‑target elements are included in the total count but omitted from the 5‑element vector.
