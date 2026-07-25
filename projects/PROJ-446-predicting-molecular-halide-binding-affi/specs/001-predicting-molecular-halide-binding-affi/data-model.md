# Data Model: Predicting Molecular Halide Binding Affinities

## Overview

This document defines the data structures used in the pipeline. It ensures that the implementation adheres to the schema constraints defined in `contracts/` and supports the statistical requirements of the study.

## Entity Definitions

### 1. HostMolecule
Represents the organic host compound.
- **Attributes**:
  - `host_id`: Unique string identifier (e.g., "HOST_001").
  - `smiles`: Canonical SMILES string.
  - `inchi`: InChI string (optional, for verification).
  - `source`: "NIST", "PubChem", or "Simulated".

### 2. BindingMeasurement
Represents a single experimental or simulated binding event.
- **Attributes**:
  - `measurement_id`: Unique string.
  - `host_id`: Foreign key to `HostMolecule`.
  - `halide_identity`: One of "F-", "Cl-", "Br-", "I-".
  - `binding_constant`: Float (log K or ΔG).
  - `solvent`: One of "acetonitrile", "chloroform", "dichloromethane".
  - `reference_doi`: String (or "SIMULATED" if simulated).

### 3. ModelRun
Represents a trained model instance and its performance.
- **Attributes**:
  - `run_id`: Unique string.
  - `model_type`: "random_forest" or "gradient_boosting".
  - `fold_metrics`: List of dicts (fold index, R², RMSE).
  - `metrics_mean`: Dict (R²_mean, RMSE_mean).
  - `metrics_std`: Dict (R²_std, RMSE_std).
  - `feature_stability`: List of dicts (feature_name, CV, is_stable).
  - `data_mode`: "Real" or "Simulated".

## Data Flow

1. **Raw Input**: Scraped HTML or Simulated Generator Output.
2. **Processed CSV**: `data/processed/halide_binding_data.csv` (Wide format: one row per measurement).
   - Columns: `host_id`, `smiles`, `halide_identity`, `binding_constant`, `solvent`, `charge_density`, `cavity_volume`, `ecfp_0`, `ecfp_1`, ...
3. **Model Output**: `data/processed/model_runs.json` (Aggregated metrics).
4. **Feature Output**: `data/processed/feature_analysis.json` (Stability and interpretation).

## Schema Constraints

- **Data Types**: All floats must be standard IEEE 754. SMILES must be valid RDKit parsable strings.
- **Constraints**:
  - `halide_identity` MUST be in ["F-", "Cl-", "Br-", "I-"].
  - `solvent` MUST be in ["acetonitrile", "chloroform", "dichloromethane"].
  - `binding_constant` MUST be numeric.
- **Missing Data**: No nulls allowed in `host_id`, `smiles`, or `binding_constant`.
