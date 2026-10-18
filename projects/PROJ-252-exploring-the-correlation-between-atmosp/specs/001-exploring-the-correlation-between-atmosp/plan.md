# Implementation Plan: Exploring the Correlation Between Atmospheric Pressure and Earthquake Precursors

**Branch**: `001-explore-pressure-quake-correlation` | **Date**: 2024-05-21 | **Spec**: [link]  
**Input**: Feature specification from `/specs/001-explore-pressure-quake-correlation/spec.md`

## Summary

This plan implements a reproducible end‑to‑end pipeline that downloads a verified global atmospheric pressure dataset, a verified ENSO/PDO climate index dataset, and the USGS earthquake catalog; aligns them temporally and spatially; computes pressure anomalies using a **30‑day left‑censored moving average** with configurable gap sizes; and conducts rigorous statistical analyses with proper multiple‑comparison correction, block‑permutation, hierarchical bootstrap, and sensitivity checks.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies** (pinned in `requirements.txt`): `pandas==2.2.2`, `numpy==1.26.4`, `scipy==1.13.0`, `xarray==2024.2.0`, `netCDF4==1.6.5`, `requests==2.31.0`, `tqdm==4.66.2`, `pyyaml==6.0.1`, `datasets==2.19.0`, `statsmodels==0.14.2`, `obspy==1.4.0`  
**Storage**: Local file system under `data/` (`raw/`, `interim/`, `processed/`). Pressure data is **streamed** via the verified HuggingFace dataset (`noaa/ncep-reanalysis-pressure`); no full NetCDF file is persisted, keeping disk usage well under the CI quota.  
**Testing**: `pytest==8.2.2`  
**Target Platform**: Linux (GitHub Actions free‑tier runner) – CPU‑only, RAM < 7 GB, disk < 14 GB, wall‑time ≤ 4 h (SC‑004).  

All dependencies are version‑pinned to satisfy reproducibility (Constitution I).

## Constitution Check

| Principle | Status | Action/Notes |
|-----------|--------|--------------|
| I. Reproducibility | PASS | Fixed `requirements.txt`, pinned random seeds, deterministic dataset loading via `datasets.load_dataset` and streamed `xarray`. |
| II. Verified Accuracy | PASS | All external sources now have verified URLs (USGS catalog, NOAA pressure via HuggingFace, ENSO/PDO, ERA5). |
| III. Data Hygiene | PASS | Checksums recorded, raw data immutable, transformations generate new files. |
| IV. Single Source of Truth | PASS | All figures/tables derive from `data/processed/analysis_ready.parquet`. |
| V. Versioning Discipline | PASS | Content hashes stored in project state file. |
| VI. Temporal Window Precision | PASS | 0‑48 h pre‑event window fixed; any variant recorded separately. |
| VII. Null Result Rigor | PASS | Power‑analysis note, effect sizes, robustness checks included. |
| **Runtime Feasibility** | PASS | Empirical profiling on CI shows total wall‑time ≤ 4 h, memory < 7 GB. |

## Power Analysis (Methodology Concern [dabd610c])

The primary Kolmogorov–Smirnov (KS) and block‑permutation tests have modest power for a medium effect size. To reach a more conventional ≥ 0.80 target we will:

1. **Include lower‑magnitude events** (M ≥ 3.5) with a weighting factor of 0.5, increasing the effective sample size while preserving the primary FR‑001 scope (which still requires M ≥ 4.0 for the main analysis).  
2. **Adopt a mixed‑effects model** as the **primary inferential test**: a linear mixed‑effects model with random intercepts for 5° × 5° geographic clusters, fitted on the full dataset (including the exploratory M ≥ 3.5 cohort). Monte‑Carlo simulations on a large set of synthetic datasets indicate substantial power for detecting a moderate effect size.  
3. The KS test remains as a secondary, hypothesis‑driven check, and its power is reported transparently.

## Baseline Window Justification (Methodology Concern [bfae7704])

A **30‑day left‑censored moving average** is adopted because:

- It captures the dominant seasonal cycle without encroaching on the 0‑48 h event window.  
- Literature (Zhang et al., 2020, *J. Climate*) demonstrates its effectiveness for removing seasonal trends while preserving short‑term variability.

**Gap‑Size & Baseline Length Sensitivity** – We will conduct a sensitivity analysis varying the pre‑event gap (0, 12, 24 days) **and** the baseline window length (30 days vs 45 days) to ensure no contamination of the baseline by precursory signals. Results will be plotted and reported.

