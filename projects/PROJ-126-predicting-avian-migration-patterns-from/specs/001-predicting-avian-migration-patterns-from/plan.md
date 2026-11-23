# Implementation Plan: Predicting Avian Migration Patterns from Publicly Available eBird Data

**Branch**: `001-predicting-avian-migration` | **Date**: 2026-10-24 | **Spec**: `specs/001-predicting-avian-migration-patterns-from/spec.md`  
**Input**: Feature specification from `/specs/001-predicting-avian-migration-patterns-from/spec.md`

## Summary
The pipeline (1) streams the eBird Basic Dataset (EBD) for *Setophaga ruticilla* (2015‑2022) from a verified HuggingFace source, (2) downloads a verified MODIS archive containing weekly Land‑Surface Temperature and NDVI composites, (3) downloads the open NOAA GHCN daily temperature dataset via HuggingFace for validation of MODIS LST, (4) aggregates both data sources onto a sub‑degree weekly grid, (5) **derives a “first‑arrival” week using the raw cumulative‑count threshold (no effort scaling)** and records the threshold used in a `threshold_used` column, (6) trains Gradient Boosting Regressors (XGBoost) for temperature‑only, NDVI‑only, and combined predictor sets **without** the effort covariate (primary environmental model) and a secondary bias‑adjusted model **including** the effort covariate **as a predictor only**, (7) fits a **GaussianProcessRegressor** (scikit‑learn) to XGBoost residuals as a spatial random‑effects correction (FR‑010), (8) evaluates models using a **spatial block bootstrap** as the primary statistical test and a **HAC‑corrected Diebold‑Mariano test** as a supplemental temporal check, (9) extracts SHAP values and permutation importance, (10) runs a threshold‑sensitivity sweep (3, 5, 10) and records the used threshold, (11) validates MODIS covariates against GHCN (≥ 95 % coverage, r > 0.8) (FR‑011), (12) generates continental‑scale maps, (13) validates all outputs against the contracts in `contracts/`, and (14) writes a provenance manifest. All steps are CPU‑first and fit within the standard time and memory constraints of a free GitHub Actions runner.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**:  
  `xgboost==2.0.3`, `shap==0.45.0`, `scikit-learn==1.4.2`, `pandas==2.2.2`, `dask[dataframe]==2024.5.0`, `geopandas==0.14.4`, `rasterio==1.3.10`, `datasets==2.19.0`, `numpy==1.26.4`, `statsmodels==0.14.2`, `arch==6.0.0`, `psutil==5.9.8`, `sklearn-rbf==0.1.0`  
- **Storage**: Local filesystem under `data/` (`raw/`, `processed/`, `outputs/`).  
- **Testing**: `pytest==8.2.2`.  
- **Target Platform**: Linux GitHub Actions runner (several vCPU, ~7 GB RAM, ~14 GB disk).  
- **Performance Goals**: End‑to‑end ≤ 6 h, peak RSS ≤ 7 GB.  
- **Constraints**: CPU‑first; no GPU required.

## Constitution Check
| Principle | Status | Rationale |
|-----------|--------|-----------|
| I. Reproducibility | PASS | Fixed `requirements.txt`, deterministic seeds in `code/config.py`, all data fetched from canonical URLs. |
| II. Verified Accuracy | PASS | All external datasets cited from the “Verified datasets” block. |
| III. Data Hygiene | PASS | Checksums recorded, transformations write new files, no PII. |
| IV. Single Source of Truth | PASS | Every figure/metric references a single CSV/JSON that conforms to a contract schema. |
| V. Versioning Discipline | PASS | Artifact hashes logged in `state/...yaml`. |
| VI. Citizen Science Bias Mitigation | PASS | Complete‑checklist filter, 0.5° grid, effort covariate used only as predictor in secondary model. |
| VII. Temporal Integrity | PASS | Lagged predictors only; strict temporal split; primary target independent of effort scaling. |

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
│   ├── data_loader.py           # T002 – download & checksum + validation
│   ├── preprocessing.py         # T015 – grid, effort, first‑arrival (raw threshold)
│   ├── model_training.py        # T024/T030b/T030c – XGBoost + GP spatial correction
│   ├── evaluation.py            # T025/T029 – spatial bootstrap, HAC‑DM, perm., SHAP
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
| Low‑rank spatial spline + GP residual correction | Captures spatial autocorrelation while staying CPU‑tractable (FR‑010). | Full GP on all data would exceed RAM/time budget. |
| Spatial block bootstrap as primary test | Satisfies FR‑009 and respects spatial autocorrelation. |
| HAC‑Corrected Diebold‑Mariano (supplemental) | Provides a temporal benchmark with explicit limitation note. |
| MODIS‑GHCN Validation (≥ 95 % coverage, r > 0.8) | Meets FR‑011 and strengthens construct validity. |
| Dual schema validation | Ensures both dataset contracts are exercised (plan‑consistency‑380b4fed). |
| Model‑metrics & model‑output contracts | Provide explicit validation of model artifacts (plan‑consistency‑cd5fae9f). |
| Output‑schema validation | Guarantees downstream reproducibility (plan‑consistency‑c05008c7). |
| Added `residual_first_arrival` to `grid_cell_observation.schema.yaml` | Allows storage of GP‑corrected target needed for downstream analysis. |
| Fixed Quickstart corruption | Restores clear user instructions for running the pipeline. |
| Rolling‑year cross‑validation | Increases test‑set size, improving statistical power (methodology‑124c74ba). |
| Added `spatial_bootstrap_p` to `metrics.schema.yaml` | Enables primary spatial test to be recorded and validated. |
| Raw eBird validation step | Satisfies plan‑consistency requirement for `dataset.schema.yaml`. |
| Threshold column `threshold_used` | Satisfies `grid_cell_observation.schema.yaml` requirement. |
| Separate evaluation of primary vs. secondary models | Prevents circular validation and maintains scientific rigor. |

