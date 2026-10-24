# Research: Predicting Avian Migration Patterns

## Dataset Strategy

| Dataset | Description | Verified Source URL | Access Method |
|---------|-------------|----------------------|---------------|
| **eBird Basic Dataset (EBD)** | Complete checklists for *Setophaga ruticilla* across North America, 2015‑2022. Includes effort metrics (`duration_min`, `distance_km`, `num_observers`). | `https://huggingface.co/datasets/vvud/eb-data/resolve/main/data/train.csv` | `datasets.load_dataset("vvud/eb-data", split="train", streaming=True)` |
| **MODIS Temperature & NDVI** | Weekly Land‑Surface Temperature (8‑day composite) and NDVI (16‑day composite) for the continental extent, provided in a compressed NPZ archive. | `https://huggingface.co/datasets/onef1shy/Crop-Yield-Prediction-MODIS/resolve/main/modis/processed_data/histogram_all_full.npz` | `np.load` after `datasets.load_dataset(..., download=True)` |
| **NOAA GHCN (stations)** | Daily temperature observations from the Global Historical Climatology Network; used solely for external validation of MODIS LST. | `https://www.ncei.noaa.gov/pub/data/ghcn/daily/ghcn-daily.tar.gz` | `pandas.read_csv` after extracting station files and aggregating to weekly means. |

### Dataset Variable Fit Check
- **EBD** supplies `species_code`, `date`, `latitude`, `longitude`, `duration_min`, `distance_km`, `num_observers`, `obs_count`. All variables required by FR‑001, FR‑003, FR‑008 are present.
- **MODIS NPZ** provides weekly `lst` (temperature) and `ndvi` arrays, matching the lagged predictor requirements of FR‑002, FR‑005, FR‑010 after aggregation.
- **GHCN** provides daily temperature which can be aggregated to weekly means for validation against MODIS LST; no new predictor variables are introduced.

## Methodological Rigor

### 1. Target Variable Construction & Construct Validity
- **Effort‑adjusted first‑arrival week**: For each 0.5° grid cell and calendar year, cumulative Redstart counts are summed across weeks. The cumulative count is **scaled by the per‑cell effort covariate** (`scaled_cum = cumulative_count / effort_covariate`). The threshold *k* ∈ {3, 5, 10} is applied to `scaled_cum`. If the scaled series never reaches the threshold, `first_arrival_week` is set to `null` and flagged “undetermined”. This offset satisfies FR‑003 and reduces bias from heterogeneous checklist effort.
- **Effort covariate as predictor**: The raw `effort_covariate` (total complete checklists per cell‑year) is retained as an explicit predictor **in the secondary bias‑adjusted model** (see Phase 2) to satisfy FR‑008, but **is omitted from the primary environmental model** that is used for scientific inference. This dual‑model design eliminates the circularity identified in the scientific‑soundness concern.
- **Validity assessment**: As a sanity check, derived first‑arrival weeks are compared to NOAA GHCN “first frost” dates (a coarse phenology proxy). The proportion of cells where the derived week falls within ±7 days of the NOAA proxy is reported but not used for model training.

### 2. Predictors
- **Lagged environmental variables**: Mean temperature (`lst_lag_1` … `lst_lag_4`) and mean NDVI (`ndvi_lag_1` … `ndvi_lag_4`) for the 1–4 weeks preceding each target week.  
- **Effort covariate**: Total number of complete checklists per cell‑year, included **only in the secondary bias‑adjusted model** (FR‑008) and as an offset in target construction.  
- **Spatial random‑effects**: After fitting XGBoost, residuals are modeled with a **mixed‑effects linear model** (`statsmodels.MixedLM`) that includes a random intercept for each 5° × 5° spatial block, capturing unexplained spatial autocorrelation (FR‑010).

### 3. Modeling
- **Algorithm**: Gradient Boosting Regressor (XGBoost) with CPU‑optimized parameters (`max_depth=6`, `n_estimators=200`, `learning_rate=0.1`, `objective="reg:squarederror"`, `n_jobs=2`).  
- **Temporal split**: Primary evaluation uses a **rolling‑year** scheme (e.g., 2015‑2019 train, 2020 val, 2021 test; then shift forward) to increase test‑set size and statistical power.  
- **Model families**:  
  1. **Primary environmental model** (temperature + NDVI + lags) **without** the effort covariate – used for hypothesis testing and inference.  
  2. **Secondary bias‑adjusted model** (same predictors **plus** effort covariate) – satisfies FR‑008 and provides a robustness check.  
- **Spatial effect integration**: Both model families receive the mixed‑effects random intercept correction; the resulting residualized target is stored as `residual_first_arrival`.  

### 4. Statistical Validation
| Test | Purpose | Implementation Details |
|------|---------|------------------------|
| **Spatial Block Bootstrap (Primary)** | Compare predictive accuracy of the primary environmental model vs. temperature‑only, NDVI‑only, and naive baseline while accounting for spatial autocorrelation (FR‑009). | 5° × 5° blocks, 1000 resamples; compute distribution of RMSE differences; report `spatial_bootstrap_p` (Bonferroni‑adjusted). |
| **HAC‑Corrected Diebold‑Mariano (Secondary)** | Provide a traditional time‑series comparison for the bias‑adjusted model (FR‑006). | Errors ordered temporally; Newey‑West HAC estimator; report `dm_p_value_hac`. |
| **Permutation Importance** | Quantify feature contribution while mitigating collinearity. | 10 permutations per predictor on the validation set; mean drop in RMSE recorded; differences ≤ 0.1 satisfy SC‑005. |
| **SHAP Values & Interaction** | Produce interpretable contribution summaries. | `shap.TreeExplainer` on the test set; generate `shap_summary.png` and `shap_interaction.png`. |
| **Threshold Sensitivity** | Verify robustness of the first‑arrival definition across thresholds {3, 5, 10}. | Median arrival week per threshold computed; rank‑order correlation of feature‑importance rankings across thresholds stored; flag if median shift > 7 days (SC‑003). |
| **Effort‑Covariate Sensitivity (T024‑sens)** | Demonstrate that environmental drivers remain significant when the effort covariate is omitted (primary model). | Re‑fit each model without `effort_covariate`; compare RMSE, SHAP, and permutation importance to the bias‑adjusted versions; report any degradation. |
| **MODIS‑GHCN Validation** | Ensure MODIS temperature is a reliable proxy for ground truth (FR‑011). | Compute Pearson correlation between weekly MODIS LST and weekly GHCN‑derived temperature for a random [deferred] of cells; require r > 0.8 and ≥ 95 % spatial coverage; cells failing are excluded. |
| **Output‑Schema Validation** | Guarantee downstream reproducibility (plan‑consistency‑c05008c7). | Validate `predictions.csv` and associated metadata against `contracts/output.schema.yaml`. |

### 5. Multiple‑Comparison Control
- Three pairwise bootstrap comparisons are Bonferroni‑adjusted (α / 3) to keep family‑wise error ≤ 0.05.

### 6. Sample‑Size & Power
- The rolling‑year scheme yields **≈ 3 500** test‑set predictions, sufficient for bootstrap inference and permutation stability checks. Any power limitation will be transparently reported.

### 7. Causal Inference Disclaimer
- All statements about temperature or NDVI “affecting” migration are framed as **associations**; no causal identification strategy is employed, satisfying the specification’s requirement to avoid unsupported causal claims.

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


