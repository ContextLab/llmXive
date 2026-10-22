# Data Model: Quantifying Spatial Correlations in Perovskite Solar Cell Efficiency

## Entity Definitions

### 1. ElementalMap (optional)
| Field | Type | Description |
|-------|------|-------------|
| `id` | `string` | Unique sample identifier (matches `DevicePerformance.id`). |
| `element` | `string` (enum: `"Pb"`, `"I"`, `"MA"`) | Element represented. |
| `raw_path` | `string` | Path to original EDS file under `data/raw/`. |
| `processed_path` | `string` | Path to aligned/masked array under `data/processed/`. |
| `pixel_size_nm` | `number` | Spatial resolution (nm per pixel). |
| `dimensions` | `array[integer, 2]` | Width × Height in pixels. |
| `mask_percentage` | `number` (0‑1) | Fraction of pixels masked due to defects. |
| `co_location_method` | `string` | Method used for co‑location validation (e.g., `"ID+scan_index"`). |
| `link_verified` | `boolean` | `true` if a programmatic link to an EDS file was found. |

### 2. DevicePerformance
| Field | Type | Description |
|-------|------|-------------|
| `id` | `string` | Must match `ElementalMap.id` when maps exist. |
| `pce` | `number` | Power‑Conversion Efficiency (%). |
| `j_sc` | `number` | Short‑circuit current density (mA cm⁻²). |
| `v_oc` | `number` | Open‑circuit voltage (V). |
| `source_url` | `string` | URL of the JSON/CSV source. |
| *(Optional covariates – stored in separate metadata file)* | | Processing temperature, stoichiometric ratio, film thickness are read from NREL metadata and used as model covariates but are **not** part of the unified CSV to keep schema validation simple. |

### 3. SpatialMetric (optional, present only if EDS maps are available)
| Field | Type | Description |
|-------|------|-------------|
| `map_id` | `string` | FK → `ElementalMap.id`. |
| `element` | `string` (enum: `"Pb"`, `"I"`, `"MA"`) | |
| `correlation_length_exp` | `number` (nullable) | 1/e decay from exponential fit (nm). |
| `correlation_length_gauss` | `number` (nullable) | 1/e decay from Gaussian fit (nm). |
| `correlation_length_power` | `number` (nullable) | 1/e decay from power‑law fit (nm). |
| `best_fit_model` | `string` (enum: `"exponential"`, `"gaussian"`, `"power-law"`) (nullable) | Model selected by AIC. |
| `aic_score` | `number` (nullable) | AIC of the best model. |
| `low_freq_spectral_power` | `number` | Integrated power in 0‑0.1 cycles/pixel. |
| `is_undefined` | `boolean` | Autocorrelation never decayed to 1/e within image bounds. |
| `is_censored` | `boolean` | True if correlation length exceeds image dimension. |
| `censored_value` | `number` (nullable) | Image dimension used as lower bound when censored. |
| `normalized_length` | `number` (nullable) | Length divided by max observed length for this element (used for composite metric). |
| `composite_spatial_metric` | `number` (nullable) | Primary composite metric: average of the three normalized lengths for a given sample. |
| `composite_spatial_metric_eq` | `number` (nullable) | Equal‑weight composite (same as `composite_spatial_metric`). |
| `composite_spatial_metric_var` | `number` (nullable) | Variance‑weighted composite (sensitivity analysis). |
| `composite_spatial_metric_expert` | `number` (nullable) | Expert‑assigned weighted composite (sensitivity analysis). |

### 4. DiffusionLength (optional)
| Field | Type | Description |
|-------|------|-------------|
| `sample_id` | `string` | FK → `DevicePerformance.id`. |
| `diffusion_length_nm` | `number` | Estimated charge‑carrier diffusion length (nm). |
| `method` | `string` (enum: `"TRPL"`, `"empirical_calibration"`) | Origin of the estimate. |
| `source_reference` | `string` (optional) | Citation if empirical calibration is used. |

### 5. AnalysisResult
| Field | Type | Description |
|-------|------|-------------|
| `pair` | `string` (enum: `"PCE_Jsc"`, `"PCE_Voc"`, `"Jsc_Voc"` ) | Performance variable pair analyzed. |
| `metric_type` | `string` (enum: `"pearson"`, `"spearman"`, `"gam"` ) | Statistical method used. |
| `r_value` | `number` | Correlation coefficient (Pearson r or Spearman ρ). |
| `p_value` | `number` | Raw p‑value. |
| `p_value_adj` | `number` | Benjamini‑Hochberg adjusted p‑value. |
| `confidence_interval` | `array[number, 2]` | 95 % confidence interval for the coefficient. |
| `effect_size_q` | `number` | Cohen’s q for the correlation (effect‑size). |
| `gam_deviance_explained` | `number` (nullable) | Fraction of deviance explained by GAM (if GAM applied). |
| `robustness_delta_r_max` | `number` (nullable) | Max Δr from LOO‑CV. |
| `n_samples` | `integer` (≥ 1) | Number of samples used. |
| `sensitivity_excluded` | `boolean` | `true` if sample excluded by FR‑008 sensitivity analysis. |
| `co_location_status` | `string` (enum: `"verified"`, `"mismatch"`, `"ambiguous"` ) | Outcome of co‑location validation. |
| `depth_validation_status` | `string` (enum: `"valid"`, `"flagged"`, `"excluded"` ) | Result of depth‑resolution check. |
| `linearity_flag` | `string` (enum: `"linear"`, `"nonlinear_exploratory"` ) | Outcome of linearity diagnostic (FR‑010). |

## Data Flow Overview
1. **Feasibility** → `feasibility_report.json` (counts of requested vs. found EDS maps).  
2. **Ingestion** → `unified_dataset.csv` (populated `DevicePerformance` and optional `ElementalMap`).  
3. **Validation** → `co_location_status.csv`, `depth_status.csv`.  
4. **Metric Extraction** → `spatial_metrics.csv` (may be empty).  
5. **Diffusion Length Estimation** → `diffusion_lengths.csv` (may be empty).  
6. **Modeling** → `summary_report.csv`.  
7. **Report** → `summary_report.pdf`.

## Integrity Constraints
- `DevicePerformance.id` **must be unique**.  
- If an `ElementalMap` exists, its `id` **must match** a `DevicePerformance.id`.  
- `pce` **> 0** and **< 50**.  
- `mask_percentage` **∈ [0, 1]**.  
- When `is_undefined` = `true`, all `correlation_length_*` fields are `null`.  
- Samples with `co_location_status` ≠ `"verified"` are excluded from any statistical modeling.  
- `diffusion_length.method` must be either `"TRPL"` or `"empirical_calibration"`.

---


