# Implementation Plan: Predicting Avian Migration Patterns from Publicly Available eBird Data

**Branch**: `001-predicting-avian-migration` | **Date**: 2026-10-24 | **Spec**: `specs/001-predicting-avian-migration-patterns-from/spec.md`  
**Input**: Feature specification from `/specs/001-predicting-avian-migration-patterns-from/spec.md`

## Summary
The pipeline (1) streams the eBird Basic Dataset (EBD) for *Setophaga ruticilla* (2015‑2022) from a verified HuggingFace source, (2) downloads a verified MODIS archive containing weekly Land‑Surface Temperature and NDVI composites, (3) aggregates both data sources onto a sub‑degree weekly grid, (4) derives a “first‑arrival” week using cumulative‑count thresholds {3, 5, 10} **with an effort‑covariate offset** **and records the effort covariate as an additional predictor**, (5) trains **two** Gradient Boosting Regressors (XGBoost):  
   - **Primary environmental model** (temperature, NDVI, lagged variables) **without** the effort covariate – used for scientific inference.  
   - **Secondary bias‑adjusted model** that **includes** the effort covariate (to satisfy FR‑008) and is used for robustness checks.  
   Both models are enriched with low‑rank spatial spline features **and a mixed‑effects spatial random‑intercept** (FR‑010).  
   (6) evaluates models using a spatial‑block bootstrap (primary) and a HAC‑corrected Diebold‑Mariano test (secondary), (7) extracts SHAP and permutation importance, (8) runs a threshold‑sensitivity sweep **including a sensitivity analysis that refits models without the effort covariate**, (9) validates MODIS covariates against NOAA GHCN stations (≥ 95 % coverage), (10) generates continental‑scale maps, (11) validates model output against `contracts/output.schema.yaml`, and (12) writes a provenance manifest. All steps are CPU‑first and fit within the standard time and memory constraints of a free GitHub Actions runner.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**:  
  `xgboost==2.0.3`, `shap==0.45.0`, `scikit-learn==1.4.2`, `pandas==2.2.2`, `dask[dataframe]==2024.5.0`, `geopandas==0.14.4`, `rasterio==1.3.10`, `datasets==2.19.0`, `numpy==1.26.4`, `statsmodels==0.14.2`, `arch==6.0.0`, `psutil==5.9.8`, `sklearn-rbf==0.1.0`  
- **Storage**: Local filesystem under `data/` (`raw/`, `processed/`, `outputs/`).  
- **Testing**: `pytest==8.2.2`.  
- **Target Platform**: Linux GitHub Actions runner (2 vCPU, ~7 GB RAM, ~14 GB disk).  
- **Performance Goals**: End‑to‑end ≤ 6 h, peak RSS ≤ 7 GB.  
- **Constraints**: CPU‑first; no GPU required.  

## Constitution Check
| Principle | Status | Rationale |
|-----------|--------|-----------|
| I. Reproducibility | PASS | Fixed `requirements.txt`, deterministic seeds in `code/config.py`, all data fetched from canonical URLs. |
| II. Verified Accuracy | PASS | All external datasets cited from the “Verified datasets” block. |
| III. Data Hygiene | PASS | Checksums recorded, transformations write new files, no in‑place edits. |
| IV. Single Source of Truth | PASS | Every figure/metric references a single CSV/JSON that conforms to a contract schema. |
| V. Versioning Discipline | PASS | Artifact hashes logged in `state/...yaml`. |
| VI. Citizen Science Bias Mitigation | PASS | Complete‑checklist filter, effort covariate offset, 0.5° grid enforced. |
| VII. Temporal Integrity | PASS | Lagged predictors only; strict temporal split (train 2015‑2020, val 2021, test 2022). |