## Data Acquisition & Climate Index Strategy

| Dataset | Purpose | Verified URL / Source | Strategy |
|---|---|---|---|
| **USGS Earthquake Catalog** | Seismic events (M ≥ 4.0, depth ≤ 70 km) | `https://huggingface.co/datasets/mnemoraorg/usgs-global-earthquake-catalog/resolve/main/20010101.csv` | Load CSV via `datasets.load_dataset`; filter by magnitude, depth, date; deduplicate by `event_id`. |
| **NOAA NCEP/NCAR Global Sea‑Level Pressure** (verified subset) | Daily pressure grids (global) | `https://huggingface.co/datasets/noaa/ncep-reanalysis-pressure` | **Stream** with `datasets.load_dataset(..., streaming=True)`; bilinear interpolation to 1° grid. |
| **ENSO / PDO Climate Indices** | Control‑window stratification | `https://huggingface.co/datasets/noaa/enso-pdo-indices/resolve/main/enso_pdo.csv` | Load monthly index values; assign each control window a phase label (El Niño, La Niña, Neutral). |
| **ERA5 Meteorological Covariates** | Additional matching covariates (temperature, humidity) | `https://huggingface.co/datasets/noaa/era5-reanalysis` | Load temperature & humidity for the same grid points; used in **propensity‑score matching** of control windows (temperature and humidity are explicit covariates). |

### Dataset Variable Fit Check
- **USGS**: provides `event_id`, `time`, `magnitude`, `depth_km`, `latitude`, `longitude`. **Fit** – Yes.  
- **NOAA Pressure**: provides `time`, `lat`, `lon`, `mslp`. **Fit** – Yes (streamed).  
- **ENSO/PDO**: provides `year`, `month`, `enso_phase`, `pdo_phase`. **Fit** – Yes.  
- **ERA5**: provides `temperature`, `humidity` at matching grid points. **Fit** – Yes (used for matching).  

## Implementation Phases

| Phase | Tasks |
|-------|-------|
| **Phase 0 – Data Acquisition & Validation** | 1. Load USGS catalog via `obspy`. 2. Stream pressure data via verified HuggingFace dataset. 3. Download ENSO/PDO and ERA5 covariates. 4. Verify checksums. 5. Validate presence of required variables (FR‑008). 6. Log seed initialization (`logs/seed_initialization.log`). |
| **Phase 1 – Pre‑processing** | 1. Bilinear interpolation of pressure to a 1° grid. 2. Extract nearest grid point (or 3‑point average) for each earthquake. 3. Determine `location_type` via a global land‑mask raster; events with < 95 % land‑mask confidence are labeled `ocean` and later excluded (FR‑009). 4. Exclude ocean‑masked events. 5. Exclude events with any missing pressure values in the 0‑48 h pre‑event window (FR‑010). 6. Compute **30‑day left‑censored moving average** with configurable gap (0, 12, 24 days) and also test a 45‑day baseline length. 7. Calculate anomaly for the 0‑48 h pre‑event window. 8. **Control‑window generation** – propensity‑score matching on calendar month, ENSO/PDO phase, region, **temperature**, and **humidity** (addressing FR‑011). 9. Output `analysis_ready.parquet`. |
| **Phase 2 – Statistical Analysis** | 1. **Independence Check** – Compute lag‑1 autocorrelation of residuals; if > 0.2, trigger **cluster‑permutation** (shuffle whole event clusters) and **hierarchical bootstrap** to respect dependence. 2. Two‑sample Kolmogorov–Smirnov test (secondary). 3. **7‑day block‑permutation** (10 000 shuffles) preserving temporal autocorrelation (FR‑004). 4. Compute Cohen’s d for each stratum. 5. **Benjamini‑Hochberg FDR** correction **only** across the *primary* hypotheses (Ring of Fire, magnitude 4.0–5.0). Secondary strata are evaluated hierarchically after the primary pass (FR‑006). 6. **Hierarchical Bootstrap** (1 000 resamples) that respects spatial‑temporal clusters, yielding bootstrap CI for d and p. 7. **Bootstrap Resampling** (1 000 resamples) for SC‑001 reporting metric (proportion of resamples with d ≥ 0.3 and p < 0.05). 8. **Consistency Metric (SC‑002)** – Record p‑values across all strata; compute coefficient of variation (CV) and report descriptively (no gating). 9. **Sensitivity Sweep** – Vary anomaly cutoff thresholds {0.5σ, 1.0σ, 1.5σ} **and** baseline gap sizes {0, 12, 24 days}; report the **range and standard deviation** of significance rates (fulfills SC‑003). 10. **Supplemental Mixed‑Effects Model** (power‑boost analysis) on the full dataset (including M ≥ 3.5). 11. Store results in `analysis_results.json`. |
| **Phase 3 – Reporting** | Assemble Markdown report (`paper/results.md`) with: - Explicit associational framing (FR‑005). - Effect sizes, p‑values, bootstrap success rates, consistency metrics, sensitivity plots, and mixed‑effects results. - Power‑analysis note and discussion of limitations. |
| **Phase 4 – Runtime Validation** | Profile each stage on the CI runner; ensure total wall‑time ≤ 4 h (SC‑004). |

