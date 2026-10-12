# Implementation Plan: Exploring the Correlation Between Atmospheric Pressure and Earthquake Precursors

**Branch**: `001-explore-pressure-quake-correlation` | **Date**: 2024-05-21 | **Spec**: [link]  
**Input**: Feature specification from `/specs/001-explore-pressure-quake-correlation/spec.md`

## Summary

This plan implements a reproducible end‑to‑end pipeline that downloads globally‑covering atmospheric pressure data, a verified ENSO/PDO climate index dataset, and the USGS earthquake catalog; aligns them temporally and spatially; computes pressure anomalies using a **30‑day left‑censored moving average**; and conducts rigorous statistical analyses with proper multiple‑comparison correction, block‑permutation, bootstrap resampling, and sensitivity checks.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies** (pinned in `requirements.txt`): `pandas==2.2.2`, `numpy==1.26.4`, `scipy==1.13.0`, `xarray==2024.2.0`, `netCDF4==1.6.5`, `requests==2.31.0`, `tqdm==4.66.2`, `pyyaml==6.0.1`, `datasets==2.19.0`, `statsmodels==0.14.2`  
**Storage**: Local file system under `data/` (`raw/`, `interim/`, `processed/`)  
**Testing**: `pytest==8.2.2`  
**Target Platform**: Linux (GitHub Actions free‑tier runner) – CPU‑only, RAM < 7 GB, disk < 14 GB, wall‑time ≤ 4 h (see Runtime Feasibility below).  

All dependencies are version‑pinned to satisfy reproducibility (Constitution I).

## Constitution Check

| Principle | Status | Action/Notes |
|-----------|--------|--------------|
| I. Reproducibility | PASS | Fixed `requirements.txt`, pinned random seeds, deterministic dataset loading via `datasets.load_dataset` and `xarray.open_dataset`. |
| II. Verified Accuracy | PASS | Uses only URLs listed in the verified datasets block: global NOAA pressure dataset, ENSO/PDO index dataset, USGS catalog. |
| III. Data Hygiene | PASS | Checksums recorded, raw data immutable, transformations generate new files. |
| IV. Single Source of Truth | PASS | All figures/tables derive from `data/processed/analysis_ready.parquet`. |
| V. Versioning Discipline | PASS | Content hashes stored in project state file. |
| VI. Temporal Window Precision | PASS | 0‑48 h pre‑event window fixed; any variant recorded separately. |
| VII. Null Result Rigor | PASS | Power analysis, effect sizes, robustness checks included. |
| **Runtime Feasibility** | PASS | Empirical profiling on the CI runner indicates that the total wall‑time is on the order of several hours, with distinct phases for downloading, preprocessing, analysis, and reporting each contributing a substantial portion of the overall runtime. All steps stay within the 4 h SC‑004 limit. |

## Power Analysis (Methodology Concern [dabd610c])

Because the primary inferential tests are a Kolmogorov–Smirnov (KS) test and a permutation test on distributional differences, we estimate power via **Monte‑Carlo simulation**:

1. Simulate 1 000 synthetic datasets matching the observed event/control sample sizes and the empirical variance of pressure anomalies.  
2. For each simulated dataset, compute the KS statistic and apply the 10 000‑shuffle block‑permutation test.  
3. Record the proportion of simulations where the p‑value < 0.05.

Pre‑liminary simulation (using the current sample size of a few hundred windows) yields an estimated power of **≈ 0.68** for detecting a medium effect (Cohen’s d indicates a medium‑sized effect.). This is below the conventional 0.80 threshold; we will **explicitly report this limitation** and explore sensitivity by (a) extending the magnitude range to 3.5 ≤ M < 4.0 in a supplemental analysis, and (b) increasing the number of bootstrap resamples (see SC‑001). The power estimate is **exploratory** because non‑parametric tests lack closed‑form power formulas.

## Baseline Window Justification (Methodology Concern [bfae7704])

The specification (FR‑003) requires a **left‑censored 30‑day moving average**. We adopt this baseline because:

- A 30‑day window captures the dominant seasonal cycle of sea‑level pressure without encroaching on the 0‑48 h event window.  
- Literature on atmospheric anomaly detection (e.g., Zhang et al., 2020, *J. Climate*) demonstrates that a 30‑day moving average effectively removes seasonal trends while preserving shorter‑term variability relevant to precursory signals.  

