# Data Model: Quantifying Correlations Between Solar Wind Composition and Geomagnetic Indices

## Entities

### SolarWindRecord

Represents a single hourly measurement of solar wind composition.

| Field | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `timestamp` | `datetime` | UTC timestamp (hourly resolution) | ACE Level 2 |
| `proton_density` | `float` | Proton density ($cm^{-3}$) | ACE SWEPAM (`N_p`) |
| `temperature` | `float` | Proton temperature (K) | ACE SWEPAM (`T_p`) |
| `helium_abundance` | `float` | Helium abundance (He$^{2+}$/H$^+$ ratio, %) | ACE SWICS (`He2+_ratio`) |

### GeomagneticRecord

Represents a single hourly measurement of geomagnetic activity.

| Field | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `timestamp` | `datetime` | UTC timestamp (hourly resolution) | NOAA SWPC |
| `Kp` | `float` | Planetary K-index (0–9, 1/3 steps) | NOAA |
| `Dst` | `float` | Disturbance Storm Time index (nT) | NOAA |

### SynchronizedRecord

The unified record after alignment (1-hour grid).

| Field | Type | Description |
| :--- | :--- | :--- |
| `timestamp` | `datetime` | Common UTC timestamp |
| `proton_density` | `float` | Interpolated if missing |
| `temperature` | `float` | Interpolated if missing |
| `helium_abundance` | `float` | Interpolated if missing |
| `Kp` | `float` | Interpolated if missing |
| `Dst` | `float` | Interpolated if missing |
| `interpolated_flag` | `bool` | True if any value was interpolated |

### CorrelationResult

The output of the statistical analysis.

| Field | Type | Description |
| :--- | :--- | :--- |
| `composition_param` | `str` | One of: `proton_density`, `temperature`, `helium_abundance` |
| `geomagnetic_index` | `str` | One of: `Kp`, `Dst` |
| `lag_hours` | `int` | Lag in hours (0, 1, 2, 3, 6) |
| `pearson_r` | `float` | Pearson correlation coefficient |
| `spearman_rho` | `float` | Spearman rank correlation coefficient |
| `p_raw` | `float` | Raw p-value (using $N_{eff}$) |
| `p_bonferroni` | `float` | Bonferroni-corrected p-value |
| `significant` | `bool` | True if `p_bonferroni` < 0.05 |
| `effect_size_large` | `bool` | True if `abs(pearson_r)` > 0.5 |

## Data Flow

1.  **Fetch**: Raw CSVs from ACE/NOAA → `data/raw/`.
2.  **Sync**: Parse, align, interpolate → `data/processed/synced.csv`.
3.  **Analyze**: Compute correlations → `results/correlations.csv`.
4.  **Validate**: Filter for hold-out period, check thresholds → `results/validation_report.md`.

## Constraints

*   **Missing Variables**: If `helium_abundance` is missing for > 6 hours, the pipeline aborts (FR-006).
*   **Interpolation**: Max gap for interpolation is 6 hours. Larger gaps are flagged and excluded.
*   **Lag Range**: Only 0, 1, 2, 3, 6 hours are analyzed.
