# Data Model: Predicting the Yield Strength of High-Entropy Alloys via Compositional Descriptors

## Entity Definitions

This document defines the data structures, schemas, and transformations for the HEA yield strength prediction pipeline. All data flows from `data/raw/` (immutable) to `data/processed/` (derived) and finally to `output/`.

## Entity Definitions

### HEA Composition
Represents a single high-entropy alloy entry.
- **Attributes**:
  - `composition`: Dict mapping element symbols to atomic fractions (e.g., `{"Cr": 0.2, "Fe": 0.2, ...}`).
  - `yield_strength_mpa`: Float (normalized to MPa).
  - `phase`: String (e.g., "BCC", "FCC", "Single-phase").
  - `testing_temp_c`: Float (must be 20-25°C).
  - `source`: String (dataset origin).

### Descriptor Set
Computed features per alloy.
- **Attributes**:
  - `delta`: Float (Atomic size mismatch).
  - `delta_chi`: Float (Electronegativity variance).
  - `vec`: Float (Valence electron concentration).
  - `mixing_entropy`: Float.
  - `delta_tm`: Float (Melting temperature variance).
  - `yield_strength_mpa`: Float (Target).

## Data Flow

1.  **Raw Input**: Downloaded Parquet/CSV from open repository.
2.  **Cleaning**:
    - Filter: `phase == "Single-phase"` AND `20 <= testing_temp_c <= 25`.
    - Filter: Remove rows with missing `yield_strength_mpa` or missing elemental properties.
    - Normalize: Convert all yield strength to MPa.
3.  **Transformation**:
    - Calculate descriptors (δ, Δχ, VEC, etc.) using fixed elemental tables.
    - Handle missing elemental properties: Exclude composition.
4.  **Output**:
    - `data/processed/final_dataset.csv`: Cleaned data with descriptors.
    - `output/metrics.json`: Model performance results.

## Schema Constraints

- **Yield Strength**: Must be > 0.
- **Composition**: Sum of atomic fractions must be ≈ 1.0 (within tolerance 1e-5).
- **Descriptors**: Must be finite (no NaN/Inf).
- **Phase**: Must be "Single-phase" for the final analysis set.

## Error Handling

- **Missing Data**: If N=0 after filtering, exit with code 0 and report N=0.
- **Unit Mismatch**: Log conversion factor if non-MPa units detected.
- **Collinearity**: If VIF > 10, flag descriptor and apply regularization (linear only).
