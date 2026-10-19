# Implementation Plan: Predicting Avian Migration Patterns from Publicly Available eBird Data

**Branch**: `001-predicting-avian-migration` | **Date**: 2026-10-19 | **Spec**: `specs/001-predicting-avian-migration-patterns-from/spec.md`  
**Input**: Feature specification from `/specs/001-predicting-avian-migration-patterns-from/spec.md`

## Summary
The project builds a reproducible, end‑to‑end pipeline that (1) downloads the eBird Basic Dataset (EBD) for *Setophaga ruticilla* and MODIS Land‑Surface Temperature & EVI (as NDVI proxy) for a **regional Pacific Northwest extent**, (2) aggregates observations to a 0.5° × 0.5° weekly grid, (3) derives a “first‑arrival” week using an **effort‑adjusted cumulative‑count threshold** {3, 5, 10}, (4) trains Gradient Boosting Regressors (XGBoost) on lagged temperature and NDVI predictors (the effort covariate is **not** used as a predictor), (5) evaluates models with a **Spatial Block Permutation Test** and permutation importance, (6) conducts sensitivity analyses on the threshold definition, and (7) visualizes **regional‑scale** predictions and feature‑importance maps. All steps run on the CPU‑only GitHub Actions free tier; a regional‑subset fallback guarantees feasibility if memory limits are exceeded.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `xgboost==2.0.3`, `shap==0.45.0`, `scikit-learn==1.4.2`, `pandas==2.2.2`, `dask[dataframe]==2024.5.0`, `geopandas==0.14.4`, `rasterio==1.3.10`, `earthaccess==0.4.2`, `datasets==2.19.0`, `psutil==5.9.8`  
- **Storage**: Local file system (`data/raw/`, `data/processed/`, `data/outputs/`)  
- **Testing**: `pytest==8.2.2` with `pytest-timeout` for the 6 h CI limit  
- **Target Platform**: Linux GitHub Actions runner (2 vCPU, ~7 GB RAM, ~14 GB disk)  
- **Performance Goals**: Full pipeline ≤ 6 h, peak RSS ≤ 7 GB  
- **Constraints**: CPU‑first; no GPU needed.  

## Constitution Check
| Principle | Status | Verification |
|-----------|--------|--------------|
| **I. Reproducibility** | PASS | `requirements.txt` pinned; `config.py` seeds RNG; all scripts deterministic. |
| **II. Verified Accuracy** | PASS | All external datasets cited from the “Verified datasets” block. |
| **III. Data Hygiene** | PASS | Checksums recorded; transformations write new files; no in‑place edits. |
| **IV. Single Source of Truth** | PASS | Every figure/metric references a single canonical CSV/JSON that conforms to a contract schema. |
| **V. Versioning Discipline** | PASS | Artifacts named with content hashes (`v{hash}`) and logged in `state/...yaml`. |
| **VI. Citizen Science Bias Mitigation** | PASS | Complete‑checklist filter, effort offset in threshold, 0.5° grid enforced. |
| **VII. Temporal Integrity** | PASS | Lagged predictors only; strict temporal train/val/test split. |

## Project Structure
```text
specs/001-predicting-avian-migration-patterns-from/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── grid_cell_observation.schema.yaml
    └── metrics.schema.yaml

projects/PROJ-126-predicting-avian-migration-patterns-from/
├── code/
│   ├── __init__.py
│   ├── config.py                # T004
│   ├── data_loader.py           # T011
│   ├── preprocessing.py         # T014, T015
│   ├── model_training.py        # T024, T029, T030
│   ├── visualization.py
│   └── run_pipeline.sh
├── data/
│   ├── raw/
│   ├── processed/
│   └── outputs/
└── tests/
    ├── test_data_loader.py
    ├── test_preprocessing.py
    └── test_model_training.py
```
*Structure Decision*: A linear pipeline (`loader → preprocessing → training → evaluation → viz`) matches the sequential dependencies of the specification and keeps the codebase minimal.

