# Data Model: Machine-Learned Potentials for Transition-Metal Catalysis

## Overview

This document defines the data structures used for ingesting, processing, and analyzing transition-state graphs and prediction results. All data flows through the `data/` directory, with raw data preserved and derived data versioned.

## Core Entities

### 1. TransitionStateGraph
Represents a chemical reaction transition state as a graph.

**Schema**:
```yaml
nodes:
  - atomic_number: integer  # Z of the atom
  - formal_charge: integer  # Derived or from input
  - coordination_number: integer # Derived from geometry
  - element_symbol: string  # Derived from Z
edges:
  - source_node: integer    # Index of source atom
  - target_node: integer    # Index of target atom
  - distance: float         # Euclidean distance (Å)
  - edge_type: string       # "bond" or "non-bond" (based on cutoff)
metadata:
  - reaction_id: string     # Unique identifier
  - metal_center: string    # "Pd", "Ni", or "Cu"
  - ligand_class: string    # "Group13" or "Conventional" (Derived from atomic composition: presence of B, Al, Ga donor atoms)
  - energy_dft: float       # Reference DFT energy (kcal/mol or eV)
  - barrier_height: float   # Reference barrier height (from dataset)
```

### 2. PredictionResult
Stores the output of a single GNN model inference.

**Schema**:
```yaml
reaction_id: string
energy_ml: float            # Predicted energy
error: float                # energy_ml - energy_dft
ligand_class: string        # "Group13" or "Conventional"
timestamp: string           # ISO 8601
```

### 3. EnsemblePredictionResult
Stores the aggregated output of the 5-model ensemble.

**Schema**:
```yaml
reaction_id: string
mean_energy: float          # Average of 5 predictions
variance: float             # Variance of 5 predictions (uncertainty)
individual_predictions:     # List of 5 floats
  - float
error: float
```

### 4. FeatureImportance
Maps structural descriptors to their contribution to error.

**Schema**:
```yaml
reaction_id: string
descriptor_name: string     # e.g., "M-L_bond_length", "Coordination_Number"
importance_score: float     # SHAP/IG value (applied to error residuals)
variance_explained: float   # Percentage of total error variance
```

### 5. StatisticalTestResult
Stores results of hypothesis tests.

**Schema**:
```yaml
test_type: string           # "unpaired_welch_t_test" or "mann_whitney_u"
group_a: string             # "Group13"
group_b: string             # "Conventional"
statistic: float
p_value: float
significant: boolean        # p < 0.05
```

## Data Flow

1.  **Ingestion**: Raw Parquet files (`data/raw/`) → Filtered/Graphs (`data/processed/graphs.parquet`).
    *   *Ligand Derivation*: `ligand_class` is derived from atomic composition during this step (presence of B, Al, Ga donor atoms).
2.  **Training**: Graphs → Model Weights (`models/`).
3.  **Inference**: Graphs + Weights → `data/processed/predictions.parquet`.
4.  **Analysis**: Predictions → `data/results/feature_importance.csv`, `data/results/statistical_tests.json`.

## Constraints

*   **Immutability**: Raw data in `data/raw/` is never modified.
*   **Checksums**: All files in `data/` must have a corresponding SHA-256 hash in `state/`.
*   **Formats**: Parquet for tabular data; JSON/CSV for results; Pickle/PT for models (versioned).
*   **Split Strategy**: 5-Fold Leave-Ligand-Scaffold-Out (LLSO) is used for validation to ensure generalization to new chemical spaces.
