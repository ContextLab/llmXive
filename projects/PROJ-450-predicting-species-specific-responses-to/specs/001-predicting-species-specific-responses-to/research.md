# Research: Predicting Species‑Specific Responses to Climate Change from Museum Collection Data

## Summary of Approach

This research plan details the data acquisition, processing, and statistical analysis required to fulfill the functional requirements (FR-001 to FR-012). The core methodology involves retrieving museum occurrence records from GBIF, extracting climate variables from WorldClim v2, computing niche centroids, and performing **Phylogenetic Generalized Least Squares (PGLS)** regression to relate niche shifts to regional warming. The implementation is strictly in R to comply with the project Constitution.

## Dataset Strategy

### Verified Datasets

The following datasets are verified sources for this project. All data access must use these sources or their programmatic loaders.

1. **GBIF Occurrence Data**
 * **Source**: GBIF API
 * **URL**: `
 * **Access Method**: `rgbif::occ_search` (R package).
 * **Constraints**: Query must filter `basisOfRecord="PRESERVED_SPECIMEN"`. Must handle pagination.
 * **Verification**: The endpoint ` is the standard, documented API for occurrence retrieval.

2. **WorldClim v2 Climate Layers**
 * **Source**: WorldClim
 * **URL**: `https://www.worldclim.org/data/worldclim21.html`
 * **Access Method**: Local download of `bio1` (annual mean temperature) and `bio12` (annual precipitation) for periods `1970-2000` and `1991-2020`.
 * **Constraints**: Must be pre-downloaded and stored in `data/raw/`. Format: GeoTIFF.
 * **Verification**: WorldClim v2 is the standard global climate dataset for these periods.

### Dataset Variable Fit

* **Required Variables**: Latitude, Longitude, Collection Date (GBIF); Mean Annual Temperature, Annual Precipitation (WorldClim).
* **Fit Confirmation**:
 * GBIF API returns `decimalLatitude`, `decimalLongitude`, and `eventDate` (or `basisOfRecord` for type filtering). This matches the requirement for georeferenced records.
 * WorldClim v2 provides `bio1` and `bio12` at 30 arc-second resolution. This matches the requirement for climate variables.
 * **Gap Handling**: If a species lacks records spanning 50 years, the pipeline logs a warning and excludes the species (FR-002). If a location has missing climate data (e.g., ocean), the record is flagged and excluded from centroid calculation.

## Statistical Methodology

### Niche Centroid Computation (FR-004)
For each species and period:
1. Filter records to valid lat/long and collection date range.
2. Extract `bio1` and `bio12` values at coordinates using `raster::extract`.
3. Compute arithmetic mean of `bio1` and `bio12` for the species in that period.

### Standardization and Shift Magnitude (FR-005)
1. Pool all species occurrence points across both periods.
2. Calculate global mean and standard deviation for temperature and precipitation.
3. Z-score all extracted values: $z = (x - \mu) / \sigma$.
4. Compute Euclidean distance between the z-scored centroids of the two periods: $\Delta N = \sqrt{(z_{T2} - z_{T1})^2 + (z_{P2} - z_{P1})^2}$.
* **Interpretation Note**: Due to the global z-scoring requirement, $\Delta N$ represents the species' shift **relative to the global community mean**. If the global mean shifts, the baseline shifts. This is a known limitation of the spec's FR-005.

### Regional Warming Rate (FR-006)
1. **Define Independent Envelope**: To avoid circularity, the "regional" grid is defined by a **static historical envelope** (e.g., a km buffer around the species' 1970-2000 centroid, or a fixed ° latitudinal band containing the historical centroid). This envelope does **not** shift with the modern range.
2. Extract mean temperature from the regional climate grid (independent of species points) for both periods within this static envelope.
3. Compute $\Delta T = \text{MeanTemp}_{1991-2020} - \text{MeanTemp}_{1970-2000}$.
* **Rationale**: This ensures $\Delta T$ is independent of the species' modern distribution, satisfying the "independent regional climate grid" requirement.

### Regression Analysis (FR-007, FR-011)
* **Model**: **Phylogenetic Generalized Least Squares (PGLS)**: $\Delta N = \beta_0 + \beta_1 \Delta T + \epsilon$, with phylogenetic correlation structure (via `caper` or `phylolm`).
* **Alternative (if tree unavailable)**: Weighted Least Squares (WLS) with weights = $1 / \text{Var}(\Delta N)$.
* **Global Regression**: Fit on all species.
* **Regional Regression**: Group species by latitudinal band (10° bins). Fit separate models per group.
* **Metrics**: Slope ($\beta_1$), 95% CI, $R^2$, p-value.
* **Weighting**: Weights are derived from the inverse variance of $\Delta N$ estimates (calculated in the sensitivity analysis, FR-009) to handle heteroscedasticity.

### Power Analysis (FR-012)
* **Method**: A priori power analysis using `pwr` package.
* **Parameters**: Power = 0.80, $\alpha$ = 0.05, Effect Size (slope) = [deferred based on literature].
* **Output**: Margin of error for the slope estimate. Target ≤ 0.15 for n ≥ 30 species.
* **Justification**: The sample size (n=30) is justified if the calculated margin of error meets the target. If n < 30, the limitation is explicitly reported.

### Sensitivity Analysis (FR-009)
* **Method**: Bootstrap/Subsample.
* **Procedure**: Randomly sample [deferred] of records for each species (10 replicates). Recompute $\Delta N$.
* **Output**: Mean and SD of $\Delta N$ per species. Flag if $SD \ge 0.2$.
* **Usage**: The SD is used to calculate the weights for the WLS/PGLS regression.

## Decision Rationale

* **R Environment**: Chosen to comply with Constitution Principle VI (`rgbif`, `raster`, `sf`).
* **CPU Feasibility**: All operations (CSV parsing, z-scoring, PGLS/WLS) are CPU-tractable. No deep learning or GPU-intensive methods are used.
* **Data Volume**: GBIF queries are paginated; data is processed in chunks to stay within 7GB RAM.
* **Reproducibility**: Random seeds are set for all sampling operations (`set.seed()`). All external data sources are versioned (WorldClim v2) or timestamped (GBIF query via `rgbif`).

## Known Constraints & Limitations

* **Temporal Gap**: WorldClim v2 only provides 1970-2000 and 1991-2020. The "century-scale" inference relies on the difference between these two periods.
* **Sampling Bias**: Museum data is biased towards accessible locations. The sensitivity analysis (FR-009) mitigates this but cannot eliminate it.
* **Coordinate Precision**: GBIF records may have high coordinate uncertainty. Records with `coordinateUncertaintyInMeters` > 10km (configurable) may be filtered.
* **Global Z-Scoring Limitation**: The metric $\Delta N$ is relative to the global mean. If the global community shifts, the baseline shifts. This is a known limitation of the spec's FR-005.