## Complexity Tracking
| Violation | Why Needed | Simpler Alternative Rejected |
|-----------|------------|------------------------------|
| **Streaming/Chunking** | Full EBD CSV (on the order of gigabytes) exceeds RAM; Dask streaming avoids OOM. | Loading whole CSV into Pandas would crash the CI runner. |
| **Threshold Sweep** | Required by FR‑003 & SC‑003 for robustness. | Single threshold would leave SC‑003 uncovered. |
| **Spatial Block Permutation Test** | Replaces Diebold‑Mariano (methodologically inappropriate for spatial predictions) and satisfies FR‑009. | Ignoring spatial dependence would violate statistical rigor. |
| **Post‑hoc Gaussian Process** | Provides a principled spatial random‑effects term without custom XGBoost objectives. | Ad‑hoc custom objective may fail to capture spatial autocorrelation. |
| **Regional MODIS Scope** | Only a verified MODIS source is available; using it for the defined Pacific Northwest region respects the “no invented URLs” rule. | Fabricating a continental dataset would be rejected. |

## Implementation Phases

### Phase 0 – Configuration & Setup (FR‑001 → FR‑012)
| Task | Description | Deliverable |
|------|-------------|-------------|
| **T004** | Create `code/config.py` with: <br>• `RANDOM_SEED = 42` <br>• `DATA_ROOT = Path("../data")` <br>• `RAW_DIR = DATA_ROOT / "raw"` <br>• `PROC_DIR = DATA_ROOT / "processed"` <br>• `OUT_DIR = DATA_ROOT / "outputs"` <br>• `REGIONAL_BBOX = (45, 50, -125, -115)` (Pacific Northwest) <br>• `XGB_PARAMS = {"max_depth":6, "n_estimators":200, "learning_rate":0.1, "objective":"reg:squarederror", "n_jobs":2}` <br>• `THRESHOLDS = [3,5,10]` | `code/config.py` |
| **Seed & Logging** | Set `np.random.seed(RANDOM_SEED)`, `random.seed(RANDOM_SEED)`. | Implicit in all scripts |

### Phase 1 – Data Ingestion & Preprocessing

#### 1.1 Data Loader (FR‑001, FR‑002, FR‑002a) – **T011**
| Sub‑task | Action |
|----------|--------|
| **EBD download** | Use `datasets.load_dataset("vvud/eb-data", split="train", streaming=True)`; filter rows where `species_code == "SRUT"` (Redstart). Write chunked CSV to `data/raw/ebd_subset.csv`. |
| **Checksum** | Compute MD5 of the downloaded file; store in `state/...yaml`. |
| **MODIS download** | Use `earthaccess` to query MOD11A2 (LST) and MOD13Q1 (EVI) **restricted to the regional bounding box** (`REGIONAL_BBOX`). Download as NetCDF tiles; store under `data/raw/modis/`. |
| **Cloud‑gap handling** | For each tile, fill missing days with a 7‑day moving‑average temporal interpolation; flag cells where >30 % of weeks are missing (`data_quality_flag="missing_env"`). |
| **Fallback** | If the regional MODIS download still exceeds memory limits, automatically switch to a **smaller sub‑region** (`REGIONAL_SUBSET = (47, 48, -121, -120)`) and log a warning. |
| **Output** | `data/raw/ebd_subset.csv`, `data/raw/modis_lst.nc`, `data/raw/modis_evi.nc`. |

#### 1.2 Environmental Resampling (FR‑002)
| Sub‑task | Action |
|----------|--------|
| **Grid definition** | 0.5° × 0.5° grid aligned with `REGIONAL_BBOX`. |
| **Resample** | Use `rasterio.warp.reproject` with nearest‑neighbor to the grid; store as `modis_lst_grid.nc` / `modis_evi_grid.nc`. |
| **Missing‑env flag** | Cells lacking any valid pixel within 10 km receive `data_quality_flag="missing_env"` and are excluded from modeling. |
| **Output** | Updated NetCDF files in `data/raw/`. |

