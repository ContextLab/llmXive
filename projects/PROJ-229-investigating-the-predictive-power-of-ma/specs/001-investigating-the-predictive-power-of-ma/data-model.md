# Data Model: Investigating the Predictive Power of Machine Learning for Identifying Novel Phase-Change Materials

## Overview

This document defines the data structures, schemas, and relationships used in the project. It ensures that all data artifacts are consistent, reproducible, and traceable.

## Entity Definitions

### MaterialCompound
- **Description**: Represents a chemical compound with attributes for elemental composition, crystal structure, melting point, and latent heat (if available).
- **Attributes**:
  - `material_id`: Unique identifier (string).
  - `formula`: Chemical formula (string).
  - `melting_point`: Melting point in Kelvin (float).
  - `latent_heat`: Latent heat of fusion in J/g (float, may be null).
  - `elements`: List of elemental symbols (list of strings).
  - `crystal_structure`: Crystal system (string).

### DescriptorSet
- **Description**: A collection of computed features including elemental properties and structural representations.
- **Attributes**:
  - `material_id`: Reference to MaterialCompound (string).
  - `elemental_descriptors`: Dictionary of computed elemental features (dict).
  - `graph_descriptors`: Dictionary of computed graph features (dict).
  - `collinearity_flags`: List of flags for definitionally dependent features (list of strings).

### ModelResult
- **Description**: Contains the trained model parameters, performance metrics, and derived rules or feature rankings.
- **Attributes**:
  - `model_type`: Type of model (string).
  - `metrics`: Dictionary of performance metrics (dict).
  - `feature_importance`: Ranked list of feature importances (list of dicts).
  - `symbolic_formula`: Explicit mathematical formula (string, if applicable).
  - `validation_results`: Results from external validation (dict).

## Data Flow

1. **Raw Data**: Downloaded from `matbench` (or MP via API) and stored in `data/raw`.
2. **Processed Data**: Feature-engineered data stored in `data/processed`.
3. **Results**: Model outputs and metrics stored in `data/results`.
4. **External Validation**: Literature PCMs stored in `data/external`.

## Schema Contracts

### Dataset Schema
- **File**: `contracts/dataset.schema.yaml`
- **Description**: Validates the structure of the processed dataset.

### Model Output Schema
- **File**: `contracts/model_output.schema.yaml`
- **Description**: Validates the structure of model outputs and metrics.

### Validation Result Schema
- **File**: `contracts/validation_result.schema.yaml`
- **Description**: Validates the structure of validation results.

## Data Hygiene

- **Checksums**: All raw data files are checksummed and recorded in `state/`.
- **Immutability**: Raw data is never modified; derivations are written to new files.
- **Traceability**: Every result traces back to a specific row in `data/` and a block in `code/`.

## Versioning

- **Dataset Version**: Content hash of the processed dataset.
- **Model Version**: Content hash of the trained model and its parameters.