# Research: Predicting Species Distribution Shifts Using Historical Occurrence Records and Climate Data

## 1. Problem Definition & Scope
We evaluate whether Species Distribution Models (SDMs) trained on historic North American bird occurrences (1970‑2000) can accurately predict suitability under a mid‑century climate scenario (2050, SSP2‑4.5) **and** whether those predictions remain calibrated when compared to recent observations (2005‑2020). The central hypothesis is that historic models will show a measurable decline in calibrated predictive performance when projected onto future climate, indicating niche non‑stationarity. All findings are explicitly **associational** (FR‑008) and no causal claims are made.

### Scope
- **Taxa**: 10 common North American bird species (selected to fit the 6‑hour CI budget).  
- **Temporal windows**: Historical (1970‑2000), Recent (2005‑2020) for validation, Future (2050, SSP2‑4.5) for projection.  
- **Data sources**: GBIF/eBird API (occurrences), WorldClim v2.1 (historical climate), WorldClim CMIP6 (future climate).  
- **Constraints**: CPU‑only execution on GitHub Actions free tier; total runtime ≤ 6 h; RAM ≤ 7 GB.

## 2. Dataset Strategy
Only open, programmatically accessible datasets are used. When a required dataset lacks a verified URL, this is noted explicitly.

| Dataset | Verified URL(s) | Role | Verification Status |
|---------|----------------|------|----------------------|
| Historical Occurrences (1970‑2000) | *None* (GBIF/eBird API) | Training occurrences | No verified source – open API used (see Verified Accuracy note). |
| Recent Occurrences (2005‑2020) | *None* (GBIF/eBird API) | Out‑of‑time validation | No verified source – open API used. |
| Historical Climate (WorldClim v2.1) | *None* (WorldClim download page) | Predictor variables for training | No verified source – publicly downloadable GeoTIFFs. |
| Future Climate (2050, SSP2‑4.5, WorldClim CMIP6) | *None* (WorldClim download page) | Predictor variables for projection | No verified source – publicly downloadable. |
| MaxEnt benchmark results (optional) | https://huggingface.co/datasets/P2SAMAPA/p2-maxent-irl-results/resolve/main/maxent_irl_2026-08-06.json, https://huggingface.co/datasets/maxentius42/dataset/resolve/main/dataset.csv | Reference for MaxEnt‑style surrogate implementation (not used for primary analysis) | Verified URLs (cited only for methodological reference). |

All raster files are streamed tile‑by‑tile to keep memory usage low. Downloads are recorded in `data/manifest.json` with SHA‑256 checksums; mismatches abort the pipeline (fulfills T010).

## 3. Methodology

### 3.1 Data Preprocessing (FR‑001, FR‑002, FR‑003, FR‑042, FR‑009)
1. **Download** raw occurrence CSVs and climate GeoTIFFs (`download.py`).  
2. **Breeding‑season filter** using species‑specific month ranges defined in `config.py`.  
3. **Duplicate removal** (exact lat/long matches).  
4. **Bias‑layer creation**: generate a kernel‑density raster of observation density; sample background points proportionally to this raster to mitigate heterogeneous detection effort.  
5. **Spatial thinning**:  
   - Compute nearest‑neighbor distances; set `min_distance` to the 95th percentile.  
   - If fewer than three points, fallback to a fixed 10 km threshold.  
   - Apply `utils.spatial.thin_points`.  
6. **Collinearity mitigation**: calculate Variance Inflation Factors (VIF) for the 19 Bioclim variables; drop any with VIF > 10. For the MaxEnt‑style surrogate, optionally apply PCA and retain the first five components.  
7. **Climate extraction**: Sample the selected climate variables at each occurrence using `rasterio.sample`. Missing raster values are imputed via nearest‑neighbor; points still missing are excluded.  
8. **Data‑sufficiency & Power‑Analysis** (FR‑006, FR‑011):  
   - Count records per species after thinning.  
   - Compute statistical power to detect a **minimum AUC difference of 0.05** between historical and future predictions using `statsmodels.stats.power.NormalIndPower`.  
   - Flag species with `<100` records **or** power < 0.8 as `INSUFFICIENT_DATA`.  
   - Log counts and power values in `metrics/data_sufficiency.json` (schema `data_sufficiency.schema.yaml`).  

All preprocessing steps write structured logs to `logs/preprocess.log` via `utils.logging_config.py`. A summary of before/after counts is stored in `logs/preprocess_counts.yaml` and validated against `contracts/log_counts.schema.yaml`.