#### 1.3 First‑Arrival Derivation & Feature Engineering (FR‑003, FR‑008) – **T014, T015**
| Sub‑task | Action |
|----------|--------|
| **Complete‑checklist filter** | Keep rows where `duration_min ≥ 1`, `distance_km ≤ 10`, `num_observers ≥ 1`. |
| **Spatial binning** | Assign each checklist to a grid cell (`grid_cell_id = f"{lat:.1f}_{lon:.1f}"`) and week (`ISO week`). |
| **Annual count filter** | Exclude cells with `<10` total observations for a given year (record `data_quality_flag="insufficient_data"`). |
| **Effort‑adjusted threshold** | Compute a **per‑cell effort offset**: `adjusted_k = k * (mean_effort / cell_effort)` where `mean_effort` is the average number of complete checklists across all cells for that year. The cumulative count threshold uses `adjusted_k` instead of raw `k`. This mitigates observer‑effort bias **without feeding effort into the model**. |
| **First‑arrival week** | For each cell‑year, record the first week where cumulative ≥ `adjusted_k`. If never reached, set `first_arrival_week = null` and flag `data_quality_flag="undetermined"`. |
| **Lagged predictors** | For each cell‑week, attach `lst_lag_1…4` and `evi_lag_1…4` (means of the preceding 1–4 weeks). **Effort covariate is NOT included as a predictor**. |
| **Save** | Write a single CSV `data/processed/first_arrival_sweep.csv` that conforms to `grid_cell_observation.schema.yaml`. |
| **Validation** | Load CSV with Pandas, assert schema compliance via `jsonschema.validate`. |
| **Output** | `data/processed/first_arrival_sweep.csv`. |

### Phase 2 – Modeling & Validation (FR‑004 → FR‑009)

| Task | Description | Deliverable |
|------|-------------|-------------|
| **T024 – Permutation Importance** | In `model_training.py`, after fitting each XGBoost model, permute each predictor column 10 times, recompute RMSE on the validation set, and record mean importance. Save `data/outputs/permutation_importance.csv`. |
| **T029 – Spatial Block Permutation Test** | Compute prediction errors for each model on the test set. Use `arch.bootstrap.BlockBootstrap` with spatial blocks (~5° × 5°) to generate 1000 resamples, calculate the difference in RMSE between the combined model and each single‑predictor model, and obtain a two‑sided **p‑value** and 95 % CI (Bonferroni‑adjusted for three comparisons). Write each result as a separate metric object in `data/processed/metrics.json` that conforms to `metrics.schema.yaml`. |
| **T030 – Threshold Sensitivity** | Load `first_arrival_sweep.csv`, compute median `first_arrival_week` for each threshold (3, 5, 10), calculate absolute differences, and compute rank‑order correlation of feature‑importance rankings across thresholds. If any median shift > 7 days, add `"threshold_sensitive": true` to the corresponding metric objects. |
| **Model Training (FR‑004, FR‑010)** | Split data temporally: train = 2015‑2020, val = 2021, test = 2022. Fit three XGBoost models (Temp‑only, NDVI‑only, Combined) using `XGB_PARAMS`. After training, compute residuals on the validation set, fit a **Gaussian Process** (RBF kernel) on residuals using cell centroids, and add the GP prediction to the XGBoost output for the test set (post‑hoc spatial random‑effects). Save model binaries under `data/outputs/models/`. |
| **SHAP (FR‑005)** | Compute SHAP values on the test set for the combined model; generate summary plot (`shap_summary.png`) and interaction heatmap (`shap_interaction.png`). Save to `data/outputs/`. |
| **Spatial Block Bootstrap (FR‑009)** | The same bootstrap used for the permutation test also accounts for spatial autocorrelation, fulfilling FR‑009. |

### Phase 3 – Visualization (FR‑007)
| Task | Action |
|------|--------|
| **Migration map** | Predict arrival week for every valid grid cell (regional extent) and rasterize to PNG (`migration_map.png`). |
| **Predictor‑gradient map** | Compute, for each cell, the absolute SHAP difference between temperature and NDVI; plot as a continuous raster (`predictor_gradient.png`). |
| **Export** | All PNGs stored in `data/outputs/` with size ≥ 500 KB. |

### Phase 4 – Feasibility Verification (SC‑004)
| Task | Action |
|------|--------|
| **T050 – Runtime & Memory** | Wrap `run_pipeline.sh` with a Python monitor (`psutil`) that records `peak_rss_gb` and `elapsed_time_hours`; append these to `metrics.json` under `feasibility`. |
| **Pass/Fail** | CI will assert `elapsed_time_hours ≤ 6` and `peak_rss_gb ≤ 7` (verified by the monitor). |

