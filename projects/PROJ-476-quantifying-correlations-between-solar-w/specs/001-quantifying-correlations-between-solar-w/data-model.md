# Data Model: Quantifying Correlations Between Solar Wind Composition and Geomagnetic Indices

## Entities

### SolarWindRecord
- `timestamp`: `datetime` (UTC, 1‑hour)
- `proton_density`: `float` (cm⁻³) – from **N_p**
- `temperature`: `float` (K) – from **T_p**
- `helium_abundance`: `float` (dimensionless) – from **He2+_ratio**

### GeomagneticRecord
- `timestamp`: `datetime` (UTC, 1‑hour)
- `kp_index`: `float` (0‑9)
- `dst_index`: `float` (nT)

### SynchronizedRecord
- `timestamp`: `datetime`
- `proton_density`: `float`
- `temperature`: `float`
- `helium_abundance`: `float`
- `kp_index`: `float`
- `dst_index`: `float`
- `interpolated`: `boolean` – true if any field was linearly interpolated (≤ 6 h).

### CorrelationResult
- `composition_parameter`: `string`
- `geomagnetic_index`: `string`
- `lag_hours`: `int`
- `pearson_r`: `float`
- `spearman_rho`: `float`
- `p_raw`: `float`
- `p_bonferroni`: `float`
- `significance_flag`: `boolean`
- `effect_size_flag`: `boolean`

## Data Flow

1. **Raw Ingestion** – `data/raw/ace_*.csv`, `data/raw/noaa_*.csv`.  
2. **Validation** – `code/data/validate.py` checks for `N_p`, `T_p`, `He2+_ratio`; aborts with explicit missing‑variable message (SC‑002).  
3. **Alignment** – `code/data/align.py` produces `SynchronizedRecord` rows; guarantees no NaNs (SC‑004).  
4. **Analysis** – `code/analysis/neff.py` & `correlation.py` generate `CorrelationResult` rows (30 total).  
5. **Output** – `artifacts/correlations.csv` (conforms to `contracts/analysis_schema.schema.yaml`).  
6. **Visualization** – PNG artefacts (validated by `contracts/visual_artifact.schema.yaml`).  
7. **Report** – Markdown report (`contracts/output.schema.yaml`).  

All artefacts are version‑hashed and recorded in `state/`.