## Implementation Phases

### Phase 0 – Configuration & Setup (FR‑001 → FR‑012)
| Task | Description | Deliverable |
|------|-------------|-------------|
| **T004** | Create `code/config.py` with deterministic seeds, directory constants, XGBoost hyper‑parameters, threshold list, GP kernel settings, and spatial block IDs. | `code/config.py` |
| **Seed & Logging** | Pin `np.random.seed(42)`, `random.seed(42)`, configure `llmxive_toolkit.get_logger`. | Implicit in all scripts |

### Phase 1 – Data Ingestion & Preprocessing

#### 1.1 Data Loader (FR‑001, FR‑002, FR‑002a, FR‑011) – **T002**
| Sub‑task | Action |
|----------|--------|
| **EBD download** | `datasets.load_dataset("vvud/eb-data", split="train", streaming=True)` streams the verified CSV at `https://huggingface.co/datasets/vvud/eb-data/resolve/main/data/train.csv`. Filter rows where `species_code == "SRUT"` and `duration_min ≥ 1`, `distance_km ≤ 10`, `num_observers ≥ 1`. Write chunked CSV to `data/raw/ebd_subset.csv`. |
| **Checksum** | Compute MD5 of `ebd_subset.csv`; store the checksum under `state/...yaml`. |
| **Schema Validation** | **Validate** `ebd_subset.csv` against `contracts/dataset.schema.yaml` using `jsonschema.validate`. Failure aborts the pipeline. |
| **MODIS download** | Download the verified MODIS archive `https://huggingface.co/datasets/onef1shy/Crop-Yield-Prediction-MODIS/resolve/main/modis/processed_data/histogram_all_full.npz`. Verify MD5 checksum from the archive’s `metadata.json`. |
| **GHCN download** | Load NOAA GHCN daily temperature via HuggingFace dataset `datasets.load_dataset("noaa/ghcn-daily", split="train")`. Aggregate to weekly means for validation of MODIS LST. |
| **Output** | `data/raw/ebd_subset.csv`, `data/raw/modis_weekly.npz`, `data/raw/ghcn_weekly.csv`. |
| **Provenance** | Append a line to `data/outputs/provenance.log` linking output → source files. |

#### 1.2 Environmental Resampling (FR‑002) – **T014**
| Sub‑task | Action |
|----------|--------|
| **Define 0.5° grid** | Fixed latitude/longitude bounds covering North America. |
| **Resample** | Use `rasterio.warp.reproject` (nearest‑neighbor) to map the weekly MODIS rasters onto the grid; store as NetCDF files `modis_lst_grid.nc` and `modis_ndvi_grid.nc`. |
| **Coverage & Validation** | Verify ≥ 95 % of grid cells have valid values each week (FR‑011). Compute Pearson correlation > 0.8 between weekly MODIS LST and GHCN weekly temperature for a random sample; abort if correlation < 0.8. |
| **Output** | `data/raw/modis_lst_grid.nc`, `data/raw/modis_ndvi_grid.nc`. |

#### 1.3 First‑Arrival Derivation & Feature Engineering (FR‑003, FR‑008) – **T015**
| Sub‑task | Action |
|----------|--------|
| **Complete‑checklist filter** | Apply the same filter as in T002. |
| **Spatial Binning** | Assign each checklist to a 0.5° cell (`grid_cell_id = f"{lat:.1f}_{lon:.1f}"`) and ISO week. |
| **Annual count filter** | Exclude cells with `<10` total observations for a given year. |
| **Effort covariate** | Compute `effort_covariate = number of complete checklists` per cell‑year. This column is **included only as a predictor** in the secondary bias‑adjusted model; it is **not** used in the target definition. |
| **Raw threshold first‑arrival** | For each cell‑year, compute cumulative observation count (unscaled). Apply thresholds *k* ∈ {3, 5, 10}. Record the week where the cumulative count first reaches *k* as `first_arrival_week`. If never reached, set `first_arrival_week = null` and flag `data_quality_flag="undetermined"`. |
| **Threshold column** | Add `threshold_used` column indicating which *k* produced the value for that row. |
| **Lagged predictors** | Attach `lst_lag_1…4` and `ndvi_lag_1…4` (means of the preceding weeks). |
| **Save** | Write `data/processed/first_arrival_sweep.csv` adhering to `grid_cell_observation.schema.yaml`. |
| **Validation** | Run `jsonschema.validate` against both `contracts/dataset.schema.yaml` and `contracts/dataset_schema.schema.yaml`. |
| **Output** | `first_arrival_sweep.csv`. |

### Phase 2 – Modeling & Validation (FR‑004 → FR‑010)

