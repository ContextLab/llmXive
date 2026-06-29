# Data Model: Evaluating the Correlation Between Compositional Features and Predicted Formation Energy

## Entities

### 1. Compound
Represents a single inorganic material entry.
- **ID**: `material_id` (string, e.g., "mp-1234")
- **Formula**: `composition` (string, e.g., "SiO2")
- **Formation Energy**: `formation_energy_per_atom` (float, eV/atom)
- **Crystal System**: `crystal_system` (string, e.g., "cubic", "tetragonal")
- **Chemical Family**: `chemical_family` (string, e.g., "Fe", "Si" - most abundant element)
- **Descriptors**:
  - `mean_electronegativity` (float)
  - `var_electronegativity` (float)
  - `mean_atomic_radius` (float)
  - `var_atomic_radius` (float)
  - `mean_valence_electrons` (float)
  - `var_valence_electrons` (float)
  - `mean_melting_point` (float)
  - `var_melting_point` (float)
  - `mean_ionization_energy` (float)
  - `var_ionization_energy` (float)

### 2. ModelOutput
Stores the result of a training run.
- **Model Type**: `model_name` (string: "RandomForest" or "GradientBoosting")
- **Metrics**:
  - `r2_score` (float)
  - `mae` (float)
  - `rmse` (float)
  - `train_r2` (float)
  - `null_model_r2` (float) - Baseline from shuffled properties
- **Feature Importance**: List of `{feature: str, importance: float}`.
- **Permutation Importance**: List of `{feature: str, importance: float, std: float}`.
- **VIF Scores**: List of `{feature: str, vif: float}`.

### 3. PDPData
Stores data for Partial Dependence Plots.
- **Feature**: `feature_name` (string)
- **Feature Values**: `values` (list of floats)
- **Predicted Energy**: `predictions` (list of floats)
- **Standard Deviation**: `std` (list of floats)

## Data Flow

1. **Raw Ingestion**: `data/raw/mp-2020.12.1.parquet` -> Filtered -> `data/processed/compounds_clean.csv`
2. **Descriptor Computation**: `compounds_clean.csv` -> `data/processed/compounds_descriptors.csv`
3. **Model Training**: `compounds_descriptors.csv` (Split) -> `data/evaluation/model_metrics.json`
4. **Analysis**: `model_metrics.json` -> `data/evaluation/pdp_data.json`

## Constraints

- **Missing Values**: Rows with missing `formation_energy_per_atom` or missing elemental properties are excluded.
- **Outliers**: Formation energy values outside the 1st-99th percentile are capped before training.
- **Determinism**: All random seeds are fixed (e.g., `random_state=42`).
- **Single Source of Truth**: `data/evaluation/model_metrics.json` is the sole authoritative source for all metrics. Logs and stdout are for debugging only.
