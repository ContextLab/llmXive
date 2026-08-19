# Research Background: Predicting Plant Root Architecture from Soil Nutrient Profiles

## Overview

This project investigates the relationship between soil nutrient profiles (Nitrogen, Phosphorus, Potassium, pH) and plant root architecture traits (Maximum Depth, Root Biomass). The goal is to determine if soil chemistry alone can predict root traits, and if adding species identity significantly improves predictive power.

## Data Sources

### 1. Soil Nutrient Data (SoilGrids)
- **Source**: ISRIC SoilGrids (Global Soil Information System)
- **Access**: Programmatic access via `rasterio` and `requests` to download soil property rasters.
- **Variables**:
 - `N`: Total Nitrogen (g/kg)
 - `P`: Available Phosphorus (mg/kg)
 - `K`: Exchangeable Potassium (cmol/kg)
 - `pH`: Soil pH (H2O)
- **Resolution**: 250m global resolution.
- **Processing**: Rasters are reprojected to WGS84 (EPSG:4326) before extracting values at specific sample coordinates.

### 2. Root Trait Data
- **Source**: Published datasets from Zenodo/Dryad (e.g., "Global Root Trait Database" or similar curated repositories).
- **Variables**:
 - `Max_Depth`: Maximum rooting depth (cm)
 - `Root_Biomass`: Root biomass per unit area (g/m²)
 - `Species`: Taxonomic name of the plant species
 - `Latitude`, `Longitude`: Geographic coordinates of the sample site
- **Filtering**: Only physically plausible values are retained (Depth > 0, pH 3.0-9.0).

## Methodology

### 1. Data Ingestion & Geospatial Alignment
- **Challenge**: Soil data is raster-based; trait data is point-based.
- **Solution**: Use `rasterio` to extract pixel values at trait coordinates. Ensure CRS alignment (WGS84) to avoid spatial misregistration.
- **Quality Control**: Rows with missing soil data or invalid coordinates are excluded. A strict match proportion threshold (≥0.90) is enforced to ensure data integrity.

### 2. Predictive Modeling
- **Algorithm**: Random Forest Regressor (Scikit-Learn).
- **Models**:
 - **Model A (Soil-Only)**: Predicts traits using only N, P, K, pH.
 - **Model B (Soil+Species)**: Predicts traits using N, P, K, pH + Species (One-Hot Encoded).
- **Validation**:
 - **Stratified 5-Fold CV**: Ensures balanced representation of species across folds.
 - **Leave-One-Species-Out (LOSO)**: Tests generalizability to unseen species.
- **Baseline**: Mean-prediction model (predicting the mean of the training fold) is used to calculate R² gain.

### 3. Statistical Significance & Constitution Principles
- **Permutation Tests**:
 - For Model A: Permute target variable to establish null distribution.
 - For Model B: Permute soil features stratified by species to test if species adds unique signal.
- **Constitution Principle 002 (SC-002)**:
 - **Criterion**: ΔR² (Model B - Model A) ≥ 0.05 AND p-value < 0.05.
 - **Interpretation**: If passed, species identity provides significant predictive power beyond soil chemistry alone.
- **Association vs. Causation**: All findings are framed as associational (FR-006). We do not claim soil nutrients *cause* specific root architectures, but that they are predictive indicators.

### 4. Sensitivity Analysis
- **Goal**: Validate robustness of feature importance rankings.
- **Method**: Sweep p-value thresholds (0.01 to 0.10) and track stability of top-3 features.
- **Standard**: Significance level justification is based on community standards in ecological modeling (typically α = 0.05).

## Key Findings (Expected)

- **Soil Predictability**: Soil nutrients alone (Model A) may explain a moderate portion of root trait variance (R² ~ 0.2-0.4).
- **Species Effect**: Adding species identity (Model B) is expected to significantly improve predictions (ΔR² > 0.05), confirming that genetic/phylogenetic factors are critical.
- **Feature Importance**: pH and Nitrogen are likely the most influential soil predictors.
- **Robustness**: Top features should remain stable across a range of p-value thresholds, indicating robust signals.

## Limitations

- **Spatial Resolution**: 250m soil rasters may not capture micro-scale heterogeneity relevant to root growth.
- **Data Availability**: Trait data is often sparse in certain biomes, potentially biasing the model.
- **Correlation**: The models identify associations, not causal mechanisms. Experimental validation is required for causal claims.

## References

1. Hengl, T., et al. (2017). SoilGrids250m: Global gridded soil information based on machine learning. *PLOS ONE*.
2. Kattge, J., et al. (2020). TRY plant trait database – enhanced coverage and open access. *Global Change Biology*.
3. Breiman, L. (2001). Random Forests. *Machine Learning*.
4. O'Hara, R. B., & Kotze, D. J. (2010). Do not log-transform count data. *Methods in Ecology and Evolution*.
5. **Community Standard**: The significance threshold of α = 0.05 is adopted from standard ecological and agricultural research practices (e.g., *Ecological Applications*, *Journal of Ecology*).