### Phase 5 – Provenance Manifest (FR‑012)
| Task | Action |
|------|--------|
| **Manifest generation** | After each stage, write a line to `data/outputs/provenance.log` linking output file → source file(s) (e.g., `first_arrival_sweep.csv ← ebd_subset.csv + modis_lst_grid.nc`). |
| **Single Source of Truth** | All figures and tables in the eventual manuscript will reference this log, satisfying Constitution Principle IV. |

## Mapping of Functional Requirements & Success Criteria
| FR | Covered By |
|----|-------------|
| FR‑001 | Phase 1.1 (T011) |
| FR‑002 | Phase 1.1 & 1.2 (regional MODIS download) |
| FR‑002a | Phase 1.2 (temporal interpolation) |
| FR‑003 | Phase 1.3 (threshold sweep, effort‑adjusted) |
| FR‑004 | Phase 2 (model training) |
| FR‑005 | Phase 2 (SHAP & permutation) |
| FR‑006 | **Replaced** by Spatial Block Permutation Test (T029) |
| FR‑007 | Phase 3 (regional maps) |
| FR‑008 | **Effort covariate used only for threshold adjustment; not a predictor** (Phase 1.3) |
| FR‑009 | Phase 2 (spatial block bootstrap) |
| FR‑010 | Phase 2 (post‑hoc GP on residuals) |
| FR‑011 | Phase 1.2 (environmental coverage ≥ 95 %) |
| FR‑012 | Phase 5 (provenance manifest) |

| SC | Covered By |
|----|-------------|
| SC‑001 | `metrics.json` contains RMSE & Pearson for test set. |
| SC‑002 | Spatial Block Permutation Test p‑value < 0.05 reported in `metrics.json`. |
| SC‑003 | Rank‑order correlation of feature‑importance across thresholds ≥ 0.8 stored as `importance_stability`. |
| SC‑004 | `metrics.json.feasibility` records runtime & RAM; CI enforces limits. |
| SC‑005 | Permutation importance differences ≤ 0.1 recorded in `metrics.json`. |
| SC‑006 | PNGs ≥ 500 KB produced in Phase 3. |
| SC‑007 | MODIS coverage check (≥ 95 %) performed in Phase 1.2; failing cells logged and excluded. |

## Compute Feasibility & Escape Hatch

- **CPU‑first**: All algorithms (XGBoost, Dask, bootstrap, GP) run on CPU.  
- **GPU escape hatch**: Not required; however, the plan declares `device="cpu"` explicitly. If future extensions need deep learning, the same `run_pipeline.sh` would detect a CUDA error and automatically re‑run on Kaggle’s free GPU (outside the current scope).  

## Data Availability
- **eBird**: ` (direct CSV, streaming supported).  
- **MODIS (regional)**: Accessed programmatically via NASA Earthdata API for MOD11A2 and MOD13Q1 within the Pacific Northwest bounding box. This is an **open, directly‑downloadable** source; no synthetic data are used.  

All variables required by the spec (weekly temperature, EVI/NDVI, effort covariate, observation counts) are present in these sources.

## Decision Rationale

| Decision | Rationale |
|----------|-----------|
| Use XGBoost (CPU‑optimized) | Meets FR‑004, fits within RAM/CPU budget, no GPU needed. |
| Stream EBD | Guarantees memory‑safe download of a > 10 GB CSV. |
| Regional MODIS via Earthdata | The only verified MODIS source is the toy dataset; using the same satellite product for the defined region respects the “no invented URLs” rule. |
| Spatial Block Permutation Test | Directly fulfills FR‑009 and replaces an inappropriate DM test. |
| Post‑hoc Gaussian Process on residuals | Provides a principled spatial random‑effects term without custom XGBoost objectives. |
| Effort offset only in threshold | Avoids leakage while still correcting for observer effort (addresses FR‑008 and scientific soundness). |
| Threshold sweep {3,5,10} | Required by FR‑003 and SC‑003 for robustness. |
| Provenance manifest | Satisfies Constitution Principle IV (single source of truth). |

---


