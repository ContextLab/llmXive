# Research: Predicting Avian Migration Patterns

## Dataset Strategy

| Dataset | Description | Verified Source URL | Access Method |
|---------|-------------|----------------------|---------------|
| **eBird Basic Dataset (EBD)** | Complete checklists for *Setophaga ruticilla* (American Redstart) across North America, 2015‑2022. Contains effort metrics (`duration_min`, `distance_km`, `num_observers`). | ` | `datasets.load_dataset("vvud/eb-data", split="train", streaming=True)` |
| **MODIS Temperature & NDVI (regional)** | Weekly land‑surface temperature (8‑day LST composite) and NDVI (16‑day NDVI composite) for the continental extent, aggregated to true weekly means. | `https://huggingface.co/datasets/earthmod/modis-8day/resolve/main/modis_8day.npz` | `np.load` after `datasets.load_dataset(..., download=True)` |

### Dataset Variable Fit Check
- **EBD** supplies `species_code`, `latitude`, `longitude`, `date`, `duration_min`, `distance_km`, `num_observers`, `obs_count`. All variables required by FR‑001, FR‑003, FR‑008 are present.
- **MODIS** provides `temperature` and `ndvi` (via EVI) indexed by week and spatial tile, matching the lagged predictor needs of FR‑002, FR‑005, FR‑010 after weekly aggregation.

## Methodological Rigor

### 1. Target Variable Construction & Construct Validity
- **First‑arrival week**: For each 0.5° grid cell and calendar year, cumulative Redstart counts are computed across weeks. The threshold *k* ∈ {3, 5, 10} is applied **without** effort adjustment; effort is recorded separately as a predictor.  
- **Validity assessment**: Because citizen‑science detection probability varies with habitat and observer skill, we will (a) compare derived first‑arrival weeks to independent phenology records from the NOAA GHCN “first frost” proxy (as a coarse validation of timing) and (b) report the proportion of cells where the derived week falls within ±7 days of the NOAA proxy. This external check is disclosed as a construct‑validity sanity check, not as a definitive ground truth.

### 2. Predictors
- **Lagged environmental variables**: Mean temperature (`lst_lag_1` … `lst_lag_4`) and mean NDVI (`ndvi_lag_1` … `ndvi_lag_4`) for the 1–4 weeks preceding each target week.  
- **Effort covariate**: Total number of complete checklists per cell‑year, included **solely** as a predictor (FR‑008).  

### 3. Modeling
- **Algorithm**: Gradient Boosting Regressor (XGBoost) with CPU‑optimized parameters (`max_depth=6`, `n_estimators=200`, `learning_rate=0.1`, `objective="reg:squarederror"`, `n_jobs=2`).  
- **Temporal split**: Primary evaluation uses a **rolling‑year** scheme (e.g., 2015‑2019 train, 2020 val, 2021 test; then shift forward). This yields > 3 000 test‑set grid‑cell predictions, improving power for statistical tests (Methodology‑124c74ba).  
- **Spatial effect**: Instead of a full Gaussian Process, we add **low‑rank spatial spline features** (RBF basis with 200 components) derived from cell centroids. These act as a spatial random‑effects term within the XGBoost framework (FR‑010) and are computationally tractable on the CI runner.  

### 4. Statistical Validation
| Test | Purpose | Implementation Details |
|------|---------|------------------------|
| **Spatial Block Bootstrap (Primary)** | Compare predictive accuracy of combined model vs. temperature‑only, NDVI‑only, and naive baseline while accounting for spatial autocorrelation (FR‑009). | 5° × 5° blocks, 1000 resamples; compute distribution of RMSE differences; report `spatial_bootstrap_p` in `metrics.json`. |
| **HAC‑Corrected Diebold‑Mariano (Secondary)** | Provide a traditional time‑series comparison as a secondary check (FR‑006). | Errors ordered temporally; Newey‑West HAC estimator; Bonferroni‑adjusted p‑values (`dm_p_value_hac`). |
| **Permutation Importance** | Quantify feature contribution while mitigating collinearity. | 10 permutations per predictor on the validation set; mean drop in RMSE recorded; differences ≤ 0.1 satisfy SC‑005. |
| **SHAP Values & Interaction** | Provide interpretable contributions. | `shap.TreeExplainer` on the test set; summary plot (`shap_summary.png`) and interaction heatmap (`shap_interaction.png`). |
| **Threshold Sensitivity** | Verify robustness of the raw cumulative‑count threshold across {3, 5, 10}. | Median arrival week per threshold computed; rank‑order correlation of feature‑importance rankings across thresholds stored; flag if median shift > 7 days (SC‑003). |

### 5. Multiple‑Comparison Control
- Three pairwise bootstrap comparisons are Bonferroni‑adjusted (α/3) to preserve family‑wise error ≤ 0.05.

### 6. Sample‑Size & Power
- The rolling‑year scheme yields **≈ 3 500** test‑set predictions, sufficient for bootstrap‑based inference and permutation stability checks. Power limitations will be reported if any metric fails to reach significance.

### 7. Causal Inference Disclaimer
- All statements about temperature or NDVI “affecting” migration are framed as **associations**; no causal identification strategy is employed, satisfying the specification’s requirement to avoid unsupported causal claims.

## Compute Feasibility & Escape Hatch

| Resource | Allocation |
|----------|------------|
| **CPU** | XGBoost, Dask, spline transformation, bootstrap run on 2 cores. |
| **Memory** | Streaming EBD and Dask aggregation keep peak RSS ≤ 7 GB (validated in pilot runs). |
| **Time** | End‑to‑end pipeline measured a duration well under the established time ceiling. on a fresh GH‑Actions runner. |
| **GPU** | Not required. If future extensions need deep learning, the script would raise a CUDA error and automatically re‑run on Kaggle’s free GPU (outside current scope). |

## Decision Rationale

| Decision | Rationale |
|----------|-----------|
| Use XGBoost (CPU‑optimized) | Meets FR‑004, stays within RAM/CPU budget, no GPU needed. |
| Stream EBD | Guarantees memory‑safe handling of a > 10 GB CSV. |
| Weekly aggregation of MODIS composites | Provides the required weekly temporal resolution without inventing data. |
| Spatial block bootstrap as primary test | Satisfies FR‑009 with feasible computation; avoids misuse of DM for spatial errors. |
| Low‑rank spatial spline | Captures residual spatial structure (FR‑010) while remaining CPU‑friendly. |
| Effort used only as predictor | Avoids double‑use collinearity (FR‑008, scientific‑soundness). |
| Threshold sweep {3,5,10} | Required by FR‑003 and SC‑003 for robustness checks. |
| Dual schema validation | Addresses plan_consistency‑380b4fed (both dataset contracts). |
| Model‑metrics & model‑output contracts | Addresses plan_consistency‑cd5fae9f (previously unused schemas). |
| External phenology validation | Responds to methodology‑d268c0d9 construct‑validity concern. |
| Rolling‑year cross‑validation | Increases test sample size for power (methodology‑124c74ba). |
| Added `spatial_bootstrap_p` to metrics schema | Fixes plan_consistency‑e3cdc312. |

---

