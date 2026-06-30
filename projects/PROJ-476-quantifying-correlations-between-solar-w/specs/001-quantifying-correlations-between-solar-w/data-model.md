# Data Model: Quantifying Correlations Between Solar Wind Composition and Geomagnetic Indices

## Entities

### 1. SolarWindRecord
Represents a single hourly observation of solar wind composition.

| Field | Type | Description | Units |
| :--- | :--- | :--- | :--- |
| `timestamp` | `datetime` | UTC timestamp of the measurement. | ISO 8601 |
| `proton_density` | `float` | Proton number density. | cm⁻³ |
| `temperature` | `float` | Proton temperature. | K |
| `helium_abundance` | `float` | Helium abundance ratio (He²⁺/H⁺). | % (or dimensionless) |

### 2. GeomagneticRecord
Represents a single hourly observation of geomagnetic activity.

| Field | Type | Description | Units |
| :--- | :--- | :--- | :--- |
| `timestamp` | `datetime` | UTC timestamp of the measurement. | ISO 8601 |
| `kp_index` | `float` | Planetary K index (0-9). | dimensionless |
| `dst_index` | `float` | Disturbance Storm Time index. | nT |

### 3. SynchronizedRecord
The merged record after alignment to the 1-hour grid.

| Field | Type | Source |
| :--- | :--- | :--- |
| `timestamp` | `datetime` | Grid |
| `proton_density` | `float` | SolarWindRecord (interpolated if missing) |
| `temperature` | `float` | SolarWindRecord (interpolated if missing) |
| `helium_abundance` | `float` | SolarWindRecord (interpolated if missing) |
| `kp_index` | `float` | GeomagneticRecord (interpolated if missing) |
| `dst_index` | `float` | GeomagneticRecord (interpolated if missing) |
| `interpolated` | `bool` | True if any value was filled by interpolation. |

### 4. CorrelationResult
The output of the statistical analysis for a specific pair and lag.

| Field | Type | Description |
| :--- | :--- | :--- |
| `param_name` | `str` | Name of solar wind parameter (e.g., "helium_abundance"). |
| `index_name` | `str` | Name of geomagnetic index (e.g., "dst_index"). |
| `lag_hours` | `int` | Time lag in hours (0, 1, 2, 3, 6). |
| `pearson_r` | `float` | Pearson correlation coefficient. |
| `spearman_rho` | `float` | Spearman rank correlation coefficient. |
| `n_raw` | `int` | Raw sample size. |
| `n_eff` | `float` | Effective sample size after autocorrelation adjustment. |
| `p_raw` | `float` | Raw p-value (t-distribution with $N_{eff}$). |
| `p_bonferroni` | `float` | Bonferroni-corrected p-value. |
| `is_significant` | `bool` | True if `p_bonferroni` < 0.05. |

## Data Flow

1.  **Input**: Raw ACE CSV, Raw NOAA CSV (or synthetic).
2.  **Transform**: `align.py` merges, resamples to 1h, interpolates gaps ≤ 6h.
3.  **Output**: `data/processed/synced.csv` (SynchronizedRecord).
4.  **Transform**: `correlation.py` iterates pairs and lags, computes stats.
5.  **Output**: `data/processed/correlation_results.csv` (CorrelationResult).
