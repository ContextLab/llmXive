# Data Model: Predicting Molecular Halide Binding Affinities with Machine Learning

## Entity Definitions

### HostMolecule
Represents an organic host compound.
- `host_id`: Unique identifier (hash of SMILES).
- `smiles`: Canonical SMILES string (required).
- `inchi`: InChI string (optional, for validation).
- `descriptors`: Dictionary of RDKit descriptors (charge_density, cavity_volume, hbd_count, etc.).
- `ecfp4`: Binary vector (1024 bits) representing ECFP4 fingerprint.

### BindingMeasurement
Represents a single experimental measurement.
- `measurement_id`: Unique identifier.
- `host_id`: Foreign key to `HostMolecule`.
- `halide_identity`: Enum {F⁻, Cl⁻, Br⁻, I⁻}.
- `binding_constant`: Float (log K or ΔG in kcal/mol).
- `units`: Enum {log_K, kcal_mol}.
- `solvent`: Enum {acetonitrile, chloroform, dichloromethane}.
- `source`: Enum {NIST, PubChem, Simulated}.
- `reference_doi`: DOI of the source publication (if available).

### ModelRun
Represents a trained model instance.
- `run_id`: Unique identifier.
- `model_type`: Enum {random_forest, gradient_boosting}.
- `cross_validation_folds`: Integer (5).
- `r2_mean`: Float.
- `r2_std`: Float.
- `rmse_mean`: Float.
- `rmse_std`: Float.
- `feature_stability_ranking`: List of (feature_name, cv_score).

## Data Flow

1. **Ingestion**: Raw data downloaded from NIST/PubChem (or simulated) → `data/raw/`.
2. **Cleaning**: Filter by solvent, halide identity, valid SMILES → `data/processed/cleaned.csv`.
3. **Feature Engineering**: Generate descriptors, ECFP4 → `data/processed/features.csv`.
4. **Model Training**: Split by host_id → train RF/GB → `data/processed/models/`.
5. **Analysis**: Feature stability, PDPs, bootstrap CIs → `data/processed/results/`.

## Constraints & Validation

- **Solvent Filter**: Only acetonitrile, chloroform, DCM allowed.
- **Halide Filter**: Only F⁻, Cl⁻, Br⁻, I⁻ allowed.
- **Host Filter**: Retain only hosts with ≥3 halide measurements.
- **SMILES Validation**: Exclude records with invalid SMILES (RDKit parsing failure).
- **Unit Standardization**: Convert ΔG to log K if necessary; exclude ambiguous units.
- **Duplicate Handling**: If duplicate host-halide pairs exist, aggregate by taking the **mean binding constant** and logging the variance. The split strategy groups by (host_id, halide_identity) to ensure no intra-host variance leaks between train/test sets.

## Simulated Data Schema (FR-011)

If real data is insufficient:
- `log K_sim = 0.5 * charge_density + 0.3 * cavity_volume + N(0, 0.2)`
- `charge_density`: Sum of Gasteiger charges (computed from SMILES).
- `cavity_volume`: Molecular volume (Å³) via RDKit.
- `halide_identity`: Assigned based on most abundant halide in available data (or simulated uniformly).
- `source`: "Simulated".
- **Note**: This formula is hardcoded. In this mode, the model's recovery of coefficients is a trivial verification of the generation script, not an empirical discovery. **Comparative analysis is strictly prohibited.**

## File Formats

- **CSV**: `host_id, smiles, halide_identity, binding_constant, solvent, source`
- **Parquet**: For large descriptor matrices (ECFP4).
- **YAML**: Model metadata, configuration.

## Data Integrity

- **Checksums**: All raw data files checksummed (SHA-256) and recorded in `state.yaml`.
- **Versioning**: Each processed file includes a timestamp and source hash.
- **Audit Trail**: Logs of excluded records (invalid SMILES, wrong solvent, etc.) maintained.
