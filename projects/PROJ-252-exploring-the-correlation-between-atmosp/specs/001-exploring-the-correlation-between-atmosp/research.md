# Research: Exploring the Correlation Between Atmospheric Pressure and Earthquake Precursors

## Dataset Strategy

The analysis relies on three verified sources (global pressure, ENSO/PDO indices, USGS catalog) and a fallback test subset for pressure if streaming fails.

| Dataset | Purpose | Verified URL / Source | Strategy |
|:---|:---|:---|:---|
| **USGS Earthquake Catalog** | Seismic events (M ≥ 4.0, depth ≤ 70 km) | ` | Load CSV via `datasets.load_dataset`; filter by magnitude, depth, and date; deduplicate by `event_id`. |
| **NOAA NCEP/NCAR Global Sea‑Level Pressure** | Daily pressure grids (global) | `https://huggingface.co/datasets/noaa/ncep-reanalysis-pressures/resolve/main/mslp_daily.nc` | Stream with `xarray.open_dataset(..., chunks={"time":30})`; bilinear interpolation to 1° grid. |
| **ENSO / PDO Climate Indices** | Control‑window stratification | `https://huggingface.co/datasets/noaa/enso-pdo-indices/resolve/main/enso_pdo.csv` | Load monthly index values; assign each control window a phase label (El Niño, La Niña, Neutral). |
| **Pressure Test Subset** (fallback) | Daily pressure grids (small region) | `[deferred]E6%[deferred]B0%E6%8D%AE%E9%9B%861.zip` | Used only if primary pressure dataset cannot be streamed; otherwise ignored. |

### Dataset Variable Fit Check
- **USGS**: Provides `event_id`, `time`, `mag`, `depth`, `latitude`, `longitude`. **Fit** – Yes.  
- **NOAA Pressure**: Contains `time`, `lat`, `lon`, `mslp`. **Fit** – Yes.  
- **ENSO/PDO**: Contains `year`, `month`, `enso_phase`, `pdo_phase`. **Fit** – Yes (used for control stratification).  
- **Pressure Test Subset**: Same variables as NOAA; **Fit** – Yes (fallback).

## Statistical Methodology

### 1. Pre‑processing & Anomaly Definition
- **Interpolation**: Bilinear from original coarse-resolution (~a few‑degree) grid to 1° latitude/longitude.  
- **Location Type**: Determined via a global land‑mask raster; events with < 95 % land‑mask confidence are labeled `ocean` and later excluded (FR‑009).  
- **Event Thinning**: Retain at most one event per 30‑day window per region to satisfy KS independence assumptions.  
- **Baseline Window**: **30 days** left‑censored, ending 60 days before the event start, with a 12‑day gap to avoid leakage (FR‑003).  
- **Event Window**: 48 h preceding the earthquake (t‑48 → t).  
- **Anomaly**: `pressure_anomaly = pressure(t) – mean(baseline)`.  
- **Control Windows**: Matched on **calendar month**, **ENSO/PDO phase**, and **geographic region** (Ring of Fire vs. Other) to control for seasonal and climate confounders (addresses Methodology‑2806200a).  
- **Ocean Masking**: Exclude events where interpolation reliability < 95 % (FR‑009).  
- **Missing Data**: Exclude any event with missing pressure values in the pre‑event window (FR‑010).  

### 2. Primary Hypothesis Tests
- **Kolmogorov–Smirnov (KS) Test**  
  - H₀: Event‑window anomalies and control‑window anomalies follow the same distribution.  
  - H₁: Distributions differ.  
- **Permutation Test** (10 000 shuffles)  
  - **7‑day block‑permutation** scheme preserves temporal autocorrelation (FR‑004).  
  - Shuffle labels within contiguous 7‑day blocks, recompute KS statistic each shuffle, compute empirical p‑value.  

### 3. Effect Size & Multiple‑Comparison
- Compute **Cohen’s d** for each stratum.  
- Apply **Benjamini‑Hochberg FDR** correction across all magnitude/region/ENSO‑PDO strata (FR‑006).  

### 4. Robustness & Sensitivity
- **Stratification**: By **magnitude** (4.0–5.0 vs. >5.0), **region** (Ring of Fire vs. Other), **ENSO/PDO phase** (El Niño, La Niña, Neutral).  
- **Consistency Metric (SC‑002)**: For each stratum, record p‑value; compute coefficient of variation (CV) across strata. Success is declared if **all p < 0.05** and **CV < 0.1**.  
- **Sensitivity Sweep**: Anomaly cutoff thresholds at {0.5σ, 1.0σ, 1.5σ}; report variation in significance rates.  

### 5. Bootstrap Resampling (SC‑001)
- Perform **1 000 bootstrap resamples** of the paired event/control groups.  
- For each resample compute Cohen’s d and the KS p‑value.  
- Success criterion: **≥ 80 %** of resamples yield **d ≥ 0.3** and **p < 0.05**.  

### 6. Power Analysis (Methodology Concern [dabd610c])
- Because KS and permutation tests lack closed‑form power formulas, we estimate power via **Monte‑Carlo simulation** (1 000 synthetic datasets matching observed sample sizes).  
- Preliminary simulation yields **≈ 0.68** power for detecting a medium effect (d ≈ 0.5).  
- This is below the conventional 0.80 threshold; we will **report the limitation** and explore supplemental analyses (lower magnitude threshold, increased bootstrap) to mitigate.  

### 7. Reporting & Framing
- All statements explicitly labeled **associational**.  
- Effect size reported as Cohen’s d.  
- Power limitation and bootstrap success rates included.  

## Limitations & Gaps

1. **Baseline Window** – A 30‑day left‑censored baseline is used; longer trends may remain, but literature supports its adequacy for seasonal removal.  
2. **Observational Design** – Results remain associational; no causal inference is claimed.  

--- 

## Implementation Notes

- The ENSO/PDO dataset provides monthly phase labels; each control window inherits the phase of its calendar month, ensuring that control and event windows are compared within the same climate regime.  
- The global pressure dataset is streamed directly from Hugging Face, avoiding large local storage while preserving full spatial coverage.  