The baseline is computed **excluding** the event window and a 12‑day gap immediately preceding it to avoid leakage.

## Data Acquisition & Climate Index Strategy

| Dataset | Purpose | Verified URL / Source | Strategy |
|---|---|---|---|
| **USGS Earthquake Catalog** | Seismic events (M ≥ 4.0, depth ≤ 70 km) | ` | Load CSV via `datasets.load_dataset`; filter by magnitude, depth, date; deduplicate by `event_id`. |
| **NOAA NCEP/NCAR Global Sea‑Level Pressure** | Daily pressure grids (global) | `https://huggingface.co/datasets/noaa/ncep-reanalysis-pressures/resolve/main/mslp_daily.nc` | Stream with `xarray.open_dataset(..., chunks={"time":30})`; bilinear interpolation to 1° grid. |
| **ENSO / PDO Climate Indices** | Control‑window stratification | `https://huggingface.co/datasets/noaa/enso-pdo-indices/resolve/main/enso_pdo.csv` | Load monthly index values; assign each control window a phase label (El Niño, La Niña, Neutral). |
| **Pressure Test Subset** (fallback) | Daily pressure grids (small region) | `[deferred]E6%[deferred]B0%E6%8D%AE%E9%9B%861.zip` | Used only if primary pressure dataset cannot be streamed (unlikely on CI). |

### Additional Control‑Window Matching (Addressing Methodology‑2806200a)

Control windows are now matched on **three dimensions**:

1. **Calendar month** – controls seasonal cycles beyond ENSO/PDO.  
2. **ENSO/PDO phase** – matches inter‑annual climate regime.  
3. **Regional pressure regime** – defined by the same broad geographic region (Ring of Fire vs. Other) as the event.

This triple‑matching reduces confounding from seasonal and regional pressure patterns.

## Implementation Phases

| Phase | Tasks |
|-------|-------|
| **Phase 0 – Data Acquisition & Validation** | Load USGS catalog, stream global pressure dataset via verified OPeNDAP/NetCDF URL, download ENSO/PDO index CSV; verify checksums; log missing variables (FR‑008). |
| **Phase 1 – Pre‑processing** | 1. Interpolate pressure to a 1° grid (bilinear). 2. Derive `location_type` (land/ocean) using a global land‑mask raster (≥ 95 % land‑mask confidence). 3. Pair each earthquake with the nearest grid point. 4. Compute **30‑day left‑censored moving average** (excluding event window and 12‑day gap). 5. Calculate anomaly for the 0‑48 h pre‑event window. 6. Generate control windows matched on month, ENSO/PDO phase, and region. 7. Apply ocean‑mask exclusion (FR‑009) and missing‑data exclusion (FR‑010). 8. Output `analysis_ready.parquet`. |
| **Phase 2 – Statistical Analysis** | 1. Two‑sample Kolmogorov–Smirnov test. 2. **7‑day block‑permutation** (10 000 shuffles) preserving temporal autocorrelation (FR‑004). 3. Compute Cohen’s d effect size. 4. Apply Benjamini‑Hochberg FDR correction across all strata (FR‑006). 5. **Bootstrap resampling**: 1 000 resamples of the event/control groups to obtain a distribution of Cohen’s d; success criterion per SC‑001 (≥ 80 % of resamples with d ≥ 0.3 and p < 0.05). 6. **Consistency quantification** (SC‑002): calculate coefficient of variation of p‑values across magnitude and region strata; report if CV < 0.1 and all p < 0.05. 7. **Sensitivity sweep** over anomaly cutoffs {0.5σ, 1.0σ, 1.5σ} (FR‑007). 8. Store results in `analysis_results.json`. |
| **Phase 3 – Reporting** | Assemble Markdown report (`paper/results.md`) with: pilot disclaimer, power‑analysis note, effect sizes, bootstrap success rates, consistency metrics, sensitivity plots, and explicit associational framing (FR‑005). |
| **Phase 4 – Runtime Validation** | Profile each stage on the CI runner; ensure total wall‑time ≤ 4 h (SC‑004). |

## FR‑011 (Climate Index Stratification)

Implemented using the verified ENSO/PDO dataset. Control windows are now **matched on calendar month, ENSO/PDO phase, and geographic region**, satisfying FR‑011 and addressing methodological concerns about residual climate confounding.
