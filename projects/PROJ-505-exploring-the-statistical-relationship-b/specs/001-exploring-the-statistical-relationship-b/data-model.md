# Data Model: Exploring the Statistical Relationship Between Solar Wind Composition and Geomagnetic Indices

## Entity Definitions

### SolarWindSample
| Field | Type | Description |
|-------|------|-------------|
| `timestamp` | `datetime` (UTC, hourly) | Observation time |
| `velocity_km_s` | `float` | Bulk solar‑wind speed (km s⁻¹) |
| `density_cm3` | `float` | Proton density (cm⁻³) |
| `imf_nT` | `float` | IMF magnitude (nT) |
| `imf_bz_nT` | `float` | IMF Bz component (nT) |
| `o_fe_ratio` | `float` or `null` | O / Fe ion flux ratio |
| `he_h_ratio` | `float` or `null` | He / H ion flux ratio |
| `c_o_ratio` | `float` or `null` | C / O ion flux ratio |
| `epsilon` | `float` | Akasofu ε coupling function |
| `newell_flux` | `float` | Newell dΦ/dt coupling function |
| `dst_index` | `float` | Dst geomagnetic index (nT) |
| `kp_index` | `float` | Kp index (0‑9 scale) |

### RegressionModel
| Attribute | Type | Description |
|-----------|------|-------------|
| `model_type` | `str` (`"Baseline"` | `"Full"`) | Predictor set used |
| `target` | `str` (`"Dst"` | `"Kp"`) | Dependent variable |
| `coefficients` | `dict[str, float]` | Feature → coefficient |
| `p_values` | `dict[str, float]` | Feature → p‑value |
| `r_squared` | `float` | In‑sample R² |
| `adj_r_squared` | `float` | Adjusted R² |
| `vif` | `dict[str, float]` | Feature → VIF |
| `cv_r2` | `float` | Mean out‑of‑sample R² from 5‑fold TimeSeriesSplit |
| `delta_r2` | `float` (optional) | `R²_full – R²_baseline` (only for Full model) |

### PermutationResult
| Attribute | Type | Description |
|-----------|------|-------------|
| `feature` | `str` | Composition ratio tested (`o_fe_ratio`, `he_h_ratio`, `c_o_ratio`) |
| `observed_coefficient` | `float` | Coefficient from the full model on original data |
| `null_distribution` | `list[float]` | Coefficients from each block‑permuted iteration |
| `p_value` | `float` | Two‑sided p‑value |
| `significant` | `bool` | After FDR correction |

## Data Flow (textual)

1. **Synthetic Generation** → `data/raw/synthetic.parquet` (raw, unchanged).  
2. **Alignment** (`align.py`) → `data/processed/aligned_hourly.parquet`.  
3. **Coupling Functions** (`coupling_functions.py`) → `data/processed/with_coupling.parquet`.  
4. **Regression** (`regression.py`) → `baseline_model.json`, `full_model.json`.  
5. **ΔR²** (`regression.py --compute-delta`) → `delta_r2.json`.  
6. **Cross‑Validation** (`cross_validation.py`) → `cv_metrics.json`.  
7. **Permutation Test** (`permutation_test.py`) → `permutation_results.json`.  
8. **Sensitivity & FDR** (`sensitivity.py`) → `sensitivity.json`.  
9. **Reporting** (`main.py`) aggregates everything into `final_report.json` and figures under `data/artifacts/`.

## Data Hygiene & Provenance

* **Raw Files** – Stored unchanged under `data/raw/`; SHA‑256 checksums recorded in `data/raw/checksums.yaml`.  
* **Synthetic Generation** – All RNG parameters and true coefficients saved in `data/raw/synthetic_config.yaml`.  
* **Derived Files** – Every transformation writes a new file (`*_hourly.parquet`, `*_with_coupling.parquet`, `*_model.json`, etc.) whose filename includes a content hash (e.g., `aligned_20241020_ab12cd.parquet`).  
* **Metadata** – Each JSON artifact includes a `provenance` block with fields: `source_file`, `script`, `git_commit`, `timestamp`.  

*Note*: Because the composition data are synthetic, the provenance explicitly records `source: synthetic_config.yaml`. This satisfies the constitution’s traceability requirement while being transparent about the synthetic nature. When genuine ACE/WIND composition files become available, the `source` field will point to the corresponding raw file, fulfilling Principle VI.



---


