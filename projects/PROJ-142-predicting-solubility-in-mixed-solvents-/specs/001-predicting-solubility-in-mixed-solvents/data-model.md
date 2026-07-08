# Data Model: Predicting Solubility in Mixed Solvents

## 1. Domain Entities

### SolubilityRecord
Represents a single experimental measurement.
*   **Attributes**:
    *   `record_id`: Unique identifier (UUID or hash).
    *   `solute_smiles`: String (SMILES representation).
    *   `solute_mw`: Float (Molecular Weight, Da).
    *   `solvent_ids`: List of Strings (Solvent identifiers, e.g., "Water", "Ethanol").
    *   `mole_fractions`: List of Floats (Composition, sum ≈ 1.0).
    *   `experimental_logS`: Float (Target variable).
    *   `source_dataset`: String (e.g., "EPA", "MoleculeNet").
    *   `raw_row_id`: String (Original row ID from source).

### MolecularDescriptor
Computed features for a molecule.
*   **Attributes**:
    *   `solute_smiles`: String (Primary key for linkage).
    *   `morgan_fingerprint`: BitVector (2048 bits, sparse or dense array).
    *   `topological_indices`: Dict (MW, LogP, TPSA, HBA, HBD).
    *   `calculated_at`: Timestamp.

### InteractionTerm
Derived feature capturing non-linear mixing.
*   **Attributes**:
    *   `term_name`: String (e.g., "LogP_SolventPolarity_Product").
    *   `parent_descriptors`: List of Strings (e.g., ["solute_LogP", "mix_polarity"]).
    *   `operation`: String (e.g., "product", "ratio", "polynomial").
    *   `value`: Float (Computed value for a specific record).

## 2. Data Flow

1.  **Raw Ingestion**: `data/raw/` (CSV files).
2.  **Cleaning**: `data/processed/cleaned_solubility.csv` (Filtered, imputed).
3.  **Feature Engineering**: `data/processed/features_enriched.csv` (Descriptors + Interaction Terms).
4.  **Model Input**: `data/processed/model_input.parquet` (Final matrix for training).
5.  **Artifacts**: `artifacts/models/`, `artifacts/shap_plots/`.

## 3. Schema Definitions

### Processed Dataset Schema
The final dataset used for training.
*   **Columns**:
    *   `solute_smiles`: String (Not null).
    *   `solute_mw`: Float (Not null).
    *   `solute_logP`: Float (Not null).
    *   `solute_tpsa`: Float (Not null).
    *   `mix_polarity`: Float (Composition-weighted).
    *   `mix_dielectric`: Float (Composition-weighted).
    *   `interaction_logP_polarity`: Float (Product).
    *   `experimental_logS`: Float (Target, Not null).
    *   `source`: String.
*   **Constraints**:
    *   `mole_fractions` sum must be within 0.99-1.01.
    *   No null values in feature columns (imputed or dropped).

## 4. Constraints & Validation

*   **MW Filter**: All records must have `solute_mw < 500`.
*   **Composition**: Sum of `mole_fractions` must be 1.0 (tolerance 0.01).
*   **Imputation**: If KNN imputation is used, a flag `is_imputed` is added to the record.
*   **Memory**: Peak usage must not exceed 7 GB (enforced in code).