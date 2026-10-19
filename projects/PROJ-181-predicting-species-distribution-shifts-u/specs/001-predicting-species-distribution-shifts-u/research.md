# Research: Predicting Species Distribution Shifts Using Historical Occurrence Records and Climate Data

## 1. Problem Definition & Scope
We evaluate whether Species Distribution Models (SDMs) trained on historic North American bird occurrences (1970‑2000) can accurately predict suitability under a mid‑century climate scenario (2050, SSP2‑4.5) and how those predictions compare to recent observations (2005‑2020). The central hypothesis is that historic models will show a measurable decline in predictive performance when projected onto future climate, indicating niche non‑stationarity. All findings are explicitly **associational** (FR‑008) and no causal claims are made.

### Scope
- **Taxa**: 30 common North American bird species (selected to fit the 6‑hour CI budget).  
- **Temporal windows**: Historical (1970‑2000), Recent (2005‑2020) for validation, Future (2050, SSP2‑4.5) for projection.  
- **Data sources**: GBIF/eBird API (occurrences), WorldClim v2.1 (historical climate), WorldClim CMIP6 (future climate).  
- **Constraints**: CPU‑only execution on GitHub Actions free tier; total runtime ≤ 6 h; RAM ≤ 7 GB.

## 2. Dataset Strategy
Only open, programmatically accessible datasets are used. When a required dataset lacks a verified URL, this is noted explicitly.

| Dataset | Verified URL(s) | Role | Verification Status |
|---------|----------------|------|----------------------|
| Historical Occurrences (1970‑2000) | *None* (GBIF/eBird API) | Training occurrences | No verified source – open API used (see Verified Facts). |
| Recent Occurrences (2005‑2020) | *None* (GBIF/eBird API) | Out‑of‑time validation | No verified source – open API used. |
| Historical Climate (WorldClim v2.1) | *None* (WorldClim download page) | Predictor variables for training | No verified source – publicly downloadable GeoTIFFs. |
| Future Climate (2050, SSP2‑4.5, WorldClim CMIP6) | *None* (WorldClim download page) | Predictor variables for projection | No verified source – publicly downloadable. |
| MaxEnt benchmark results (optional) | https://huggingface.co/datasets/P2SAMAPA/p2-maxent-irl-results/resolve/main/maxent_irl_2026-08-06.json, https://huggingface.co/datasets/maxentius42/dataset/resolve/main/dataset.csv | Reference for MaxEnt‑style surrogate implementation (not used for primary analysis) | Verified URLs (cited only for methodological reference). |

All raster files are streamed tile‑by‑tile to keep memory usage low. Downloads are recorded in `data/manifest.json` with SHA‑256 checksums.

## 3. Methodology

### 3.1 Data Preprocessing (FR‑001, FR‑003, FR‑014)
1. **Download** raw occurrence CSVs and climate GeoTIFFs (`download.py`).  
2. **Breeding‑season filter** using species‑specific month ranges defined in `config.py`.  
3. **Duplicate removal** (exact lat/long matches).  
4. **Spatial thinning**:  
   - Compute nearest‑neighbor distances; set `min_distance` to the 95th percentile.  
   - If fewer than three points, fallback to a fixed 10 km threshold.  
   - Apply `utils.spatial.thin_points`.  
5. **Climate extraction**: Sample 19 Bioclim variables at each occurrence using `rasterio.sample`. Missing raster values are imputed via nearest‑neighbor; points still missing are excluded.  
6. **Data‑sufficiency check** (FR‑006, FR‑011):  
   - Count records per species after thinning.  
   - Compute statistical power for detecting Cohen’s h = 0.50 (source: Wikipedia) with `statsmodels`.  
   - Flag species with `<100` records **or** power < 0.8 as `INSUFFICIENT_DATA`.  
   - Log counts and power values in `metrics/data_sufficiency.json` (schema `data_sufficiency.schema.yaml`).  

### 3.2 Model Training (FR‑004, FR‑007)
- **Algorithms**:  
  - Random Forest (`sklearn.ensemble.RandomForestClassifier`, `n_estimators=500`).  
  - Bioclim (range‑envelope method).  
  - MaxEnt‑style surrogate (logistic regression with L2 regularization).  
- **Spatial block cross‑validation**: Divide the study area into a 5 × 5 grid (K = 5). Rotate held‑out block for each fold to ensure spatial independence.  
- **CPU‑only enforcement**: `utils.gpu_check.py` aborts if CUDA is detected (FR‑004).  

### 3.3 Evaluation & Projection (FR‑005, FR‑009, FR‑010)
1. **Historical validation**: Compute AUC and TSS on recent (2005‑2020) occurrences using contemporary climate.  
2. **Future projection**: Predict suitability at the same recent occurrence locations under the 2050 climate.  
3. **Niche‑stability metric**: `delta_suitability = mean(suitability_2050) – mean(suitability_2005‑2020)`.  
4. **Threshold sweep** (FR‑005): Evaluate thresholds 0.49, 0.51, 0.55, 0.60 (baseline 0.5 ± {0.01, 0.05, 0.10}); record false‑positive/negative rates.  
5. **Hierarchical bootstrap** (FR‑010):  
   - Level 1: Resample species with replacement.  
   - Level 2: Within each species, resample spatial blocks.  
   - Perform 10 000 iterations on `delta_suitability`.  
6. **Multiple‑comparison correction**: Apply Benjamini‑Hochberg (FDR = 0.05) across the four threshold tests (FR‑005).  
7. **Report generation**: Store all metrics in `metrics/model_performance.json` (schema `model_metrics.schema.yaml`) and a summary CSV in `results/summary_table.csv`. Append the disclaimer `"Findings are associational and assume niche stability"` to every report file (FR‑008).  

### 3.4 Statistical Rigor
- **Multiple‑comparison**: Benjamini‑Hochberg (FDR = 0.05).  
- **Power analysis**: Conducted before training (FR‑011) using `statsmodels.stats.power.NormalIndPower` for Cohen’s h = 0.50 (source: Wikipedia).  
- **Collinearity**: Acknowledged high correlation among Bioclim variables; Random Forest handles it implicitly, and we do not claim independent effects.  
- **Associational framing**: Enforced by FR‑008 disclaimer.  

## 4. Risks & Mitigations
| Risk | Mitigation |
|------|------------|
| GBIF API rate limits | Exponential back‑off, caching raw responses in `data/raw/`. |
| Missing raster tiles | Nearest‑neighbor imputation; log number of excluded points. |
| Insufficient records | Species flagged and excluded; report limitation clearly noted. |
| Runtime > 6 h | Limit species list, stream rasters, reduce bootstrap iterations to 5 000 if needed (still > 1 000). |
| Memory overflow | Process species sequentially; never load all rasters simultaneously. |
| Unexpected GPU presence | `gpu_check.py` aborts early with clear log. |

## 5. Decision Rationale
- **CPU‑first**: Free‑tier CI provides only CPUs; all chosen libraries run efficiently on CPU.  
- **Spatial block CV**: Prevents inflated AUC from spatial autocorrelation, satisfying ecological validity.  
- **Hierarchical bootstrap**: Captures dependence across species and spatial blocks, fulfilling FR‑010.  
- **Delta suitability**: Provides a defensible niche‑stability metric without requiring future occurrence data.  
- **Open data only**: Guarantees reproducibility on CI; no gated datasets are used.  

---