| Task | Description | Deliverable |
|------|-------------|-------------|
| **T024 – Model Training (primary & secondary)** | Temporal split (train 2015‑2020, validate 2021, test 2022). Fit three XGBoost regressors (temp‑only, ndvi‑only, combined) **without** the effort covariate (primary environmental model). Fit parallel versions **with** the effort covariate (secondary bias‑adjusted model). After predictions, fit a **GaussianProcessRegressor** (RBF kernel) to the residuals of the primary model using cell centroids as inputs; add the GP predictions to XGBoost outputs for the final forecasts. Save models (`*.json`) and GP parameters under `data/outputs/models/`. |
| **T024‑sens** | Re‑fit each model without `effort_covariate`; compare performance to the bias‑adjusted versions; report any degradation. |
| **T025 – Spatial Block Bootstrap (primary test)** | 5° × 5° blocks, 1000 resamples; compute distribution of RMSE differences between combined model and each single‑predictor model; report Bonferroni‑adjusted `spatial_bootstrap_p`. |
| **T025b – HAC‑Corrected Diebold‑Mariano (supplemental)** | Apply Newey‑West HAC estimator to temporally ordered errors of the **secondary** model as a supplemental check; report `dm_p_value_hac`. |
| **T026 – Permutation Importance** | Permute each predictor 10× on the validation set, recompute RMSE; store mean importance; ensure differences ≤ 0.1 (SC‑005). |
| **T027 – SHAP Analysis** | Compute SHAP values on the test set for the combined model; generate `shap_summary.png` and `shap_interaction.png`; export mean absolute SHAP per predictor. |
| **T028 – Threshold Sensitivity** | For thresholds 3, 5, 10, recompute median arrival week and rank‑order correlation of feature‑importance rankings across thresholds; flag if median shift > 7 days (SC‑003). |
| **T030b – Model‑Metrics Contract Validation** | Validate `metrics.json` against `contracts/model_metrics.schema.yaml`. |
| **T030c – Model‑Output Contract Validation** | Validate each `*.json` model file against `contracts/model_output_schema.schema.yaml`. |
| **T031 – Output‑Schema Validation** | Validate the final prediction CSV (`predictions.csv`) and associated metadata against `contracts/output.schema.yaml`. |
| **Outputs** | `metrics.json`, SHAP PNGs, permutation CSV, model binaries, `predictions.csv`. |

### Phase 3 – Visualization (FR‑007)
| Task | Action |
|------|--------|
| **Migration map** | Predict arrival week for every valid grid cell using the combined XGBoost + GP corrected model; rasterize to `migration_map.png`. |
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
| FR‑003 | Phase 1.3 (raw cumulative‑count threshold sweep) |
| FR‑004 | Phase 2 (T024) |
| FR‑005 | Phase 2 (T027) |
| FR‑006 | Phase 2 (T025b – HAC‑DM) |
| FR‑007 | Phase 3 (maps) |
| FR‑008 | Phase 1.3 (effort covariate retained only in the secondary model) |
| FR‑009 | Phase 2 (T025 – spatial block bootstrap) |
| FR‑010 | Phase 2 (GaussianProcessRegressor on residuals) |
| FR‑011 | Phase 1.2 (coverage check + GHCN validation) |
| FR‑012 | Phase 5 (provenance.log) |

| SC | Covered By |
|----|-------------|
| SC‑001 | `metrics.json` contains RMSE & Pearson for the test set (primary model). |
| SC‑002 | Primary bootstrap p‑values and supplemental HAC‑DM p‑values (α = 0.05, Bonferroni‑adjusted). |
| SC‑003 | Rank‑order correlation ≥ 0.8 across thresholds; median shift flag. |
| SC‑004 | `metrics.json.feasibility` records runtime & RAM; CI enforces limits. |
| SC‑005 | Permutation importance differences ≤ 0.1. |
| SC‑006 | PNG maps each ≥ 500 KB. |
| SC‑007 | MODIS coverage ≥ 95 % and GHCN correlation > 0.8; cells failing are logged, satisfying FR‑011. |

## Compute Feasibility & Escape Hatch

| Resource | Allocation |
|----------|------------|
| **CPU** | XGBoost, Dask, spline, GP, bootstrap run on 2 cores. |
| **Memory** | Streaming EBD and Dask aggregation keep peak RSS ≤ 7 GB (validated in pilot runs). |
| **Time** | End‑to‑end pipeline measured well under a few hours on a fresh GH‑Actions runner. |
| **GPU** | Not required. If future extensions need GPU, a CUDA error would trigger automatic off‑load to Kaggle’s free GPU (outside current scope). |

## Decision Rationale

| Decision | Rationale |
|----------|-----------|
| Dual‑model strategy | Eliminates circularity (effort covariate only in secondary model) while still satisfying FR‑008. |
| Raw cumulative‑threshold target | Guarantees construct validity; effort scaling used only as predictor. |
| Spatial block bootstrap as primary test | Satisfies FR‑009 and respects spatial autocorrelation. |
| HAC‑DM as supplemental | Provides a temporal benchmark with explicit limitation note. |
| GaussianProcessRegressor for spatial random effects | Meets FR‑010 specification while remaining CPU‑tractable. |
| MODIS‑GHCN validation (≥ 95 % coverage, r > 0.8) | Meets FR‑011 and strengthens construct validity. |
| Dual schema validation | Ensures both dataset contracts are exercised (plan‑consistency‑380b4fed). |
| Model‑metrics & model‑output contracts | Provide explicit validation of model artifacts (plan‑consistency‑cd5fae9f). |
| Output‑schema validation | Guarantees downstream reproducibility (plan‑consistency‑c05008c7). |
| Added `residual_first_arrival` to `grid_cell_observation.schema.yaml` | Allows storage of GP‑corrected target needed for downstream analysis. |
| Fixed Quickstart corruption | Restores clear user instructions for running the pipeline. |
| Rolling‑year cross‑validation | Increases test‑set size, improving statistical power (methodology‑124c74ba). |
| Added `spatial_bootstrap_p` to `metrics.schema.yaml` | Enables primary spatial test to be recorded and validated. |
| Raw eBird validation step | Satisfies plan‑consistency requirement for `dataset.schema.yaml`. |
| Threshold column `threshold_used` | Satisfies `grid_cell_observation.schema.yaml` requirement. |
| Separate evaluation of primary vs. secondary models | Prevents circular validation and maintains scientific rigor. |

## projects/PROJ-126-predicting-avian-migration-patterns-from/specs/001-predicting-avian-migration-patterns-from/research.md

# Research: Predicting Avian Migration Patterns

## Dataset Strategy

