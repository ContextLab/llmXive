# Data Model: Predicting Adsorption Isotherm Parameters

## Entities & Relationships

### Adsorbate
*Represents the gas molecule being adsorbed.*
- `molecule_id` (PK): Unique identifier.
- `smiles`: Canonical SMILES string.
- `molecular_weight` (float): g/mol.
- `polarizability` (float): Å³.
- `van_der_waals_volume` (float): Å³.
- `polar_surface_area` (float): Å².
- `h_bond_donors` (int).
- `h_bond_acceptors` (int).

### Adsorbent
*Represents the porous material.*
- `material_id` (PK): Unique identifier (e.g., MOF-1000 ID).
- `surface_area` (float): m²/g.
- `pore_volume` (float): cm³/g.
- `crystal_structure`: String.

### IsothermRecord
*Links adsorbate and adsorbent; contains target parameters.*
- `record_id` (PK).
- `molecule_id` (FK).
- `material_id` (FK).
- `isotherm_type`: String (e.g., "Type I").
- `langmuir_capacity` (float): mmol/g (Target).
- `henry_constant` (float): mmol/g/bar (Target).
- `freundlich_exponent` (float).

## Data Flow

1.  **Raw Input**: CSV/Parquet with `smiles`, `material_id`, `K_H`, `Q_max`.
2.  **Filter**: `isotherm_type == "Type I"` AND `K_H` NOT NULL AND `Q_max` NOT NULL.
3.  **Enrich**: Join with `molecule_id` to compute RDKit descriptors.
4.  **Normalize**: Convert units (e.g., cm²/g -> m²/g).
5.  **Split**: Group by `material_id` -> Train ([deferred]), Test ([deferred]).
6.  **Model Input (Full)**: Feature matrix (X) = [Descriptors, Adsorbent Properties]. Target (y) = `langmuir_capacity`.
7.  **Model Input (Reduced)**: Feature matrix (X') = [Top 3 Descriptors from SHAP]. Target (y) = `langmuir_capacity`.
8.  **Output**: Predictions, SHAP values, P-values, Reduced Model Metrics.

## Schema Definitions

See `contracts/dataset.schema.yaml` and `contracts/model_output.schema.yaml` for machine-readable schemas.

## Key Artifacts

- `data/processed/cleaned_adsorption.csv`: The primary dataset after filtering and descriptor calculation.
- `data/models/best_full_model.pkl`: The best-performing model on the full feature set.
- `data/models/best_reduced_model.pkl`: The best-performing model on the Top 3 features (SC-003).
- `data/reports/feature_importance.json`: SHAP values and p-values.
- `data/benchmarks/runtime_log.json`: Execution timing and status.