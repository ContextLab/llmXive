# Research: Predicting Species Distribution Shifts Using Historical Occurrence Records and Climate Data

## 1. Problem Definition & Scope
We assess whether Species Distribution Models (SDMs) trained on historic North‑American bird occurrences (1970‑2000) can accurately predict suitability under a mid‑century climate scenario (2050, SSP2‑4.5) **and** remain calibrated when compared to recent observations (2005‑2020). The central hypothesis is that historic models will show a measurable decline in calibrated predictive performance when projected onto future climate, indicating niche non‑stationarity. All findings are explicitly **associational** (FR‑008) and no causal claims are made.

### Scope
- **Taxa**: 8 common North‑American bird species (selected to fit the CI compute budget).  
- **Temporal windows**: Historical (1970‑2000), Recent (2005‑2020) for validation, Future (2050 SSP2‑4.5) for projection.  
- **Data sources**: GBIF/eBird API (occurrences), WorldClim v2.1 (historical climate), WorldClim CMIP6 (future climate).  
- **Constraints**: CPU‑only execution on free‑tier CI; total runtime ≤ 6 h; RAM ≤ 7 GB.

## 2. Dataset Strategy
Only open, programmatically accessible datasets are used. When a required dataset lacks a verified URL, this is noted explicitly.

| Dataset | Verified URL(s) | Role | Verification Status |
|---------|----------------|------|----------------------|
| Historical Occurrences (1970‑2000) | *None* (GBIF/eBird API) | Training data | Verified via Reference‑Validator (recorded in `data/manifest.json`). |
| Recent Occurrences (2005‑2020) | *None* (GBIF/eBird API) | Out‑of‑time validation | Verified via Reference‑Validator (recorded in `data/manifest.json`). |
| Historical Climate (WorldClim v2.1) | *None* (WorldClim download page) | Predictors for training | Verified via Reference‑Validator (recorded in `data/manifest.json`). |
| Future Climate (2050 SSP2‑4.5, WorldClim CMIP6) | *None* (WorldClim download page) | Predictors for projection | Verified via Reference‑Validator (recorded in `data/manifest.json`). |
| MaxEnt benchmark (reference only) | https://huggingface.co/datasets/P2SAMAPA/p2-maxent-irl-results/resolve/main/maxent_irl_2026-08-06.json, https://huggingface.co/datasets/maxentius42/dataset/resolve/main/dataset.csv | Methodological reference (not primary analysis) | Verified URLs. |

All raster files are streamed tile‑by‑tile; downloads are recorded in `data/manifest.json` with SHA‑256 checksums; mismatches abort execution (fulfills T010).

## 3. Methodology

### 3.1 Data Preprocessing (FR‑001, FR‑002, FR‑003, FR‑014, FR‑009, FR‑006, FR‑011, SC‑004)
1. **Download** raw occurrence CSVs and climate GeoTIFFs (`download.py`).  
2. **Breeding‑season filter** using species‑specific month ranges defined in `config.py`.  
3. **Duplicate removal** (identical lat/long).  
4. **Spatial thinning**: compute nearest‑neighbor distances; set `min_distance` to the 95th percentile (dynamic) or fallback to 10 km (FR‑014). Apply `utils.spatial.thin_points`.  
5. **Bias‑layer creation**: generate a kernel‑density raster of observation effort; this raster is later used for bias‑corrected background sampling **both during training and when evaluating on the recent test set** (addresses FR‑006 consistency).  
6. **Collinearity mitigation**: calculate VIF for the 19 Bioclim variables; drop any with VIF > 10 (FR‑009).  
7. **Climate extraction**: sample rasters at occurrence points using `rasterio.sample`; nearest‑neighbor imputation for missing cells.  
8. **Data‑sufficiency & Power analysis**:  
   - Count records per species after thinning.  
   - Perform a **simulation‑based power analysis**: bootstrap AUC values **500 times** per species, compute empirical power to detect a ΔAUC = 0.05 (Cohen’s h = 0.50, α = 0.05).  
   - Flag species with `<100` records **or** power < 0.8 as `INSUFFICIENT_DATA`. Results stored in `metrics/data_sufficiency.json`.  
9. **Data‑acquisition completeness (SC‑004)**: compute (a) proportion of species with ≥100 thinned records and (b) proportion of records with non‑null climate values; write summary to `metrics/data_acquisition_completeness.json`.  
All steps log before/after counts to `logs/preprocess_counts.yaml` (validated against `contracts/log_counts.schema.yaml`) and write a structured `logs/preprocess.log`.

