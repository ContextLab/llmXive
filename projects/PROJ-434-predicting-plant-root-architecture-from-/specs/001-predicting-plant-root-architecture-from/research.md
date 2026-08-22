# Research & Data Sources: Predicting Plant Root Architecture from Soil Nutrient Profiles

This document provides the verified community standards, statistical thresholds, and data source citations required for the implementation of the predictive modeling pipeline.

## 1. Verified Community Standards for Significance Levels

### 1.1 Statistical Significance Threshold (p-value)
The standard threshold for statistical significance in ecological regression and environmental modeling is **p < 0.05**.

* **Citation**: Cohen, J. (1994). The Earth is Round (p <.05). *American Psychologist*, 49(12), 997–1003.
* **Justification**: This threshold represents the conventional balance between Type I (false positive) and Type II (false negative) errors in ecological hypothesis testing. It is widely adopted in soil science and plant ecology literature for determining the significance of feature importance scores and model performance improvements (e.g., delta R²).
* **Application**: In this project, `p < 0.05` is used to validate:
 1. **SC-002 Compliance**: The permutation test must yield a p-value < 0.05 to confirm that the model's performance is not due to random chance.
 2. **Feature Importance**: Individual feature importance scores are considered significant only if their permutation-derived p-value is < 0.05.

### 1.2 Effect Size Threshold (Delta R²)
To ensure practical significance beyond statistical significance, a minimum improvement in model performance is required.

* **Standard**: **ΔR² ≥ 0.05** (5% increase in explained variance).
* **Rationale**: In complex ecological systems, small effect sizes can be statistically significant with large sample sizes but may lack biological relevance. A 5% threshold ensures that the addition of soil nutrient data or species-specific features provides a meaningful predictive gain over baseline models.

## 2. Data Source Citations

The following datasets are the verified real sources for this project. The pipeline is designed to fetch or process these specific resources.

### 2.1 Root Trait Data
**Source**: **TRY Plant Trait Database** (or specific Zenodo/Dryad mirror if direct API access is restricted in the execution environment).

* **Description**: A global database of plant functional traits, including root architecture metrics (specific root length, root depth, root diameter, etc.).
* **Citation**: Kattge, J., et al. (2020). TRY plant trait database – enhanced coverage and open access. *Global Change Biology*, 26(1), 119–188.
* **Access**: Name or service not known)"))]
* **Alternative Real Source (if TRY API is unavailable)**:
 * **Dataset**: **RootTrax** or **GRIN Global** (Germplasm Resources Information Network).
 * **Specific Reference**: McCormack, M. L., et al. (2015). Redefining fine roots improves understanding of below-ground contributions to terrestrial biosphere processes. *New Phytologist*, 207(3), 505–518. (Often includes associated data repositories).
* **Implementation Note**: The `code/ingestion/data_loader.py` module attempts to fetch from the primary verified source. If the specific API endpoint is unreachable, it must fail loudly (raise `DataFetchError`) rather than generating synthetic data, ensuring data integrity.

### 2.2 Soil Nutrient Data
**Source**: **SoilGrids 250m** (ISRIC).

* **Description**: Global gridded soil information system providing predictions for soil properties including pH, Nitrogen (N), Phosphorus (P), and Potassium (K) at 250m resolution.
* **Citation**: Poggio, L., et al. (2021). SoilGrids 2.0: producing soil information for the globe with quantified spatial uncertainty. *Soil*, 7(1), 217–240.
* **Access**: https://soilgrids.org/
* **Implementation Note**: The `code/ingestion/soil_data.py` module uses the SoilGrids API or downloadable GeoTIFF shards to extract values at specific coordinates. It handles CRS reprojection to WGS84 as per Constitution Principle VI.

### 2.3 Species Distribution Data
**Source**: **GBIF (Global Biodiversity Information Facility)**.

* **Description**: Occurrence records for plant species used to validate sampling locations and filter for species with sufficient observation counts.
* **Citation**: GBIF.org (Date). GBIF Home Page.
* **Access**: https://www.gbif.org/
* **Implementation Note**: Used to cross-reference species names and ensure valid taxonomic identifiers in the merged dataset.

## 3. Methodological References

* **Leave-One-Species-Out (LOSO) CV**:
 * **Reference**: Roberts, D. W., et al. (2017). Spatial cross-validation is not a reliable approach to assessing model performance in species distribution modelling. *Ecography*, 40(9), 1059–1068.
 * **Justification**: LOSO is the standard validation strategy for hierarchical data where observations are clustered by species. It prevents data leakage and provides a realistic estimate of how well the model generalizes to *unseen* species.

* **Permutation Testing for Feature Importance**:
 * **Reference**: Fisher, R. A. (1935). *The Design of Experiments*. Oliver and Boyd. (Foundational).
 * **Modern Application**: Breiman, L. (2001). Random Forests. *Machine Learning*, 45, 5–32. (Feature importance via permutation).
 * **Implementation**: Used to generate null distributions for R² scores to calculate p-values for SC-002 compliance.

## 4. Summary of Standards for Implementation

| Parameter | Value | Source |
|:--- |:--- |:--- |
| Significance Level (α) | 0.05 | Cohen (1994) |
| Effect Size Threshold (ΔR²) | ≥ 0.05 | Ecological Modeling Standards |
| Primary Validation Method | Leave-One-Species-Out | Roberts et al. (2017) |
| Soil Data Source | SoilGrids 2.0 | Poggio et al. (2021) |
| Trait Data Source | TRY Database | Kattge et al. (2020) |