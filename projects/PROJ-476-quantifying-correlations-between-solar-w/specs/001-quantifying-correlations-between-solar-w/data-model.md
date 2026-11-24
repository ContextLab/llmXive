# Data Model: Quantifying Correlations Between Solar Wind Composition and Geomagnetic Indices

## Entities

### SolarWindRecord (raw, ACE)
| Field | Type | Description | Source |
|---|---|---|---|
| `timestamp` | `datetime` | UTC epoch of measurement | ACE SWEPAM / SWICS Level 2 |
| `N_p` | `float` | Proton density (cm⁻³) | SWEPAM |
| `T_p` | `float` | Proton temperature (K) | SWEPAM |
| `He2+_ratio` | `float` | He²⁺/H⁺ abundance ratio | SWICS |

### GeomagneticRecord (raw, NOAA/Kyoto)
| Field | Type | Description | Source |
|---|---|---|---|
| `timestamp` | `datetime` | UTC hour | NOAA SWPC / Kyoto WDC |
| `Kp` | `float` | Planetary K‑index (0–9) | NOAA |
| `Dst` | `float` | Disturbance Storm Time index (nT) | Kyoto |

### SynchronizedRecord (`data/processed/synced.csv`)
| Field | Type | Description |
|---|---|---|
| `timestamp` | `datetime` (ISO‑8601) | 1‑h UTC grid |
| `proton_density` | `float` | `N_p`; interpolated if gap ≤ 6 h |
| `temperature` | `float` | `T_p`; interpolated if gap ≤ 6 h |
| `helium_abundance` | `float` | `He2+_ratio`; interpolated if gap ≤ 6 h |
| `Kp` | `float` | Hourly Kp |
| `Dst` | `float` | Hourly Dst |
| `interpolated_flag` | `bool` | True if any column in the row was interpolated |

### StormFilteredRecord (in‑memory)
| Field | Type | Description |
|---|---|---|
| `timestamp` | `datetime` | Subset of `SynchronizedRecord` where `Dst < -50` nT |
| *(inherits all other columns)* |  |  |

### CorrelationResult (`results/*.csv`)
| Field | Type | Description |
|---|---|---|
| `composition_parameter` | `str` | `proton_density` | `temperature` | `helium_abundance` |
| `geomagnetic_index` | `str` | `Kp` | `Dst` |
| `lag_hours` | `int` | 0 | 1 | 2 | 3 | 6 |
| `pearson_r` | `float` | Pearson correlation coefficient |
| `spearman_rho` | `float` | Spearman rank correlation |
| `n_eff` | `float` | Effective sample size (Pyper & Peterman) |
| `p_raw` | `float` | Raw p‑value (Pearson t‑approx or Spearman permutation) |
| `p_bonferroni` | `float` | Bonferroni‑adjusted p‑value |
| `significant` | `bool` | `p_bonferroni < 0.05` |
| `effect_size_large` | `bool` | `|pearson_r| > 0.5` |
| `evaluability_flag` | `bool` | False if valid observations < 30 or n_eff < 30 |

## Data Flow
1. **Fetch** → `data/raw/` (ACE CSVs, Kp/Dst text files) + `checksums.json`.  
2. **Sync** → `data/processed/synced.csv`.  
3. **Storm filter** (optional) → in‑memory `StormFilteredRecord`.  
4. **Analyze** → `results/full_correlations.csv` (full) and optionally `results/storm_correlations.csv`.  
5. **Validate** → `results/validation_correlations.csv`, `validation_report.md`.  
6. **Visualise** → `figures/*.png`.

## Constraints
- **Missing variable** → abort with explicit error (SC‑002).  
- **Interpolation** only for gaps ≤ 6 h; longer gaps are excluded.  
- **Lag set** fixed to {0,1,2,3,6}.  
- **Evaluability floor**: ≥ 30 valid observations **and** `n_eff ≥ 30`; otherwise `evaluability_flag = False`.  
- **File size limits**: PNG ≤ 5 MB (FR‑008).  

---

