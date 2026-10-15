# Data Model: Exploring the Statistical Relationship Between Solar Wind Composition and Geomagnetic Indices

## Entity Definitions

### SolarWindSample
| Field | Type | Description |
|-------|------|-------------|
| `timestamp` | `datetime` (UTC, hourly) | Observation time |
| `velocity_km_s` | `float` | Bulk solar‑wind speed (km s⁻¹) |
| `density_cm3` | `float` | Proton density (cm⁻³) |
| `imf_nT` | `float` | Interplanetary Magnetic Field magnitude (nT) |
| `imf_bz_nT` | `float` | IMF Bz component (nT) |
| `o_fe_ratio` | `float` | O / Fe ion flux ratio |
| `he_h_ratio` | `float` | He / H ion flux ratio |
| `c_o_ratio` | `float` | C / O ion flux ratio |
| `epsilon` | `float` | Akasofu ε coupling function parameter |
| `newell_flux` | `float` | Newell dΦ/dt coupling function parameter |

### GeomagneticIndex
| Field | Type | Description |
|-------|------|-------------|
| `timestamp` | `datetime` (UTC, hourly) | Observation time (matches SolarWindSample) |
| `dst_index` | `float` | Dst index (nT) |
| `kp_index` | `float` | Kp index (0‑9 scale) |

### RegressionModel
| Attribute | Type | Description |
|-----------|------|-------------|
| `model_type` | `str` (`"Baseline"` / `"Full"`) | Which predictor set was used |
| `target` | `str` (`"Dst"` / `"Kp"`) | Dependent variable |
| `coefficients` | `dict[str, float]` | Feature → coefficient |
| `p_values` | `dict[str, float]` | Feature → p‑value |
| `r_squared` | `float` | In‑sample R² |
| `adj_r_squared` | `float` | Adjusted R² |
| `vif` | `dict[str, float]` | Feature → VIF |
| `cv_r2` | `float` | Mean out‑of‑sample R² from 5‑fold TimeSeriesSplit |
| `delta_r2` | `float` *(optional)* | `R²_full – R²_baseline` (only for Full model) |

### PermutationResult
| Attribute | Type | Description |
|-----------|------|-------------|
| `feature` | `str` | Composition ratio tested (`o_fe_ratio`, etc.) |
| `observed_coefficient` | `float` | Coefficient from the full model on the original data |
| `null_distribution` | `list[float]` | Coefficients from each block‑permuted iteration |
| `p_value` | `float` | Two‑sided p‑value |
| `significant` | `bool` | After FDR correction |

## Data Flow Diagram (textual)

1. **Ingestion** (`generate_synthetic_data.py`) → raw synthetic files (`data/raw/`).  
2. **Alignment** (`align.py`) → hourly median dataset (`data/processed/aligned.parquet`).  
3. **Feature Engineering** (`coupling_functions.py`) → enriched dataset (`data/processed/with_coupling.parquet`).  
4. **Model Fitting** (`regression.py`) → `baseline_model.json`, `full_model.json`.  
5. **ΔR² & VIF** computed inside `regression.py`.  
6. **Cross‑Validation** (`cross_validation.py`) → `cv_metrics.json`.  
7. **Permutation Test** (`permutation_test.py`) → `permutation_results.json`.  
8. **Sensitivity & FDR** (`sensitivity.py`) → `sensitivity.json`.  
9. **Reporting** (`main.py`) aggregates all JSON/CSV into final tables & plots (`data/artifacts/`).  

## Data Hygiene & Provenance

* **Raw Files** – Stored unchanged under `data/raw/`. Checksums (`sha256`) recorded in `data/raw/checksums.yaml`.  
* **Synthetic Generation** – Parameters (`seed`, distributions, injected effect size) saved in `data/raw/synthetic_config.yaml`.  
* **Derived Files** – Every transformation writes a new file under `data/processed/` or `data/artifacts/` with a filename that includes a content hash (e.g., `aligned_20241015_abcdef.parquet`).  
* **Metadata** – Each artifact JSON includes a `provenance` block with `source_file`, `script`, `git_commit`, and `timestamp`.  

*Note*: Because the dataset is synthetic, the provenance metadata explicitly records that the source is `synthetic_config.yaml`, satisfying Constitution Principle VI while maintaining full traceability.

---



