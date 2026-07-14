# Data Model: 001-predict-root-architecture

## Overview

This document defines the data structures used throughout the pipeline, from ingestion to final reporting. All data is processed in Pandas DataFrames, serialized to Parquet for efficiency, and validated against the schemas defined in `contracts/`.

## Entity Definitions

### 1. RawRootPhenotype
Represents the raw ingestion from PlantPheno or RootReader.
*   **Source**: `data/raw/plantpheno_raw.parquet` (or txt converted)
*   **Attributes**:
    *   `species` (string): Plant species name.
    *   `root_length` (float): Total root length (cm).
    *   `branching_density` (float): Branches per cm.
    *   `surface_area` (float): Total surface area (cm²).
    *   `geographic_location` (string): "lat,lon" or "lat;lon".
    *   `data_source_type` (string): "observational" or "experimental".
    *   `experimental_id` (string): Unique study identifier.

### 2. RawSoilNutrient
Represents raw soil data (ISRIC or local).
*   **Source**: `data/raw/isric_raw.csv`
*   **Attributes**:
    *   `latitude` (float): Decimal degrees.
    *   `longitude` (float): Decimal degrees.
    *   `phosphorus_concentration` (float): mg/kg.
    *   `nitrogen_concentration` (float): mg/kg.
    *   `depth` (float): Soil depth in cm.
    *   `measurement_date` (date): YYYY-MM-DD.

### 3. MergedDataset (Processed)
The cleaned, joined, and transformed dataset ready for modeling.
*   **Source**: `data/processed/merged_root_soil.parquet`
*   **Attributes**:
    *   `species` (category): Categorical species.
    *   `root_length_log` (float): Log-transformed root length.
    *   `branching_density_log` (float): Log-transformed branching density.
    *   `surface_area_log` (float): Log-transformed surface area.
    *   `phosphorus_z` (float): Z-score normalized P.
    *   `nitrogen_z` (float): Z-score normalized N.
    *   `latitude` (float): Geographic latitude (fixed effect).
    *   `longitude` (float): Geographic longitude (fixed effect).
    *   `sample_count` (int): Number of observations for this species.
    *   `exclusion_reason` (string): "n<20", "missing_nutrient", "experimental", or null.

### 4. ModelOutput
Serialized results from the modeling phase.
*   **Source**: `artifacts/models/lmm_results.json`
*   **Attributes**:
    *   `model_type` (string): "LMM" or "RandomForest".
    *   `adj_r2` (float): Adjusted R-squared.
    *   `rmse` (float): Root Mean Squared Error.
    *   `coefficients` (dict): Map of predictor to coefficient.
    *   `p_values` (dict): Map of predictor to Bonferroni-corrected p-values.
    *   `cv_r2_mean` (float): Mean R² from 5-fold CV.
    *   `cv_coeff_stability` (float): Standard deviation of nutrient coefficients across folds.
    *   `lrt_p_value` (float): P-value from Likelihood Ratio Test (Full vs Null).
    *   `collinearity_vif` (dict): VIF for predictors.
    *   `association_only` (boolean): Flag indicating no causal claims are made.
    *   `literature_overlap` (boolean): True if 95% CI overlaps with literature range.

## Data Flow Diagram

```mermaid
graph TD
    A[Raw PlantPheno] -->|Ingest & Parse| B(RawRootPhenotype)
    C[Raw ISRIC/Local] -->|Ingest & Parse| D(RawSoilNutrient)
    B -->|Filter: n>=20, observational| E[Filtered Roots]
    D -->|Filter: valid coords| F[Filtered Soils]
    E -->|Join: Geo Nearest Neighbor (10km)| G[Merged Raw]
    G -->|Impute (KNN k=5, Predictor-Only, Fit-Apply)| H[Imputed Data]
    H -->|Transform: Log Roots, Z Nutrients| I[MergedDataset]
    I -->|Split: By Species| J[Train/Val/Test]
    J -->|LMM | K[ModelOutput]
    J -->|RF | L[ModelOutput]
    K -->|Plot | M[Visualization]
    L -->|Plot | M
    M -->|Report | N[Final Report]
```

## Transformation Rules

1.  **Filtering**:
    *   Exclude `data_source_type == "experimental"` (FR-012).
    *   Exclude species with count < 20 (FR-001).
    *   Exclude rows where P or N is missing (FR-001).
2.  **Imputation**:
    *   **Predictor-Only**: KNN (k=5, Euclidean) uses only `phosphorus`, `nitrogen`, `latitude`, `longitude`. **Excludes** root metrics.
    *   **Fit-Apply**: Imputer fitted on Training fold only, applied to all folds.
    *   **Fallback**: If no neighbors in training set, exclude sample from evaluation (no mean imputation).
3.  **Transformation**:
    *   `log(x + 1e-6)` for root metrics (FR-003, Const. VII).
    *   `(x - mean) / std` for nutrients (FR-003, Const. VII).
4.  **Splitting**:
    *   Group by `species`.
    *   Shuffle species list.
    *   Assign 5 folds.
    *   No row-level mixing.