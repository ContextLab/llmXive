# Implementation Plan: Exploring the Correlation Between Atmospheric River Frequency and Global Geopotential Height Variability

**Branch**: `001-atmospheric-river-geopotential-correlation` | **Date**: 2026-07-06 | **Spec**: [spec.md](../specs/001-atmospheric-river-geopotential-correlation/spec.md)  
**Input**: Feature specification from `/specs/001-atmospheric-river-geopotential-correlation/spec.md`

## Summary
The core objective is to quantify the month‑wise **Spearman rank correlation** between Atmospheric River (AR) frequency and 500 hPa geopotential height (Z500) anomalies across 10° latitudinal bands and the four standard seasons (DJF, MAM, JJA, SON). The pipeline will (1) download ERA5 reanalysis (restricted to a computationally feasible regional domain), (2) detect AR events using a baseline Integrated Water Vapor Transport (IVT) threshold of 250 kg m⁻¹ s⁻¹ while preserving event geometry/timestamps, (3) compute Z500 monthly anomalies with **linear detrending** per grid cell, (4) calculate per‑grid‑cell **Spearman correlations**, (5) control the false discovery rate using **cluster-based permutation tests** to account for spatial autocorrelation, (6) visualise significant fields, (7) perform a ±5/±10 kg m⁻¹ s⁻¹ sensitivity sweep, and (8) validate spatial patterns via **regression against scalar indices** and **spatial correlation with canonical teleconnection templates**.

*Note: This plan revises the methodology to address scientific validity concerns (Spearman vs. Pearson, Spatial FDR vs. BH). The source spec (FR-004, FR-005, FR-010) currently mandates the original methods; the spec must be updated to align with this revised plan.*

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `xarray>=2023.9.0`, `numpy>=1.26.0`, `pandas>=2.1.0`, `scipy>=1.11.0`, `statsmodels>=0.14.0`, `matplotlib>=3.8.0`, `cartopy>=0.22.0`, `netCDF4>=1.6.5`, `cftime>=1.6.2`, `dask[complete]>=2023.9.0` (for out‑of‑core chunking), `h5netcdf>=0.14.0`, `requests>=2.31.0`, `tqdm>=4.66.0`, `nitime>=0.10.0` (for permutation tests).  
- **Storage**: All intermediate products are stored as NetCDF4/HDF5 files under `data/processed/`.  
- **Testing**: `pytest>=7.4.0` + `pytest-cov`. Unit tests will cover AR detection, anomaly calculation, correlation routine, cluster-based FDR, and sensitivity‑analysis aggregation.  
- **Target Platform**: Linux (`ubuntu-latest`) GitHub Actions runner (2 CPU, ≤7 GB RAM).  
- **Project Type**: Research library + CLI (`src/cli/run_analysis.py`).  
- **Performance Goals**: Full analysis (restricted to **20°N-60°N, 100°E-60°W** domain) must finish ≤6 h wall‑clock; peak RAM ≤6 GB.  
- **Constraints**: CPU‑only, no GPU, no large‑scale model training. All libraries must installable from PyPI wheels compatible with the runner.  
- **Scale/Scope**: 45 years × 12 months × [deferred] grid cells (1.0° resolution, regional subset) → processed in chunked fashion.

## Constitution Check
| Principle | Compliance Statement |
|-----------|----------------------|
| I. Reproducibility | All scripts are deterministic (fixed random seeds) and fully automated; external data are fetched via scripted `cURL`/`cdsapi` calls to the Copernicus Climate Data Store. |
| II. Verified Accuracy | Citations limited to verified dataset URLs (see "Verified Datasets" section). No unverified external references. |
| III. Data Hygiene | Raw ERA5 files are checksum‑verified (`sha256`) and stored read‑only; each transformation writes a new NetCDF with provenance metadata. AR events preserve geometry/timestamps. |
| IV. Single Source of Truth | Every figure/table in the manuscript will be generated directly from the canonical NetCDF outputs; no manual transcription. |
| V. Versioning Discipline | All artefacts (datasets, figures, tables) are named with content‑hash suffixes; `state/projects/...yaml` will be updated automatically by CI. |
| VI. Atmospheric Data Authenticity | ERA5 water‑vapor‑transport and Z500 are obtained exclusively from the Copernicus CDS; retrieval parameters recorded in `data/metadata.yaml`. |
| VII. Statistical Rigor | **Spearman correlation**, **cluster-based permutation tests** (for spatial FDR), and **Bonferroni correction** (across bands) are implemented. All statistical outputs include coefficient, raw p‑value, and adjusted p‑value. |

