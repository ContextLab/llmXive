# Data Model: Predicting Plant Drought Tolerance from RSA Data

## 1. Entity-Relationship Overview

The data model consists of three primary entities: `RootImage` (from MGB3), `RSAMetrics` (derived), and `PhysioTrait` (from TRY). These are merged into a single analysis table `StudyData`.

### Entities

1.  **RootImage** (Source: MGB3)
    *   `image_id`: Unique identifier for the image or sample.
    *   `species_name`: Scientific name of the plant.
    *   `raw_path`: Path to the raw image file.

2.  **RSAMetrics** (Derived: Depth, Branching, Surface Area)
    *   `metric_id`: Unique identifier.
    *   `image_id`: Foreign key to `RootImage`.
    *   `depth`: Maximum vertical extent (mm).
    *   `branching_density`: Number of branches per unit length.
    *   `surface_area`: Total surface area (mm²).
    *   `total_length`: Total root length (mm).

3.  **PhysioTrait** (Source: TRY)
    *   `trait_id`: Unique identifier.
    *   `species_name`: Scientific name (Foreign key to `RSAMetrics` via species).
    *   `stomatal_conductance`: Value (mmol m⁻² s⁻¹).
    *   `photosynthetic_rate`: Value (µmol m⁻² s⁻¹).
    *   `condition`: "stressed" or "optimal" (if available).

4.  **StudyData** (Merged Analysis Table)
    *   `sample_id`: Unique identifier for the merged row.
    *   `species_name`: String.
    *   `depth`: Float.
    *   `branching_density`: Float.
    *   `surface_area`: Float.
    *   `stomatal_conductance`: Float (Target 1).
    *   `photosynthetic_rate`: Float (Target 2).
    *   `drought_class`: **NULL** (Classification step FR-007/FR-008 is dropped).

## 2. Data Flow

1.  **Ingestion**: Raw MGB3 images -> `RSAMetrics` table (via OpenCV pipeline).
2.  **Enrichment**: `RSAMetrics` + `PhysioTrait` (via `species_name`) -> `StudyData`.
3.  **Preprocessing**:
    *   Missing values: Listwise deletion or mean imputation (documented).
    *   Collinearity Check: Calculate VIF. If > 5, apply Ridge/Lasso (or conditional PCA).
    *   Normalization: Standardize predictors for Ridge/Lasso and LMM.
4.  **Modeling**: `StudyData` -> `ModelResult` (Ridge/Lasso, LMM).

## 3. Schema Definitions

### Input Schema (MGB3 Images)
- `image_id`: string
- `species_name`: string
- `image_path`: string

### Input Schema (TRY CSV)
- `species_name`: string
- `stomatal_conductance`: float
- `photosynthetic_rate`: float
- `condition`: string (optional)

### Output Schema (Model Results)
- `model_type`: string ("Ridge", "Lasso", "LMM")
- `target_variable`: string
- `r_squared`: float
- `p_value`: float
- `coefficients`: dict
- `vif_scores`: dict
- `random_effects_variance`: float (for LMM)
