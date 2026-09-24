# Data Model: Predicting Polymer Degradation Pathways

## Overview

This document defines the data structures used throughout the project, from raw ingestion to final model output. All data is stored in `data/` and processed in `src/`.

## Entities

### 1. PolymerRecord (Raw/Intermediate)
Represents a single polymer entry before graph conversion.

| Field | Type | Description | Source/Constraint |
| :--- | :--- | :--- | :--- |
| `id` | str | Unique identifier (hash of SMILES + env params) | Generated |
| `smiles` | str | Canonical SMILES string | Verified Dataset |
| `raw_source` | str | URL or source identifier | Verified Dataset |
| `is_polyester` | bool | True if functional group detected | RDKit Filter |
| `temp_c` | float | Temperature in Celsius | Synthetic Default (25.0) |
| `ph` | float | pH level | Synthetic Default (7.0) |
| `uv_exposure` | float | UV intensity (arbitrary units) | Synthetic Default (0.0) |
| `label` | str | Degradation pathway | Synthetic / Curation Flag |
| `label_source` | str | "synthetic" or "curated" | Logic |
| `validation_flag` | str | "valid", "missing_env", "invalid_smiles" | Logic |

### 2. MolecularGraph (Processed)
The graph representation used for GNN input.

| Field | Type | Description |
| :--- | :--- | :--- |
| `node_features` | Tensor [N, F] | Atom features (type, degree, etc.) |
| `edge_index` | Tensor [2, E] | Connectivity matrix |
| `edge_features` | Tensor [E, F] | Bond features (type, conjugation) |
| `global_features` | Tensor [G] | Environmental vector [pH, Temp, UV] |
| `target` | int | Class index (0: Hydrolysis, 1: Oxidation, 2: Photolysis) |
| `augmented_id` | str | ID linking to original record (for tracking) |

### 3. PredictionResult (Output)
Result of the GNN inference on a test sample.

| Field | Type | Description |
| :--- | :--- | :--- |
| `record_id` | str | Original record ID |
| `predicted_class` | str | Predicted degradation pathway |
| `confidence` | float | Softmax probability for predicted class |
| `is_low_confidence` | bool | True if confidence < 0.6 |
| `motif_importance` | Dict | {motif_name: score} |
| `attribution_map` | Tensor | Node-level importance scores |

### 4. StatisticalReport (Final)
Aggregated results for the final report.

| Field | Type | Description |
| :--- | :--- | :--- |
| `metric_name` | str | e. g., "Macro-F1", "χ² p-value" |
| `value` | float | Measured value |
| `confidence_interval` | Tuple | (lower, upper) from CV/LOO |
| `significance` | str | "significant" if p < 0.05 |
| `top_motifs` | List | Ranked list of motifs with correlation strength |

## Data Flow

1.  **Ingestion**: `raw/` (JSONL/CSV) -> `processed/polymer_records.csv` (PolymerRecord).
2.  **Conversion**: `polymer_records.csv` -> `processed/molecular_graphs.pt` (MolecularGraph).
3.  **Augmentation**: `molecular_graphs.pt` -> `processed/augmented_graphs.pt` (2x size).
4.  **Training**: `augmented_graphs.pt` -> `models/gnn_weights.pt` + `logs/training_log.json`.
5.  **Inference**: `processed/test_graphs.pt` -> `results/predictions.json` (PredictionResult).
6.  **Analysis**: `predictions.json` -> `reports/statistical_report.json` (StatisticalReport).

## Constraints & Validation

*   **SMILES Validity**: All SMILES must pass RDKit `MolFromSmiles` check. Invalid entries are logged and excluded.
*   **Label Integrity**: If `label_source` is "synthetic", the record is included in training but flagged in the final report as simulation-based.
*   **Missing Values**: If environmental data is missing, defaults are applied and `validation_flag` is set to "missing_env".
*   **Size Limit**: If `n < 150`, the system automatically switches to LOO validation (FR-009).