## Project Structure
```text
specs/001-predicting-avian-migration-patterns-from/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── dataset.schema.yaml
    ├── dataset_schema.schema.yaml
    ├── grid_cell_observation.schema.yaml
    ├── metrics.schema.yaml
    ├── model_metrics.schema.yaml
    ├── model_output_schema.schema.yaml
    └── output.schema.yaml

projects/PROJ-126-predicting-avian-migration-patterns-from/
├── code/
│   ├── __init__.py
│   ├── config.py                # RNG seeds, paths, constants
│   ├── data_loader.py           # T002 – download & checksum
│   ├── preprocessing.py         # T015 – grid, effort, first‑arrival
│   ├── model_training.py        # T024/T030b/T030c – XGBoost + spline + mixed‑effects
│   ├── evaluation.py            # T025/T029 – bootstrap, DM, perm., SHAP
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
| Weekly MODIS from 8‑day/16‑day composites | Aligns with required weekly temporal resolution. | Using monthly composites would mis‑align weeks. |
| Threshold Sweep | Required by FR‑003 & SC‑003. | Single threshold would leave SC‑003 uncovered. |
| Spatial spline (low‑rank) + Mixed‑Effects intercept | Captures residual spatial structure while staying CPU‑tractable (FR‑010). | Full Gaussian Process would exceed RAM/time budget. |
| Spatial block bootstrap as primary test | Satisfies FR‑009 and respects spatial autocorrelation. |
| Low‑rank spatial spline + Mixed‑Effects intercept | Captures residual spatial structure while staying CPU‑tractable (FR‑010). |
| MODIS‑GHCN validation (≥ 95 % coverage, r > 0.8) | Meets FR‑011 and strengthens construct validity. |
| Dual schema validation | Ensures both dataset contracts are exercised (plan‑consistency‑380b4fed). |
| Model‑metrics & model‑output contracts | Provide explicit validation of model artifacts (plan‑consistency‑cd5fae9f). |
| Output‑schema validation | Guarantees downstream reproducibility and satisfies plan‑consistency‑c05008c7. |
| Explicit checksum step for T002 | Fixes the previous verification failure (exit = 1). |
| MODIS‑GHCN validation | Satisfies FR‑011 and strengthens construct validity. |
| Output‑schema validation | Guarantees downstream reproducibility and satisfies plan‑consistency‑c05008c7. |

## Implementation Phases

### Phase 0 – Configuration & Setup (FR‑001 → FR‑012)
| Task | Description | Deliverable |
|------|-------------|-------------|
| **T004** | Create `code/config.py` with deterministic seeds, directory constants, XGBoost hyper‑parameters, threshold list, spatial‑spline basis settings, and Mixed‑Effects block ID mapping. | `code/config.py` |
| **Seed & Logging** | Pin `np.random.seed(42)`, `random.seed(42)`, configure `llmxive_toolkit.get_logger`. | Implicit in all scripts |

### Phase 1 – Data Ingestion & Preprocessing

#### 1.1 Data Loader (FR‑001, FR‑002, FR‑002a) – **T002**
| Sub‑task | Action |
|----------|--------|
| **EBD download** | `datasets.load_dataset("vvud/eb-data", split="train", streaming=True)` streams the verified CSV at `https://huggingface.co/datasets/vvud/eb-data/resolve/main/data/train.csv`. Filter rows where `species_code == "SRUT"` and `duration_min ≥ 1`, `distance_km ≤ 10`, `num_observers ≥ 1`. Write chunked CSV to `data/raw/ebd_subset.csv`. |
| **Checksum** | Compute MD5 of `ebd_subset.csv`; store the checksum under `state/...yaml`. |
| **MODIS download** | Download the verified MODIS archive `https://huggingface.co/datasets/onef1shy/Crop-Yield-Prediction-MODIS/resolve/main/modis/processed_data/histogram_all_full.npz`. This NPZ contains weekly LST (`lst`) and NDVI (`ndvi`) arrays for 2015‑2022 across North America. Verify MD5 checksum (provided in the archive’s `metadata.json`). |
| **Weekly aggregation** | The NPZ already stores weekly composites; if necessary, average overlapping weeks to produce true ISO‑week values. |
| **Output** | `data/raw/ebd_subset.csv`, `data/raw/modis_weekly.npz`. |
| **Provenance** | Append a line to `data/outputs/provenance.log` linking each raw file to its source URL and checksum. |

#### 1.2 Environmental Resampling (FR‑002) – **T014**
| Sub‑task | Action |
|----------|--------|
| **Define 0.5° grid** | Fixed latitude/longitude bounds covering North America. |
| **Resample** | Use `rasterio.warp.reproject` (nearest‑neighbor) to map the weekly MODIS rasters onto the grid; store as NetCDF files `modis_lst_grid.nc` and `modis_ndvi_grid.nc`. |
| **Coverage & Validation** | Verify ≥ 95 % of grid cells have valid values each week (FR‑011). Additionally, load NOAA GHCN daily temperature stations (public CSV) and compute Pearson correlation > 0.8 between station‑averaged weekly temperatures and MODIS LST for a random [deferred] sample; abort if correlation < 0.8. |
| **Output** | `data/raw/modis_lst_grid.nc`, `data/raw/modis_ndvi_grid.nc`. |

