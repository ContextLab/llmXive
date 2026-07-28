# Data Model: Predicting the Effect of Alloying on the Poisson's Ratio of Aluminum Alloys

## Overview

This document defines the data structures, transformations, and schemas used in the project. The data flow is: `Raw Download` → `Filtered/Normalized` → `ILR-Transformed` → `Model Input`. The model learns the direct mapping from composition to Poisson's ratio without intermediate physical derivations (e.g., VRH bounds) due to missing elemental constants.

## Entity Definitions

### 1. Raw Alloy Record
The raw data structure as downloaded from OpenML.
- `id`: Unique identifier (integer).
- `composition`: Dictionary of element atomic fractions (e.g., `{"Cu": 0.05, "Mg": 0.02, ...}`).
- `poisson_ratio`: Float (unitless).
- `youngs_modulus`: Float (unit: GPa or MPa).
- `source`: String (e.g., "OpenML").
- `measurement_method`: String (e.g., "Ultrasonic", "Derived", "Calculation").

### 2. Cleaned Alloy Record
The record after filtering and unit normalization.
- `alloy_id`: String.
- `cu_frac`: Float (atomic fraction).
- `mg_frac`: Float.
- `si_frac`: Float.
- `zn_frac`: Float.
- `mn_frac`: Float.
- `al_frac`: Float (calculated as `1.0 - sum(other_fractions)`).
- `poisson_ratio`: Float (unitless).
- `youngs_modulus`: Float (normalized to GPa).
- `is_monolithic`: Boolean (true if non-composite).
- `is_independent_measurement`: Boolean (true if `measurement_method` is "Ultrasonic" or similar).
- `data_quality_flag`: String (e.g., "PASS", "MISSING_COMPOSITION", "SUM_MISMATCH", "DERIVED_MEASUREMENT").

### 3. ILR-Transformed Record
The record ready for model training.
- `ilr_1`: Float (First ILR coordinate).
- `ilr_2`: Float.
- `ilr_3`: Float.
- `ilr_4`: Float.
- `ilr_5`: Float (Optional, depending on the number of components).
- `poisson_ratio`: Float (Target).

## Data Flow Diagram

```mermaid
graph TD
    A[Raw Data Download (OpenML 42347)] --> B{Filter: Monolithic?}
    B -- No --> C[Exclude]
    B -- Yes --> D{Check: Missing Values?}
    D -- Yes --> C
    D -- No --> E{Check: Sum of Fractions?}
    E -- < 0.95 --> C
    E -- >= 0.95 --> F{Check: Independence?}
    F -- Not Independent (Derived) --> C
    F -- Independent --> G[Normalize Units: GPa]
    G --> H[Calculate Al Balance]
    H --> I[ILR Transformation]
    I --> J[Train/Test Split]
    J --> K[Model Training]
    K --> L[Physical Sanity Check]
```

## Transformation Logic

### Unit Normalization
- If `youngs_modulus` unit is "MPa", divide by 1000.
- If `poisson_ratio` is not unitless (rare), flag error.

### Compositional Balance
- Ensure `sum(Cu, Mg, Si, Zn, Mn) >= 0.95`.
- If sum < 0.95, exclude the record (per spec).
- Calculate `Al_frac = 1.0 - (Cu + Mg + Si + Zn + Mn)`.

### Independence Check
- Filter records where `measurement_method` is NOT "Ultrasonic" or "Independent".
- This ensures Poisson's ratio is not derived solely from Young's modulus (FR-009).

### ILR Transformation
- Input: Vector `x = [Cu, Mg, Si, Zn, Mn, Al]`.
- Method: Isometric Log-Ratio (ILR) using a sequential binary partition or standard orthonormal basis.
- Output: `z = ilr(x)`.
- Implementation: Use `compositional` library or `scikit-bio` (if available) or custom implementation.

### Physical Sanity Check
- Validate that predicted Poisson's ratio values fall within the theoretical range for isotropic materials (0.0 <= nu <= 0.5).
- Flag any predictions outside this range for review.
- Note: This is a post-hoc validation, not a derivation from missing elemental constants.

## Schema Validation

The implementation will validate data against the schemas defined in `contracts/`.