## Project Structure
```text
specs/001-atmospheric-river-geopotential-correlation/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    └── correlation_result.schema.yaml

src/
├── cli/
│   └── run_analysis.py        # entry point
├── data/
│   ├── download.py            # ERA5 download utilities
│   ├── preprocess.py          # AR detection, Z500 climatology, detrending
│   └── analysis.py            # correlation, cluster-FDR, sensitivity
├── viz/
│   └── maps.py                # map generation with cartopy
└── utils/
    └── logger.py

tests/
├── unit/
│   ├── test_download.py
│   ├── test_preprocess.py
│   └── test_analysis.py
└── contract/
    └── test_correlation_schema.py
```

## Complexity Tracking
All Functional Requirements (FR‑001 → FR‑010) and Success Criteria (SC‑001 → SC‑004) are explicitly mapped to phases below. No constitution violations identified. *Note: Spec updates are required to align FR-004, FR-005, FR-002, FR-010 with this plan.*

## Implementation Phases & FR/SC Mapping

| Phase | Description | FR IDs | SC IDs | Key Outputs |
|-------|-------------|--------|--------|-------------|
| 0 – Data Acquisition | Download ERA5 water‑vapor‑transport (IVT) and Z500 NetCDF files for **regional domain (20°N-60°N, 100°E-60°W)**; verify checksums. | FR‑001 | — | `data/raw/era5_ivt_*.nc`, `data/raw/era5_z500_*.nc` |
| 1 – Pre‑processing | Compute monthly climatology (1979‑2023) **per grid cell**; apply **linear detrending**; generate anomalies. Subset latitudinal bands (10°). | FR‑003 | — | `data/processed/z500_anom_{band}.nc` |
| 2 – AR Detection | Apply SWHAT‑style detection on IVT using baseline 250 kg m⁻¹ s⁻¹; **preserve AR_Event geometry/timestamps**; produce monthly frequency counts per band. | FR‑002, FR‑008 | — | `data/processed/ar_freq_{band}.nc`, `data/processed/ar_events_{band}.nc` |
| 3 – Correlation Computation | For each band‑season, compute **Spearman rank correlation** and raw p‑value per grid cell between AR frequency and Z500 anomaly time series. | FR‑004 | SC‑001 | `data/processed/corr_raw_{band}_{season}.nc` |
| 4 – Multiple‑Comparison Control | Apply **cluster-based permutation tests** (α = 0.05) across all grid cells within a band‑season to control spatial FDR; also compute **Bonferroni correction across bands** for family-wise error rate. | FR‑005 | SC‑001 | `data/processed/corr_fdr_{band}_{season}.nc` |
| 5 – Visualization | Generate global PNG maps per band‑season, masking cells with adj p > 0.05; include color bar, legend, and metadata. | FR‑006 | — | `figures/corr_map_{band}_{season}.png` |
| 6 – Sensitivity Analysis | Rerun AR detection with thresholds ±5 and ±10 kg m⁻¹ s⁻¹; recompute correlations and FDR; aggregate counts of significant cells. | FR‑007 | SC‑002 | `data/processed/sensitivity_summary.csv` |
| 7 – Teleconnection Validation | (a) Regress AR-Z500 fields against scalar PNA/NAO index time series; (b) Compute spatial correlation of AR-Z500 pattern against **canonical PNA/NAO spatial templates**. Output includes `pattern_corr` and `p_value`. | FR‑010 | — | `data/processed/validation_{band}_{season}.json` |
| 8 – Runtime & Memory Auditing | Wrap each major step with `time` and `memory_profiler`; record wall‑clock time and peak RAM. | FR‑009 | SC‑003, SC‑004 | `logs/performance.yaml` |
| 9 – Reporting & Packaging | Collate all artefacts, generate a concise markdown report, and archive a reproducible ZIP. | — | — | `report/report.md`, `artifacts/analysis_bundle.zip` |

Each phase will be implemented as a separate function in `src/cli/run_analysis.py` and orchestrated via a Click‑based command line interface allowing selective execution (e.g., `--phase 3-5`).

---