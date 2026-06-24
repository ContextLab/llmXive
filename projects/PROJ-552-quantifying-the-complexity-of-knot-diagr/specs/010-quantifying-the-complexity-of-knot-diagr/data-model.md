# Data Model: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

**Feature Branch**: `001-knot-complexity-analysis`  
**Date**: 2026-06-12  

## Entity Definitions

### KnotRecord

Represents a single prime knot with attributes including crossing number, braid index, alternating classification, and hyperbolic volume.

**Attributes**:
- `knot_id`: String (e.g., "8_19")
- `crossing_number`: Integer
- `braid_index`: Integer (nullable)
- `hyperbolic_volume`: Float (nullable, > 0 for hyperbolic)
- `is_alternating`: Boolean (nullable)
- `data_quality_flags`: List[String] (e.g., "missing_braid_index", "volume_zero")
- `missing_invariant_flags`: List[String] (e.g., "no_representation_available")
- `source`: String ("knot_atlas")
- `checksum`: String (SHA-256 of raw record)

### InvariantsDataset

Aggregated collection of `KnotRecord` entities with computed relationships and metadata.

**File Path**: `data/processed/cleaned_knots.parquet`  
**Schema**: Validated against `contracts/knot_record.schema.yaml`

### RegressionModel

Represents fitted model with attributes including model type, coefficients, goodness-of-fit metrics, and training/validation split information.

**Attributes**:
- `model_type`: String ("linear", "polynomial", "logarithmic")
- `predictors`: List[String]
- `target`: String
- `coefficients`: Dict[String, Float]
- `r_squared`: Float
- `aic`: Float
- `bic`: Float
- `mae`: Float

**File Path**: `data/processed/regression_results.json`

## Data Hygiene & Transformations

All data transformations follow Constitution Principle III (Data Hygiene):

1.  **Raw Data**: `data/raw/knot_atlas_raw.json` (immutable, checksummed).
2.  **Derived Data**: `data/processed/cleaned_knots.parquet` (new file, no in-place modification).
3.  **Checksums**: SHA-256 recorded in `data/` directory manifest.
4.  **Logs**: Timestamped logs stored in `docs/reproducibility/`.

## File Paths

| Artifact | Path | Description |
|----------|------|-------------|
| Raw Data | `data/raw/knot_atlas_raw.json` | Unmodified download from Knot Atlas |
| Cleaned Data | `data/processed/cleaned_knots.parquet` | Validated, filtered, cleaned dataset |
| Plots | `data/plots/crossing_vs_braid.png` | Exploratory scatter plots |
| Reproducibility | `docs/reproducibility/` | Checksums, logs, derivation notes |
