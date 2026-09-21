# Data Model: Predicting Crystal Structures from Molecular Fingerprints

## Overview

This document defines the data structures, schemas, and relationships used in the project. It ensures that the implementation adheres to the project's data hygiene and reproducibility principles.

## Entity Definitions

### 1. MoleculeRecord
Represents a single chemical entry derived from the COD. **Note**: Each unique (SMILES, Space Group) pair is a distinct record.

| Field | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `cod_id` | string | Unique identifier from COD (e.g., "1500001") | CIF `_database_code` |
| `smiles` | string | Canonical SMILES string | `pybel` conversion |
| `space_group` | string | The specific space group for this record (training label) | CIF `_symmetry_space_group_name_H-M` |
| `lattice_volume` | float | Volume of the unit cell (Å³) | Calculated from lattice parameters |
| `fingerprint` | list[int] | 2048-bit ECFP4 vector (0/1) | `rdkit` generation |
| `is_polymorph` | bool | True if this SMILES has multiple space groups in the dataset | Derived (count by SMILES) |
| `polymorph_count` | int | Number of unique space groups for this SMILES | Derived |
| `scaffold_id` | string | Bemis-Murcko scaffold identifier | `rdkit` extraction |
| `atom_count` | int | Total number of atoms | Derived from SMILES |
| `molecular_weight` | float | Molecular weight (g/mol) | Derived from SMILES |
| `metal_ratio` | float | Ratio of metal atoms to total atoms | Derived (filter logic) |
| `organic_flag` | bool | True if molecule has C-H-O-N-S-P backbone (allows Na, K, Cl, etc.) | Derived (filter logic) |

**Filtering Logic**: 
- **Organic**: Must contain C, H, O, N, S, or P. 
- **Allowed Counter-ions**: Na, K, Cl, Br, I, F, Mg, Ca are allowed if the backbone exists. 
- **Excluded**: Pure inorganic salts (no C-H backbone) or >20% metal content by atom count.

### 2. ModelMetrics
Represents the evaluation results for a specific model run.

| Field | Type | Description |
| :--- | :--- | :--- |
| `model_type` | string | "RandomForest", "GradientBoosting", "Ridge" |
| `task` | string | "space_group_classification", "lattice_volume_regression" |
| `accuracy` | float | Accuracy (for classification) |
| `macro_f1` | float | Macro-averaged F1 score (for classification) |
| `top_k_accuracy` | float | Top-K Accuracy (K=5) for classification |
| `prediction_entropy` | float | Average entropy of prediction for polymorphic cases |
| `r_squared` | float | R-squared (for regression) |
| `mae` | float | Mean Absolute Error (for regression) |
| `baseline_accuracy` | float | Accuracy of majority-class baseline |
| `baseline_r2_mw` | float | R-squared of Molecular Weight baseline for volume |
| `run_id` | string | Unique hash of the run configuration |

### 3. FeatureImportance
Represents the mapping between a fingerprint bit and its predictive power.

| Field | Type | Description |
| :--- | :--- | :--- |
| `bit_index` | int | Index in the 2048-bit vector (0-2047) |
| `importance_score` | float | Permutation importance or SHAP value |
| `substructure_smiles` | string | Representative substructure (SMARTS/SMILES) |
| `collision_count` | int | Number of unique substructures mapping to this bit |
| `is_ambiguous` | bool | True if `collision_count` > 1 |

## Data Flow

1.  **Raw Data**: COD CIF files (compressed or uncompressed).
2.  **Processed Data**: `data/processed/crystal_molecules.parquet` containing `MoleculeRecord` fields.
3.  **Model Input**: `MoleculeRecord` (fingerprint + scaffold_id) split into train/test.
4.  **Model Output**: `ModelMetrics` JSON and `FeatureImportance` CSV.

## Constraints & Validations

- **SMILES Validity**: Must be parseable by `rdkit`. If not, the record is dropped.
- **Fingerprint Length**: Must be exactly 2048 bits.
- **Space Group**: Must be a valid Hermann-Mauguin symbol.
- **Lattice Volume**: Must be > 0.
- **Scaffold Uniqueness**: The `scaffold_id` must be unique per scaffold, but can appear multiple times in the dataset (across different molecules).
- **Distinct Samples**: Each (SMILES, Space Group) pair is a distinct record.