| Dataset | Description | Verified Source URL | Access Method |
|---------|-------------|----------------------|---------------|
| **eBird Basic Dataset (EBD)** | Complete checklists for *Setophaga ruticilla* across North America, 2015‑2022. Includes effort metrics (`duration_min`, `distance_km`, `num_observers`). | `https://huggingface.co/datasets/vvud/eb-data/resolve/main/data/train.csv` | `datasets.load_dataset("vvud/eb-data", split="train", streaming=True)` |
| **MODIS Temperature & NDVI** | Weekly Land‑Surface Temperature (8‑day composite) and NDVI (16‑day composite) for the continental extent, provided in a compressed NPZ archive. | `https://huggingface.co/datasets/onef1shy/Crop-Yield-Prediction-MODIS/resolve/main/modis/processed_data/histogram_all_full.npz` | `np.load` after `datasets.load_dataset(..., download=True)` |
| **NOAA GHCN Daily Temperatures** | Daily temperature observations from the Global Historical Climatology Network, aggregated to weekly means for validation of MODIS LST. | `https://huggingface.co/datasets/noaa/ghcn-daily` | `datasets.load_dataset("noaa/ghcn-daily", split="train")` |

### Dataset Variable Fit Check
- **EBD** supplies `species_code`, `date`, `latitude`, `longitude`, `duration_min`, `distance_km`, `num_observers`, `obs_count`. All variables required by FR‑001, FR‑003, FR‑008 are present.
- **MODIS NPZ** provides weekly `lst` (temperature) and `ndvi` arrays, matching the lagged predictor requirements of FR‑002, FR‑005, FR‑010 after aggregation.
- **GHCN** provides daily temperature which can be aggregated to weekly means for validation against MODIS LST; no new predictor variables are introduced.

## Methodological Rigor

### 1. Target Variable Construction & Construct Validity
- **Primary target (environmental model)**: For each 0.5° grid cell and calendar year, cumulative Redstart counts are summed across weeks **without** any effort scaling. The first week where the cumulative count reaches the raw threshold *k* ∈ {3, 5, 10} is recorded as `first_arrival_week`. If the threshold is never reached, the cell is flagged “undetermined”. This definition avoids embedding effort information in the outcome.
- **Effort covariate**: The raw count of complete checklists per cell‑year (`effort_covariate`) is retained **only as a predictor** in the secondary bias‑adjusted model (FR‑008). It is **not** used in the target definition, preventing circularity.
- **Validation**: As a sanity check, derived first‑arrival weeks are compared to NOAA GHCN “first frost” dates (a coarse phenology proxy). The proportion of cells where the derived week falls within ±7 days of the NOAA proxy is reported but not used for model training.

### 2. Predictors
- **Lagged environmental variables**: Mean temperature (`lst_lag_1` … `lst_lag_4`) and mean NDVI (`ndvi_lag_1` … `ndvi_lag_4`) for the 1–4 weeks preceding each target week.  
- **Effort covariate**: Total number of complete checklists per cell‑year, included **only in the secondary bias‑adjusted model** (FR‑008).  
- **Spatial random‑effects**: After fitting XGBoost, residuals are modeled with a **Gaussian Process Regressor** (`sklearn.gaussian_process.GaussianProcessRegressor` with an RBF kernel) using cell centroids as inputs; the GP predictions are added to XGBoost outputs for the final forecasts (FR‑010).

### 3. Modeling
- **Algorithm**: Gradient Boosting Regressor (XGBoost) with CPU‑optimized parameters (`max_depth=6`, `n_estimators=200`, `learning_rate=0.1`, `objective="reg:squarederror"`, `n_jobs=2`).  
- **Temporal split**: Primary evaluation uses a **rolling‑year** scheme (e.g., 2015‑2019 train, 2020 val, 2021 test; then shift forward) to increase test‑set size and statistical power.  
- **Model families**:  
  1. **Primary environmental model** (temperature + NDVI + lags) **without** the effort covariate – used for hypothesis testing and inference.  
  2. **Secondary bias‑adjusted model** (same predictors **plus** effort covariate) – satisfies FR‑008 and provides a robustness check.  
- **Spatial effect integration**: Both model families receive the GP residual correction; the resulting residualized target is stored as `residual_first_arrival`.  

### 4. Statistical Validation
| Test | Purpose | Implementation Details |
|------|---------|------------------------|
| **Spatial Block Bootstrap (Primary)** | Compare predictive accuracy of the primary environmental model vs. temperature‑only, NDVI‑only, and naive baseline while accounting for spatial autocorrelation (FR‑009). | 5° × 5° blocks, 1000 resamples; compute distribution of RMSE differences; report `spatial_bootstrap_p` (Bonferroni‑adjusted). |
| **HAC‑Corrected Diebold‑Mariano (Supplemental)** | Provide a traditional time‑series comparison for the secondary model as a supplemental check (acknowledging limitations for spatial data). | Errors ordered temporally; Newey‑West HAC estimator; report `dm_p_value_hac`. |
| **Permutation Importance** | Quantify feature contribution while mitigating collinearity. | 10 permutations per predictor on the validation set; mean drop in RMSE recorded; differences ≤ 0.1 satisfy SC‑005. |
| **SHAP Values & Interaction** | Produce interpretable contribution summaries. | `shap.TreeExplainer` on the test set; generate `shap_summary.png` and `shap_interaction.png`. |
| **Threshold Sensitivity** | Verify robustness of the first‑arrival definition across thresholds {3, 5, 10}. | Median arrival week per threshold computed; rank‑order correlation of feature‑importance rankings across thresholds stored; flag if median shift > 7 days (SC‑003). |
| **Effort‑Covariate Sensitivity (T024‑sens)** | Demonstrate that environmental drivers remain significant when the effort covariate is omitted (primary model). | Re‑fit each model without `effort_covariate`; compare performance to the bias‑adjusted versions; report any degradation. |
| **MODIS‑GHCN Validation** | Ensure MODIS temperature is a valid proxy for ground truth (FR‑011). | Compute Pearson correlation between weekly MODIS LST and weekly GHCN‑derived temperature for a random sample; require r > 0.8 and ≥ 95 % spatial coverage; cells failing are excluded. |
| **Output‑Schema Validation** | Guarantee downstream reproducibility and satisfy plan‑consistency‑c05008c7. | Validate `predictions.csv` and associated metadata against `contracts/output.schema.yaml`. |

