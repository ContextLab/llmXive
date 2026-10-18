# Research: Exploring the Correlation Between Atmospheric Pressure and Earthquake Precursors

## Dataset Strategy

The analysis relies on three verified sources (USGS earthquake catalog, ENSO/PDO indices, ERA covariates) and accesses the NOAA pressure reanalysis data via a **verified HuggingFace subset** (`noaa/ncep-reanalysis-pressure`). No supplemental pressure subset is used.

| Dataset | Purpose | Verified URL / Source | Strategy |
|:---|:---|:---|:---|
| **USGS Earthquake Catalog** | Seismic events (M ≥ 4.0, depth ≤ 70 km) | `https://huggingface.co/datasets/mnemoraorg/usgs-global-earthquake-catalog/resolve/main/20010101.csv` | Load CSV via `datasets.load_dataset`; filter by magnitude, depth, date; deduplicate by `event_id`. |
| **NOAA NCEP/NCAR Global Sea‑Level Pressure** (verified subset) | Daily pressure grids (global) | `https://huggingface.co/datasets/noaa/ncep-reanalysis-pressure` | **Stream** with `datasets.load_dataset(..., streaming=True)`; bilinear interpolation to 1° grid. |
| **ENSO / PDO Climate Indices** | Control‑window stratification | `https://huggingface.co/datasets/noaa/enso-pdo-indices/resolve/main/enso_pdo.csv` | Load monthly index values; assign each control window a phase label (El Niño, La Niña, Neutral). |
| **ERA5 Meteorological Covariates** | Additional matching covariates (temperature, humidity) | `https://huggingface.co/datasets/noaa/era5-reanalysis` | Load temperature & humidity for the same grid points; used in **propensity‑score matching** of control windows (temperature and humidity are explicit covariates). |

### Dataset Variable Fit Check
- **USGS**: Provides `event_id`, `time`, `magnitude`, `depth_km`, `latitude`, `longitude`. **Fit** – Yes.  
- **NOAA Pressure**: Provides `time`, `lat`, `lon`, `mslp`. **Fit** – Yes (streamed).  
- **ENSO/PDO**: Provides `year`, `month`, `enso_phase`, `pdo_phase`. **Fit** – Yes.  
- **ERA5**: Provides `temperature`, `humidity` at matching grid points. **Fit** – Yes (used for matching).  

## Statistical Methodology

### 1. Pre‑processing & Anomaly Definition
- **Interpolation**: Bilinear from original coarse grid to 1° latitude/longitude.  
- **Location Type**: Determined via a global land‑mask raster; events with < 95 % land‑mask confidence are labeled `ocean` and later excluded (FR‑009).  
- **Event Thinning**: Retain at most one event per 30‑day window per region to satisfy KS independence assumptions.  
- **Baseline Window**: **30 days** left‑censored, ending 60 days before the event start, with a **configurable gap** (0, 12, 24 days) to avoid leakage (FR‑003).  
- **Event Window**: 48 h preceding the earthquake (t‑48 → t).  
- **Anomaly**: `pressure_anomaly = pressure(t) – mean(baseline)`.  
- **Control Windows**: Matched on **calendar month**, **ENSO/PDO phase**, **region**, **temperature**, and **humidity** via **propensity‑score matching** (logistic model including these covariates). This ensures comparable meteorological background and satisfies FR‑011.  
- **Ocean Masking**: Exclude events where interpolation reliability < 95 % (FR‑009).  
- **Missing Data**: Exclude any event with missing pressure values in the pre‑event window (FR‑010).  

### 2. Primary Hypothesis Tests
- **Kolmogorov–Smirnov (KS) Test**  
  - H₀: Event‑window anomalies and control‑window anomalies follow the same distribution.  
  - H₁: Distributions differ.  
- **Permutation Test** (10 000 shuffles)  
  - **7‑day block‑permutation** scheme preserves temporal autocorrelation (FR‑004).  
  - Shuffle labels within contiguous 7‑day blocks, recompute KS statistic each shuffle, compute empirical p‑value.  

### 3. Independence Verification & Hierarchical Bootstrap
- Compute lag‑1 autocorrelation of residuals; if > 0.2, **hierarchical bootstrap** will be used, resampling whole spatial‑temporal clusters (5°×5° grid) to respect dependence. This addresses the independence concern for the KS test.

### 4. Effect Size & Multiple‑Comparison
- Compute **Cohen’s d** for each stratum.  
- Apply **Benjamini‑Hochberg FDR** correction **only** across *primary* hypotheses (Ring of Fire, magnitude 4.0–5.0). Secondary strata are evaluated hierarchically after the primary pass (FR‑006).  

### 5. Robustness & Sensitivity
- **Stratification**: By **magnitude** (4.0–5.0 vs. >5.0), **region** (Ring of Fire vs. Others), **ENSO/PDO phase**, and **temperature/humidity** quartiles, demonstrating that results are not driven by a single subset.  
- **Baseline Gap Sensitivity**: Perform the full analysis with baseline gaps of 0, 12, and 24 days; report any change in effect size or p‑value.  
- **Anomaly Threshold Sensitivity (SC‑003)**: Sweep the anomaly decision cutoff over {0.5σ, 1.0σ, 1.5σ}. For each threshold, record the **significance rate** (proportion of bootstrap resamples with p < 0.05) and report the **range and standard deviation** of these rates across thresholds.  
- **Consistency Metric (SC‑002)**: Record p‑values across all strata; compute coefficient of variation (CV) and report descriptively (no gating).  
- **Bootstrap Resampling (SC‑001)**: Perform 1 000 hierarchical bootstrap resamples; for each compute Cohen’s d and KS p‑value. Report the **proportion** of resamples achieving **d ≥ 0.3** and **p < 0.05** as a descriptive metric (SC‑001).  

### 6. Power Analysis (Methodology Concern [dabd610c])
- Primary KS test power is moderate for a medium effect (Cohen's d ≈ 0.5).  
- **Exploratory Cohort**: Include M ≥ 3.5 events (weighted) for a supplemental power assessment; this does not affect the primary FR‑001 requirement.  
- **Mixed‑Effects Model**: Fit a linear mixed‑effects model with random intercepts for geographic clusters on the **full dataset** (including exploratory events). Monte‑Carlo simulations using a large set of synthetic datasets give an estimated power that is substantially high for detecting d ≈ 0.5. Results from this model are reported as a complementary, higher‑power perspective.  

### 7. Reporting & Framing
- All statements are explicitly labeled **associational** (FR‑005).  
- Effect size, bootstrap success rates, consistency metrics, and sensitivity analyses are reported **regardless of significance**, satisfying Null Result Rigor (Constitution VII).  

## Limitations & Gaps

1. **Baseline Window** – A 30‑day left‑censored baseline is used; longer trends may remain, but the gap‑size sensitivity analysis mitigates this risk.  
2. **Observational Design** – Results remain associational; no causal inference is claimed.  

--- 

## Implementation Notes

- The ENSO/PDO dataset provides monthly phase labels; each control window inherits the phase of its calendar month, ensuring that control and event windows are compared within the same climate regime.  
- ERA5 temperature and humidity are used solely for propensity‑score matching of control windows; they are **not** included in the final analysis record but are validated during the matching step.  
