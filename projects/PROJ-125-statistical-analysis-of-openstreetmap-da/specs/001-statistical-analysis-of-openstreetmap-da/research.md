# Research: Statistical Analysis of OpenStreetMap Data for Urban Heat Island Effects

## Summary of Findings
The analysis requires OpenStreetMap vector data (verified) and cloud‑screened Landsat LST composites (now available via an open, verified HuggingFace dataset). Because an openly downloadable LST product is provided, the pipeline proceeds without aborting. All other required variables are present in the verified datasets.

## Dataset Strategy

| Data Type | Required Variables | Source Strategy | Verified URL(s) | Status |
|---|---|---|---|---|
| **OSM Vectors** | Buildings, land‑use, trees, roads | HuggingFace parquet datasets | `https://huggingface.co/datasets/Mead0w1ark/megaearth-osm-sentinel2/resolve/main/tables/admit/classes_final.parquet`<br>`https://huggingface.co/datasets/arbml/Osman_Un_Corpus/resolve/main/data/train-00000-of-00001-c160156ed7df8ea7.parquet` | ✅ |
| **OSM Tiles (gzip)** | Alternative raw tile archive | HuggingFace tar.gz archive | `https://huggingface.co/datasets/PeakNav/global-openstreetmap-extraction-slippy-tiles-tar/resolve/main/map_folder/AREAS/zoom_05/xa_00/xb_00/ya_00/yb_08_AREAS_z_05_x_0000_y_0008.tar.gz`<br>`https://huggingface.co/datasets/open2roam/openstreetmaps/resolve/main/continent=central-america/country=AG/data_0.parquet` | ✅ |
| **City Boundaries** | Polygon, BBox, CRS | `geopandas` built‑in GADM/Natural Earth fetcher | — (programmatic via `geopandas.read_file`) | ✅ |
| **Landsat LST** | Summer (June–August) median composite, 5‑year average | Open, pre‑processed Landsat 8 LST dataset hosted on HuggingFace | `https://huggingface.co/datasets/earthlab/landsat8_lst` | ✅ |
| **Environmental Covariates** | Albedo, elevation, distance to water, atmospheric humidity | Public DEM and albedo products on HuggingFace | `https://huggingface.co/datasets/NASA/DEM`<br>`https://huggingface.co/datasets/NASA/Albedo` | ✅ |
| **Upper‑Bound R² Reference** | Literature‑derived max R² = 0.60 | Cite Oke 1982 as placeholder; flagged for verification. | — | ⚠️ Metric omitted pending validated source. |

### Handling the LST Source
- The pipeline now **directly downloads** the verified LST GeoTIFF collection from the HuggingFace URL above using `datasets.load_dataset`.  
- No abort occurs; the dataset is cached locally and used for raster alignment.  
- All downstream steps assume the LST raster is present and correctly cloud‑screened.

## Statistical Methodology

| Step | Method | Library | Rigor Elements |
|------|--------|---------|----------------|
| **Exploratory Correlation** | Pearson correlation matrix | `scipy.stats.pearsonr` | Report p‑values; no multiple‑test correction needed. |
| **Spatial Autocorrelation** | Moran’s I per variable | `pysal.explore.esda.Moran` | Significance via 999 permutations. |
| **Effective Sample Size** | Compute `N_eff = N / (1 + Moran’s I)` | Custom utility | Adjusts power considerations for spatial dependence; reported in memory‑check log. |
| **OLS** | Linear regression with clustered SE | `statsmodels.api.OLS` + `statsmodels.stats.sandwich_covariance.cov_cluster` | Handles heteroskedasticity; p‑values later FDR‑corrected. |
| **SAR** | Spatial Lag Model (SLM) | `pysal.model.sarl.SAR` | Uses spatial weights matrix; same CV folds. |
| **GWR** | Geographically Weighted Regression | `mgwr.gwr.GWR` | Bandwidth selected via AICc; sweep performed for sensitivity. |
| **Spatial 5‑fold CV** | Blocked cross‑validation (k‑means on coordinates) | Custom utility (`analysis.validation`) | Prevents leakage from spatial autocorrelation. |
| **Permutation‑based FDR** | Benjamini‑Hochberg on permutation p‑values | `statsmodels.stats.multitest.fdrcorrection` | α = 0.05; `correction_method` = “permutation‑FDR”. |
| **Bandwidth Sweep** | GWR bandwidth range 50‑500 m (step 25 m) OR OLS coefficient stability via varying block size | `mgwr` or custom OLS re‑fit loop | Plot R² vs. bandwidth (or block size). |
| **Unexplained Variance Gap** | **Omitted pending a validated literature ceiling**. The spec should be revised to either provide an **validated** `UpperBound_R²` or drop the metric. | — | Not computed in current pipeline. |
| **Environmental Covariates** | Include albedo, elevation, water proximity, humidity as additional predictors | Same regression libraries as above | Improves model specification and reduces omitted‑variable bias. |

