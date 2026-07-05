# Data Model: Predicting Molecular Diffusion Coefficients in Liquids with Graph Neural Networks

## 1. Overview

This document defines the data structures used throughout the pipeline, from raw ingestion to model prediction. The data model is designed to be immutable at the raw level and derived at the processed level, adhering to the project's Data Hygiene principle.

## 2. Raw Data Schema

**Source**: NIST TRC Database (via `thermo` Python library).
**Format**: CSV (exported from `thermo` query).
**File**: `data/raw/diffusion_data.csv`

| Column | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `smiles` | String | SMILES string of the solute. | Valid RDKit SMILES; no missing values. |
| `solvent` | String | Solvent name or ID. | Must map to known descriptors. |
| `diffusion_coeff` | Float | Experimental diffusion coefficient ($cm^2/s$). | Must be > 0. |
| `viscosity` | Float | Solvent viscosity (cP). | Required for featurization. |
| `dielectric` | Float | Solvent dielectric constant. | Required for featurization. |

**Handling Missing Data**:
If any of the above columns are missing or invalid for a row, the row is excluded and logged with `[MISSING_DATA_EXCLUDED]`.

## 3. Processed Data Schema (Featurized)

**Source**: `ingestion.py`
**Format**: JSONL (JSON Lines)
**File**: `data/processed/featurized_data.jsonl`

Each line is a JSON object representing a single molecule-solvent pair.

```json
{
  "id": "unique_record_id",
  "smiles": "CCO",
  "solvent": "water",
  "target": 2.3e-5,
  "solvent_descriptors": {
    "viscosity": 0.89,
    "dielectric": 78.4
  },
  "graph": {
    "node_features": [[6, 1, 0, 0], [6, 1, 0, 0], [8, 1, 0, 0]],
    "edge_index": [[0, 1], [1, 0], [1, 2], [2, 1]],
    "edge_features": [[1, 0, 0], [1, 0, 0], [1, 0, 0], [1, 0, 0]]
  },
  "fingerprint": [0, 1, 0, ..., 0] 
}
```

**Fields**:
*   `node_features`: List of atom features (Atomic Number, Degree, Hybridization, Formal Charge).
*   `edge_index`: COO format for edges (source, target).
*   `edge_features`: Bond type, conjugation, stereo.
*   `fingerprint`: Morgan fingerprint bit vector (2048 bits) for baseline.

## 4. Model Artifacts

**Source**: `train.py`
**Format**: `.pt` (PyTorch state dict)
**File**: `code/models/{model_name}_fold_{k}.pt`

| Model | Description |
| :--- | :--- |
| `mpnn_fold_{k}.pt` | Trained MPNN weights for fold $k$. |
| `baseline1_fold_{k}.pt` | Trained Linear Regression (Fingerprint+Solvent) coefficients for fold $k$. |
| `baseline2_fold_{k}.pt` | Trained Linear Regression (Solvent-Only) coefficients for fold $k$. |

## 5. Output Schema (Results)

**Source**: `eval.py`, `sensitivity.py`
**Format**: JSON
**File**: `docs/reports/results.json`

```json
{
  "experiment_id": "exp_001",
  "date": "2026-06-26",
  "metrics": {
    "gnn": {
      "pearson_r": 0.75,
      "rmse": 0.05,
      "fold_scores": [0.72, 0.78, 0.74, 0.76, 0.73]
    },
    "baseline1": {
      "pearson_r": 0.65,
      "rmse": 0.08,
      "fold_scores": [0.62, 0.68, 0.64, 0.66, 0.63]
    },
    "baseline2": {
      "pearson_r": 0.60,
      "rmse": 0.09,
      "fold_scores": [0.58, 0.62, 0.59, 0.61, 0.60]
    }
  },
  "statistical_test": {
    "test_type": "Wilcoxon Signed-Rank",
    "comparisons": [
      {
        "model_a": "GNN",
        "model_b": "Baseline1",
        "p_value": 0.001,
        "significant": true
      },
      {
        "model_a": "GNN",
        "model_b": "Baseline2",
        "p_value": 0.002,
        "significant": true
      }
    ]
  },
  "sensitivity": {
    "message_passing_steps": {
      "1": {"r": 0.70, "rmse": 0.06},
      "2": {"r": 0.75, "rmse": 0.05},
      "3": {"r": 0.74, "rmse": 0.05}
    },
    "ablation_no_solvent": {
      "r": 0.55,
      "rmse": 0.12
    }
  }
}
```

## 6. Data Flow Diagram

```mermaid
graph TD
    A[NIST TRC via thermo] -->|Ingestion| B[Featurized JSONL]
    B -->|Train| C[MPNN Model]
    B -->|Train| D[Linear Baseline 1 (FP+Solvent)]
    B -->|Train| E[Linear Baseline 2 (Solvent-Only)]
    C -->|Eval| F[Results JSON]
    D -->|Eval| F
    E -->|Eval| F
    F -->|Sensitivity| G[Sensitivity Report]
```