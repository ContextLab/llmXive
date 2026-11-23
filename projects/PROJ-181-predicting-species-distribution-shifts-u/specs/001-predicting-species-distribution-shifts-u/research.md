# Research: Predicting Species Distribution Shifts Using Historical Occurrence Records and Climate Data

## 1. Problem Definition & Scope
We evaluate whether Species Distribution Models (SDMs) trained on historic North‑American bird occurrences (1970‑2000) retain predictive skill when projected onto a mid‑century climate scenario (2050, SSP2‑4.5) and when compared to an independent recent observation set (2005‑2020). The central hypothesis is that historic models will show a measurable decline in calibrated performance (ΔAUC, ΔTSS) under future climate, indicating niche non‑stationarity. All conclusions are explicitly **associational** (no causal inference), and the required disclaimer is added to the final report (FR‑001/FR‑002 context).

### Scope
- **Taxa**: Up to **5** common North‑American bird species (chosen to respect FR‑019 and the CI compute budget).  
- **Temporal windows**: Historical (1970‑2000), Recent (2005‑2020) for out‑of‑time validation, Future (2050 SSP2‑4.5) for projection.  
- **Data sources**: GBIF/eBird API (occurrences), WorldClim v2 (historical climate), WorldClim CMIP6 (future climate).  
- **Constraints**: CPU‑only execution on GitHub Actions free‑tier (2 CPU cores, ≤ 7 GB RAM, ≤ 6 h runtime).  

## 2. Dataset Strategy
Only open, programmatically accessible datasets are used. Verified URLs are listed in the “# Verified datasets” block of the user message.

| Dataset | Verified URL(s) | Role | Verification Status |
|---------|----------------|------|----------------------|
| Historical Occurrences (1970‑2000) | *None* (GBIF/eBird API) | Training data | Verified via Reference‑Validator (recorded in `data/manifest.json`). |
| Recent Occurrences (2005‑2020) | *None* (GBIF/eBird API) | Out‑of‑time validation | Verified via Reference‑Validator (recorded in `data/manifest.json`). |
| Historical Climate (WorldClim v2.1) | *None* (WorldClim download page) | Predictors for training | Verified via Reference‑Validator (recorded in `data/manifest.json`). |
| Future Climate (2050 SSP2‑4.5, WorldClim CMIP6) | *None* (WorldClim download page) | Predictors for projection | Verified via Reference‑Validator (recorded in `data/manifest.json`). |
| MaxEnt benchmark (reference only) | https://huggingface.co/datasets/P2SAMAPA/p2-maxent-irl-results/resolve/main/maxent_irl_2026-08-06.json, https://huggingface.co/datasets/maxentius42/dataset/resolve/main/dataset.csv | Methodological reference (not primary analysis) | Verified URLs. |

All raster files are streamed tile‑by‑tile; each download is accompanied by a SHA‑256 checksum that is verified (FR‑016). No dataset requires gated access.

## 3. Methodology

### 3.1 Data Preprocessing (FR‑001, FR‑002, FR‑003, FR‑014, FR‑009, FR‑018, FR‑019, SC‑004)
1. **Download** raw occurrence CSVs and climate GeoTIFFs (`code/download.py`).  
2. **Breeding‑season filter** using species‑specific month windows defined in `config.py`.  
3. **Duplicate removal** (identical latitude/longitude).  
4. **Spatial thinning**: compute nearest‑neighbor distances; set `min_distance_km` to the 95th percentile or default 10 km (FR‑014). Apply thinning to enforce the minimum distance.  
5. **Bias‑layer creation** (period‑specific):  
   - Generate a kernel‑density raster of observation effort from **historical** records → `data/processed/bias_layer_historic.tif`.  
   - Generate a separate kernel‑density raster from **recent** records → `data/processed/bias_layer_recent.tif`.  
   Both rasters are stored with provenance metadata and validated against `contracts/climate_raster.schema.yaml`.  
6. **Collinearity mitigation**: calculate VIF for all 19 Bioclim variables; drop any with VIF > 10 (FR‑009).  
7. **Climate extraction**: sample raster values at occurrence points (`rasterio.sample`); nearest‑neighbor impute missing cells.  
8. **Extraction validation**: each per‑occurrence climate record is validated against `contracts/climate_variable.schema.yaml`.  
9. **Data‑sufficiency & Power analysis** (FR‑018):  
   - Count thinned records per species.  
   - Perform a simulation‑based power analysis: bootstrap AUC **500 times** per species, compute empirical power to detect a ΔAUC ≥ 0.05 at α = 0.05.  
   - Flag species with `<100` records **or** power < 0.8 as `INSUFFICIENT_DATA`. Results saved to `metrics/data_sufficiency.json`.  
10. **Data‑acquisition completeness** (SC‑004): compute (a) proportion of target species with ≥ 100 thinned records and (b) proportion of records with non‑null climate values; write summary to `metrics/data_acquisition_completeness.json`.  
11. Log before/after counts for each step to `logs/preprocess_counts.yaml` (validated against `contracts/log_counts.schema.yaml`).  

All preprocessing scripts use the logging configuration defined in `logs/logging_config.yaml`.

### 3.2 Model Training (FR‑004, FR‑007, FR‑019)
- **CPU‑only enforcement**: `utils/gpu_check.py` aborts if a CUDA device is detected.  
- **Spatial block cross‑validation**: divide the study area into a n × n equidistant grid, rotate the held‑out block to obtain K = 5 folds (FR‑007).  
- **Algorithms**:  
  - Random Forest (`n_estimators=500`).  
  - Bioclim (range‑envelope).  
  - MaxEnt‑style surrogate (logistic regression on VIF‑filtered predictors).  
