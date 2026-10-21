# Implementation Plan: Statistical Analysis of OpenStreetMap Data for Urban Heat Island Effects

**Branch**: `PROJ-125-statistical-analysis-of-openstreetmap-da` | **Date**: 2026-10-21 | **Spec**: `specs/001-statistical-analysis-of-openstreetmap-da/spec.md`  
**Input**: Feature specification from `specs/001-statistical-analysis-of-openstreetmap-da/spec.md`

## Summary
The pipeline will (1) ingest OpenStreetMap vector layers and cloud‑screened Landsat thermal rasters for up to ten configured cities, (2) reproject all layers to a locally‑determined UTM zone and rasterize to a 30 m grid, (3) compute exploratory spatial statistics, (4) fit OLS, SAR, and GWR models with a memory‑aware fallback to OLS‑only, (5) evaluate models using 5‑fold spatial cross‑validation, (6) apply permutation‑based FDR correction, (7) conduct a bandwidth‑sweep sensitivity analysis (or OLS coefficient‑stability sweep in degraded mode), (8) calculate the Unexplained Variance Gap, and (9) generate reproducible CSV/plot artifacts and a final report. All steps are deterministic, checkpointed, and respect the memory caps of a GitHub Actions free‑tier runner.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `osmnx`, `geopandas`, `rasterio`, `xarray`, `numpy`, `pandas`, `scikit-learn`, `statsmodels`, `pysal` (for SAR), `mgwr` (for GWR), `psutil`, `ruff`, `black`, `pytest`.  
- **Storage**: Local filesystem under `data/` (raw, processed, results).  
- **Testing**: `pytest` with coverage ≥ 80 % for core modules; linting via `ruff` + `black`.  
- **Target Platform**: Linux CI runner (2 CPU, ~7 GB RAM, ~14 GB disk).  
- **Constraints**: Peak RAM ≤ 6 GB; degrade to OLS‑only when RAM > 5 GB or cell count ≥ 500 k. No GPU required.  
- **Scale/Scope**: Up to ten cities; each city raster ≤ 500 k cells after optional spatial sampling.

## Constitution Check
| Principle | Status | Action |
|-----------|--------|--------|
| I. Reproducibility | **PASS** | Fixed seeds, pinned `requirements.txt`, deterministic data fetch URLs. |
| II. Verified Accuracy | **PASS** | All external citations will be validated; FR‑010’s literature ceiling will be flagged for verification. |
| III. Data Hygiene | **PASS** | Checksums recorded for every raw file; transformations are immutable. |
| IV. Single Source of Truth | **PASS** | All statistics drawn from `data/results/metrics.csv` and referenced in the report. |
| V. Versioning Discipline | **PASS** | Artifact hashes stored in project state YAML. |
| VI. Spatial Resolution Integrity | **PASS** | Reprojection to local UTM, 30 m aggregation, and explicit logging of methods (nearest‑neighbor, bilinear). |
| VII. Proxy Validity Boundaries | **PASS** | Unexplained Variance Gap and sensitivity analysis included per FR‑010/FR‑009. |

## Project Structure
```text
specs/001-statistical-analysis-of-openstreetmap-da/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── dataset.schema.yaml
│   ├── metrics.schema.yaml
│   ├── model_output.schema.yaml
│   └── output.schema.yaml
└── tasks.md   # generated later
```

```text
projects/PROJ-125-statistical-analysis-of-openstreetmap-da/
├── code/
│   ├── __init__.py
│   ├── config.py                # seeds, MAX_MEMORY_GB, MAX_SAMPLES, city list
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── io.py                # download, checksum, rasterize
│   │   └── memory.py            # psutil monitor, fallback trigger
│   ├── models/
│   │   ├── __init__.py
│   │   ├── ols.py
│   │   ├── sar.py
│   │   └── gwr.py
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── exploratory.py       # corr, Moran's I
│   │   └── validation.py        # spatial CV, FDR
│   └── main.py                  # orchestrates pipeline
├── data/
│   ├── raw/
│   ├── processed/
│   └── results/
├── tests/
│   ├── unit/
│   │   ├── test_config.py
│   │   ├── test_memory.py
│   │   └── test_io.py
│   └── integration/
│       └── test_pipeline.py
├── docs/
│   └── quickstart.md
└── requirements.txt
```

