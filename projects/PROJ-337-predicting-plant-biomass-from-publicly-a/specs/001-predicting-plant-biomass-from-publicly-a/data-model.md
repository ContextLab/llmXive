# Data Model: Predicting Plant Biomass from Publicly Available Hyperspectral Imagery

## Entity-Relationship Overview

The data model consists of three core entities: `HyperspectralCube`, `SiteMetadata`, and `ModelResult`. The pipeline transforms raw data into an analysis-ready table and produces model evaluation artifacts.

### Core Entities

#### 1. HyperspectralCube
Represents a spatially indexed set of spectral reflectance values.
-   **Attributes**:
    -   `scene_id` (str): Unique identifier for the scene.
    -   `spectral_bands` (list[float]): Reflectance values for each band (hundreds of bands).
    -   `atmospherically_corrected` (bool): Flag indicating if correction was applied.
    -   `reflectance_range` (tuple[float, float]): Min and max reflectance (expected [0, 1]).
-   **Derived**: `spectral_indices` (e.g., NDVI, EVI) calculated from bands.

#### 2. SiteMetadata
Contains location, environmental context, and ground-truth biomass values.
-   **Attributes**:
    -   `site_id` (str): Unique site identifier.
    -   `location` (dict): Lat, Lon, Elevation.
    -   `biomass` (float): Ground-truth biomass (kg/m² or similar). **Constraint**: Must be derived from independent measurements (field or LiDAR), not spectral data.
    -   `structural_proxy` (float): Canopy height or similar (if available). **Constraint**: Must be derived from LiDAR point clouds, not spectral indices (VIF check required).
    -   `exclusion_reason` (str): Reason for exclusion (e.g., "missing_label", "cloud_cover", "biomass_tautology").
-   **Relationship**: Linked to `HyperspectralCube` via `site_id` or `scene_id`.

#### 3. ModelResult
Stores performance metrics and hyperparameters.
-   **Attributes**:
    -   `model_type` (str): "RandomForest", "TabPFN", "NullBaseline".
    -   `fold` (int): Cross-validation fold index.
    -   `rmse` (float): Root Mean Squared Error.
    -   `mae` (float): Mean Absolute Error.
    -   `r2` (float): Coefficient of Determination.
    -   `hyperparameters` (dict): Model settings (e.g., `n_estimators`, `max_depth`).
    -   `feature_importance` (dict): Mapping of feature names to importance scores.
    -   `p_value` (float): Significance p-value vs. null baseline (corrected using Nadeau & Bengio).
    -   `corrected_p_value` (float): Bonferroni-corrected p-value.

## Data Flow

1.  **Raw Input**: `raw/neon_hyperspectral.zip` (NEON data), `raw/neon_metadata.json`.
2.  **Processed Input**: `processed/corrected_cubes.parquet` (atmospherically corrected).
3.  **Analysis-Ready**: `final/analysis_ready.csv` (merged spectral + metadata, no null biomass, exclusion rate <= 5%).
4.  **Model Output**: `results/model_results.json` (metrics per fold), `results/ablation_summary.json`.
5.  **Sensitivity Output**: `results/sensitivity_sweep.json` (metrics per threshold).
6.  **Runtime Output**: `results/runtime_metrics.json` (total pipeline time).

## Constraints & Validations

-   **Reflectance Range**: All reflectance values must be in [0, 1]. Values outside this range are flagged or corrected.
-   **Missing Data**: Rows with missing biomass are dropped; exclusion rate logged. **Hard Stop**: If >5% dropped, pipeline halts.
-   **Checksums**: All raw files are checksummed before processing.
-   **Memory**: Data loading must handle large files via streaming or chunking.
-   **Provenance**: Biomass labels must be verified as independent of spectral predictors.
-   **Collinearity**: Structural proxies must pass VIF check (< 5) against spectral bands.

## Schema Evolution

-   **v1.0**: Initial schema with spectral bands, biomass, and basic metadata.
-   **v1.1**: Added structural proxies and atmospheric correction flags.
-   **v1.2**: Added feature importance, p-values, and runtime metrics.