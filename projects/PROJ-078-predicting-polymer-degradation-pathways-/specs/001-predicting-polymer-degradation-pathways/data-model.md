# Data Model: Polymer Degradation Pipeline Feasibility Study

## Overview

This document defines the data structures used throughout the project, ensuring consistency between ingestion, preprocessing, training, and analysis. The data model is designed to support the lightweight GNN architecture and the statistical validation requirements. **Note**: The `degradation_pathway` field is populated with `"unknown"` for all records in the current feasibility study due to the absence of ground-truth labels.

## Entities

### 1. PolymerRecord
Represents a single entry from the source data.
- **`smiles`**: `string` - Canonical SMILES string of the polymer.
- **`degradation_pathway`**: `string` - Categorical label. **Always "unknown"** in the current feasibility study due to missing ground truth.
- **`temperature`**: `float` - Temperature in Kelvin (Celsius converted).
- **`ph`**: `float` - pH value.
- **`uv_exposure`**: `float` - UV exposure level (normalized).
- **`source`**: `string` - Origin of the record (e.g., "nist", "materials_project", "smiles-proxy").
- **`flags`**: `list[string]` - List of flags (e.g., "missing_ph", "imputed_temp", "missing_pathway").

### 2. MolecularGraph
The graph representation of a `PolymerRecord` used for GNN input.
- **`node_features`**: `tensor` - Matrix of shape (num_atoms, feature_dim). Features include atomic number, hybridization, degree, and environmental conditions (broadcasted).
- **`edge_index`**: `tensor` - Matrix of shape (2, num_edges) representing bond connectivity.
- **`edge_features`**: `tensor` - Matrix of shape (num_edges, edge_feature_dim). Features include bond type, conjugation, and environmental conditions (broadcasted).
- **`label`**: `int` - Encoded degradation pathway label. **Always encoded as "unknown"** in the current feasibility study.

### 3. MotifImportance
Derived metric linking a structural motif to a degradation pathway (for technical demonstration only).
- **`motif_id`**: `string` - Unique identifier for the subgraph pattern.
- **`structure`**: `string` - SMILES representation of the motif.
- **`pathway`**: `string` - Associated degradation pathway. **Always "unknown"** in the current feasibility study.
- **`importance_score`**: `float` - Score from Integrated Gradients (technical demonstration only).
- **`p_value`**: `float` - Significance from Null Attribution Test (algorithmic validation only).

## Data Flow

1.  **Ingestion**: Raw data from sources (NIST, Materials Project, or SMILES proxies) is loaded into `PolymerRecord` objects.
2.  **Preprocessing**: `PolymerRecord` is converted to `MolecularGraph` using RDKit. Missing values are imputed/flagged. **All records are flagged as `missing_pathway`**.
3.  **Feasibility Study**: `MolecularGraph` objects are fed into a *randomly initialized* GNN.
4.  **Attribution**: `MotifImportance` objects are generated from model predictions and Integrated Gradients (technical demonstration only).
5.  **Validation**: `MotifImportance` objects are used in Null Attribution Tests to validate the algorithm.
6.  **Statistical Analysis**: A χ² test is performed on the distribution of structural motifs in the dataset.

## Schema Definitions

See `contracts/polymer_record.schema.yaml` and `contracts/model_output.schema.yaml` for formal YAML schemas.

## Constraints

- **SMILES Validity**: All SMILES strings must be valid according to RDKit. Invalid strings are logged and excluded.
- **Label Presence**: If `degradation_pathway` is missing (which is always true for proxy data), the record is flagged as `missing_pathway` and excluded from any supervised training.
- **Environmental Defaults**: Missing `temperature`, `ph`, or `uv_exposure` are imputed with community-standard defaults (e.g., 298K, pH 7, 0 UV) and flagged.
- **Graph Size**: Graphs must be within memory limits (typically < 1000 atoms for CPU feasibility).
