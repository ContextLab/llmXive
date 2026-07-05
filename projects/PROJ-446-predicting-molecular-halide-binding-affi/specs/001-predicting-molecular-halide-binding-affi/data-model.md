# Data Model: Predicting Molecular Halide Binding Affinities with Machine Learning

## 1. Overview

This document defines the data structures, schemas, and relationships for the project. All data artifacts must adhere to these contracts to ensure reproducibility and validation.

## 2. Core Entities

### 2.1 HostMolecule
Represents a unique organic host compound.

| Attribute | Type | Description | Constraints |
|-----------|------|-------------|-------------|
| `host_id` | String | Unique identifier (e.g., hash of SMILES) | Primary Key, Unique |
| `smiles` | String | Canonical SMILES string | Not Null, Valid RDKit parse |
| `inchi` | String | IUPAC InChI string | Nullable |
| `molecular_weight` | Float | Calculated molecular weight | > 0 |
| `logp` | Float | Partition coefficient (XLogP) | Nullable |
| `hbd_count` | Integer | Hydrogen bond donor count | ≥ 0 |
| `hba_count` | Integer | Hydrogen bond acceptor count | ≥ 0 |
| `ecfp4` | Array[Int] | ECFP4 fingerprint vector | Length=2048 |

### 2.2 BindingMeasurement
Represents a single experimental binding event.

| Attribute | Type | Description | Constraints |
|-----------|------|-------------|-------------|
| `measurement_id` | String | Unique ID | Primary Key |
| `host_id` | String | Foreign Key to HostMolecule | Not Null |
| `halide_identity` | Enum | F-, Cl-, Br-, I- | Not Null |
| `binding_constant` | Float | log K value | Not Null |
| `units` | String | "logK" or "kcal/mol" | Not Null |
| `solvent` | String | Solvent name | Not Null |
| `source` | Enum | "NIST", "PubChem", "Simulated" | Not Null |
| `reference_doi` | String | Source DOI | Nullable |

### 2.3 ModelRun
Represents a trained model instance and its results.

| Attribute | Type | Description | Constraints |
|-----------|------|-------------|-------------|
| `run_id` | String | Unique ID | Primary Key |
| `model_type` | Enum | "RandomForest", "GradientBoosting" | Not Null |
| `host_split_seed` | Integer | Random seed for splitting | Not Null |
| `cv_folds` | Integer | Number of folds | 5 |
| `r2_mean` | Float | Mean R² across folds | [-∞, 1] |
| `r2_std` | Float | Std dev of R² | ≥ 0 |
| `rmse_mean` | Float | Mean RMSE | ≥ 0 |
| `rmse_std` | Float | Std dev of RMSE | ≥ 0 |
| `feature_importance` | JSON | Ranked list of features | Not Null |

## 3. Data Flow

1. **Raw Data**: Downloaded to `data/raw/` (checksummed).
2. **Ingestion**: `data_ingestion.py` parses raw files, validates SMILES, and outputs `data/processed/raw_binding_data.csv`. **If simulated**, validates against `dataset.schema.yaml` before writing.
3. **Filtering**: `feature_engineering.py` filters for ≥3 halides/host and non-aqueous solvents, outputs `data/processed/filtered_dataset.csv`.
4. **Feature Generation**: Adds ECFP4 and descriptors, outputs `data/processed/feature_matrix.parquet`.
5. **Modeling**: `model_training.py` reads feature matrix, performs CV, outputs `data/processed/model_results.json`.
6. **Analysis**: `analysis.py` generates statistical reports and plots.

## 4. Constraints & Invariants

- **Invariant 1**: A `host_id` must appear in at most one fold of any cross-validation split.
- **Invariant 2**: All `binding_constant` values must be standardized to `log K` before modeling.
- **Invariant 3**: If `source` is "Simulated", a warning flag is set in the metadata.
- **Invariant 4**: No PII or sensitive data is present in any dataset.
- **Invariant 5**: Simulated data must be generated using the physics-based model defined in `research.md` Section 2.2.