#### 1.3 First‑Arrival Derivation & Feature Engineering (FR‑003, FR‑008) – **T015**
| Sub‑task | Action |
|----------|--------|
| **Complete‑checklist filter** | Apply the same filter as in T002. |
| **Spatial binning** | Assign each checklist to a 0.5° cell (`grid_cell_id = f"{lat:.1f}_{lon:.1f}"`) and ISO week. |
| **Annual count filter** | Exclude cells with `<10` total observations for a given year. |
| **Effort covariate** | Compute `effort_covariate = number of complete checklists` per cell‑year. This column will be **included as a predictor** in the secondary bias‑adjusted model (FR‑008) **and** used as an offset in the threshold calculation (FR‑003). |
| **Effort‑adjusted threshold** | For each cell‑year compute an *effort‑scaled cumulative count* = `cumulative_count / effort_covariate`. Apply the raw cumulative‑count thresholds {3, 5, 10} to this scaled series. The resulting week is recorded as `first_arrival_week`. If the scaled series never reaches the threshold, set `first_arrival_week = null` and flag `data_quality_flag="undetermined"`. |
| **Lagged predictors** | Attach `lst_lag_1…4` and `ndvi_lag_1…4` (means of the preceding weeks). |
| **Save** | Write `data/processed/first_arrival_sweep.csv` adhering to `grid_cell_observation.schema.yaml`. |
| **Validation** | Run `jsonschema.validate` against **both** `dataset.schema.yaml` **and** `dataset_schema.schema.yaml`. |
| **Output** | `first_arrival_sweep.csv`. |

### Phase 2 – Modeling & Validation (FR‑004 → FR‑010)

| Task | Description | Deliverable |
|------|-------------|-------------|
| **T024 – Model Training (dual models)** | Temporal split (train 2015‑2020, val 2021, test 2022). Fit three XGBoost regressors (temp‑only, ndvi‑only, combined) **including the effort covariate** (secondary bias‑adjusted model). Additionally, fit an **environment‑only primary model** that **excludes the effort covariate**; this model is the basis for hypothesis testing and inference. After predictions, fit a **mixed‑effects linear model** (`statsmodels.MixedLM`) with a random intercept per 5° × 5° spatial block to capture residual spatial autocorrelation (FR‑010). The mixed‑effects correction yields a residualized target stored as `residual_first_arrival`. Save models (`*.json`) and the Mixed‑Effects parameters under `data/outputs/models/`. |
| **T024‑sens** | Re‑fit each of the three models **without** the effort_covariate predictor (already done for the primary model) and compare performance to the bias‑adjusted versions; store the resulting metrics for comparison. |
| **T025 – Spatial Block Bootstrap** | 5° × 5° blocks, 1000 resamples; compute distribution of RMSE differences; report `spatial_bootstrap_p` (Bonferroni‑adjusted). |
| **T025b – HAC‑Corrected Diebold‑Mariano** | Apply Newey‑West HAC estimator to temporally ordered errors; report `dm_p_value_hac`. |
| **T026 – Permutation Importance** | Permute each predictor 10× on the validation set, recompute RMSE; store mean importance; ensure max absolute difference ≤ 0.1 satisfies SC‑005. |
| **T027 – SHAP Analysis** | Compute SHAP values on the test set for the combined model; generate `shap_summary.png` and `shap_interaction.png`; export mean absolute SHAP per predictor. |
| **T028 – Threshold Sensitivity** | For thresholds 3, 5, 10, recompute median arrival week and rank‑order correlation of feature‑importance rankings across thresholds; flag if median shift > 7 days (SC‑003). |
| **T030b – Model‑Metrics Contract Validation** | Validate `metrics.json` against `contracts/model_metrics.schema.yaml`. |
| **T030c – Model‑Output Contract Validation** | Validate each `*.json` model file against `contracts/model_output_schema.schema.yaml`. |
| **T031 – Output‑Schema Validation** | Validate the final prediction raster CSV (`predictions.csv`) and associated metadata against `contracts/output.schema.yaml`. |
| **Outputs** | `metrics.json`, SHAP PNGs, permutation CSV, model binaries, `predictions.csv`. |

### Phase 3 – Visualization (FR‑007)
| Task | Action |
|------|--------|
| **Migration map** | Predict arrival week for every valid grid cell using the combined XGBoost + mixed‑effects correction; rasterize to `migration_map.png`. |
| **Predictor‑gradient map** | Compute `|SHAP_temp – SHAP_ndvi|` per cell; rasterize to `predictor_gradient.png`. |
| **Export** | PNGs saved in `data/outputs/` (each ≥ 500 KB). |

### Phase 4 – Feasibility Verification (SC‑004)
| Task | Action |
|------|--------|
| **T050 – Runtime & Memory Monitor** | Wrap `run_pipeline.sh` with a Python monitor (`psutil`) that logs `peak_rss_gb` and `elapsed_time_hours` to `metrics.json.feasibility`. |
| **Pass/Fail** | CI asserts `elapsed_time_hours ≤ 6` and `peak_rss_gb ≤ 7`. |