### 3.2 Model Training (FR‑004, FR‑007, FR‑008)
- **Algorithms**:  
  - Random Forest (`sklearn.ensemble.RandomForestClassifier`, `n_estimators=500`).  
  - Bioclim (range‑envelope method).  
  - MaxEnt‑style surrogate (logistic regression on VIF‑filtered or PCA‑reduced predictors).  
- **Spatial block cross‑validation**: Divide the study area into a 5 × 5 grid (K = 5). Rotate held‑out block for each fold to ensure spatial independence.  
- **CPU‑only enforcement**: `utils/gpu_check.py` aborts with clear log if CUDA is detected (FR‑004).  
- **Model‑artifact validation**: each saved model (`*.pkl`) is checked against `contracts/model_artifact.schema.yaml`.

### 3.3 Evaluation & Projection (FR‑005, FR‑009, FR‑010, SC‑001, SC‑003)
1. **Calibration check** on recent test set: compute Brier score and calibration curve; only models with Brier < 0.2 proceed to projection.  
2. **Historical validation**: compute AUC and TSS on recent occurrences (2005‑2020) using contemporary climate.  
3. **Future projection**: predict suitability at the same recent occurrence locations under the 2050 climate.  
4. **Environmental Similarity (MOP/MESS)**: assess extrapolation risk by quantifying the proportion of future pixels that fall within the analogous climate space defined by the historical training data.  
5. **Niche‑stability metric**: combine calibrated AUC change with the MOP proportion to produce a composite stability score (higher values indicate stable niches).  
6. **Threshold sweep** (FR‑005): evaluate thresholds 0.49, 0.55, 0.60 (baseline 0.5 ± {0.01, 0.10}); record false‑positive/negative rates.  
7. **Hierarchical bootstrap** (FR‑010):  
   - Level 1: Resample species with replacement (10 species).  
   - Level 2: Within each species, resample spatial blocks.  
   - Perform **2 000** iterations on the composite stability score.  
8. **Multiple‑comparison correction**: Apply Benjamini‑Hochberg (FDR = 0.05) across the three threshold tests (FR‑005).  
9. **Report generation**: Store all metrics in `metrics/model_performance.json` (schema `model_metrics.schema.yaml`) and a summary CSV in `results/summary_table.csv`. Append the disclaimer `"Findings are associational and assume niche stability"` to every report file (FR‑008).  

### 3.4 Statistical Rigor
- **Multiple‑comparison**: Benjamini‑Hochberg (FDR = 0.05).  
- **Power analysis**: Detect ΔAUC = 0.05 with ≥ 0.8 power (effect size = 0.05, source: statistical power analysis).  
- **Collinearity**: VIF screening removes highly collinear predictors; PCA used for MaxEnt surrogate.  
- **Calibration**: Brier score threshold ensures models are not severely mis‑calibrated before projection.  
- **Associational framing**: Enforced by FR‑008 disclaimer.  

## 4. Risks & Mitigations
| Risk | Mitigation |
|------|------------|
| GBIF API rate limits | Exponential back‑off, caching raw responses in `data/raw/`. |
| Missing raster tiles | Nearest‑neighbor imputation; log number of excluded points. |
| Insufficient records | Species flagged and excluded; report limitation clearly noted. |
| Runtime > 6 h | Limit to 10 species, 2 000 bootstrap iterations, stream rasters, early abort on checksum mismatch. |
| Memory overflow | Process rasters tile‑by‑tile; VIF screening reduces predictor count. |
| Unexpected GPU presence | `gpu_check.py` aborts early with clear log. |
| Bias in occurrence data | Bias‑layer creation and bias‑corrected background sampling (FR‑042). |
| Model misspecification before projection | Calibration check (Brier < 0.2) before any future projection. |
| Extrapolation beyond observed climate | MOP/MESS analysis to quantify analog climate space. |

## 5. Decision Rationale
- **CPU‑first**: Free‑tier CI provides only CPUs; all chosen libraries run efficiently on CPU.  
- **Spatial block CV**: Prevents inflated AUC from spatial autocorrelation, satisfying ecological validity.  
- **Bias correction**: Addresses heterogeneous detection effort, a known source of sampling bias.  
- **Calibration before projection**: Guarantees that only well‑behaved models are used for future scenarios.  
- **Environmental similarity**: Provides an independent assessment of niche stability that does not rely solely on model‑generated scores.  
- **Reduced workload**: Guarantees completion within the 6‑hour CI budget while preserving scientific integrity.  

---