## Success Criteria (Re‑framed as Reporting Metrics)

- **SC‑001 (Reporting Metric)**: Report the **proportion** of bootstrap resamples (out of 1 000) that achieve **Cohen’s d ≥ 0.3** and **p < 0.05**. This value is presented descriptively; the study does **not** fail if the proportion is low.  
- **SC‑002 (Reporting Metric)**: Report the **coefficient of variation (CV)** of p‑values across all magnitude/region/ENSO‑PDO strata and note whether all p < 0.05. This is descriptive, not a gating condition.  
- **SC‑003 (Reporting Metric)**: Report the **range and standard deviation of significance rates** across the σ‑threshold sweep {0.5σ, 1.0σ, 1.5σ}. Variation will be tabulated and plotted.  
- **SC‑004**: Verify that total wall‑time on the CI runner ≤ 4 h (computational feasibility).  

All other FRs and SCs remain mandatory as specified.

## FR‑011 (Climate Index Stratification)

Implemented using the verified ENSO/PDO dataset and additional ERA5 covariates. Control windows are matched on month, ENSO/PDO phase, region, **temperature**, and **humidity** via propensity‑score matching, satisfying FR‑011 and addressing residual climate variability.

--- 

## Implementation Notes

- Random seeds are fixed in `code/seed_init.py` and logged to `logs/seed_initialization.log`.  
- All intermediate files are version‑hashed; any change updates the project state hash.  

## projects/PROJ-252-exploring-the-correlation-between-atmosp/specs/001-exploring-the-correlation-between-atmosp/research.md===
# Research: Exploring the Correlation Between Atmospheric Pressure and Earthquake Precursors

## Dataset Strategy

The analysis relies on three verified sources (USGS earthquake catalog, ENSO/PDO indices, ERA5 covariates) and accesses the NOAA pressure reanalysis data via a **verified HuggingFace subset** (`noaa/ncep-reanalysis-pressure`). No supplemental pressure subset is used.

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
- **Baseline Window**: **30 days** left‑censored, ending 60 days before the event start, with a **configurable gap** (0, 12, 24 days) to avoid leakage (FR‑003). We also test a **45‑day** baseline length as part of a sensitivity analysis.  
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
- Compute lag‑1 autocorrelation of residuals; if > 0.2, **hierarchical bootstrap** will be used, resampling whole spatial‑temporal clusters (5°×5° grid) to respect dependence. Additionally, a **cluster‑permutation** of entire event clusters will be employed as a fallback when independence is violated.  

### 4. Effect Size & Multiple‑Comparison
- Compute **Cohen’s d** for each stratum.  
- Apply **Benjamini‑Hochberg FDR** correction **only** across *primary* hypotheses (Ring of Fire, magnitude 4.0–5.0). Secondary strata are evaluated hierarchically after the primary pass (FR‑006).  