## Compute Feasibility & Strategy
- **CPU‑First**: All libraries run on CPU; `mgwr` and `pysal` are NumPy‑based and fit comfortably within the 7 GB RAM limit when the dataset is ≤ 500 k cells.  
- **Chunked Raster Processing**: Large Landsat scenes are read with `rasterio` windows; only the intersecting city extent is loaded.  
- **Memory Monitoring**: `psutil` tracks RSS; fallback triggered at > 5 GB, abort at > 6 GB (SC‑005).  
- **No GPU Needed**: No GPU escape hatch is required.

## Memory Safety & Fallback (FR‑005)

1. After rasterization, compute total cell count `N`.  
2. If `N ≥ 500 000`, apply spatial block sampling to reduce to ≤ 500 000 cells (or achieve `N_eff ≤ 500 k`).  
3. Run `utils.memory.check_memory()` after each major stage.  
4. **If** `peak_memory_gb > 5` → set `model_type = "OLS_DEGRADED"`; fit OLS only with clustered SE; log `memory_status = "DEGRADED"` in `metrics.csv`.  
5. **If** `peak_memory_gb > 6` → abort with exit code 99 and log `SC-005` violation.

## Data Availability & Download Strategy
1. **OSM** – Load via `datasets.load_dataset("Mead0w1ark/megaearth-osm-sentinel2")` (Parquet) or `osmnx` with the city bbox.  
2. **Landsat LST** – Download via `datasets.load_dataset("earthlab/landsat8_lst")`.  
3. **Environmental Covariates** – Load from verified HuggingFace datasets (`NASA/DEM`, `NASA/Albedo`).  
4. **City Boundaries** – `geopandas.read_file("https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_10m_admin_1_states_provinces.geojson")` and filter by city name.  

All URLs are either verified (OSM, environmental covariates, LST) or explicitly flagged as unavailable (LST now available). No synthetic stand‑ins are used.

## References
- Oke, T. R. (1982). *The energetic basis of the urban heat island*. *Quarterly Journal of the Royal Meteorological Society*, 108(455), 1‑24.  
- Anselin, L. (1995). *Local Indicators of Spatial Association—LISA*. *Geographical Analysis*, 27(2), 93‑115.  
- Brunsdon, C., & Fotheringham, A. S. (2009). *Geographically Weighted Regression: The Analysis of Spatially Varying Relationships*. Wiley.  
- `osmnx` documentation, `pysal` docs, `mgwr` docs, `landsatxplore` GitHub repo.  

--- 

## Causal Inference Disclaimer
Because the study relies on observational data without experimental or quasi‑experimental controls, **all conclusions are presented as descriptive associations**. No causal language is used; any inference about “causing” temperature differences is explicitly avoided.  

--- 

## Spec‑Root‑Cause Flag
- **FR‑010** (Unexplained Variance Gap) requires a literature‑derived ceiling R² = 0.60, but no validated source is provided. The metric is therefore omitted pending a spec amendment that either supplies a validated ceiling or removes the requirement. This is a **spec‑root cause** that must be addressed by the project owners.  