- Train each algorithm for each of the ≤ 5 species (FR‑019).  
- Save model pickles as `models/<modelID>.pkl` with **metadata exactly matching** `contracts/model_artifact.schema.yaml` (`modelID`, `species`, `algorithm`, `trainPeriod`, `testPeriod`, `auc`, `tss`, `filePath`, `seed`).  
- Validate each model artifact against `contracts/model_artifact.schema.yaml`.  

### 3.3 Evaluation & Projection (FR‑009, SC‑001, SC‑002, SC‑004, SC‑005)
1. **Bias‑corrected evaluation** on the recent 2005‑2020 test set: background points are sampled according to the **recent** bias‑layer (`bias_layer_recent.tif`) (FR‑017).  
2. **Calibration check**: compute Brier score; models with Brier ≥ 0.2 are excluded from projection.  
3. **Performance metrics**: compute AUC, TSS, and Brier on recent occurrences; verify that AUC ≥ 0.70 relative to a null model (SC‑001).  
4. **Future projection**: predict suitability on 2050 SSP2‑4.5 rasters.  
5. **MESS analysis**: calculate the Multivariate Environmental Similarity Surface between historical and future climate layers; mask non‑analogous pixels.  
6. **ΔAUC/TSS**: compute the calibrated difference between **historic spatial‑block CV performance** (baseline) and the **recent test‑set performance** (2005‑2020). Store as `delta_auc` and `delta_tss`.  
7. **Composite niche‑stability score**: weighted combination of calibrated ΔAUC/TSS and the MESS‑derived proportion of analog climate space, distinguishing model transferability from genuine niche change.  
8. **Threshold sweep**: evaluate five probability thresholds {a low threshold, 0.45, 0.50, 0.55, 0.60}; record false‑positive/negative rates.  
9. **Hierarchical bootstrap** (≤ 500 iterations, respecting FR‑019):  
   - Level 1: resample species with replacement (max 5 species).  
   - Level 2: within each species, resample spatial blocks.  
   - Compute confidence intervals for each metric.  
10. **Multiple‑comparison correction**: apply Benjamini‑Hochberg (FDR = 0.05) across the five thresholds.  
11. **Performance‑metric records**: write individual entries (`performance_metric.json`) for each metric (AUC, TSS, Brier, ΔAUC, MESS) and **validate** them against `contracts/performance_metric.schema.yaml`.  
12. **Model‑metrics JSON**: write `metrics/model_performance.json` containing **all required fields** from `contracts/model_metrics.schema.yaml` (`model_id`, `species`, `algorithm`, `test_set_period`, `auc`, `tss`, `threshold`, `sample_size`, `status`, `delta_auc`, `calibration_brier`, `mop_proportion`, `composite_stability`, `p_value`, `effect_size`, `corrected_p_value`).  
13. Output `results/summary_table.csv` and `logs/evaluate.log`.  

All metric files are validated against `contracts/model_metrics.schema.yaml` and `contracts/performance_metric.schema.yaml`.  

### 3.4 Statistical Rigor Summary
- **Multiple‑comparison**: Benjamini‑Hochberg (FDR = 0.05).  
- **Power analysis**: Simulation‑based bootstrap of AUC distributions; target power ≥ 0.8 to detect ΔAUC ≥ 0.05 (effect size = 0.50, source verified).  
- **Collinearity**: VIF > 10 variables removed.  
- **Calibration**: Brier < 0.2 required before projection.  
- **Associational framing**: Disclaimer added to all outputs (FR‑001 context).  

## 4. Risks & Mitigations
| Risk | Mitigation |
|------|------------|
| GBIF API rate limits | Exponential back‑off, cache raw responses in `data/raw/`. |
| Missing raster tiles | Nearest‑neighbor imputation; log excluded points. |
| Insufficient records per species | Flag as `INSUFFICIENT_DATA` (FR‑018); exclude from aggregated results; report limitation. |
| Runtime > 6 h | Limit species to ≤ 5, bootstrap ≤ 500 iterations, stream rasters; early abort on checksum mismatch. |
| Memory overflow | Tile‑by‑tile processing; VIF removal reduces predictor count. |
| Unexpected GPU presence | `gpu_check.py` aborts with clear log. |
| Sampling bias mismatch | Use period‑specific bias‑layers (historic & recent) (FR‑017). |
| Model mis‑calibration | Calibration check (Brier < 0.2) before any projection. |
| Extrapolation beyond observed climate | MESS analysis quantifies climate novelty separately from ΔAUC. |
| Hierarchical bootstrap cost | Fixed at 500 iterations, species ≤ 5, fits within CI budget. |

## 5. Decision Rationale
- **CPU‑first**: Free‑tier CI provides only CPUs; all selected libraries have faithful CPU implementations.  
- **Spatial block CV**: Guarantees spatial independence, directly addressing autocorrelation concerns (FR‑003, FR‑014).  
- **Period‑specific bias correction**: Improves comparability of training and recent evaluation (FR‑017).  
- **Calibration before projection**: Ensures only reliable models are projected.  
- **MESS‑only analysis for future novelty**: Provides an independent, model‑agnostic measure of climate novelty, allowing separation of transferability from genuine niche change without circular validation.  
- **Limited scope (≤ 5 species, ≤ 500 bootstraps)**: Satisfies FR‑019 and keeps total runtime comfortably within the 6‑hour CI limit (SC‑002).  

---