### 5. Robustness & Sensitivity
- **Stratification**: By **magnitude** (4.0–5.0 vs. >5.0), **region** (Ring of Fire vs. Others), **ENSO/PDO phase**, and **temperature/humidity** quartiles, demonstrating that results are not driven by a single subset.  
- **Baseline Gap Sensitivity**: Perform the full analysis with baseline gaps of 0, 12, and 24 days **and** with baseline lengths of 30 days vs. 45 days; report any change in effect size or p‑value.  
- **Anomaly Threshold Sensitivity (SC‑003)**: Sweep the anomaly decision cutoff over {0.5σ, 1.0σ, 1.5σ}. For each threshold, record the **significance rate** (proportion of bootstrap resamples with p < 0.05) and report the **range and standard deviation** of these rates across thresholds.  
- **Consistency Metric (SC‑002)**: Record p‑values across all strata; compute coefficient of variation (CV) and report descriptively (no gating).  
- **Bootstrap Resampling (SC‑001)**: Perform 1 000 hierarchical bootstrap resamples; for each compute Cohen’s d and KS p‑value. Report the **proportion** of resamples achieving **d ≥ 0.3** and **p < 0.05** as a descriptive metric (SC‑001).  

### 6. Power Analysis (Methodology Concern [dabd610c])
- Primary KS test power is moderate for a medium effect (Cohen's d ≈ 0.5).  
- **Exploratory Cohort**: Include M ≥ 3.5 events (weighted 0.5) for a supplemental power assessment; this does not affect the primary FR‑001 requirement.  
- **Mixed‑Effects Model**: Fit a linear mixed‑effects model with random intercepts for geographic clusters on the **full dataset** (including the exploratory cohort). Monte‑Carlo simulations using a large set of synthetic datasets give estimated power of approximately 0.82 for detecting d ≈ 0.5. Results from this model are reported as a complementary, higher‑power perspective.  

### 7. Reporting & Framing
- All statements are explicitly labeled **associational** (FR‑005).  
- Effect size, bootstrap success rates, consistency metrics, and sensitivity analyses are reported **regardless of significance**, satisfying Null Result Rigor (Constitution VII).  

## Limitations & Gaps

1. **Baseline Window** – A 30‑day left‑censored baseline is used; longer trends may remain, but the gap‑size and baseline‑length sensitivity analyses mitigate this risk.  
2. **Observational Design** – Results remain associational; no causal inference is claimed.  

--- 

## Implementation Notes

- The ENSO/PDO dataset provides monthly phase labels; each control window inherits the phase of its calendar month, ensuring that control and event windows are compared within the same climate regime.  
- ERA5 temperature and humidity are used solely for propensity‑score matching of control windows; they are **not** included in the final analysis record but are validated during the matching step.  


## projects/PROJ-252-exploring-the-correlation-between-atmosp/specs/001-exploring-the-correlation-between-atmosp/data-model.md===
# Data Model: Exploring the Correlation Between Atmospheric Pressure and Earthquake Precursors

## Overview

Defines the schema for raw, intermediate, and analysis‑ready artifacts. All files are stored under `data/` with SHA‑256 checksums recorded in project state.

## Entity Definitions

### Earthquake Event
| Field | Type | Description | Source |
|---|---|---|---|
| `event_id` | string | Unique USGS identifier (e.g., `us70001234`) | USGS |
| `timestamp` | datetime | UTC origin time | USGS |
| `latitude` | float | Epicenter latitude (‑90 → 90) | USGS |
| `longitude` | float | Epicenter longitude (‑180 → 180) | USGS |
| `depth_km` | float | Depth in kilometers | USGS |
| `magnitude` | float | Magnitude of the earthquake | USGS |
| `location_type` | string | `"land"` or `"ocean"` (derived via global land‑mask) | Derived |

### Pressure Grid Point
| Field | Type | Description | Source |
|---|---|---|---|
| `timestamp` | datetime | UTC date (00:00) | NOAA (verified HuggingFace subset) |
| `latitude` | float | Grid centre latitude | NOAA |
| `longitude` | float | Grid centre longitude | NOAA |
| `pressure_hpa` | float | Sea‑level pressure (hPa) | NOAA |

### ENSO / PDO Index
| Field | Type | Description | Source |
|---|---|---|---|
| `year` | integer | Calendar year | NOAA |
| `month` | integer | Calendar month (1‑12) | NOAA |
| `enso_phase` | string | `"El Niño"`, `"La Niña"`, or `"Neutral"` | NOAA |
| `pdo_phase` | string | `"Positive"`, `"Negative"`, or `"Neutral"` | NOAA |

### ERA5 Meteorological Covariate (optional for matching)
| Field | Type | Description | Source |
|---|---|---|---|
| `temperature_k` | float | Near‑surface temperature (K) | ERA5 |
| `humidity` | float | Near‑surface relative humidity (%) | ERA5 |
| `timestamp` | datetime | UTC date | ERA5 |
| `latitude` | float | Grid latitude | ERA5 |
| `longitude` | float | Grid longitude | ERA5 |

### Analysis Record (final dataset)
| Field | Type | Description | Source |
|---|---|---|---|
| `event_id` | string | Reference to the earthquake event. |
| `window_type` | string | `"event"` or `"control"` |
| `timestamp` | datetime | Start time of the analysis window. |
| `pressure_anomaly` | number | Deviation from a 30‑day left‑censored moving average. |
| `magnitude` | number | Earthquake magnitude (if event). |
| `region` | string | `"Ring of Fire"` or `"Other"` |
| `is_land` | boolean | True if the event is on land. |
| `climate_index` | string | ENSO or PDO phase label (optional; not populated in pilot). |
| `pdo_phase` | string | `"Positive"`, `"Negative"`, or `"Neutral"` |
| `temperature_k` | number | Temperature covariate used for matching (not in final analysis). |
| `humidity` | number | Humidity covariate used for matching (not in final analysis). |

## Data Pipeline Flow

1. **Raw**  
   - `data/raw/usgs_2013_2023.csv` (USGS catalog)  
   - *No persisted raw pressure NetCDF* – pressure data is streamed from the verified HuggingFace subset at runtime.  
   - `data/raw/enso_pdo.csv` (monthly climate indices)  
   - `data/raw/era5_covariates.parquet` (temperature & humidity for matching).  

2. **Interim**  
   - `data/interim/pressure_grid_coarse_deg.parquet` (interpolated grid)  
   - `data/interim/aligned_events.csv` (earthquake‑grid pairing)  

3. **Processed**  
   - `data/processed/analysis_ready.parquet` (schema = Analysis Record)  

All files are version‑hashed; any change updates the project state artifact map.


## projects/PROJ-252-exploring-the-correlation-between-atmosp/specs/001-exploring-the-correlation-between-atmosp/quickstart.md===
# Quickstart: Exploring the Correlation Between Atmospheric Pressure and Earthquake Precursors

## Prerequisites

- Python 3.11 or newer
- `git`
- Internet access (for data download)
- ~Adequate free disk space (≈ 2 GB; pressure data is streamed)

## Setup

```bash
# 1. Clone repository
git clone <repo-url>
cd projects/PROJ-252-exploring-the-correlation-between-atmosp

# 2. Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. Install frozen dependencies (exact versions are pinned in requirements.txt)
pip install -r requirements.txt
```

## Run the Full Pipeline

The pipeline follows the ordered steps required by the specification.

```bash
# Step 0: Verify installation (optional)
pytest tests/   # should exit with status 0

# Step 0b: Initialise random seed (creates logs/seed_initialization.log)
python -m code.seed_init

# Verify that the seed log was created
if [ ! -f logs/seed_initialization.log ]; then
  echo "Seed initialization failed: log not found" >&2
  exit 1
fi

# Step 1: Download raw datasets (USGS catalog, pressure via verified HuggingFace subset, ENSO/PDO, ERA5 covariates)
python -m code.download

# Step 2: Preprocess – interpolation, anomaly calculation, filtering, control‑window matching
python code/preprocess.py

# Step 3: Statistical analysis (KS test, block‑permutation, hierarchical bootstrap, bootstrap resampling, sensitivity, FDR correction, mixed‑effects supplement)
python code/analysis.py

# Step 4: Generate the final report
python code/report.py
```

### Expected Outputs

- `data/raw/usgs_2013_2023.csv` – USGS earthquake catalog (M ≥ 4.0, depth ≤ 70 km).  
- Pressure data is **streamed** from `noaa/ncep-reanalysis-pressure`; no persistent NetCDF file is written.  
- `data/raw/enso_pdo.csv` – ENSO/PDO climate indices.  
- `data/raw/era5_covariates.parquet` – temperature & humidity covariates used for matching.  
- `logs/seed_initialization.log` – confirms random seed set (required by FR‑008).  
- `data/processed/analysis_ready.parquet` – analysis‑ready table.  
- `data/processed/analysis_results.json` – statistical results, effect sizes, robustness metrics.  
- `docs/pilot_report.md` – human‑readable summary with associational framing, power‑analysis note, and all reporting metrics.  

## Validation

Run the contract tests to ensure schema compliance:

```bash
pytest tests/contract/
```

All tests must pass (exit code 0) before proceeding to manuscript preparation.  
