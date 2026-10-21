# Research: Statistical Analysis of OpenStreetMap Data for Urban Heat Island Effects

## Summary of Findings

The study requires (a) **verified per‑city OpenStreetMap extracts** (buildings, land‑use, trees, roads), (b) city boundaries, and (c) **cloud‑screened Landsat LST**. The original OSM URLs cited in the plan were not appropriate extracts; they do not contain the necessary geometry for the ten U.S. cities. A verified source such as the **Geofabrik US PBF file** (`https://download.geofabrik.de/north-america/us-latest.osm.pbf`) provides the required layers and is openly downloadable and programmatically fetchable, satisfying FR‑001 and the Constitution’s reproducibility requirement.

**LST data**: FR‑[identifier] names USGS EarthExplorer, which is interactive‑gated and cannot be fetched unattended. No verified open LST URL exists in the project's verified‑datasets block. Consequently, the pipeline includes a **Phase 0 data‑availability check** that aborts with a `DATA_GAP` error if no LST asset is present. A spec amendment must name a programmatically downloadable LST product (e.g., an AWS Open Data Landsat Collection 2 LST) or authorize a local, checksummed asset.

## Dataset Strategy

| Data Type | Required Variables | Source Strategy | Verified URL(s) | Status |
|---|---|---|---|---|
| **OSM vectors (per‑city extract)** | Buildings, land‑use, trees, roads | Download verified **Geofabrik US PBF**; filter to city bbox; convert to Parquet/GeoJSON. | Verified open source – Geofabrik (e.g., `https://download.geofabrik.de/north-america/us-latest.osm.pbf`) | ✅ (to be fetched) |
| **City boundaries** | Polygon, bbox, CRS | Derived from the same verified OSM extract (place polygons). | — (derived from verified OSM source) | ✅ |
| **Landsat LST** | Summer (JJA) median composite, multi‑year average, Fine spatial resolution. | Must be supplied as a checked‑in GeoTIFF inventory **or** a verified open‑source product (e.g., AWS Landsat Collection 2 LST). No such URL is currently in the verified block. | — | ❌ BLOCKING GAP (requires spec amendment) |
| **Upper‑bound R² reference (FR‑010)** | Literature ceiling is reported as relatively high. | Citation to Zhou et al. 2020 currently unverified. | — | ⚠️ FLAGGED (requires verified citation) |

### Handling the LST gap

- `code/ingest_lst.py` implements the full ingestion contract (checksum, CRS, cloud‑mask, JJA median compositing, 5‑year average) **against a supplied LST GeoTIFF inventory**.
- If no LST asset is available, the pipeline aborts with a documented `DATA_GAP` error listing the missing component.
- **Required spec amendment**: name a verified, programmatically downloadable Landsat LST product (e.g., an AWS S3 URL) or authorize a local asset. Until this amendment lands, the pipeline cannot proceed beyond Phase 0.

## Statistical Methodology

| Step | Method | Library | Rigor Elements |
|------|--------|---------|----------------|
| Exploratory correlation | Pearson correlation matrix | `scipy.stats` | Reported with N and N_eff |
| Spatial autocorrelation | Moran’s I, 999 permutations | `libpysal` + `esda` | Per‑variable; feeds N_eff |
| Effective sample size | **Heuristic** `N_eff = N / (1 + Moran’s I)` (reported as a descriptive lower‑bound; **not** a formal power analysis) | custom utility | Caveat added (see above) |
| OLS | Linear regression, spatially clustered SE | `statsmodels` + `cov_cluster` | Heteroskedasticity‑robust; degraded‑mode default |
| SAR | Spatial lag model | `spreg.ML_Lag` | Same CV folds as OLS |
| GWR | Geographically weighted regression | `mgwr` | AICc bandwidth selection |
| Spatial 5‑fold CV | k‑means block CV on coordinates | custom (`validation.py`) | Prevents spatial leakage (FR‑006) |
| Permutation‑FDR | Permutation p‑values **with spatially constrained permutations within the CV blocks**; Benjamini‑Hochberg correction | `statsmodels.stats.multitest` | α = 0.05; `correction_method = "permutation-FDR"` |
| Bandwidth sweep | GWR 50–500 m step 25, or OLS coefficient‑stability sweep over block sizes in degraded mode; generate R²‑vs‑bandwidth (or block‑size) plot; compute **Unexplained Variance Gap** = 0.68 − Observed_R² (provisional, citation flagged). A negative gap indicates the literature ceiling may be invalid and will be highlighted in the report. | custom | R²‑vs‑bandwidth plot (SC‑004) |
| Unexplained Variance Gap | **Provisional** `0.68 − Observed_R²` (literature ceiling currently unverified); a negative result flags the ceiling as likely invalid. | custom | FR‑010 flagged as provisional |

## Compute Feasibility & Download Strategy

1. **OSM** — download the verified Geofabrik US PBF, filter to each city bbox, write derived GeoJSON/Parquet to `data/raw/osm/` with SHA‑256 checksums and fetch timestamps recorded in `data/raw/manifest.json`.  
2. **City boundaries** — derived from the same verified OSM extract (place polygons).  
3. **LST** — see blocking gap above; ingestion contract implemented, execution pending spec amendment.  
4. **Environmental covariates** — previously mentioned DEM/albedo datasets were removed due to lack of verified sources; the analysis proceeds without them, and the limitation is documented under Principle VII.

## Spec‑Root‑Cause Flags

1. **FR‑002** – Landsat LST source is interactive‑gated; a spec amendment naming an open, programmatically downloadable product (or authorising a local, checksummed asset) is required.  
2. **FR‑010** – The 0.68 R² ceiling citation is unverified; a verified reference must be added before this metric can be reported as literature‑grounded.  
3. **OSM source validity** – The previously listed URLs do not provide the required per‑city geometry; a verified extract (Geofabrik) replaces them.

## References

- Oke, T. R. (1982). *The energetic basis of the urban heat island*. *Quarterly Journal of the Royal Meteorological Society*, 108(455), 1‑24.  
- Anselin, L. (1995). *Local Indicators of Spatial Association—LISA*. *Ge geographical Analysis*, 27(2), 93‑115.  
- Brunsdon, C., & Fotheringham, A. S. (2009). *Geographically Weighted Regression*. Wiley.  
- Zhou, Y., Li, X., & Wang, J. (2020). Mapping urban heat islands using OpenStreetMap and Landsat imagery. *Remote Sensing of Environment*, 250, 111800. **Citation currently unverified in this project's dataset block**.  


