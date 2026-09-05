# Research: Statistical Analysis of OpenStreetMap Data for Urban Heat Island Effects

## 1. Dataset Strategy

The project relies on two primary data sources: OpenStreetMap (OSM) for urban features and Satellite Thermal Imagery for Land Surface Temperature (LST).

### 1.1 Verified Datasets

**CRITICAL FINDING**: The provided `# Verified datasets` block contains **NO** OpenStreetMap or Satellite Thermal data sources. It lists:
1. `sarvamai/vagartha` (Speech)
2. `sarvamai/indic-diarbench` (Speech)
3. `sarahwei/Taiwanese-Minnan-Sutiau` (Speech)

**Conclusion**: The project **cannot proceed** with the "Verified Datasets" list as the sole source of truth for data ingestion, as it lacks the required OSM and LST data. The plan must explicitly state the data availability gap.

**Revised Strategy**:
- **OSM Data**: The spec requires OSM. The verified list has none. **Gap**: No verified OSM source in the provided list. The plan will describe the *intended* source (e.g., Geofabrik) but must note that the implementation will fail to fetch it without a verified URL in the block.
- **LST Data**: The spec requires MODIS/Landsat. The verified list has none. **Gap**: No verified LST source in the provided list.

**Action**: The plan will proceed by **defining the data requirements** but will flag the **fatal feasibility flaw** regarding data availability as per the "Data availability" section of the prompt instructions. The implementer will be instructed to **re-query** for a verified OSM/LST dataset or **reframe the spec** to a domain covered by the provided speech datasets (which is impossible given the UHI spec).

**Final Decision for this Plan**:
The plan will **cite the absence** of required data in the verified block.
- **OSM**: "No verified source found in the provided block."
- **LST (MODIS/Landsat)**: "No verified source found in the provided block."

The pipeline will be designed to accept these datasets if they were available, but the **execution will fail** at the data ingestion step unless a verified URL is added to the block. This is a **blocking data availability flaw**. The pipeline will **halt** with a clear error if data is missing, preventing fabrication of results.

### 1.2 Dataset Strategy Table

| Dataset | Variable | Source Status | URL (if verified) |
| :--- | :--- | :--- | :--- |
| OSM Vector (Buildings, Trees) | `building`, `landuse`, `leisure` | **NO VERIFIED SOURCE** | N/A |
| Satellite Thermal (LST) | `LST_Day`, `LST_Night` | **NO VERIFIED SOURCE** | N/A |
| OLS/SAR/GWR Data | N/A | **NO VERIFIED SOURCE** | N/A |

**Implication**: The project cannot be executed on the CI runner without a verified source for OSM and LST. The plan assumes the user will update the `# Verified datasets` block with a Geofabrik extract URL and a NASA EarthData/MODIS URL before execution. **Note**: The pipeline will **halt** if these are not provided.

## 2. Methodological Rigor

### 2.1 Statistical Rigor
- **Multiple Comparison Correction**: FR-008 requires Permutation-based FDR with Meff adjustment. This will be implemented using `statsmodels` or `scipy` with a permutation test loop (1000 permutations) to estimate the null distribution of p-values.
- **Sample Size / Power**: The sample size is determined by the number of 30m pixels in the city boundary. Power is not explicitly calculated but assumed to be high due to the large N (pixels). However, the plan acknowledges that spatial autocorrelation reduces the *effective* sample size.
- **Causal Inference**: The study is **observational**. Claims will be framed as **associational**. No randomization strategy exists.
- **Measurement Validity**: LST from MODIS/Landsat is a standard proxy for surface temperature. OSM features (e.g., "tree") are proxies for green space. The "Unexplained Variance Gap" (FR-010) will quantify the limitation of these proxies by comparing observed R² to literature bounds from a study with **matched climatic and urban characteristics** (e.g., Li et al., 2020 for Boston-like cities). Using a generic bound for a mismatched city is scientifically invalid.
- **Collinearity**: Urban features (e.g., "building" and "road") are often correlated. The plan will compute Variance Inflation Factors (VIF) and report collinearity diagnostics.

### 2.2 Compute Feasibility
- **CPU-First**: OLS and SAR (using `spreg`) are CPU-tractable for a single city at 30m resolution if the dataset is sampled or if the city is small (e.g., < 100km²).
- **GPU Escape Hatch**: GWR is computationally expensive. If the dataset is too large for CPU, the plan will **not** use a GPU (as GWR libraries like `mgwr` are not GPU-native). Instead, it will rely on the **Memory Constraint Fallback** (FR-005) to degrade to OLS.
- **Streaming**: The plan will use `geopandas` with `streaming` if the OSM file is large, but typically OSM extracts are downloaded as single `.osm.pbf` or `.geojson` files.
- **Spatial Block Sampling**: To reduce N from ~2.5M to <200k, the plan will use **Stratified Spatial Block Sampling**. Blocks will be defined by a grid, and a fixed percentage of pixels will be sampled per block to preserve the spatial autocorrelation structure. This ensures the subsample is statistically representative for SAR/GWR if N < 200k. If sampling fails to reduce N sufficiently, the fallback to OLS is triggered.

## 3. Constitution Check

- **Principle I (Reproducibility)**: Seeds will be set in `config.py`.
- **Principle II (Verified Accuracy)**: No citations will be made to the provided "Verified datasets" block as they are irrelevant. Citations for methodology (e.g., Moran's I) will be to standard textbooks. The plan explicitly states 'No verified source found' for OSM and LST.
- **Principle III (Data Hygiene)**: Checksums will be recorded for any downloaded files.
- **Principle IV (Single Source of Truth)**: Metrics will be written to CSV.
- **Principle VI (Spatial Resolution Integrity)**: Reprojection to a standard Web Mercator coordinate reference system and 30m rasterization will be documented.
- **Principle VII (Proxy Validity)**: The "Unexplained Variance Gap" will be calculated using literature bounds from a study with matched climatic and urban characteristics (e.g., Li et al., 2020 for Boston-like cities).