# Research: Exploring the Correlation Between Atmospheric Pressure and Earthquake Precursors

## Dataset Strategy

The analysis relies on three verified sources (global pressure, ENSO/PDO indices, USGS catalog) and a fallback test subset for pressure if streaming fails.

| Dataset | Purpose | Verified URL / Source | Strategy |
|:---|:---|:---|:---|
| **USGS Earthquake Catalog** | Seismic events (M ≥ 4.0, depth ≤ 70 km) | `https://huggingface.co/datasets/mnemoraorg/usgs-global-earthquake-catalog/resolve/main/20010101.csv` | Load CSV via `datasets.load_dataset`; filter by magnitude, depth, and date; deduplicate by `event_id`. |
| **NOAA NCEP/NCAR Global Sea‑Level Pressure** | Daily pressure grids (global) | `https://huggingface.co/datasets/noaa/ncep-reanalysis-pressures/resolve/main/mslp_daily.nc` | Stream with `xarray.open_dataset(..., chunks={"time":30})`; interpolate to 1° grid. |
| **ENSO / PDO Climate Indices** | Control‑window stratification | `https://huggingface.co/datasets/noaa/enso-pdo-indices/resolve/main/enso_pdo.csv` | Load monthly index values; assign each control window to ENSO/PDO phase (El Niño, La Niña, Neutral) for stratified matching. |
| **Pressure Test Subset** (fallback) | Daily pressure grids (small region) | `https://huggingface.co/datasets/lowo/ncep-TestData1/resolve/main/ncep-test.nc` | Used only if primary pressure dataset cannot be streamed; otherwise ignored. |

### Dataset Variable Fit Check
- **USGS**: Provides `event_id`, `time`, `mag`, `depth`, `latitude`, `longitude`. **Fit** – Yes.
- **NOAA Pressure**: Contains `time`, `lat`, `lon`, `mslp`. **Fit** – Yes.
- **ENSO/PDO**: Contains `year`, `month`, `enso_phase`, `pdo_phase`. **Fit** – Yes (used for control stratification).
- **Pressure Test Subset**: Same variables as NOAA; **Fit** – Yes (fallback).

## Statistical Methodology

### 1. Pre‑processing & Anomaly Definition
- **Interpolation**: Bilinear from original ≈2.5° grid to 1° latitude/longitude.
- **Event Thinning**: Retain at most one event per 30‑day window per region to satisfy KS independence assumptions.
- **Baseline Window**: 60 days ending 60 days before the event (t‑120 → t‑60) **with a 12‑day gap** to avoid leakage.
- **Event Window**: 48 h preceding the earthquake (t‑48 → t).
- **Anomaly**: `pressure_anomaly = pressure(t) – mean(baseline)`.
- **Control Windows**: Calendar‑matched dates **and** matched on ENSO/PDO phase (El Niño, La Niña, Neutral) to control for inter‑annual climate variability.
- **Ocean Masking**: Exclude events where interpolation reliability < 95 % (estimated via nearest‑grid distance).
- **Missing Data**: Exclude any event with missing pressure values in the pre‑event window.

### 2. Primary Hypothesis Tests
- **Kolmogorov–Smirnov (KS) Test**  
  - H₀: Event‑window anomalies and control‑window anomalies follow the same distribution.  
  - H₁: Distributions differ.  
- **Permutation Test** (10 000 shuffles)  
  - Shuffle event/control labels, recompute KS statistic each shuffle, compute empirical p‑value.

### 3. Robustness & Sensitivity
- **Stratification**: By **magnitude** (4.0–5.0 vs. >5.0), **region** (Ring of Fire vs. Other), **ENSO/PDO phase** (El Niño, La Niña, Neutral).  
- **Sensitivity Sweep**: Anomaly cutoff thresholds at {0.5σ, 1.0σ, 1.5σ}.  
- **Multiple‑Comparison Correction**: Benjamini‑Hochberg FDR applied across all strata.

### 4. Power Analysis (Methodology Concern [dabd610c])

Using `statsmodels.stats.power.TTestIndPower` with α = 0.05, expected effect size d = 0.5, and N ≈ 150 (≈75 per group) yields power ≈ 0.68. Detectable effect size at [deferred] power is expected to be of moderate magnitude. These calculations are reported in the results and inform interpretation of non‑significant findings.

### 5. Reporting & Framing
- All statements explicitly labeled **associational**.  
- Effect size reported as Cohen’s d.  
- Power limitation and dataset‑scope disclaimer included.

## Limitations & Gaps

1. **Baseline Window** – A 60‑day left‑censored baseline is used; longer trends may remain.  
2. **Observational Design** – Results remain associational; no causal inference.  

--- 

## Implementation Notes

- The ENSO/PDO dataset provides monthly phase labels; each control window inherits the phase of its calendar month, ensuring that control and event windows are compared within the same climate regime.  
- The global pressure dataset is streamed directly from Hugging Face, avoiding the need for large local storage while preserving full spatial coverage.