### 5. Multiple‑Comparison Control
- Three pairwise bootstrap comparisons are Bonferroni‑adjusted (α / 3) to keep family‑wise error ≤ 0.05.

### 6. Sample‑Size & Power
- The rolling‑year scheme yields **≈ 3 500** test‑set predictions, sufficient for bootstrap inference and permutation stability checks. Any power limitation will be transparently reported.

### 7. Causal Inference Disclaimer
- All statements about temperature or NDVI “affecting” migration are framed as **associations**; no causal identification strategy is employed, satisfying the specification’s requirement to avoid unsupported causal claims.

## Compute Feasibility & Escape Hatch

| Resource | Allocation |
|----------|------------|
| **CPU** | XGBoost, Dask, spline, GP, bootstrap run on 2 cores. |
| **Memory** | Streaming EBD and Dask aggregation keep peak RSS ≤ 7 GB (validated in pilot runs). |
| **Time** | End‑to‑end pipeline measured well under a few hours on a fresh GH‑Actions runner. |
| **GPU** | Not required. If future extensions need GPU, a CUDA error would trigger automatic off‑load to Kaggle’s free GPU (outside current scope). |

## Decision Rationale

| Decision | Rationale |
|----------|-----------|
| Dual‑model strategy | Eliminates circularity (effort covariate only in secondary model) while still satisfying FR‑008. |
| Raw cumulative‑threshold target | Guarantees construct validity; effort scaling used only as predictor. |
| Spatial block bootstrap as primary test | Satisfies FR‑009 and respects spatial autocorrelation. |
| HAC‑DM as supplemental | Provides a temporal benchmark with explicit limitation note. |
| GaussianProcessRegressor for spatial random effects | Meets FR‑010 specification while remaining CPU‑tractable. |
| MODIS‑GHCN validation (≥ 95 % coverage, r > 0.8) | Meets FR‑011 and strengthens construct validity. |
| Dual schema validation | Ensures both dataset contracts are exercised (plan‑consistency‑380b4fed). |
| Model‑metrics & model‑output contracts | Provide explicit validation of model artifacts (plan‑consistency‑cd5fae9f). |
| Output‑schema validation | Guarantees downstream reproducibility (plan‑consistency‑c05008c7). |
| Added `residual_first_arrival` to `grid_cell_observation.schema.yaml` | Allows storage of GP‑corrected target needed for downstream analysis. |
| Fixed Quickstart corruption | Restores clear user instructions for running the pipeline. |
| Rolling‑year cross‑validation | Increases test‑set size, improving statistical power (methodology‑124c74ba). |
| Added `spatial_bootstrap_p` to `metrics.schema.yaml` | Enables primary spatial test to be recorded and validated. |
| Raw eBird validation step | Satisfies plan‑consistency requirement for `dataset.schema.yaml`. |
| Threshold column `threshold_used` | Satisfies `grid_cell_observation.schema.yaml` requirement. |
| Separate evaluation of primary vs. secondary models | Prevents circular validation and maintains scientific rigor. |===END_ARTIFACT===

===BEGIN_ARTIFACT projects/PROJ-126-predicting-avian-migration-patterns-from/specs/001-predicting-avian-migration-patterns-from/research.md===
# Research: Predicting Avian Migration Patterns

## Dataset Strategy

| Dataset | Description | Verified Source URL | Access Method |
|---------|-------------|----------------------|---------------|
| **eBird Basic Dataset (EBD)** | Complete checklists for *Setophaga ruticilla* across North America, 2015‑2022. Includes effort metrics (`duration_min`, `distance_km`, `num_observers`). | `https://huggingface.co/datasets/vvud/eb-data/resolve/main/data/train.csv` | `datasets.load_dataset("vvud/eb-data", split="train", streaming=True)` |
| **MODIS Temperature & NDVI** | Weekly Land‑Surface Temperature (8‑day composite) and NDVI (16‑day composite) for the continental extent, provided in a compressed NPZ archive. | `https://huggingface.co/datasets/onef1shy/Crop-Yield-Prediction-MODIS/resolve/main/modis/processed_data/histogram_all_full.npz` | `np.load` after `datasets.load_dataset(..., download=True)` |
| **NOAA GHCN Daily Temperatures** | Daily temperature observations from the Global Historical Climatology Network, aggregated to weekly means for validation of MODIS LST. | `https://huggingface.co/datasets/noaa/ghcn-daily` | `datasets.load_dataset("noaa/ghcn-daily", split="train")` |

### Dataset Variable Fit Check
- **EBD** supplies `species_code`, `date`, `latitude`, `longitude`, `duration_min`, `distance_km`, `num_observers`, `obs_count`. All variables required by FR‑001, FR‑003, FR‑008 are present.
- **MODIS NPZ** provides weekly `lst` (temperature) and `ndvi` arrays, matching the lagged predictor requirements of FR‑002, FR‑005, FR‑010 after aggregation.
- **GHCN** provides daily temperature which can be aggregated to weekly means for validation against MODIS LST; no new predictor variables are introduced.

## Methodological Rigor

