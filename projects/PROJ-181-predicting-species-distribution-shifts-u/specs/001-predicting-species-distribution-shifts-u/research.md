# Research: Predicting Species Distribution Shifts Using Historical Occurrence Records and Climate Data

## 1. Problem Definition & Scope
We assess the reliability of Species Distribution Models (SDMs) for forecasting North American bird range shifts under climate change. The central hypothesis is that models trained on historic occurrence (1970‑2000) will show a measurable change in predicted suitability when climate is projected to 2050, indicating niche non‑stationarity. All findings are framed as **associational** (FR‑008) and no causal inference is claimed.

### Scope
- **Taxa**: ~20–50 common North American bird species (selected to meet compute limits).  
- **Temporal windows**: Historical (1970‑2000), Recent (2005‑2020) for validation, Future (2050, SSP2‑4.5) for projection.  
- **Data sources**: GBIF/eBird API (occurrences), WorldClim v2.1 (historical climate), WorldClim CMIP6 (future climate).  
- **Constraints**: CPU‑only execution on GitHub Actions free tier; total runtime ≤ 6 h; RAM ≤ 7 GB.

## 2. Dataset Strategy
Only open, programmatically accessible datasets are used. No gated data are involved.

| Dataset | Source / Verified URL | Role | Verification |
|---------|----------------------|------|--------------|
| Historical Occurrences (1970‑2000) | GBIF API (`pygbif`) – programmatic fetch (verified by executed code) | Training occurrences | **Verified** (GBIF API reachable) |
| Recent Occurrences (2005‑2020) | GBIF API (`pygbif`) – programmatic fetch | Out‑of‑time validation | **Verified** |
| Historical Climate | WorldClim v2.1 – <https://worldclim.org/data/worldclim21.html> (download via `wget`) | Predictor variables (Bio1‑Bio19) for training | **Verified** |
| Future Climate (2050, SSP2‑4.5) | WorldClim CMIP6 – <https://worldclim.org/data/cmip6.html> (download via `wget`) | Predictor variables for projection | **Verified** |

All rasters are stored as GeoTIFFs (30 arc‑seconds, EPSG:4326). Downloads are streamed tile‑by‑tile to keep RAM usage low.

## 3. Methodology

### 3.1 Data Preprocessing (FR‑001, FR‑003, FR‑014)
1. **Download** raw occurrence CSVs and climate GeoTIFFs.  
2. **Filter** records to species‑specific breeding months (defined in `config.py`).  
3. **Deduplicate** exact coordinate matches.  
4. **Spatial thinning**:  
   - Compute nearest‑neighbor distances, take the 95th percentile as `min_distance`.  
   - If fewer than three points, fallback to a fixed 10 km threshold.  
   - Apply `utils.spatial.thin_points`.  
5. **Climate extraction**: Sample each raster at occurrence coordinates using `rasterio.sample`. Missing raster values are imputed via nearest‑neighbor interpolation; points still missing after imputation are excluded.  
6. **Data‑sufficiency check** (FR‑006, FR‑011):  
   - Count records per species after thinning.  
   - Compute statistical power for detecting Cohen’s h = 0.50 (effect size = 0.50, source: Wikipedia).  
   - Flag species with `<100` records **or** power < 0.8 as `INSUFFICIENT_DATA`.  
   - Log counts and power values in `metrics/data_sufficiency.json` (schema `data_sufficiency.schema.yaml`).  

### 3.2 Model Training (FR‑004, FR‑007)
- **Algorithms**: Random Forest (`sklearn.ensemble.RandomForestClassifier`), Bioclim (range envelope), MaxEnt‑style surrogate (logistic regression with L2 regularization).  
- **Spatial block cross‑validation**:  
  - Divide the study area bounding box into a 5 × 5 grid (K = 5 blocks).  
  - Rotate held‑out block for each fold, ensuring spatial independence (FR‑007).  
- **CPU‑only enforcement**: `utils.gpu_check.py` aborts if CUDA is detected (FR‑004).  
- **Null model**: Predicts mean prevalence; its AUC serves as the baseline for SC‑001.  

### 3.3 Evaluation & Projection (FR‑005, FR‑009, FR‑010)
1. **Historical validation**: Compute AUC and TSS on recent (2005‑2020) occurrences using the *contemporary* climate (2005‑2020 WorldClim).  
2. **Future projection**: Predict suitability at the *same* recent occurrence locations under 2050 climate.  
3. **Niche‑stability metric**: `delta_Suitability = mean(suitability_2050) – mean(suitability_2005‑2020)`. This directly measures the impact of climate change on predicted suitability without requiring future occurrence data.  
4. **Threshold sweep** (FR‑005): Evaluate suitability thresholds at 0.49, 0.51, 0.55, 0.60 (baseline 0.5 ± {0.01, 0.05, 0.10}). Record false‑positive/negative rates for each.  
5. **Hierarchical bootstrap** (FR‑010):  
   - Level 1: Resample species with replacement.  
   - Level 2: Within each species, resample spatial blocks.  
   - Perform 10 000 iterations on `delta_Suitability`.  
6. **Multiple‑comparison correction**: Apply Benjamini‑Hochberg to the four threshold tests (FR‑005).  
7. **Report**: Store all metrics in `metrics/model_performance.json` (schema `model_metrics.schema.yaml`). Append the disclaimer `"Findings are associational and assume niche stability"` to every report file (FR‑008).

### 3.4 Statistical Rigor
- **Multiple‑comparison**: Benjamini‑Hochberg (FDR = 0.05).  
- **Power analysis**: Conducted pre‑training (FR‑011).  
- **Collinearity**: Acknowledge high correlation among Bioclim variables; Random Forest inherently handles it.  
- **Associational framing**: Explicit disclaimer added per FR‑008.  

## 4. Risks & Mitigations
| Risk | Mitigation |
|------|------------|
| GBIF API rate limits | Exponential back‑off, caching raw responses in `data/raw/`. |
| Missing raster tiles | Nearest‑neighbor imputation; log number of excluded points. |
| Insufficient records | Species flagged and excluded; report limitation. |
| Runtime > 6 h | Limit species list, use streaming raster reads, reduce bootstrap iterations if needed (still ≥ 5 000). |
| Memory overflow | Process species sequentially; never load all rasters simultaneously. |
| Unexpected GPU presence | `gpu_check.py` aborts early with clear log. |

## 5. Decision Rationale
- **CPU‑first**: Free‑tier CI provides only CPUs; all chosen libraries run efficiently on CPU.  
- **Spatial block CV**: Prevents inflated AUC from spatial autocorrelation (essential for ecological validity).  
- **Hierarchical bootstrap**: Captures dependence across species and spatial blocks, satisfying FR‑010.  
- **Delta suitability**: Provides a defensible niche‑stability metric without requiring unavailable future occurrence data.  
- **Open data only**: Guarantees reproducibility on CI; no gated datasets used.  

---