## Implementation Phases & FR/SC Coverage
| Phase | Tasks | FR IDs | SC IDs | Notes |
|-------|-------|--------|--------|-------|
| **1. Data Ingestion** | - Download city boundary via `geopandas` (GADM/Natural Earth).<br>- Pull OSM vectors (buildings, land‑use, trees, roads) using `osmnx` or HuggingFace parquet URLs.<br>- Pull cloud‑screened Landsat LST composite (5‑year median) via NASA EarthData API. | FR‑001, FR‑002, FR‑012 | SC‑001, SC‑002 | Landsat source is not in the verified list; pipeline will abort with clear error if download fails. |
| **2. Preprocessing** | - Reproject all layers to local UTM (city centroid) or EPSG:3857 fallback.<br>- Rasterize OSM features to 30 m grid (nearest‑neighbor for categorical, bilinear for continuous).<br>- Align LST raster to same grid.<br>- Write transformation log (`data/processed/transformation_log.json`). | FR‑003, FR‑011 | SC‑001 | Logs satisfy Principle VI. |
| **3. Exploratory Spatial Stats** | - Compute Pearson correlation matrix.<br>- Compute Moran’s I for LST and each covariate (`pysal`). | FR‑004 | SC‑001 | Results stored in `data/results/exploratory.csv`. |
| **4. Memory Safety & Sampling** | - Estimate cell count N.<br>- If N ≥ 500 k, apply spatial block sampling to reduce to ≤ 500 k cells.<br>- Run `psutil` monitor; if peak > 5 GB trigger OLS‑DEGRADED flag; if > 6 GB abort with code 99. | FR‑005 (fallback), Memory Constraint rule | SC‑005 | `memory_status` column records “OK” or “DEGRADED”. |
| **5. Model Fitting** | - OLS (baseline) using `statsmodels`.<br>- SAR (Spatial Lag Model) via `pysal`. <br>- GWR via `mgwr`. <br>- In degraded mode only OLS (clustered SE). | FR‑005, FR‑007 | SC‑001, SC‑005 | Model type recorded in metrics CSV (`model_type`). |
| **6. Spatial Cross‑Validation** | - Create 5 spatial blocks (k‑means on coordinates).<br>- Fit each model on 4 blocks, predict on held‑out block.<br>- Aggregate RMSE, MAE, R². | FR‑006 | SC‑001 | Prevents leakage from spatial autocorrelation. |
| **7. Multiple‑Comparison Correction** | - Collect p‑values for all predictors across models.<br>- Apply permutation‑based FDR (`statsmodels.stats.multitest.fdrcorrection`). | FR‑008 | SC‑003 | `correction_method` column set to “permutation‑FDR”. |
| **8. Sensitivity Analysis** | - If GWR fitted: sweep bandwidth (e.g., 50 – 500 m) and record R² curve.<br>- If degraded: sweep OLS coefficient stability by varying spatial block size.<br>- Save plot to `data/results/plots/sensitivity_<model>.png`. | FR‑009 | SC‑004 | Plot referenced in final report. |
| **9. Unexplained Variance Gap** | - Compute `UpperBound_R² – Observed_R²` where `UpperBound_R² = 0.60` (literature‑derived placeholder).<br>- Document source uncertainty in report (see reviewer note). | FR‑010 | SC‑001 | Value flagged for verification; does not affect pipeline execution. |
| **10. Reporting & Export** | - Assemble `metrics.csv` (rows per model) with required columns.<br>- Bundle plots and a markdown summary into `data/results/reports/`. | All FRs (output) | SC‑001, SC‑004 | All artifacts are deterministic given fixed seeds. |
| **11. Linting & Validation** | - Run `ruff check code/` and `black --check code/`.<br>- Emit `lint_report.txt`. | T037 | — | Fails pipeline if lint errors remain. |
| **12. Quickstart Validation** | - Execute `docs/quickstart.md` steps in a fresh venv (script `scripts/validate_quickstart.sh`).<br>- Log outcome to `quickstart_validation.log`. | T041 | — | Guarantees reproducibility of installation instructions. |
| **13. Specification Update** | - Amend `spec.md` to explicitly state that `OLS_DEGRADED` is the governing rule for memory constraints (per FR‑005). | T042 | — | Provides transparent governance. |

## Risk & Mitigation
- **Missing verified Landsat source**: Pipeline aborts early with informative error; reviewer can supply an open URL or accept the limitation.
- **Memory overflow**: Real‑time monitoring + deterministic fallback ensures SC‑005 compliance.
- **Unverified literature ceiling for FR‑010**: Metric calculated but flagged; future work can replace 0.60 with an empirically derived bound.

---