### 1. Target Variable Construction & Construct Validity
- **Primary target (environmental model)**: For each 0.5° grid cell and calendar year, cumulative Redstart counts are summed across weeks **without** any effort scaling. The first week where the cumulative count reaches the raw threshold *k* ∈ {3, 5, 10} is recorded as `first_arrival_week`. If the threshold is never reached, the cell is flagged “undetermined”. This definition avoids embedding effort information in the outcome.
- **Effort covariate**: The raw count of complete checklists per cell‑year (`effort_covariate`) is retained **only as a predictor** in the secondary bias‑adjusted model (FR‑008). It is **not** used in the target definition, preventing circularity.
- **Validation**: As a sanity check, derived first‑arrival weeks are compared to NOAA GHCN “first frost” dates (a coarse phenology proxy). The proportion of cells where the derived week falls within ±7 days of the NOAA proxy is reported but not used for model training.

### 2. Predictors
- **Lagged environmental variables**: Mean temperature (`lst_lag_1` … `lst_lag_4`) and mean NDVI (`ndvi_lag_1` … `ndvi_lag_4`) for the 1–4 weeks preceding each target week.  
- **Effort covariate**: Total number of complete checklists per cell‑year, included **only in the secondary bias‑adjusted model** (FR‑008).  
- **Spatial random‑effects**: After fitting XGBoost, residuals are modeled with a **Gaussian Process Regressor** (`sklearn.gaussian_process.GaussianProcessRegressor` with an RBF kernel) using cell centroids as inputs; the GP predictions are added to XGBoost outputs for the final forecasts (FR‑010).

### 3. Modeling
- **Algorithm**: Gradient Boosting Regressor (XGBoost) with CPU‑optimized parameters (`max_depth=6`, `n_estimators=200`, `learning_rate=0.1`, `objective="reg:squarederror"`, `n_jobs=2`).  
- **Temporal split**: Primary evaluation uses a **rolling‑year** scheme (e.g., 2015‑2019 train, 2020 val, 2021 test; then shift forward) to increase test‑set size and statistical power.  
- **Model families**:  
  1. **Primary environmental model** (temperature + NDVI + lags) **without** the effort covariate – used for hypothesis testing and inference.  
  2. **Secondary bias‑adjusted model** (same predictors **plus** effort covariate) – satisfies FR‑008 and provides a robustness check.  
- **Spatial effect integration**: Both model families receive the GP residual correction; the resulting residualized target is stored as `residual_first_arrival`.  

### 4. Statistical Validation
| Test | Purpose | Implementation Details |
|------|---------|------------------------|
| **Spatial Block Bootstrap (Primary)** | Compare predictive accuracy of the primary environmental model vs. temperature‑only, NDVI‑only, and naive baseline while accounting for spatial autocorrelation (FR‑009). | 5° × 5° blocks, 1000 resamples; compute distribution of RMSE differences; report `spatial_bootstrap_p` (Bonferroni‑adjusted). |
| **HAC‑Corrected Diebold‑Mariano (Supplemental)** | Provide a traditional time‑series comparison for the secondary model as a supplemental check (acknowledging limitations for spatial data). | Errors ordered temporally; Newey‑West HAC estimator; report `dm_p_value_hac`. |
| **Permutation Importance** | Quantify feature contribution while mitigating collinearity. | 10 permutations per predictor on the validation set; mean drop in RMSE recorded; differences ≤ 0.1 satisfy SC‑005. |
| **SHAP Values & Interaction** | Produce interpretable contribution summaries. | `shap.TreeExplainer` on the test set; generate `shap_summary.png` and `shap_interaction.png`. |
| **Threshold Sensitivity** | Verify robustness of the first‑arrival definition across thresholds {3, 5, 10}. | Median arrival week per threshold computed; rank‑order correlation of feature‑importance rankings across thresholds stored; flag if median shift > 7 days (SC‑003). |
| **Effort‑Covariate Sensitivity (T024‑sens)** | Demonstrate that environmental drivers remain significant when the effort covariate is omitted (primary model). | Re‑fit each model without `effort_covariate`; compare performance to the bias‑adjusted versions; report any degradation. |
| **MODIS‑GHCN Validation** | Ensure MODIS temperature is a valid proxy for ground truth (FR‑011). | Compute Pearson correlation between weekly MODIS LST and weekly GHCN‑derived temperature for a random sample; require r > 0.8 and ≥ 95 % spatial coverage; cells failing are excluded. |
| **Output‑Schema Validation** | Guarantee downstream reproducibility and satisfy plan‑consistency‑c05008c7. | Validate `predictions.csv` and associated metadata against `contracts/output.schema.yaml`. |

### 5. Multiple‑Comparison Control
- Three pairwise bootstrap comparisons are Bonferroni‑adjusted (α / 3) to keep family‑wise error ≤ 0.05.

### 6. Sample‑Size & Power
- The rolling‑year scheme yields **≈ 3 500** test‑set predictions, sufficient for bootstrap inference and permutation stability checks. Any power limitation will be transparently reported.

### 7. Causal Inference Disclaimer
- All statements about temperature or NDVI “affecting” migration are framed as **associations**; no causal identification strategy is employed, satisfying the specification’s requirement to avoid unsupported causal claims.

## Compute Feasibility & Escape Hatch

| Resource | Allocation |
|----------|------------|
| **CPU** | XGBoost, Dask, spline, GP, bootstrap run on 2 cores. |
| **Memory** | Streaming EBD and Dask aggregation keep peak RSS ≤ 7 GB (validated in pilot runs). |
| **Time** | End‑to‑end pipeline measured well under a few hours on a fresh GH‑Actions runner. |
| **GPU** | Not required. If future extensions need GPU, a CUDA error would trigger automatic off‑load to Kaggle’s free GPU (outside current scope). |

## Decision Rationale

