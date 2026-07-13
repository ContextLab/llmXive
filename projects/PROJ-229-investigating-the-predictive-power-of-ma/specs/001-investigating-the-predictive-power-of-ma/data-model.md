# Data Model: Investigating the Predictive Power of Machine Learning for Identifying Novel Phase-Change Materials

## Entity Definitions

### MaterialCompound
Represents a chemical compound with attributes for elemental composition, crystal structure, and thermodynamic properties.

**Attributes**:
- `mp_id`: Unique identifier (string).
- `formula`: Chemical formula (string).
- `melting_point`: Melting point in Kelvin (float, nullable).
- `heat_capacity`: Heat capacity in J/(mol·K) (float, nullable).
- `latent_heat`: Latent heat of fusion in J/mol (float, nullable).
- `structure`: Crystal structure representation (object/graph).
- `source`: Data source (string: "materials_project" or "literature").

### DescriptorSet
A collection of computed features including elemental properties and structural representations.

**Attributes**:
- `mp_id`: Foreign key to `MaterialCompound`.
- `atomic_number_mean`: Mean atomic number of constituent elements (float).
- `electronegativity_mean`: Mean electronegativity (float).
- `atomic_radius_mean`: Mean atomic radius (float).
- `graph_features`: Vector of graph-based descriptors (array of floats).
- `symmetry_features`: Vector of symmetry-based descriptors (array of floats).

### ModelResult
Contains the trained model parameters, performance metrics, and derived rules.

**Attributes**:
- `model_id`: Unique identifier (string).
- `model_type`: Type of model (string: "random_forest", "gradient_boosting", "symbolic_regression").
- `r2_score`: R² score on validation set (float).
- `feature_importance`: Dictionary of feature importance (object).
- `symbolic_formula`: Explicit mathematical formula (string, nullable).
- `shap_values`: SHAP values for interpretation (array of floats, nullable).

## Data Flow

1.  **Raw Data**: Fetched from Materials Project API (`raw_materials.json`).
2.  **Cleaned Data**: Filtered for non-null melting points (`cleaned_materials.csv`).
3.  **Features**: Computed descriptors (`features.csv`).
4.  **Models**: Trained models and metrics (`model_results.json`).
5.  **Validation**: External validation results (`validation_results.csv`).

## Schema Constraints

- **Uniqueness**: `mp_id` must be unique in `MaterialCompound`.
- **Non-Null**: `formula`, `mp_id`, `melting_point` (for training) must be non-null.
- **Range**: `melting_point` > 0, `heat_capacity` > 0.
- **Integrity**: `DescriptorSet.mp_id` must exist in `MaterialCompound`.