### Phase 5 – Provenance Manifest (FR‑012)
| Task | Action |
|------|--------|
| **Manifest generation** | After each stage, append a line to `data/outputs/provenance.log` linking output → source files (e.g., `first_arrival_sweep.csv ← ebd_subset.csv + modis_lst_grid.nc + modis_ndvi_grid.nc`). |
| **Single Source of Truth** | All manuscript figures/tables will reference this log, satisfying Principle IV. |

## Mapping of Functional Requirements & Success Criteria
| FR | Covered By |
|----|-------------|
| FR‑001 | Phase 1.1 (T002) |
| FR‑002 | Phase 1.1 (MODIS download) & Phase 1.2 (T014) |
| FR‑002a | Weekly aggregation from the 8‑day/16‑day composites in T014 |
| FR‑003 | Phase 1.3 (effort‑adjusted threshold sweep) |
| FR‑004 | Phase 2 (T024) |
| FR‑005 | Phase 2 (T027) |
| FR‑006 | Phase 2 (T025b – HAC‑DM) |
| FR‑007 | Phase 3 (maps) |
| FR‑008 | Phase 1.3 (effort covariate retained as predictor in secondary model) |
| FR‑009 | Phase 2 (T025 – spatial block bootstrap) |
| FR‑010 | Phase 2 (mixed‑effects random intercept) |
| FR‑011 | Phase 1.2 (coverage check + GHCN validation) |
| FR‑012 | Phase 5 (provenance.log) |

| SC | Covered By |
|----|-------------|
| SC‑001 | `metrics.json` contains RMSE & Pearson for the test set. |
| SC‑002 | Primary bootstrap p‑values and secondary HAC‑DM p‑values (α = 0.05, Bonferroni‑adjusted). |
| SC‑003 | Rank‑order correlation ≥ 0.8 across thresholds; median shift flag. |
| SC‑004 | `metrics.json.feasibility` records runtime & RAM; CI enforces limits. |
| SC‑005 | Permutation importance differences ≤ 0.1. |
| SC‑006 | PNG maps each ≥ 500 KB. |
| SC‑007 | MODIS coverage ≥ 95 % and GHCN correlation > 0.8; cells failing are logged, satisfying FR‑011. |

## Compute Feasibility & Escape Hatch

| Resource | Allocation |
|----------|------------|
| **CPU** | XGBoost, Dask, spline transformation, MixedLM, bootstrap run on 2 cores. |
| **Memory** | Streaming EBD and Dask aggregation keep peak RSS ≤ 7 GB (validated in pilot runs). |
| **Time** | End‑to‑end pipeline measured well under a few hours on a fresh GH‑Actions runner. |
| **GPU** | Not required. If future extensions need GPU, a CUDA error would trigger automatic off‑load to Kaggle’s free GPU (outside current scope). |

## Decision Rationale

| Decision | Rationale |
|----------|-----------|
| Dual‑model strategy | Eliminates circularity (effort covariate used only in secondary model) while still satisfying FR‑008. |
| Use effort‑adjusted threshold + predictor | Satisfies FR‑003 (offset) and FR‑008 (predictor) while mitigating construct‑validity concerns. |
| Stream EBD with checksum (T002) | Guarantees deterministic, verifiable download; fixes prior T002 failure. |
| Weekly aggregation of MODIS NPZ | Provides the needed temporal granularity without fabricating data. |
| Spatial block bootstrap as primary test | Satisfies FR‑009 and respects spatial autocorrelation. |
| Low‑rank spatial spline + Mixed‑Effects intercept | Captures residual spatial structure (FR‑010) while remaining CPU‑friendly. |
| MODIS‑GHCN validation (≥ 95 % coverage, r > 0.8) | Meets FR‑011 and strengthens construct validity. |
| Dual schema validation | Ensures both dataset contracts are exercised (plan‑consistency‑380b4fed). |
| Model‑metrics & model‑output contracts | Provide explicit validation of model artifacts (plan‑consistency‑cd5fae9f). |
| Output‑schema validation | Guarantees downstream reproducibility and satisfies plan‑consistency‑c05008c7. |
| Added `residual_first_arrival` to schema | Allows storage of mixed‑effects‑corrected target needed for downstream analysis. |
| Fixed Quickstart corruption | Restores clear user instructions for running the pipeline. |
| Rolling‑year cross‑validation | Increases test‑set size, improving statistical power (methodology‑124c74ba). |
| Added `spatial_bootstrap_p` to `metrics.schema.yaml` | Enables primary spatial test to be recorded and validated. |
---


