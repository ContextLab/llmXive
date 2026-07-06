# Data Model: Predicting Molecular Diffusion Coefficients

## 1. Overview

This document defines the data structures used in the pipeline, from raw input to model artifacts. All data transformations are immutable; new files are created for each derived version.

## 2. Raw Data Schema

**Source**: CSV or Parquet file (User provided or verified dataset).
**Constraints**: Must contain `smiles`, `solvent_type`, `diffusion_coefficient`.

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| `smiles` | string | SMILES string of the solute molecule. | Yes |
| `solvent_type` | string | Name of the solvent (e.g., "Water", "Ethanol"). | Yes |
| `diffusion_coefficient` | float | Experimental diffusion coefficient (units: cm²/s or m²/s). | Yes |
| `temperature` | float (optional) | Temperature in Kelvin. | No |

## 3. Featurized Data Schema (Processed)

**Output Format**: JSONL (one record per molecule-solvent pair).
**Generation**: `code/featurization.py`.

| Field | Type | Description |
|-------|------|-------------|
| `record_id` | string | Unique hash of the record. |
| `smiles` | string | Original SMILES. |
| `solvent_type` | string | Original solvent name. |
| `target` | float | Normalized diffusion coefficient (log10). |
| `graph` | object | PyTorch Geometric Data object serialized to JSON. |
| `graph.node_features` | list of lists | Atom features: [atomic_num, hybridization, formal_charge]. |
| `graph.edge_index` | list of lists | Bond connections: [source_idx, target_idx]. |
| `graph.edge_features` | list of lists | Bond features: [bond_type, is_aromatic]. |
| `solvent_features` | object | Scalar descriptors. |
| `solvent_features.viscosity` | float | Viscosity in cP. |
| `solvent_features.dielectric` | float | Dielectric constant. |
| `status` | string | "valid" or "excluded". |
| `exclusion_reason` | string (nullable) | e.g., "MISSING_DATA_EXCLUDED", "INVALID_SMILES". |

## 4. Model Artifact Schema

**Output Format**: Pickle (`.pt` or `.pkl`).
**Generation**: `code/training.py`.

| Field | Type | Description |
|-------|------|-------------|
| `model_type` | string | "mpnn" or "linear_baseline". |
| `architecture` | dict | Hyperparameters used (layers, hidden_dim, etc.). |
| `state_dict` | dict | PyTorch state dictionary. |
| `scaler` | object | Scikit-learn scaler used for target normalization. |
| `training_config` | dict | Seed, epochs, fold number. |
| `metrics` | dict | Validation RMSE, Pearson r. |

## 5. Result Report Schema

**Output Format**: JSON.
**Generation**: `code/evaluation.py`.

| Field | Type | Description |
|-------|------|-------------|
| `experiment_id` | string | Unique run ID. |
| `dataset_stats` | dict | Total rows, excluded rows, valid rows. |
| `fold_results` | list of dict | Metrics for each CV fold. |
| `fold_results[].fold_id` | int | Fold number (0-4). |
| `fold_results[].gnn_rmse` | float | GNN RMSE. |
| `fold_results[].gnn_r` | float | GNN Pearson r. |
| `fold_results[].baseline_rmse` | float | Baseline RMSE. |
| `fold_results[].baseline_r` | float | Baseline Pearson r. |
| `aggregated` | dict | Mean and std of metrics across folds. |
| `statistical_test` | dict | Paired t-test results. |
| `statistical_test.p_value` | float | P-value. |
| `statistical_test.significant` | bool | True if p < 0.05. |
| `sensitivity_analysis` | list | Results of hyperparameter sweeps. |
| `ablation_study` | dict | Results without solvent descriptors. |
