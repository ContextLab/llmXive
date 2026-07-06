# Research: Exploring the Correlation Between Atmospheric River Frequency and Global Geopotential Height Variability

## Overview
The research plan operationalises the functional requirements (FR‑001 → FR‑010) using publicly‑available reanalysis data. All steps are fully scripted, container‑compatible, and designed to run on a free‑tier GitHub Actions runner. *Note: Methodological revisions (Spearman, Cluster-FDR) are required to address scientific validity concerns; the source spec must be updated to reflect these changes.*

## Dataset Strategy
| Need | Variable(s) | Verified Source(s) | Acquisition Method |
|------|-------------|--------------------|--------------------|
| Water‑vapor transport (IVT) for AR detection | `integrated_vapor_transport` (kg m⁻¹ s⁻¹) | **Copernicus Climate Data Store (ERA5 Reanalysis)**: | CDS API script (cdsapi) requesting `type: reanalysis`, `variable: integrated_vapor_transport`, `year: 1979-2023`, `month: 01-12`, `area: [60, -100, 20, 60]` (regional subset). |
| 500 hPa geopotential height (Z500) | `z` (m) | **Copernicus Climate Data Store (ERA5 Reanalysis)**: | CDS API script (cdsapi) requesting `type: reanalysis`, `variable: geopotential`, `pressure_level: 500`, `year: 1979-2023`, `month: 01-12`, `area: [60, -100, 20, 60]`. |
| Seasonal indices for validation | PNA, NAO indices | NOAA Climate Data Store (public URL) | `requests.get` from NOAA FTP; stored under `data/external/`. |
| Canonical Teleconnection Templates | PNA, NAO spatial patterns | NOAA Climate Prediction Center (CPC): https://www.cpc.ncep.noaa.gov/data/teledoc/telecontents.shtml | Downloaded as NetCDF/CSV; stored under `data/external/`. |
| Optional: seasonal mask files (DJF, MAM, JJA, SON) | None (derived) | — | Generated from month numbers in preprocessing step. |

> **Note**: The HuggingFace URL previously cited was a single file snapshot and insufficient for the 1979-2023 scope. The plan now relies exclusively on the Copernicus CDS API for full temporal coverage, with explicit retrieval parameters documented in `data/metadata.yaml`.

## Methodological Decisions & Rationale

| Decision | Rationale | Reference |
|----------|-----------|-----------|
| Use **Spearman rank correlation** for association between AR frequency and Z500 anomalies. | AR frequency is a count variable (discrete, zero-inflated); Spearman is robust to non-normality and monotonic relationships. | (Methodological revision) |
| **Cluster-based permutation tests** for multiple-comparison control. | Accounts for strong spatial autocorrelation in geopotential fields; avoids inflated FDR from standard BH. | (Methodological revision) |
| **Bonferroni correction** applied **across latitudinal bands**. | Controls family-wise error rate for the set of bands, as required by Constitution Principle VII. | (Constitution alignment) |
| **Linear detrending** of Z500 time series before anomaly calculation. | Removes secular climate trends to isolate teleconnection signals. | (Methodological revision) |
| **Regional domain subset (20°N-60°N, 100°E-60°W)**. | Ensures feasibility within h/7GB RAM constraints on free-tier runner. | (Compute feasibility) |
| **Teleconnection validation**: (a) Regression against scalar indices; (b) Spatial correlation with canonical templates. | Resolves category error; validates against both time-series dynamics and spatial patterns. | (Methodological revision) |
| **AR_Event structure preservation**. | Ensures traceability of frequency counts back to specific event geometries/timestamps. | (Data Hygiene) |

## Statistical Rigor Checklist
- **Multiple testing**: Cluster-based permutation tests applied per band-season; Bonferroni applied across bands.
- **Power considerations**: 45 years × 12 months provides ~540 temporal samples; sufficient for rank correlation estimation.
- **Causal inference**: Observational study; all statements limited to *associational* claims.
- **Measurement validity**: ERA5 IVT and Z500 are peer-reviewed reanalysis products; citations to ECMWF documentation recorded in `data/metadata.yaml`.
- **Collinearity**: AR frequency and Z500 anomalies are distinct physical fields; no predictor collinearity present.

## Expected Deliverables
1. **Spearman correlation coefficient matrices** (raw and cluster-FDR adjusted) per latitudinal band and season (NetCDF).
2. **Significance masks** (binary NetCDF) for downstream visualisation.
3. **Global PNG maps** with colour-scaled correlations and masked non-significant cells.
4. **Sensitivity-analysis summary CSV** (percentage change in significant cell counts).
5. **Validation report** (JSON) linking significant patterns to PNA/NAO indices (including `pattern_corr` and `p_value`).
6. **Performance log** (`performance.yaml`) containing total runtime and peak RAM.
7. **Reproducibility package** (`analysis_bundle.zip`) with code, data hashes, and environment file.

---