# Data Model: Predicting Alloy Phase Diagrams from Compositional Data

## Entities

### 1. AlloyComposition
Represents a specific mixture of elements.
*   `composition_id`: Unique identifier (e.g., "Cu-Al-0.5-0.5").
*   `elements`: List of elemental symbols (e.g., ["Cu", "Al"]).
*   `fractions`: List of atomic fractions (e.g., [0.5, 0.5]).
*   `system`: Alloy system name (e.g., "Cu-Al").
*   `descriptors`: Dictionary of derived features.
    *   `mean_atomic_radius`: Float (Angstroms).
    *   `electronegativity_variance`: Float.
    *   `valence_electron_count`: Float.

### 2. PhaseBoundary
Represents a point on the phase diagram.
*   `boundary_id`: Unique identifier.
*   `composition_id`: Foreign key to `AlloyComposition`.
*   `temperature`: Float (Kelvin) - **CALPHAD-assessed**.
*   `phase_type`: String (e.g., "Liquidus", "Solidus").
*   `source`: String (e.g., "Materials Project API").

### 3. ModelMetrics
Stores performance results.
*   `fold_id`: Integer (LOSO fold index).
*   `system_held_out`: String (Name of the system excluded in this fold).
*   `mae`: Float (Mean Absolute Error).
*   `r2`: Float (R-squared score).
*   `null_model_mae`: Float (Baseline MAE for comparison).
*   `error_flags`: List of strings (e.g., ["LOW_DATA_DENSITY", "HIGH_VARIANCE"]).
*   `std_dev_error`: Float (Standard deviation of prediction error for the system).

### 4. VisualConsistencyMetrics
Stores visual fidelity results (replaces IoU).
*   `system`: String (Name of the alloy system).
*   `vcs_score`: Float (Visual Consistency Score, based on MAE of boundary lines).
*   `max_error`: Float (Maximum error in the reconstructed boundary).
*   `notes`: String (e.g., "Primary lines only for Fe-C").

## Data Flow

1.  **Raw Ingestion**: API Response (JSON) → `data/raw/materials_project_raw.jsonl`.
2.  **Cleaning**: Filter `MISSING_TEMP_COORDS` → `data/raw/cleaned.jsonl`.
3.  **Feature Engineering**: Calculate descriptors → `data/processed/alloy_features.csv`.
4.  **Training**: `alloy_features.csv` → `data/results/model.pkl` + `data/results/metrics.json`.
5.  **Visualization**: `model.pkl` + `alloy_features.csv` → `data/results/plots/{system}.png` + `data/results/visual_metrics.json`.

## Assumptions

*   The Materials Project API returns consistent JSON structures for phase boundaries.
*   Elemental properties are static and can be hardcoded or loaded from a standard library.
*   The "system" is defined by the unique pair/triple of elements (e.g., "Cu-Al" is distinct from "Al-Cu").
*   The target variable is CALPHAD-assessed temperature, not experimental temperature.
*   `LOW_DATA_DENSITY` is triggered if sample size < 5 OR standard deviation of prediction error > 0.5.