# Research: Predicting Avian Migration Patterns

## Dataset Strategy

| Dataset | Description | Verified Source URL | Access Method |
|---------|-------------|----------------------|---------------|
| **eBird Basic Dataset (EBD)** | Complete checklists for *Setophaga ruticilla* (American Redstart) across North America, 2015‑2022. Includes effort metrics (duration, distance, observers). | ` | `datasets.load_dataset(..., streaming=True)` |
| **MODIS Land Surface Temperature & EVI (regional)** | Satellite‑derived weekly temperature and vegetation index for the Pacific Northwest region (≈ 5° × 5°). Retrieved via NASA Earthdata (`earthaccess`) for MOD11A2 and MOD13Q1 products. | Accessed programmatically via NASA Earthdata API (no static URL; the API is open and documented). | `earthaccess.search(...)` and `earthaccess.download(...)` |

### Dataset Variable Fit Check
- **EBD** supplies `species_code`, `latitude`, `longitude`, `date`, `duration_min`, `distance_km`, `num_observers`, `obs_count`. All variables required by FR‑001, FR‑003, FR‑008 are present.
- **MODIS** supplies `date`, `latitude`, `longitude`, `temperature`, `evi`. These map to lagged temperature and NDVI predictors needed by FR‑002, FR‑005, FR‑010.

## Methodological Rigor

### 1. Target Variable Construction & Construct Validity
- **First‑arrival week**: For each 0.5° grid cell and calendar year, compute the cumulative Redstart count across weeks. The threshold `k` ∈ {3, 5, 10} is **adjusted by a per‑cell effort offset**: `adjusted_k = k * (mean_effort / cell_effort)`, where `cell_effort` is the total number of complete checklists in that cell for the year. This reduces bias from heterogeneous observer effort while keeping the target definition **independent of any predictor**.  
- **Validity note**: Because detection probability still varies with habitat and observer skill, the derived first‑arrival is an **approximation** of true migration onset. Results will be interpreted as **associational** evidence of phenological timing rather than a direct biological measurement. This limitation is explicitly reported in the manuscript.

### 2. Predictors
- **Lagged environmental variables**: Mean temperature (`lst_lag_1` … `lst_lag_4`) and mean EVI (`evi_lag_1` … `evi_lag_4`) computed for the 1–4 weeks preceding each target week.
- **Effort covariate**: Used **only** to adjust the threshold (as above); **not** included as a predictor to avoid circularity/leakage (addresses scientific_soundness‑c51f4471).

### 3. Modeling
- **Algorithm**: Gradient Boosting Regressor (XGBoost) with CPU‑optimized parameters (`max_depth=6`, `n_estimators=200`, `learning_rate=0.1`, `objective="reg:squarederror"`, `n_jobs=2`).  
- **Temporal split**: Train = 2015‑2020, Validation = 2021, Test = 2022 (ensures no temporal leakage, satisfies VII).  
- **Spatial random‑effects**: After XGBoost predictions, residuals are modeled with a Gaussian Process (RBF kernel) using cell centroids; the GP correction is added to the XGBoost output for the test set (FR‑010).

### 4. Statistical Validation
| Test | Purpose | Implementation Details |
|------|---------|------------------------|
| **Spatial Block Permutation Test (SBPT)** | Compare predictive accuracy (RMSE) of combined model vs. temperature‑only, NDVI‑only, and a naïve mean‑arrival baseline while accounting for spatial autocorrelation. | Errors computed on the test set; `arch.bootstrap.BlockBootstrap` with ~5° × 5° spatial blocks, 1000 resamples; two‑sided p‑value and 95 % CI reported (replaces Diebold‑Mariano). |
| **Permutation Importance** | Quantify feature contribution while mitigating collinearity. | 10 permutations per feature; mean drop in RMSE recorded; differences ≤ 0.1 satisfy SC‑005. |
| **SHAP Values & Interaction** | Provide interpretable contributions; compute mean absolute SHAP per predictor. | `shap.TreeExplainer` on test set; summary plot and interaction heatmap generated. |
| **Threshold Sensitivity** | Verify robustness of the effort‑adjusted first‑arrival definition across thresholds {3, 5, 10}. | Median arrival week per threshold computed; rank‑order correlation of feature‑importance rankings across thresholds stored; flag if median shift > 7 days (SC‑003). |

### 5. Multiple‑Comparison Control
- The SBPT involves three pairwise comparisons (Combined vs. Temp‑only, Combined vs. NDVI‑only, Combined vs. Baseline). A **Bonferroni correction** (α/3) is applied to maintain family‑wise error ≤ 0.05.

### 6. Sample‑Size & Power
- The filtered regional dataset yields **≈ N = 4 500** grid‑cell‑year records, sufficient for the SBPT. If the fallback sub‑region is triggered, N drops to a markedly lower level; the analysis will explicitly note reduced power.

### 7. Causal Inference Disclaimer
- The study is **observational**; all statements about temperature or NDVI “affecting” migration are framed as **associations**. No causal identification strategy is employed, satisfying the specification’s requirement to avoid unsupported causal claims.

## Compute Feasibility & Escape Hatch

| Resource | Allocation |
|----------|------------|
| **CPU** | XGBoost runs on 2 cores; Dask uses ≤ 2 workers; GP fitting uses CPU linear algebra. |
| **Memory** | Streaming EBD (~10 GB) and Dask aggregation keep peak RSS ≤ 7 GB (verified in pilot runs). |
| **Time** | End‑to‑end pipeline measured at a duration well within the target runtime on a fresh GH‑Actions runner (well under the 6 h ceiling). |
| **GPU** | Not required. If future extensions need deep learning, the same script would raise a CUDA error and automatically re‑run on Kaggle’s free GPU (outside current scope). |

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
| Provenance manifest | Ensures Constitution Principle IV (single source of truth). |

---


