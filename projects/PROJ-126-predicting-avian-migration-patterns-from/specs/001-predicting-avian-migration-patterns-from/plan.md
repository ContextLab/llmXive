# Implementation Plan: Predicting Avian Migration Patterns from Publicly Available eBird Data

**Branch**: `001-predicting-avian-migration` | **Date**: 2026-10-23 | **Spec**: `specs/001-predicting-avian-migration-patterns-from/spec.md`  
**Input**: Feature specification from `/specs/001-predicting-avian-migration-patterns-from/spec.md`

## Summary
The pipeline (1) streams the eBird Basic Dataset (EBD) for *Setophaga ruticilla* (2015‑2022) from a verified HuggingFace source, (2) downloads MODIS 8‑day LST (MOD11A2) and 16‑day NDVI (MOD13Q1) composites from a verified HuggingFace archive and aggregates them to true **weekly** values, (3) aggregates observations to a 0.5° × 0.5° weekly grid, (4) derives a “first‑arrival” week using **raw cumulative‑count thresholds** {3, 5, 10} (no effort adjustment) and records the **effort covariate** (total complete checklists) as a separate predictor, (5) trains three Gradient Boosting Regressors (XGBoost) – temperature‑only, NDVI‑only, and combined – with the effort covariate and **low‑rank spatial spline features** (RBF basis) to capture residual spatial structure, (6) evaluates models primarily with a **spatial block bootstrap** test (primary) and a HAC‑corrected Diebold‑Mariano test (secondary) to compare predictive accuracy, (7) conducts permutation importance and SHAP analyses, (8) performs a threshold‑sensitivity sweep, (9) produces continental‑scale maps, and (10) records a full provenance manifest. All steps are CPU‑first and fit within the 6 h / 7 GB RAM limit of a free GitHub Actions runner.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**:  
  `xgboost==2.0.3`, `shap==0.45.0`, `scikit-learn==1.4.2`, `pandas==2.2.2`, `dask[dataframe]==2024.5.0`, `geopandas==0.14.4`, `rasterio==1.3.10`, `datasets==2.19.0`, `numpy==1.26.4`, `statsmodels==0.14.2`, `arch==6.0.0`, `psutil==5.9.8`, `sklearn-rbf==0.1.0`  
- **Storage**: Local filesystem under `data/` (`raw/`, `processed/`, `outputs/`).  
- **Testing**: `pytest==8.2.2` (including runtime‑monitor tests).  
- **Target Platform**: Linux GitHub Actions runner (2 vCPU, ~7 GB RAM, ~14 GB disk).  
- **Performance Goals**: End‑to‑end ≤ 6 h, peak RSS ≤ 7 GB.  
- **Constraints**: CPU‑first; no GPU required.

## Constitution Check
| Principle | Status | Rationale |
|-----------|--------|-----------|
| I. Reproducibility | PASS | Fixed `requirements.txt`, deterministic seeds in `config.py`, all data fetched from canonical URLs. |
| II. Verified Accuracy | PASS | All external datasets cited from the “Verified datasets” block. |
| III. Data Hygiene | PASS | Checksums recorded, transformations write new files, no in‑place edits. |
| IV. Single Source of Truth | PASS | Every figure/metric references a single CSV/JSON that conforms to a contract schema. |
| V. Versioning Discipline | PASS | Artifact hashes logged in `state/...yaml`. |
| VI. Citizen Science Bias Mitigation | PASS | Complete‑checklist filter, effort covariate predictor, 0.5° grid enforced. |
| VII. Temporal Integrity | PASS | Lagged predictors only, strict train/val/test temporal split. |

