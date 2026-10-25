# Data Model: Quantifying Correlations Between Solar Wind Composition and Geomagnetic Indices

## Entities

### SolarWindRecord (raw, from ACE via cdasws)

| Field | Type | Description | Source |
|:---|:---|:---|:---|
| `timestamp` | `datetime` | UTC epoch of measurement | ACE SWEPAM / SWICS Level 2 |
| `N_p` | `float` | Proton density (cm⁻³) | ACE SWEPAM |
| `T_p` | `float` | Proton temperature (K) | ACE SWEPAM |
| `He2+_ratio` | `float` | He²⁺/H⁺ abundance ratio | ACE SWICS |

### GeomagneticRecord (raw)

| Field | Type | Description | Source |
|:---|:---|:---|:---|
| `timestamp` | `datetime` | UTC timestamp (hourly) | NOAA SWPC / Kyoto WDC |
| `Kp` | `float` | Planetary K-index (0–9, thirds) | NOAA SWPC |
| `Dst` | `float` | Disturbance Storm Time index (nT) | Kyoto WDC |

### SynchronizedRecord (`data/processed/synced.csv`)

| Field | Type | Description |
|:---|:---|:---|
| `timestamp` | `datetime` (ISO‑8601 UTC) | Common 1‑hour grid timestamp |
| `proton_density` | `float` | cm⁻³; interpolated if gap ≤ 6 h |
| `temperature` | `float` | K; interpolated if gap ≤ 6 h |
| `helium_abundance` | `float` | He²⁺/H⁺ ratio; interpolated if gap ≤ 6 h |
| `Kp` | `float` | 0–9 |
| `Dst` | `float` | nT |
| `interpolated_flag` | `bool` | True if any value in the row was linearly interpolated |

### StormFilteredRecord (derived, used for analysis)

| Field | Type | Description |
|:---|:---|:---|
| `timestamp` | `datetime` (ISO‑8601 UTC) | Subset of `SynchronizedRecord` where `Dst < -50` nT |
| *(all other columns inherited from `SynchronizedRecord`)* |  |  |

### CorrelationResult (`results/*.csv`)

| Field | Type | Description |
|:---|:---|:---|
| `composition_parameter` | `str` | `proton_density` \| `temperature` \| `helium_abundance` |
| `geomagnetic_index` | `str` | `Kp` \| `Dst` |
| `lag_hours` | `int` | 0, 1, 2, 3, or 6 |
| `pearson_r` | `float` | Pearson coefficient |
| `spearman_rho` | `float` | Spearman coefficient |
| `n_eff` | `float` | Pyper & Peterman effective sample size |
| `p_raw` | `float` | Raw p‑value (t‑approx, df = n_eff − 2) |
| `p_bonferroni` | `float` | min(1, 30 × p_raw) |
| `significant` | `bool` | True if `p_bonferroni < 0.05` |
| `effect_size_large` | `bool` | True if `|pearson_r| > 0.5` |
| `evaluability_flag` | `bool` | False if valid observations < 30 **or** `n_eff < 30` (data_resources‑9faf82e0) |

## Data Flow

1. **Fetch** → `data/raw/{ace_swpam.csv, ace_swics.csv, kp.txt, dst.txt}` + `checksums.json`.  
2. **Sync** → `data/processed/synced.csv` (7 columns).  
3. **Storm filter** → `StormFilteredRecord` (in‑memory; no separate file).  
4. **Analyze** → `results/full_correlations.csv`.  
5. **Validate** → `results/validation_correlations.csv`, `results/validation_report.md`.  
6. **Plot** → `figures/*.png`.

## Constraints

- Missing required variable ⇒ abort with explicit error (SC‑002).  
- Linear interpolation only for gaps ≤ 6 h; longer gaps excluded from analysis.  
- Lags restricted to no lag, 1, 2, 3, 6 h.  
- Evaluability floor: at least 30 valid observations **and** `n_eff ≥ 30`; otherwise `evaluability_flag` = False.