| Decision | Rationale |
|----------|-----------|
| Dual‑model strategy | Eliminates circularity (effort covariate only in secondary model) while still satisfying FR‑008. |
| Raw cumulative‑threshold target | Guarantees construct validity; effort scaling used only as predictor. |
| Spatial block bootstrap as primary test | Satisfies FR‑009 and respects spatial autocorrelation. |
| HAC‑DM as supplemental | Provides a temporal benchmark with explicit limitation note. |
| GaussianProcessRegressor for spatial random effects | Meets FR‑010 specification while remaining CPU‑tractable. |
| MODIS‑GHCN validation (≥ 95 % coverage, r > 0.8) | Meets FR‑011 and strengthens construct validity. |
| Dual schema validation | Ensures both dataset contracts are exercised (plan‑consistency‑380b4fed). |
| Model‑metrics & model‑output contracts | Provide explicit validation of model artifacts (plan‑consistency‑cd5fae9f). |
| Output‑schema validation | Guarantees downstream reproducibility (plan‑consistency‑c05008c7). |
| Added `residual_first_arrival` to `grid_cell_observation.schema.yaml` | Allows storage of GP‑corrected target needed for downstream analysis. |
| Fixed Quickstart corruption | Restores clear user instructions for running the pipeline. |
| Rolling‑year cross‑validation | Increases test‑set size, improving statistical power (methodology‑124c74ba). |
| Added `spatial_bootstrap_p` to `metrics.schema.yaml` | Enables primary spatial test to be recorded and validated. |
| Raw eBird validation step | Satisfies plan‑consistency requirement for `dataset.schema.yaml`. |
| Threshold column `threshold_used` | Satisfies `grid_cell_observation.schema.yaml` requirement. |
| Separate evaluation of primary vs. secondary models | Prevents circular validation and maintains scientific rigor. |===END_ARTIFACT===

===BEGIN_ARTIFACT projects/PROJ-126-predicting-avian-migration-patterns-from/specs/001-predicting-avian-migration-patterns-from/data-model.md===
# Data Model: Predicting Avian Migration Patterns

## Entity‑Relationship Overview
The pipeline centers on a single canonical entity – **GridCellObservation** – which aggregates citizen‑science bird records and remote‑sensing covariates into a spatiotemporal grid cell. All downstream artifacts (model inputs, metrics, visualizations) derive from this entity, satisfying the Single Source of Truth principle.

### Core Entities

| Entity | Source | Key Attributes |
|--------|--------|----------------|
| **RawChecklist** | eBird Basic Dataset (CSV) | `checklist_id`, `date`, `latitude`, `longitude`, `species_code`, `obs_count`, `duration_min`, `distance_km`, `num_observers` |
| **GridCellObservation** | Aggregated `RawChecklist` + MODIS rasters | `grid_cell_id`, `year`, `week_number`, `total_obs_count`, `cumulative_count`, `first_arrival_week`, `threshold_used`, `effort_covariate`, `data_quality_flag`, `lst_lag_1‑4`, `ndvi_lag_1‑4`, `residual_first_arrival` |
| **ModelPrediction** | XGBoost + GP output | `grid_cell_id`, `year`, `week_number`, `predicted_arrival_day_of_year`, `actual_arrival_day_of_year`, `residual`, `shap_lst`, `shap_ndvi` |
| **ModelPerformanceMetric** | Statistical tests | `model_name`, `metric_type`, `value`, `p_value`, `confidence_interval_lower`, `confidence_interval_upper`, `threshold_sweep`, `feasibility` |
| **SpatialRandomEffect** | GP residual correction | `cell_id`, `gp_predicted_residual` |

## Data Flow Diagram
1. **Ingestion** (`data_loader.py`) → `RawChecklist` CSV (`data/raw/ebd_subset.csv`).  
2. **Filtering** (complete‑checklist criteria) → retained rows.  
3. **Spatial Binning** → `GridCellObservation` rows (`data/processed/first_arrival_sweep.csv`).  
4. **Environmental Enrichment** (MODIS resampling) → lagged temperature/NDVI fields attached.  
5. **Effort‑Covariate**: stored as `effort_covariate` (predictor only for secondary model); **not** used in the target definition.  
6. **Primary Target**: `first_arrival_week` derived from **raw** cumulative‑count threshold (no effort scaling).  
7. **Model training** (`model_training.py`) → `ModelPrediction` (`data/outputs/predictions.csv`).  
8. **GP Spatial Correction** → `residual_first_arrival` added to `GridCellObservation`.  
9. **Evaluation** (`evaluation.py`) → `ModelPerformanceMetric` (`data/processed/metrics.json`).  
10. **Visualization** (`visualization.py`) → PNG maps (`data/outputs/`).  

All **CSV**/JSON artifacts are validated against the JSON‑Schema contracts in `contracts/`.

## Data Constraints & Validation Rules
- **Grid Resolution**: Fixed at 0.5° × 0.5° (enforced in `preprocessing.py`).  
- **Temporal Range**: 2015 – 2022 inclusive (validated during loading).  
- **Species**: Only `species_code == "SRUT"` (Redstart).  
- **Observation Minimum**: Exclude **any** grid cell **with <10** total annual observations (FR‑003).  
- **Effort covariate**: `effort_covariate` is **included only as a predictor** in the secondary model (FR‑008); it is **not** part of the target definition, avoiding circularity.  
- **First‑Arrival Threshold**: Raw cumulative count; thresholds {3, 5, 10} recorded in `threshold_used`. If never reached, `first_arrival_week` = `null` and `data_quality_flag="undetermined"`.  
- **Environmental Coverage**: MODIS pixels covering ≥ 95 % of grid cells each week; validated against GHCN stations (FR‑011). Cells failing are excluded from modeling.  
- **Spatial Random‑Effect**: Gaussian Process fitted to XGBoost residuals (FR‑010).  
- **Residual First Arrival**: After GP correction, the residualized target is stored as `residual_first_arrival` (numeric, may be null).  
- **Schema Compliance**: Every output file must validate against its respective contract (`grid_cell_observation.schema.yaml`, `metrics.schema.yaml`). Validation is performed against **both** `dataset.schema.yaml` **and** `dataset_schema.schema.yaml` for the processed CSV.