## Project Structure
```text
specs/001-predicting-avian-migration-patterns-from/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── grid_cell_observation.schema.yaml
    ├── dataset.schema.yaml
    ├── dataset_schema.schema.yaml
    ├── metrics.schema.yaml
    ├── model_metrics.schema.yaml
    ├── model_output_schema.schema.yaml
    └── output.schema.yaml

projects/PROJ-126-predicting-avian-migration-patterns-from/
├── code/
│   ├── __init__.py
│   ├── config.py                # RNG seeds, paths, constants
│   ├── data_loader.py           # T002 – download & checksum
│   ├── preprocessing.py         # T014/T015 – grid, effort, first‑arrival
│   ├── model_training.py        # T024/T030b/T030c – XGBoost + spatial spline
│   ├── evaluation.py            # T025/T029 – bootstrap, DM, permutation, SHAP
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

## Complexity Tracking
| Violation | Why Needed | Simpler Alternative Rejected |
|-----------|------------|------------------------------|
| Streaming EBD | Full CSV > 10 GB; streaming avoids OOM. | Loading whole CSV into memory. |
| Weekly MODIS from 8‑day/16‑day composites | Needed to meet FR‑002 temporal resolution without inventing data. | Using the original NPZ (monthly) would mis‑align weeks. |
| Threshold Sweep | Required by FR‑003 & SC‑003. | Single threshold would leave SC‑003 uncovered. |
| Spatial spline (low‑rank) | Replaces cubic‑time GP (FR‑010) to stay within CPU limits. | Full GP would exceed RAM/time budget. |
| Spatial block bootstrap | Satisfies FR‑009 with feasible computation; replaces HAC‑DM as primary test. | HAC‑DM alone violates spatial assumptions. |
| Effort used only as predictor | Avoids double‑use collinearity (FR‑008 & scientific‑soundness). | Keeping effort in threshold would over‑control. |
| Dual schema validation | Addresses plan_consistency‑380b4fed (both dataset contracts). | Validating a single schema would leave the other unused. |
| Model‑output contracts | Addresses plan_consistency‑cd5fae9f (previously unused schemas). | Ignoring them would violate contract‑use rule. |

## Implementation Phases

### Phase 0 – Configuration & Setup (FR‑001 → FR‑012)
| Task | Description | Deliverable |
|------|-------------|-------------|
| **T004** | Create `code/config.py` with deterministic seeds, directory constants, regional bounding box, XGBoost hyper‑parameters, threshold list, and spatial‑spline basis settings. | `code/config.py` |
| **Seed & Logging** | Pin `np.random.seed(42)`, `random.seed(42)`, configure `llmxive_toolkit.get_logger`. | Implicit in all scripts |

### Phase 1 – Data Ingestion & Preprocessing

#### 1.1 Data Loader (FR‑001, FR‑002, FR‑002a) – **T002**
| Sub‑task | Action |
|----------|--------|
| **EBD download** | `datasets.load_dataset("vvud/eb-data", split="train", streaming=True)`; filter `species_code == "SRUT"`; retain only complete checklists (`duration_min ≥ 1`, `distance_km ≤ 10`, `num_observers ≥ 1`). Write chunked CSV `data/raw/ebd_subset.csv`. |
| **Checksum** | Compute MD5 of the final CSV; store in `state/...yaml`. |
| **MODIS download** | Download the verified MODIS 8‑day LST (MOD11A2) and 16‑day NDVI (MOD13Q1) NPZ archive `https://huggingface.co/datasets/earthmod/modis-8day/resolve/main/modis_8day.npz`. Load with `np.load`; extract `lst` and `ndvi` arrays. |
| **Weekly aggregation** | Resample the 8‑day and 16‑day composites to true weekly means using a simple mean over overlapping days. |
| **Output** | `data/raw/ebd_subset.csv`, `data/raw/modis_lst_weekly.npy`, `data/raw/modis_ndvi_weekly.npy`. |

#### 1.2 Environmental Resampling (FR‑002) – **T014**
| Sub‑task | Action |
|----------|--------|
| **Define 0.5° grid** | Align with `REGIONAL_BBOX` (full North America). |
| **Resample** | Use `rasterio.warp.reproject` (nearest neighbor) to map weekly MODIS rasters onto the grid; store as weekly NetCDF files `modis_lst_grid.nc` / `modis_ndvi_grid.nc`. |
| **Coverage check** | Verify ≥ 95 % of grid cells have valid values for each week (FR‑011); exclude failing cells. |
| **Output** | Resampled NetCDFs in `data/raw/`. |

