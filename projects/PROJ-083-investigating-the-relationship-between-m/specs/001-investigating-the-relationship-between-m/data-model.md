# Data Model: Investigating the Relationship Between Molecular Topology and Reaction Selectivity

## Overview

This document defines the data structures, schemas, and transformations used in the pipeline. All data is stored in `data/` with checksums.

## Entities

### 1. ReactionRecord
Represents a single chemical reaction from the USPTO-50k dataset.

**Fields**:
- `reaction_id`: Unique identifier (string).
- `reactant_smiles`: SMILES string of the reactant (string).
- `reaction_type`: Inferred type (e.g., "EAS") (string).
- `theoretical_regioisomer_count`: Integer count of distinct possible regioisomers derived via template enumeration (int).
- `is_valid`: Boolean flag for data quality (bool).
- `distribution_status`: String indicating the distribution check result (e.g., "normal", "degenerate", "zero-inflated") (string).

**Source**: Raw USPTO-50k dataset.
**Transformation**: Filtered for EAS, parsed, validated, and enumerated.

### 2. TopologicalDescriptor
Computed graph properties for a reactant molecule.

**Fields**:
- `reaction_id`: Foreign key to ReactionRecord (string).
- `wiener_index`: Wiener index value (float).
- `balaban_index`: Balaban index value (float).
- `zagreb_index`: Zagreb index value (float).
- `calculation_status`: "success", "invalid_topology", "failed" (string).

**Source**: `rdkit` calculations on `reactant_smiles`.
**Transformation**: Calculated in `descriptors.py`.

### 3. ModelResult
Output of the statistical analysis.

**Fields**:
- `model_type`: "Poisson", "ZeroInflatedPoisson", "RandomForest", or "BinaryClassifier" (string).
- `r_squared`: Coefficient of determination (float).
- `rmse`: Root Mean Square Error (float).
- `p_values`: Dictionary of p-values for each predictor (dict).
- `vif_scores`: Dictionary of Variance Inflation Factor scores for predictors (dict).
- `cross_validation_folds`: Number of folds used (int).
- `distribution_check`: Description of target distribution (e.g., "degenerate", "normal", "zero-inflated") (string).
- `deviation_from_linearity`: Metric quantifying non-linearity in the structural correlation (float).

**Source**: `modeling.py`.
**Transformation**: Aggregated from cross-validation runs.

## Data Flow

1.  **Raw**: `data/raw/uspto-50k.parquet` (Downloaded, checksummed).
2.  **Filtered**: `data/processed/eas_reactions.csv` (Filtered EAS subset).
3.  **Enriched**: `data/processed/descriptors.csv` (Joined with topological indices and theoretical counts).
4.  **Results**: `data/processed/model_results.json` (Aggregated metrics).

## Constraints

- **SMILES Validity**: All SMILES must be valid according to `rdkit`.
- **Index Range**: Indices must be non-negative floats.
- **Count Range**: `theoretical_regioisomer_count` must be a positive integer (≥ 1).
- **Distribution Status**: Must be one of ["normal", "degenerate", "zero-inflated"].
