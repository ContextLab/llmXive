# Data Model: Molecular Topology and Reaction Selectivity

## 1. Overview

This document defines the data structures used throughout the pipeline. All data is stored in `data/` with checksums recorded in the project state.

## 2. Core Entities

### 2.1 ReactionRecord
Represents a single chemical reaction.
- **source**: `data/raw/uspto_50k.parquet` (or jsonl)
- **derived**: `data/processed/eas_filtered.csv`

| Field | Type | Description |
| :--- | :--- | :--- |
| `reaction_id` | string | Unique identifier (hash of reactants+products). |
| `reactant_smiles` | string | SMILES string of the reactant molecule. |
| `product_smiles` | string | SMILES string(s) of the product molecule(s). |
| `eas_confirmed` | boolean | True if reaction matches EAS pattern. |
| `selectivity_target` | integer | **Theoretical Regioisomer Count** (derived from reactant symmetry). |
| `topology_valid` | boolean | True if all descriptors calculated successfully. |

### 2.2 TopologicalDescriptor
Stores computed graph indices.
- **source**: `data/processed/eas_filtered.csv`
- **derived**: `data/processed/descriptors.parquet`

| Field | Type | Description |
| :--- | :--- | :--- |
| `reaction_id` | string | Foreign key to ReactionRecord. |
| `wiener_index` | float | Wiener index value. |
| `balaban_index` | float | Balaban index value. |
| `zagreb_index` | float | Zagreb index value. |
| `calculation_status` | string | "OK", "INVALID_GRAPH", "TIMEOUT". |

### 2.3 ModelResult
Stores model outputs and metrics.
- **source**: `code/modeling.py`
- **derived**: `data/models/results.json`

| Field | Type | Description |
| :--- | :--- | :--- |
| `model_type` | string | "Ordinal", "RandomForest", "Poisson" (baseline only). |
| `cv_strategy` | string | "5-fold", "LOO". |
| `r_squared` | float | R² or Pseudo-R². |
| `rmse` | float | Root Mean Squared Error. |
| `coefficients` | object | Map of feature name to coefficient. |
| `p_values` | object | Map of feature name to p-value. |
| `vif_scores` | object | Variance Inflation Factors. |
| `fallback_triggered` | boolean | True if fallback model was used (always False for this project). |
| `halt_reason` | string | "Insufficient Variance" if halted due to constant target. |

## 3. Data Flow

1.  **Ingestion**: Raw USPTO -> `ReactionRecord` (filtered EAS).
2.  **Descriptor Calculation**: `ReactionRecord` -> `TopologicalDescriptor`.
3.  **Target Derivation**: `ReactionRecord` (reactant SMILES) -> `selectivity_target` (symmetry count).
4.  **Modeling**: `TopologicalDescriptor` + `selectivity_target` -> `ModelResult`.

## 4. Constraints

- **Missing Data**: SMILES parsing errors -> log error, exclude row.
- **Invalid Topology**: Descriptor failure -> flag row, exclude from regression.
- **Degenerate Target**: Variance=0 -> halt with "Insufficient Variance".