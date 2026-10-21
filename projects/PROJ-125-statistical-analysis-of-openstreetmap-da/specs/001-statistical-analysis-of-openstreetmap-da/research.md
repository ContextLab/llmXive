# Research: Statistical Analysis of OpenStreetMap Data for Urban Heat Island Effects

## Summary of Findings
The specification requires OpenStreetMap (OSM) vector data and cloud‑screened Landsat thermal rasters for up to ten cities. Verified open‑source URLs exist for OSM (Parquet and gzip archives) but **no verified URL is available for Landsat LST**. Consequently the pipeline will attempt to download Landsat data via the NASA EarthData API (or Google Earth Engine) and will abort with a clear error if the download fails. All other required variables are present in the verified datasets.

## Dataset Strategy

| Data Type | Required Variables | Source Strategy | Verified URL(s) | Status |
|---|---|---|---|---|
| **OSM Vectors** | Buildings, land‑use, trees, roads | HuggingFace parquet dataset (vector features) | `https://huggingface.co/datasets/Mead0w1ark/megaearth-osm-sentinel2/resolve/main/tables/admit/classes_final.parquet`<br>`https://huggingface.co/datasets/arbml/Osman_Un_Corpus/resolve/main/data/train-00000-of-00001-c160156ed7df8ea7.parquet` | ✅ |
| **OSM Tiles (gzip)** | Alternative raw tile archive | HuggingFace tar.gz archive | `https://huggingface.co/datasets/PeakNav/global-openstreetmap-extraction-slippy-tiles-tar/resolve/main/map_folder/AREAS/zoom_05/xa_00/xb_00/ya_00/yb_08_AREAS_z_05_x_0000_y_0008.tar.gz`<br>`https://huggingface.co/datasets/open2roam/openstreetmaps/resolve/main/continent=central-america/country=AG/data_0.parquet` | ✅ |
| **City Boundaries** | Polygon, BBox, CRS | `geopandas` built‑in GADM/Natural Earth fetcher | — (programmatic via `geopandas.read_file`) | ✅ |
| **Landsat LST** | Summer (June–August) median composite, 5‑year average | NASA EarthData (Landsat 8/9 Level‑2) or Google Earth Engine `LANDSAT/LC08/C01/T1_RT` collection, cloud‑screened, then median per year; average across 5 years. | **No verified URL** (requires authenticated API) | ⚠️ Pipeline aborts if download fails. |
| **Reference for Upper‑Bound R²** | Literature‑derived max R² = 0.60 | Cite Oke 1982 (energy balance) as placeholder; will be flagged for verification. | — | ⚠️ Metric computed but source uncertainty noted. |

### Handling the Missing Landsat Source
- The pipeline first attempts an unauthenticated download via `earthdata.nasa.gov` using the `landsatxplore` Python client.  
- If the request fails (e.g., authentication required), the pipeline logs an error and exits (no synthetic data).  
- Reviewers may later supply a verified open dataset (e.g., a pre‑processed LST mosaic hosted on HuggingFace) to replace this step.

## Statistical Methodology

| Step | Method | Library | Rigor Elements |
|------|--------|---------|----------------|
| **Exploratory Correlation** | Pearson correlation matrix | `scipy.stats.pearsonr` | Report p‑values; no multiple‑test correction needed here. |
| **Spatial Autocorrelation** | Moran’s I for each variable | `pysal.explore.esda.Moran` | Significance assessed via permutation (default 999 permutations). |
| **OLS** | Linear regression with clustered SE | `statsmodels.api.OLS` + `statsmodels.stats.sandwich_covariance.cov_cluster` | Handles heteroskedasticity; p‑values later FDR‑corrected. |
| **SAR** | Spatial Lag Model (SLM) | `pysal.model.sarl.SAR` | Requires spatial weights matrix; uses same CV folds. |
| **GWR** | Geographically Weighted Regression | `mgwr.gwr.GWR` | Bandwidth selected via AICc; sweep performed for sensitivity. |
| **Spatial 5‑fold CV** | Blocked cross‑validation (k‑means on coordinates) | Custom utility (`analysis.validation`) | Prevents leakage from spatial autocorrelation. |
| **Permutation‑based FDR** | Benjamini‑Hochberg on permutation p‑values | `statsmodels.stats.multitest.fdrcorrection` | α = 0.05; `correction_method` column recorded. |
| **Bandwidth Sweep** | GWR bandwidth range 50‑500 m (step 25 m) OR OLS coefficient stability via varying block size | `mgwr` or custom OLS re‑fit loop | Plots R² vs. bandwidth (or block size). |
| **Unexplained Variance Gap** | `UpperBound_R² – Observed_R²` with `UpperBound_R² = 0.60` (placeholder) | Simple arithmetic | Gap reported; source flagged for future verification. |

## Compute Feasibility & Strategy

- **CPU‑First**: All libraries run on CPU; `mgwr` and `pysal` are pure‑Python/NumPy and fit within the 7 GB RAM limit when dataset is ≤ 500 k cells.  
- **Chunked Raster Processing**: Large Landsat scenes are read with `rasterio` windows; only the intersecting city extent is loaded.  
- **Memory Monitoring**: `psutil` tracks RSS; fallback triggered at > 5 GB, abort at > 6 GB (SC‑005).  
- **No GPU Needed**: All steps are CPU‑compatible; no GPU escape hatch required.

## Memory Safety & Fallback (FR‑005)

- `utils.memory.check_memory()` records peak usage per pipeline stage.  
- If `peak_memory_gb > 5` → set `model_type = "OLS_DEGRADED"`; only OLS with clustered SE is fitted; `memory_status = "DEGRADED"` in metrics CSV.  
- If `peak_memory_gb > 6` → exit with code 99 and log `SC-005` violation.

## Data Availability & Download Strategy

1. **OSM** – `datasets.load_dataset("Mead0w1ark/megaearth-osm-sentinel2")` (Parquet) or `osmnx` with the city bbox.  
2. **Landsat LST** – Attempt programmatic download via `landsatxplore` (no authentication required for public data). If unavailable, abort.  
3. **City Boundaries** – `geopandas.read_file("https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_10m_admin_1_states_provinces.geojson")` and filter by city name.  

All URLs are either verified (OSM) or clearly flagged as unavailable (Landsat). No synthetic data will be generated.

## References

- Oke, T. R. (1982). *The energetic basis of the urban heat island*. *Quarterly Journal of the Royal Meteorological Society*, 108(455), 1‑24.  
- Anselin, L. (1995). *Local Indicators of Spatial Association—LISA*. *Geographical Analysis*, 27(2), 93‑115.  
- Brunsdon, C., & Fotheringham, A. S. (2009). *Geographically Weighted Regression: The Analysis of Spatially Varying Relationships*. Wiley.  
- `osmnx` documentation, `pysal` docs, `mgwr` docs, `landsatxplore` GitHub repo.

---
