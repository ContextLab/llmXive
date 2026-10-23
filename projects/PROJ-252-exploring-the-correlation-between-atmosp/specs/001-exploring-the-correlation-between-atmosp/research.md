# Research: Exploring the Correlation Between Atmospheric Pressure and Earthquake Precursors

## Dataset Strategy

The project now uses two verified, programmatically‑downloadable datasets:

| Dataset | Purpose | Verified URL / Source | Strategy |
|:---|:---|:---|:---|
| **USGS Earthquake Catalog (monthly feed)** | Seismic events (M ≥ 4.0, depth ≤ 70 km) | `https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_month.csv` | Load CSV via `pandas.read_csv`, filter by date/magnitude/depth, deduplicate by `event_id`. |
| **NOAA NCEP/NCAR Reanalysis Surface Pressure** | Daily global sea‑level pressure grids (1990‑2023) | `https://psl.noaa.gov/data/gridded/data.ncep.reanalysis.surface.html` (accessed via OPeNDAP) | Stream with `xarray.open_dataset(..., chunks={"time": 30})`, interpolate to nearest 1° grid point for each earthquake, compute left‑censored 30‑day moving‑average anomalies. |
| **ENSO / PDO indices, ERA5 temperature & humidity** | Control‑window matching (required by FR‑011) | *No verified URL in the provided list* | **Deferred** – currently use simple random control windows; document limitation and plan to add matching when datasets become available. |

### Dataset Variable Fit Check
- **USGS CSV** supplies `event_id`, `timestamp`, `latitude`, `longitude`, `depth_km`, `magnitude` – all required by FR‑001, FR‑008, FR‑009, FR‑010. **Fit** – Yes.  
- **Pressure Reanalysis** provides `timestamp`, `latitude`, `longitude`, `pressure_hpa` – satisfies FR‑002. **Fit** – Yes.  
- **Climate indices** – not available; variable fit cannot be confirmed (deferred).

## Statistical Methodology (Primary)

With pressure anomalies now available, the core analysis proceeds as follows:

1. **Pre‑processing** – Interpolate pressure to the nearest 1° grid point for each earthquake, compute daily anomalies by subtracting a left‑censored 30‑day moving average (baseline gap selectable).  
2. **Control‑window generation** – Simple random temporal sampling within the same calendar month, preserving seasonal structure (full ENSO/PDO/temperature/humidity matching deferred).  
3. **Primary Test** – **Block‑permutation test** (10 000 iterations, 7‑day blocks) on the **mean pressure‑anomaly difference** between event and control windows. For each permutation compute Cohen’s d; the p‑value is the proportion of permuted |d| ≥ observed |d|.  
4. **Bootstrap CI** – 1 000 bootstrap resamples of the observed Cohen’s d to obtain a 95 % confidence interval.  
5. **Multiple‑testing correction** – Hierarchical Benjamini‑Hochberg FDR (α = 0.05) applied to secondary subgroup tests (region, magnitude).  
6. **Robustness & Sensitivity** – (Deferred) anomaly‑threshold sweeps {0.5σ, 1.0σ, 1.5σ} and baseline‑gap sensitivity (12, 20, 30 days).  

All findings are explicitly framed as **associational**, complying with Constitution II.

## Limitations & Gaps

- **Climate‑index matching** is not performed due to lack of verified ENSO/PDO and ERA5 datasets; simple random controls are used instead.  
- **Power analysis** is conducted after pressure data integration (Phase 4) because effect size estimation requires the predictor variable.  
- **Observational design** – causal claims are avoided per Constitution II.  

---

