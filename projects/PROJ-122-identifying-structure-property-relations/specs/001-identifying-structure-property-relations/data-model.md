# Data Model: Identifying Structure-Property Relationships in Polymer Blends

## Entities

### 1. PolymerBlend
Represents a single blend entry.
*   `id`: Unique identifier (UUID or hash).
*   `components`: List of `Component` objects.
*   `measured_tg_k`: Glass transition temperature in Kelvin (Target).
*   `measured_modulus_gpa`: Young's Modulus in GPa (Target).
*   `source`: Origin of data (e.g., "NIST", "MaterialsProject").
*   `validation_status`: "PASS" or "FAIL" (based on weight fraction and SMILES checks).
*   `data_quality_flag`: Boolean indicating if the record passed all validation checks.

### 2. Component
Represents a constituent polymer in a blend.
*   `smiles`: SMILES string.
*   `weight_fraction`: Float (0.0 - 1.0).
*   `is_minor`: Boolean (True if weight fraction < 0.05).

### 3. MolecularDescriptor
Computed properties for a monomer/component.
*   `molecular_weight`: Float.
*   `tpsa`: Topological Polar Surface Area (Float).
*   `rotatable_bonds`: Integer.
*   `fractional_free_volume`: Float.
*   `hansen_solubility`: Tuple (D, P, H).
*   `count`: Total number of descriptors (Must be $\ge 15$).

### 4. InteractionFeature
Derived features for the blend (Baselines).
*   `predicted_tg_fox`: Float (Fox Equation).
*   `predicted_tg_gordon_taylor`: Float.
*   `vif_scores`: Dict of descriptor names to VIF values.

## Data Flow

1.  **Raw Ingest**: Fetch from APIs/CSVs -> `data/raw/`.
2.  **Validation**: Check units, SMILES, weight fractions -> `data/processed/cleaned.csv`.
3.  **Feature Gen**: Apply RDKit -> `data/features/descriptors.csv`.
4.  **Baseline Calc**: Compute Fox/GT equations -> `data/features/baselines.csv`.
5.  **Model Input**: Final feature matrix (X) and targets (y).

## Constraints & Rules

*   **Unit Constraint**: All temperatures MUST be in Kelvin. All moduli MUST be in GPa.
*   **Physical Bounds**: Predicted Tg > 0 K; Predicted Modulus >= 0 GPa.
*   **Missing Data**: If SMILES is missing for any component with $w > 0.05$, the row is excluded.
*   **Collinearity**: VIF > 5.0 triggers sensitivity analysis (no auto-exclusion).
*   **Data Quality**: Records failing validation are excluded; the exclusion rate is tracked for SC-004.
*   **No Synthetic Data**: No target variables (Tg, Modulus) will be synthesized or simulated.