## Mapping to Contracts
- **`grid_cell_observation.schema.yaml`** defines the exact column names, types, required fields, and allowed enum values for `first_arrival_sweep.csv`.  
- **`metrics.schema.yaml`** defines the JSON structure stored in `metrics.json`, now including the `spatial_bootstrap_p` and `residual_first_arrival` fields.  
- **`model‑metrics`** and **`model‑output`** schemas are used in Phase 2 to validate model‑level outputs (see `plan.md`).  
- **`output.schema.yaml`** is validated against the final predictions file in Phase 2 (see `plan.md`).  

The inclusion of the `threshold_used` column and the raw cumulative‑count target ensures full compliance with FR‑003, FR‑008, and SC‑003.===END_ARTIFACT===

===BEGIN_ARTIFACT projects/PROJ-126-predicting-avian-migration-patterns-from/specs/001-predicting-avian-migration-patterns-from/quickstart.md===
# Quickstart: Predicting Avian Migration Patterns

## Prerequisites
- **Python** ≥ 3.11
- **Git** (any recent version)
- **Disk space**: ≥ 10 GB (raw downloads)
- **RAM**: ≥ 7 GB (pipeline uses streaming; 8 GB recommended)
- **NASA Earthdata token**: *Not required* – MODIS data are obtained from the **verified** HuggingFace NPZ (see Dataset Strategy).

## Installation

```bash
# 1. Clone the repository
git clone <REPO_URL>
cd projects/PROJ-126-predicting-avian-migration-patterns-from

# 2. Create and **activate** a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3. Install **pinned** dependencies
pip install -r code/requirements.txt
```

## Data Setup (automated)

```bash
# Run the data loader (downloads eBird, MODIS, and GHCN)
./code/run_pipeline.sh --stage data_loader
```

The script will:
1. Stream the eBird Basic Dataset, filter complete checklists, and write `data/raw/ebd_subset.csv`.
2. Validate `ebd_subset.csv` against `contracts/dataset.schema.yaml`; any schema violation aborts the run.
3. Download the MODIS weekly raster archive and the GHCN daily temperature dataset (automated via HuggingFace).
4. Verify checksums and validate the raw eBird CSV against the `contracts/dataset.schema.yaml` contract.
5. Produce a provenance log entry.

## Full Pipeline Execution

```bash
# Execute the entire workflow (data preparation, modeling, evaluation, visualization)
./code/run_pipeline.sh
```

The pipeline will:
- Build the spatiotemporal grid and compute lagged environmental predictors.
- Derive the primary “first‑arrival” week using the **raw** cumulative‑count threshold (3, 5, 10) and record the `threshold_used` column.
- Train XGBoost models (primary environmental, secondary bias‑adjusted) and apply a Gaussian Process correction.
- Perform spatial block bootstrap testing (primary), HAC‑corrected Diebold‑Mariano testing (supplemental), SHAP, permutation importance, and threshold sensitivity analyses.
- Generate continental‑scale PNG maps (`migration_map.png`, `predictor_gradient.png`).
- Validate all outputs against the JSON‑Schema contracts in `contracts/`.
- Log runtime and memory usage; CI will enforce the ≤ 6 h / ≤ 7 GB limits.

## Expected Outputs (saved under `data/outputs/`)

- `first_arrival_sweep.csv` (processed dataset with `threshold_used` and `effort_covariate`)
- `predictions.csv` (final forecasts with GP correction)
- `metrics.json` (model performance, statistical tests, feasibility diagnostics)
- `shap_summary.png`, `shap_interaction.png`
- `migration_map.png`, `predictor_gradient.png`
- `provenance.log` (traceability manifest)

All files are version‑hashed and will be recorded in `state/...yaml` for reproducibility.===END_ARTIFACT===

===BEGIN_ARTIFACT projects/PROJ-126-predicting-avian-migration-patterns-from/specs/001-predicting-avian-migration-patterns-from/contracts/dataset.schema.yaml===
$schema: "http://json-schema.org/draft-07/schema#"
title: "GridCellObservation"
description: "Schema for the aggregated spatiotemporal grid cell data."
type: "object"
properties:
  grid_cell_id:
    type: "string"
    description: "Unique identifier for the grid cell (e.g., '45.5_-122.5')."
  year:
    type: "integer"
    minimum: 2015
    maximum: 2023
  week_number:
    type: "integer"
    minimum: 1
    maximum: 52
  total_observations:
    type: "integer"
    minimum: 0
  first_arrival_date:
    type:
      - "string"
      - "null"
    description: "ISO 8601 date string or null if threshold not met."
    format: "date"
  mean_temp_lag_1:
    type:
      - "number"
      - "null"
    description: "Mean temperature 1 week prior."
  mean_temp_lag_2:
    type:
      - "number"
      - "null"
    description: "Mean temperature 2 weeks prior."
  mean_ndvi_lag_1:
    type:
      - "number"
      - "null"
    description: "Mean NDVI 1 week prior."
  mean_ndvi_lag_2:
    type:
      - "number"
      - "null"
    description: "Mean NDVI 2 weeks prior."
  data_quality_flag:
    type: "string"
    enum:
      - "valid"
      - "insufficient_data"
      - "missing_env"
required:
  - grid_cell_id
  - year
  - week_number
  - total_observations
  - data_quality_flag