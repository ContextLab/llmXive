# Data Model: Identifying Structure-Property Relationships in Polymer Blends

## Entities

### PolymerBlend
Represents a single polymer blend entry.
*   **Attributes**:
    *   `id`: Unique identifier (string).
    *   `components`: List of component objects.
        *   `smiles`: SMILES string (string).
        *   `weight_fraction`: Float (0.0 to 1.0).
    *   `tg_k`: Glass Transition Temperature (Kelvin).
    *   `youngs_modulus_gpa`: Young's Modulus (GPa).
    *   `source`: Origin dataset (string).
    *   `validation_status`: 'valid', 'invalid_units', 'invalid_smiles', 'invalid_composition'.

### MolecularDescriptor
Represents a computed property of a monomer.
*   **Attributes**:
    *   `smiles`: Input SMILES (string).
    *   `mw`: Molecular Weight (float).
    *   `tpsa`: Topological Polar Surface Area (float).
    *   `rotatable_bonds`: Count (int).
    *   `ffv`: Fractional Free Volume (float).
    *   `h_bond_donors`: Count (int).
    *   `h_bond_acceptors`: Count (int).
    *   `logp`: Partition coefficient (float).
    *   *(15+ descriptors total)*.

### InteractionFeature
Represents derived features for a blend.
*   **Attributes**:
    *   `blend_id`: Reference to PolymerBlend.
    *   `weighted_avg_<desc>`: Weighted average of descriptor.
    *   `diff_<desc>`: Absolute difference of descriptor between components.
    *   `fox_tg`: Predicted Tg via Fox equation.
    *   `gordon_taylor_tg`: Predicted Tg via Gordon-Taylor equation.

## Data Flow

1.  **Raw Data** (`data/raw/`): Immutable downloads (CSV/JSON).
2.  **Ingested Data** (`data/processed/harmonized.csv`): Cleaned, unit-converted, validated rows.
3.  **Feature Matrix** (`data/processed/features.parquet`): Pandas DataFrame with descriptors + interaction features.
4.  **Model Artifacts** (`data/artifacts/`): Pickled models, SHAP values, stability reports.

## Constraints

*   **Units**: Tg must be in Kelvin; Modulus in GPa.
*   **Composition**: Sum of weight fractions must be within 1.0 ± 0.02.
*   **SMILES**: Must be parsable by RDKit.
*   **Missing Data**: Rows with missing SMILES for components > 0.05 weight fraction are excluded.