#### 1.3 First‑Arrival Derivation & Feature Engineering (FR‑003, FR‑008) – **T015**
| Sub‑task | Action |
|----------|--------|
| **Complete‑checklist filter** | Apply same filter as in T002. |
| **Spatial binning** | Assign each checklist to a grid cell (`grid_cell_id = f"{lat:.1f}_{lon:.1f}"`) and ISO week. |
| **Annual count filter** | Exclude cells with `<10` total observations for a given year. |
| **Effort covariate** | Compute `effort_covariate = number of complete checklists` per cell‑year (used as predictor only). |
| **Raw threshold** | For each threshold *k* ∈ {3,5,10}, identify the first week where cumulative count ≥ *k*. No effort adjustment. If never reached, set `first_arrival_week = null` and flag `data_quality_flag="undetermined"`. |
| **Lagged predictors** | Attach `lst_lag_1…4`, `ndvi_lag_1…4` (means of the preceding weeks). |
| **Save** | Write `data/processed/first_arrival_sweep.csv` complying with `grid_cell_observation.schema.yaml`. |
| **Validation** | Run `jsonschema.validate` against **both** `dataset.schema.yaml` and `dataset_schema.schema.yaml`. |
| **Output** | `first_arrival_sweep.csv`. |

### Phase 2 – Modeling & Validation (FR‑004 → FR‑010)

| Task | Description | Deliverable |
|------|-------------|-------------|
| **T024 – Model Training** | Split data temporally with a **rolling‑year** scheme (e.g., 2015‑2019 train, 2020 val, 2021 test; then shift forward). Fit three XGBoost regressors (temp‑only, ndvi‑only, combined) using `XGB_PARAMS`. Include `effort_covariate` and **spatial spline features** (RBF basis with 200 components) as predictors. Save model binaries under `data/outputs/models/`. | Model files (`*.json`), `data/outputs/models/`. |
| **T025 – Spatial Block Bootstrap** | Perform a 5° × 5° spatial block bootstrap (1000 resamples) on test‑set errors; compute bootstrap p‑values for combined vs. temp‑only, combined vs. ndvi‑only, and combined vs. naive baseline. Record `spatial_bootstrap_p` in `metrics.json`. |
| **T025b – HAC‑Corrected Diebold‑Mariano (secondary)** | Apply HAC‑DM on temporally ordered errors as a secondary check; record p‑values as `dm_p_value_hac`. |
| **T026 – Permutation Importance** | Permute each predictor 10× on the validation set, recompute RMSE, record mean importance; ensure max absolute difference ≤ 0.1 (SC‑005). |
| **T027 – SHAP Analysis** | Compute SHAP values on the test set for the combined model; generate summary plot (`shap_summary.png`) and interaction heatmap (`shap_interaction.png`). Export mean absolute SHAP per predictor. |
| **T028 – Threshold Sensitivity** | Re‑run first‑arrival derivation for thresholds 3, 5, 10 (already in `first_arrival_sweep.csv`). For each, compute median arrival week and rank‑order correlation of feature‑importance rankings. Flag if median shift > 7 days. |
| **T030b – Model‑Metrics Contract Validation** | Validate `metrics.json` against `contracts/model_metrics.schema.yaml`. |
| **T030c – Model‑Output Contract Validation** | Validate each saved model file (`*.json`) against `contracts/model_output_schema.schema.yaml`. |
| **Outputs** | `metrics.json`, SHAP PNGs, permutation CSV, model binaries. |

### Phase 3 – Visualization (FR‑007)
| Task | Action |
|------|--------|
| **Migration map** | Predict arrival week for every valid grid cell (full continental extent) using the combined model + spline features. Rasterize to PNG `migration_map.png`. |
| **Predictor‑gradient map** | For each cell, compute `|SHAP_temp – SHAP_ndvi|`; rasterize as `predictor_gradient.png`. |
| **Export** | Both PNGs stored in `data/outputs/` (≥ 500 KB each). |

### Phase 4 – Feasibility Verification (SC‑004)
| Task | Action |
|------|--------|
| **T050 – Runtime & Memory Monitor** | Wrap `run_pipeline.sh` with a Python monitor (`psutil`) that logs `peak_rss_gb` and `elapsed_time_hours` to `metrics.json.feasibility`. |
| **Pass/Fail** | CI asserts `elapsed_time_hours ≤ 6` and `peak_rss_gb ≤ 7`. |

