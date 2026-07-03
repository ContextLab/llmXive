# Data Model: 001-molecular-reactivity

## Overview

This document defines the data structures used throughout the project, including raw data ingestion, processed features, and model outputs. All data models are designed to be serializable to Parquet/CSV and compatible with the contract schemas.

## Entity Definitions

### 1. ReactionRecord

Represents a single chemical reaction from the raw dataset.

| Attribute | Type | Description | Source |
|-----------|------|-------------|--------|
| `reaction_id` | string | Unique identifier for the reaction. | USPTO ID |
| `smiles_reactants` | string | SMILES string of reactants. | USPTO `reactants` |
| `smiles_products` | string | SMILES string of products. | USPTO `products` |
| `reaction_type` | string | Inferred class: "SN1", "SN2", or "Diels-Alder". | Template Matching |
| `yield_value` | float | Experimental yield (0.0 - 1.0). | USPTO `yield` |
| `context_group` | string | Grouping key for normalization (e.g., "SN1", or "SN1-catalyst-X"). | Derived |
| `normalized_yield` | float | Z-score of yield within `context_group`. | Derived |
| `yield_percentile` | float | Rank of `normalized_yield` within group (0.0-1.0). | Derived |
| `is_success` | boolean | Binary flag: 1 if yield > 0.5, else 0. | Derived |
| `metric_type` | string | "spearman" or "auc_roc" based on degeneracy check. | Derived |
| `status` | string | "valid", "malformed", "excluded". | Processing Log |

**Validation Rules**:
- `smiles_reactants` and `smiles_products` must be valid SMILES (parsed by RDKit).
- `reaction_type` must be one of the three allowed classes or "unknown".
- `yield_value` must be in [0.0, 1.0] or NaN.
- `normalized_yield` must be finite.

### 2. FeatureVector

Represents the numerical encoding of a reaction's reactants.

| Attribute | Type | Description | Derivation |
|-----------|------|-------------|------------|
| `reaction_id` | string | Link to ReactionRecord. | ReactionRecord.id |
| `molecular_weight` | float | Total MW of reactants. | RDKit `CalcExactMolWt` |
| `atom_count` | int | Total number of atoms. | RDKit `GetNumAtoms` |
| `bond_count_single` | int | Number of single bonds. | RDKit `GetNumBonds` (type=1) |
| `bond_count_double` | int | Number of double bonds. | RDKit `GetNumBonds` (type=2) |
| `bond_count_aromatic` | int | Number of aromatic bonds. | RDKit `GetNumBonds` (type=4) |
| `tpsa` | float | Topological Polar Surface Area. | RDKit `CalcTPSA` |
| `logp` | float | Estimated LogP. | RDKit `CalcCrippenDescriptors` |
| `rotatable_bonds` | int | Number of rotatable bonds. | RDKit `CalcNumRotatableBonds` |
| `ring_count` | int | Total number of rings. | RDKit `GetRingInfo` |
| `fingerprint` | list[int] | **Reduced** Morgan fingerprint (100 bits, top features selected by SelectKBest). | RDKit + SelectKBest |

**Validation Rules**:
- All numerical features must be finite (no NaN/Inf).
- `fingerprint` must be a list of **100** integers (0 or 1).

### 3. ModelResult

Represents the output of a single training fold.

| Attribute | Type | Description | Source |
|-----------|------|-------------|--------|
| `fold_id` | int | Cross-validation fold number (0-4). | CV Split |
| `spearman_rho` | float | Spearman correlation for this fold. | Evaluation |
| `auc_roc` | float | AUC-ROC if binary degeneracy triggered. | Evaluation |
| `p_value` | float | P-value from permutation test for this fold. | Evaluation |
| `class_conditional_p_value` | float | P-value from class-conditional permutation. | Evaluation |
| `los_cv_score` | float | Spearman correlation from Leave-One-Scaffold-Out. | Evaluation |
| `training_time` | float | Time taken to train (seconds). | Timer |
| `hyperparams` | dict | JSON string of hyperparameters used. | Config |
| `model_path` | string | Path to saved model artifact. | Filesystem |

**Validation Rules**:
- `spearman_rho` must be in [-1.0, 1.0].
- `p_value` must be in [0.0, 1.0].
- `training_time` must be positive.

## Data Flow

1.  **Ingestion**: Raw USPTO Parquet -> `ReactionRecord` (raw).
2.  **Filtering**: `ReactionRecord` (raw) -> `ReactionRecord` (filtered, by template).
3.  **Normalization**: `ReactionRecord` -> `ReactionRecord` (with `normalized_yield`, `yield_percentile`).
4.  **Feature Extraction**: `ReactionRecord` (filtered) -> `FeatureVector` (Raw 2048-bit fingerprints).
5.  **Dimensionality Reduction**: Raw fingerprints -> **Reduced 100-bit fingerprints** (via SelectKBest).
6.  **Training**: Reduced `FeatureVector` + `normalized_yield` -> `ModelResult`.
7.  **Evaluation**: `ModelResult` -> Aggregated statistics (Spearman ρ, p-value, LOSO score).

## Storage Formats

- **Raw Data**: Parquet (`data/raw/uspto_mit_subset.parquet`).
- **Filtered Data**: Parquet (`data/processed/filtered_reactions.parquet`).
- **Features**: Parquet (`data/processed/features.parquet`) - contains reduced fingerprints.
- **Model Artifacts**: Pickle (`data/models/fold_0.pkl`).
- **Results**: JSON/CSV (`data/results/cv_results.csv`).