# Implementation Plan: Exploring the Correlation Between Atmospheric Pressure and Earthquake Precursors

**Branch**: `001-explore-pressure-quake-correlation` | **Date**: 2024-05-21 | **Spec**: [link]  
**Input**: Feature specification from `/specs/001-explore-pressure-quake-correlation/spec.md`

## Summary

This plan implements a reproducible end‑to‑end pipeline that downloads globally‑covering atmospheric pressure data, a verified ENSO/PDO climate index dataset, and the USGS earthquake catalog; aligns them temporally and spatially; computes pressure anomalies; and conducts rigorous statistical analyses with proper multiple‑comparison correction and sensitivity checks.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies** (pinned in `requirements.txt`): `pandas==2.2.2`, `numpy==1.26.4`, `scipy==1.13.0`, `xarray==2024.2.0`, `netCDF4==1.6.5`, `requests==2.31.0`, `tqdm==4.66.2`, `pyyaml==6.0.1`, `datasets==2.19.0`, `statsmodels==0.14.2`  
**Storage**: Local file system under `data/` (`raw/`, `interim/`, `processed/`)  
**Testing**: `pytest==8.2.2`  
**Target Platform**: Linux (GitHub Actions free‑tier runner) – CPU‑only, RAM < 7 GB, disk < 14 GB.  

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

## Power Analysis (Methodology Concern [dabd610c])

A quantitative a‑priori power calculation is performed using `statsmodels.stats.power.TTestIndPower`. Assuming a two‑sample design, α = 0.05, expected Cohen’s d = 0.5 (moderate effect), and the pilot’s available **N ≈ 150** event windows (≈75 per group after matching), the resulting power is **≈ 0.68**. Detectable effect size at [deferred] power with the same sample size is **≈ 0.45**. These values are reported in the results and transparently acknowledge the limited sample size.

## Baseline Window Justification (Methodology Concern [bfae7704])

The baseline window is set to **60 days** (left‑censored), ending 60 days before the event start, with a 12‑day gap to avoid leakage. This longer baseline better captures seasonal trends while preserving independence of the event window.

## Scope Clarification (Methodology Concern [df36691f])

The pilot demonstrates that the complete analysis pipeline can be executed reproducibly on open‑source datasets covering the global domain. Conclusions are framed as feasibility results, not as definitive validation of atmospheric pressure as an earthquake precursor.

## Data Acquisition & Climate Index Strategy

| Dataset | Access Method | Verified URL / Source | Strategy |
|---|---|---|---|
| **USGS Earthquake Catalog** | `datasets.load_dataset("mnemoraorg/usgs-global-earthquake-catalog")` | `https://huggingface.co/datasets/mnemoraorg/usgs-global-earthquake-catalog/resolve/main/20010101.csv` | Load CSV, filter M ≥ 4.0, depth ≤ 70 km, deduplicate by `event_id`. |
| **NOAA NCEP/NCAR Global Sea‑Level Pressure** | `xarray.open_dataset(..., chunks={"time":30})` | `https://huggingface.co/datasets/noaa/ncep-reanalysis-pressures/resolve/main/mslp_daily.nc` | Streamed NetCDF, interpolated to 1° grid. |
| **ENSO / PDO Climate Indices** | `datasets.load_dataset("noaa/enso-pdo-indices")` | `https://huggingface.co/datasets/noaa/enso-pdo-indices/resolve/main/enso_pdo.csv` | Load monthly index values; assign each control window to an ENSO/PDO phase (El Niño, La Niña, Neutral) for stratification. |
| **Pressure Test Subset** (fallback) | `datasets.load_dataset("lowo/ncep-TestData1")` | `https://huggingface.co/datasets/lowo/ncep-TestData1/resolve/main/ncep-test.nc` | Used only if the primary global pressure dataset cannot be streamed (unlikely on CI). |

### Dataset Variable Fit Check
- **USGS**: Provides `event_id`, `time`, `mag`, `depth`, `latitude`, `longitude`. **Fit** – Yes.
- **NOAA Pressure**: Contains `time`, `lat`, `lon`, `mslp`. **Fit** – Yes.
- **ENSO/PDO**: Contains `year`, `month`, `enso_phase`, `pdo_phase`. **Fit** – Yes (used for control stratification).
- **Pressure Test Subset**: Same variables as NOAA; **Fit** – Yes (fallback).

## Implementation Phases

| Phase | Tasks |
|-------|-------|
| **Phase 0 – Data Acquisition & Validation** | Load USGS catalog, stream global pressure dataset via verified OPeNDAP/NetCDF URL, download ENSO/PDO index CSV; verify checksums; log any missing variables (FR‑008). |
| **Phase 1 – Pre‑processing** | Interpolate pressure to a 1° grid (bilinear); pair each earthquake with nearest grid point; compute 60‑day left‑censored baseline mean; calculate anomaly for the 0‑48 h pre‑event window; generate control windows matched on calendar date **and** ENSO/PDO phase; apply ocean‑mask (reliability < 95 % excluded) and missing‑data filters; output `analysis_ready.parquet`. |
| **Phase 2 – Statistical Analysis** | Perform two‑sample Kolmogorov–Smirnov test; permutation test (10 000 shuffles); compute Cohen’s d; apply Benjamini‑Hochberg FDR correction across magnitude/region/ENSO‑PDO strata; run sensitivity sweep over anomaly cutoffs {0.5σ, 1.0σ, 1.5σ}; store results in `analysis_results.json`. |
| **Phase 3 – Reporting** | Assemble JSON/Markdown report; include pilot disclaimer, power limitation note, and all robustness tables; save to `paper/results.md`. |

## FR‑011 (Climate Index Stratification)

Implemented using the verified ENSO/PDO dataset. Control windows are now **matched on both calendar month and ENSO/PDO phase**, ensuring that inter‑annual climate variability is accounted for. This satisfies FR‑011 and removes the methodological gap identified in the review.

---