### 3.2 Model Training (FR‑004, FR‑007, FR‑008)
- **Algorithms**: Random Forest (`sklearn.ensemble.RandomForestClassifier`, `n_estimators=500`), Bioclim (range‑envelope), MaxEnt‑style surrogate (logistic regression on VIF‑filtered predictors).  
- **Spatial block CV**: 5‑fold, 5 × 5 equidistant grid, rotating held‑out block (FR‑007).  
- **CPU‑only enforcement**: `utils/gpu_check.py` aborts if CUDA is detected (FR‑004).  
- **Model artifacts** saved as pickle files under `models/` and validated against `contracts/model_artifact.schema.yaml`.  

### 3.3 Evaluation & Projection (FR‑005, FR‑009, FR‑010, SC‑001, SC‑003)
1. **Bias‑corrected evaluation** on recent test set: background points are sampled according to the same bias‑layer used during training, ensuring comparable sampling effort.  
2. **Calibration check**: compute Brier score; only models with Brier < 0.2 proceed to projection.  
3. **Historical validation**: compute AUC and TSS on recent records (2005‑2020).  
4. **Future projection**: predict suitability under 2050 climate, compute **MOP (Mobility‑Oriented Parity) similarity** between historical and future climate spaces. Non‑analogous pixels are masked out.  
5. **ΔAUC after MOP masking**: calculate calibrated AUC decline only on analog climate pixels; store as `delta_auc`.  
6. **Composite niche‑stability metric**: weighted combination of calibrated ΔAUC and MOP proportion, providing a measure that separates extrapolation risk from true niche change.  
7. **Threshold sweep** (FR‑005): evaluate thresholds 0.40, 0.45, 0.50, 0.55, 0.60; record false‑positive/negative rates.  
8. **Hierarchical bootstrap** (FR‑010):  
   - Level 1: Resample species with replacement (8 species).  
   - Level 2: Within each species, resample spatial blocks.  
   - Perform **500 iterations** (fits CI budget).  
9. **Multiple‑comparison correction**: Benjamini‑Hochberg (FDR = 0.05) across the five threshold tests (FR‑005).  
10. **Outputs**: `metrics/model_performance.json`, `results/summary_table.csv`, `logs/evaluate.log`.  

All metrics conform to `contracts/model_metrics.schema.yaml`.

### 3.4 Statistical Rigor
- **Multiple‑comparison**: Benjamini‑Hochberg (FDR = 0.05).  
- **Power analysis**: Simulation‑based bootstrap of AUC distributions to detect ΔAUC = 0.05 with ≥ 0.8 power (effect size = 0.50, source: Cohen’s h).  
- **Collinearity**: VIF > 10 variables removed.  
- **Calibration**: Brier < 0.2 required before projection.  
- **Associational framing**: Enforced by appending the disclaimer `"Findings are associational and assume niche stability"` to all report files (FR‑008).  

## 4. Risks & Mitigations
| Risk | Mitigation |
|------|------------|
| GBIF API rate limits | Exponential back‑off, caching raw responses in `data/raw/`. |
| Missing raster tiles | Nearest‑neighbor imputation; log excluded points. |
| Insufficient records per species | Species flagged as `INSUFFICIENT_DATA` (FR‑006); excluded from aggregation; report limitation. |
| Runtime > 6 h | Limit to 8 species, 500 bootstrap iterations, stream rasters, early abort on checksum mismatch. |
| Memory overflow | Tile‑by‑tile raster processing; VIF screening reduces predictors. |
| Unexpected GPU presence | `gpu_check.py` aborts with clear log. |
| Sampling bias | **Bias‑layer applied consistently to both training and recent evaluation** (addressing FR‑006). |
| Model mis‑calibration | Calibration check (Brier < 0.2) before any projection. |
| Extrapolation beyond observed climate | **MOP‑only analysis** quantifies climate novelty separately from ΔAUC. |
| Hierarchical bootstrap cost | Reduced to 500 iterations; species limited to 8. |

## 5. Decision Rationale
- **CPU‑first**: Free‑tier CI provides only CPUs; all chosen libraries have faithful CPU implementations.  
- **Spatial block CV**: Ensures spatial independence, addressing autocorrelation concerns.  
- **Bias correction**: Improves background sampling realism and is applied to both training and recent evaluation.  
- **Calibration before projection**: Guarantees only reliable models are used for future scenarios.  
- **MOP‑only analysis**: Provides an independent, non‑model‑based assessment of niche stability, separating transferability from genuine ecological change.  
- **Reduced workload**: Guarantees completion within the 6‑hour CI budget while preserving scientific integrity.  

---



