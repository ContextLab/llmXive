# Data Model: Exploring the Statistical Relationship Between Solar Wind Composition and Geomagnetic Indices

## Entity Definitions

### SolarWindSample
| Field | Type | Description |
|-------|------|-------------|
| `timestamp` | `datetime` (UTC, hourly) | Observation time on the hourly grid. |
| `velocity_km_s` | `float` | Bulk solar‑wind speed (km s⁻¹). |
| `density_cm3` | `float` | Proton density (cm⁻³). |
| `imf_nT` | `float` | IMF magnitude (nT). |
| `imf_bz_nT` | `float` | IMF Bz component (nT). |
| `o_fe_ratio` | `float` or `null` | Oxygen‑to‑Iron ion flux ratio (may be missing for hours without a 2‑hour measurement). |
| `he_h_ratio` | `float` or `null` | Helium‑to‑Hydrogen ion flux ratio. |
| `c_o_ratio` | `float` or `null` | Carbon‑to‑Oxygen ion flux ratio. |
| `epsilon` | `float` | Akasofu ε coupling function (computed from bulk parameters). |
| `newell_flux` | `float` | Newell dΦ/dt coupling function (computed from bulk parameters). |
| `dst_index` | `float` | Dst geomagnetic index (nT). |
| `kp_index` | `float` | Kp index (0‑9 scale). |

*Note*: The composition fields are optional for the **primary baseline analysis**; they become required only when real composition data are present and Principle VI is amended.

### RegressionModel
| Attribute | Type | Description |
|-----------|------|-------------|
| `model_type` | `str` (`"Baseline"` | `"Full"`) | Predictor set used. |
| `target` | `str` (`"Dst"` | `"Kp"`) | Dependent variable. |
| `coefficients` | `dict[str, float]` | Feature → coefficient. |
| `p_values` | `dict[str, float]` | Feature → p‑value. |
| `r_squared` | `float` | In‑sample R². |
| `adj_r_squared` | `float` | Adjusted R². |
| `vif` | `dict[str, float]` | Feature → VIF. |
| `cv_r2` | `float` | Mean out‑of‑sample R² from 5‑fold TimeSeriesSplit. |
| `delta_r2` | `float` (optional) | `R²_full – R²_baseline` (only for Full model). |

### PermutationResult
| Attribute | Type | Description |
|-----------|------|-------------|
| `feature` | `str` | Composition ratio tested (`o_fe_ratio`, `he_h_ratio`, `c_o_ratio`). |
| `observed_coefficient` | `float` | Coefficient from the full model on original data. |
| `null_distribution` | `list[float]` | Coefficients from each block‑permuted iteration. |
| `p_value` | `float` | Two‑sided p‑value. |
| `significant` | `bool` | After BH‑FDR correction. |

## Data Flow (textual)

1. **Synthetic Composition Generation** → `data/raw/synthetic_composition.parquet` (raw, unchanged).  
2. **Bulk & Geomagnetic Download** → `data/raw/ace_bulk.csv` + `data/raw/noaa_geomagnetic.parquet`.  
3. **Checksum Creation** → `data/raw/checksums.yaml`.  
4. **Alignment** (`align.py`) → `data/processed/aligned_hourly.parquet` + `alignment_report.json`.  
5. **Coupling Functions** (`coupling_functions.py`) → `data/processed/with_coupling.parquet`.  
6. **Baseline Regression** (`regression.py`) → `baseline_model.json`.  
7. **Full Regression** (`regression.py`) → `full_model.json` (only if the amendment to Principle VI is recorded and real composition is present).  
8. **ΔR²** (`regression.py --compute-delta`) → `delta_r2.json` (conditional).  
9. **Cross‑Validation** (`cross_validation.py`) → `cv_metrics.json`.  
10. **Permutation Test** (`permutation_test.py`) → `permutation_results.json` (conditional).  
11. **Sensitivity & FDR** (`sensitivity.py`) → `sensitivity.json` (conditional).  
12. **Reporting** (`main.py`) aggregates everything into `final_report.json` and generates PNG/PDF figures under `data/artifacts/figures/`.

## Data Hygiene & Provenance

* **Raw Files** – Stored unchanged under `data/raw/`; SHA‑256 checksums recorded in `data/raw/checksums.yaml`.  
* **Synthetic Generation** – All RNG parameters and true coefficients saved in `data/raw/synthetic_config.yaml`.  
* **Derived Files** – Every transformation writes a new file (`*_hourly.parquet`, `*_with_coupling.parquet`, `*_model.json`, etc.) whose filename includes a content hash (e.g., `aligned_20241020_ab12cd.parquet`).  
* **Metadata** – Each JSON artifact includes a `provenance` block with fields: `source_file`, `script`, `git_commit`, `timestamp`.  
* **Composition Provenance** – For synthetic ratios, `source: synthetic_config.yaml`; when real composition becomes available, the `source` will point to the corresponding raw CDF file, satisfying Principle VI.

--- 