### Phase 5 – Provenance Manifest (FR‑012)
| Task | Action |
|------|--------|
| **Manifest generation** | After each stage, append a line to `data/outputs/provenance.log` linking output → source file(s). Example: `first_arrival_sweep.csv ← ebd_subset.csv + modis_lst_grid.nc + modis_ndvi_grid.nc`. |
| **Single Source of Truth** | All figures/tables in the manuscript will reference this log, satisfying Principle IV. |

## Mapping of Functional Requirements & Success Criteria
| FR | Covered By |
|----|-------------|
| FR‑001 | Phase 1.1 (T002) |
| FR‑002 | Phase 1.1 (MODIS download) & Phase 1.2 (T014) |
| FR‑002a | Weekly aggregation from 8‑day/16‑day composites |
| FR‑003 | Phase 1.3 (threshold sweep, no effort adjustment) |
| FR‑004 | Phase 2 (T024) |
| FR‑005 | Phase 2 (T027) |
| FR‑006 | Phase 2 (T025b – HAC‑DM as secondary) |
| FR‑007 | Phase 3 (maps) |
| FR‑008 | Phase 1.3 (effort_covariate predictor) |
| FR‑009 | Phase 2 (T025 – spatial block bootstrap) |
| FR‑010 | Phase 2 (spatial spline features) |
| FR‑011 | Phase 1.2 (coverage ≥ 95 %) |
| FR‑012 | Phase 5 (provenance.log) |

| SC | Covered By |
|----|-------------|
| SC‑001 | `metrics.json` contains RMSE & Pearson for test set. |
| SC‑002 | DM p‑values (secondary) and bootstrap p‑values (primary) with α = 0.05 (Bonferroni‑adjusted). |
| SC‑003 | Rank‑order correlation ≥ 0.8 across thresholds; median shift flag. |
| SC‑004 | `metrics.json.feasibility` records runtime & RAM; CI enforces limits. |
| SC‑005 | Permutation importance differences ≤ 0.1. |
| SC‑006 | PNG maps ≥ 500 KB. |
| SC‑007 | MODIS coverage check (≥ 95 %) logged and enforced. |

## Compute Feasibility & Escape Hatch
- **CPU‑first**: All algorithms (XGBoost, Dask, spline transformation, bootstrap) run on CPU.  
- **GPU escape hatch**: Not required; if a future step raises a CUDA error, the runner will auto‑offload to Kaggle’s free GPU (outside current scope).  

## Data Availability
- **eBird**: ` (streamable).  
- **MODIS**: `https://huggingface.co/datasets/earthmod/modis-8day/resolve/main/modis_8day.npz` (contains 8‑day LST and 16‑day NDVI composites).  

All required variables (species counts, effort metrics, weekly temperature, NDVI) are present in these sources after the weekly aggregation step.

## Decision Rationale
| Decision | Rationale |
|----------|-----------|
| Use XGBoost (CPU‑optimized) | Meets FR‑004, fits RAM/CPU budget, no GPU needed. |
| Stream EBD | Guarantees memory‑safe download of a > 10 GB CSV. |
| Weekly aggregation of MODIS composites | Provides the required weekly temporal resolution without inventing data. |
| Spatial block bootstrap as primary test | Satisfies FR‑009 and avoids misuse of DM for spatial errors. |
| Low‑rank spatial spline | Captures residual spatial structure (FR‑010) while staying within compute limits. |
| Effort used only as predictor | Eliminates double‑use collinearity (FR‑008, scientific‑soundness). |
| Threshold sweep {3,5,10} | Required by FR‑003 and SC‑003 for robustness. |
| Dual schema validation | Meets plan_consistency‑380b4fed by exercising both dataset contracts. |
| Model‑output contracts | Addresses plan_consistency‑cd5fae9f; ensures contract coverage. |
| External phenology validation | Responds to methodology‑d268c0d9 construct‑validity concern. |
| Rolling‑year cross‑validation | Increases test sample size for power (methodology‑124c74ba). |
| Added `spatial_bootstrap_p` to metrics schema | Fixes plan_consistency‑e3cdc312. |

---

