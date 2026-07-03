# Research: Predicting Avian Foraging Guilds from Public eBird Data and Land Cover Maps

## Dataset Strategy

This project relies on two primary datasets, verified for reachability and format.

| Dataset | Source / URL | Format | Usage in Plan | Verification Status |
|:--- |:--- |:--- |:--- |:--- |
| **eBird Basic Dataset (EBD)** | **Primary**: `https://ebird.org/data/download/basic` (Official Cornell Lab) <br> **Fallback (CI)**: ` (Verified S3 Mirror) | CSV / Parquet | Source of occurrence records (lat, lon, species). Used to filter top 25 species and extract coordinates. | **Verified**: Official source confirmed. Fallback verified for CI feasibility. |
| **NLCD 2019 Land Cover** | ` (USGS EarthExplorer) | GeoTIFF (ZIP) | Source of land cover classification. Used to extract proportions within 100m buffers of eBird points. | **Verified**: Matches Constitution Principle VI and Spec FR-002. |

**Data Fit Assessment**:
- **EBD**: Contains species IDs, latitude, longitude, and observation counts. The `species_id` field allows mapping to external foraging guilds. The record count allows selection of the top 25. The full EBD is ~100M records; filtering to top 25 species (estimated ~1-5M records) ensures the dataset fits within 7 GB RAM.
- **NLCD**: Provides 30m resolution land cover classes (Forest, Grassland, Wetland, Urban, etc.) for the contiguous US. This resolution is sufficient for 100m buffering.
- **Potential Mismatch**: The official EBD download may be slow. The fallback S3 mirror is a pre-filtered subset designed to fit CI constraints while maintaining statistical power.

**Foraging Guild Labels**:
- Labels (ground, canopy, aerial) are NOT in the EBD.
- **Source**: External ornithological literature (e.g., *Birds of the World* by Cornell Lab of Ornithology).
- **Strategy**: A static lookup table (`data/guilds.yaml`) will be curated in the `code/` directory, mapping common species IDs to their guilds. This table will be versioned and cited against primary literature.

## Analytical Methodology

### 1. Data Processing (FR-001, FR-002, FR-003)
- **Filtering**: Load EBD, group by `species_id`, count records. Select a representative subset of top-ranked items. Filter out species with <50 observations.
- **Buffering**: For each observation point (lat, lon), create a 100m circular buffer.
- **Zonal Statistics**: Use `rasterio` and `geopandas` to calculate the proportion of each NLCD class within the buffer.
- **Aggregation**: **Crucial Step**: Aggregate land cover proportions to the **species level** (mean/median) to create a single `Species Habitat Profile` per species. This removes the confounding effect of observation count and ensures the model learns habitat-guild relationships, not species-habitat preferences.
- **Merging**: Join aggregated species profiles with guild labels via the lookup table.

### 2. Model Training (FR-004, FR-006)
- **Algorithm**: Random Forest Classifier (`sklearn.ensemble.RandomForestClassifier`).
- **Features**: Proportions of land cover classes (e.g., `forest_prop`, `grassland_prop`, `wetland_prop`, `urban_prop`) at the **species level**.
- **Target**: `foraging_guild` (categorical: ground, canopy, aerial).
- **Validation**: 5-fold Stratified Cross-Validation (stratified by `foraging_guild` to handle class imbalance).
- **Metrics**: Balanced Accuracy, Per-class F1 Score.
- **Hyperparameters**: Default `sklearn` parameters (e.g., `n_estimators=100`, `max_depth=None`) to ensure CPU feasibility. No grid search to save runtime.

### 3. Significance Testing (FR-005, FR-008, SC-002)
- **Null Hypothesis**: Guild assignment is independent of land cover profile. (i.e., Land cover does not predict guild better than random chance).
- **Method**: **Random Guild Permutation (Across Species)**.
 - Shuffle the `foraging_guild` labels across the 25 species (breaking the species-guild link).
 - Retrain the model on the permuted data.
 - Repeat the procedure multiple times to build a null distribution of balanced accuracy.
 - Calculate p-value: proportion of permuted accuracies ≥ observed accuracy.
- **Rationale**: Since guilds are static per species, permuting within species is impossible. Permuting across species tests whether the observed land cover-guild relationship is stronger than random chance.

### 4. Visualization (FR-007)
- **Confusion Matrix**: Heatmap of predicted vs. actual guilds (at species level).
- **Feature Importance**: Bar chart of mean decrease in impurity or permutation importance.
- **Spatial Map**: GeoJSON/PNG showing prediction probabilities for the top 2 species by observation count (using the aggregated model applied to their specific habitat profiles).

## Statistical Rigor & Assumptions

- **Causal Inference**: This is an **observational study**. Claims will be framed as *associations* between land cover profiles and species-level guilds. No causal claims about individual bird behavior will be made.
- **Collinearity**: Land cover classes are compositional (sum to 1.0). This introduces inherent collinearity. The Random Forest handles this reasonably well, but interpretation of "independent effect" will be avoided. Instead, we will report relative importance.
- **Measurement Validity**: Guild labels are assumed valid based on authoritative sources. Land cover validity depends on NLCD accuracy (published error rates for major classes).
- **Power**: With 25 species (N=25), the power for a 3-class classification problem is limited. However, the permutation test provides a robust assessment of whether the signal exceeds chance. Power will be reported as `[deferred]` until actual N is known.
- **Multiple Comparisons**: If per-class F1 scores are tested individually, a Bonferroni or FDR correction will be applied. The primary metric is Balanced Accuracy.

## Compute Feasibility

- **RAM**: Filtering to top 25 species and calculating 100m buffers on ~1-5M points should fit within 7 GB RAM. `rasterio` reads rasters in chunks. Aggregation reduces data to 25 rows for modeling.
- **CPU**: Random Forest on 25 rows and ~5 features is trivial. Permutation test (1000 iterations) is the heaviest step; parallelization via `n_jobs=2` will be used.
- **Disk**: Raw NLCD (~hundreds of MB), EBD (~1-2GB), processed CSV (~100MB). Well within 14 GB limit.
- **Time**: Data download (~m), Processing (~m), Training (~m), Permutation (~-3h), Viz (~large-scale). Total < 6h.

## Risks & Mitigations

- **Risk**: Official EBD download exceeds 6-hour CI limit.
 - *Mitigation*: Pipeline checks if official download is feasible. If not, it automatically switches to a verified, pre-filtered S3 subset (simulating the full EBD) to ensure CI completion.
- **Risk**: NLCD raster is missing for specific coordinates (e.g., ocean, outside US).
 - *Mitigation*: Filter out observations where NLCD data is invalid or missing. Log count of dropped points.
- **Risk**: Foraging guild data missing for a top 25 species.
 - *Mitigation*: Drop species from the final training set if guild is unknown. Log the species.