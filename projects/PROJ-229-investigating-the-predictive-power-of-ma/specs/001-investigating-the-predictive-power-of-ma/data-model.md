# Data Model: Investigating the Predictive Power of Machine Learning for Identifying Novel Phase-Change Materials

## Entity Definitions

### MaterialCompound

Represents a chemical compound with attributes for elemental composition, crystal structure, and thermodynamic properties.

- **mp_id**: `string` - Unique identifier from Materials Project.
- **formula**: `string` - Chemical formula (e.g., "H2O").
- **melting_point**: `float` - Melting point in Kelvin.
- **heat_capacity**: `float` - Heat capacity at constant pressure (J/mol·K).
- **latent_heat**: `float` - Latent heat of fusion (J/mol). May be null if imputed or unavailable.
- **structure**: `object` - Crystal structure data (e.g., lattice parameters, fractional coordinates).
- **elemental_descriptors**: `object` - Dictionary of computed elemental properties (e.g., atomic_number, electronegativity, radius).
- **structural_descriptors**: `object` - Dictionary of computed structural properties (e.g., bond_lengths, coordination_numbers, symmetry).

### DescriptorSet

A collection of computed features for a set of compounds.

- **compound_ids**: `list[string]` - List of MP IDs.
- **features**: `list[list[float]]` - 2D array of feature values (rows = compounds, columns = features).
- **feature_names**: `list[string]` - Names of the features.
- **target**: `string` - Name of the target variable (e.g., "latent_heat", "melting_point").

### ModelResult

Contains the trained model parameters, performance metrics, and derived rules.

- **model_type**: `string` - Type of model (e.g., "RandomForest", "PySR", "Lasso").
- **performance_metrics**: `object` - Dictionary of metrics (e.g., R², MSE, Spearman correlation).
- **feature_importance**: `object` - Dictionary of feature importance scores (for tree-based models).
- **symbolic_formula**: `string` - Explicit mathematical formula (for PySR or Lasso).
- **shap_values**: `array` - SHAP values for feature attribution.

### TargetDecision

Contains the decision on the target variable based on the consistency check.

- **selected_target**: `string` - The selected target variable ("latent_heat" or "melting_point").
- **correlation_value**: `float` - The Pearson correlation between melting_point and latent_heat (if available).
- **fallback_reason**: `string` - Reason for fallback (if applicable).

### CollinearityReport

Contains the results of the collinearity check.

- **flagged_dependencies**: `list[string]` - List of flagged dependency pairs.
- **adjusted_interpretation**: `string` - The adjusted interpretation text.

### FeasibilityReport

Contains the results of the feasibility check.

- **total_time**: `float` - Total time taken in seconds.
- **max_memory**: `float` - Maximum memory used in GB.
- **within_constraints**: `boolean` - Whether the constraints were met.

## Data Flow

1.  **Raw Data**: `data/raw/mp_raw.csv` (from MP API), `data/raw/nist_latent_heat.csv` (if available), `data/raw/literature_pcms.csv` (if available).
2.  **Processed Data**: `data/processed/features.csv` (elemental + structural descriptors), `data/processed/targets.csv` (melting point, latent heat).
3.  **Results**: `data/results/model_metrics.json`, `data/results/symbolic_formula.json`, `data/results/validation_results.json`, `data/results/target_decision.json`, `data/results/collinearity_report.json`, `data/results/feasibility_report.json`.

## Data Constraints

- **Memory**: Raw and processed data must fit within 7 GB RAM. Streaming or sampling will be used if necessary.
- **Disk**: Total data size must not exceed 14 GB. Intermediate files will be cleaned up.
- **Numerical Stability**: All computed features must be checked for `nan`/`inf`. Invalid values will be logged and handled.

## Schema Evolution

- **Version 1.0**: Initial schema for MP data retrieval and feature extraction.
- **Version 1.1**: Added support for NIST latent heat data and literature PCM validation.
- **Version 1.2**: Added collinearity checks, sensitivity analysis outputs, and feasibility reports.
- **Version 1.3**: Added target decision and fallback logic.