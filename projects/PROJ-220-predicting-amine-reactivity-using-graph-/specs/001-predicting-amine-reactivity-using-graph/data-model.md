# Data Model: Predicting Amine Reactivity Using Graph Neural Networks

## 1. Entity Relationship Overview

The data model flows from raw ingestion to graph representation, then to model artifacts.

```mermaid
graph TD
    A[Raw Parquet (ChEMBL/NIST)] --> B[Ingestion & Filtering]
    B --> C[Normalized ReactionRecord]
    C --> D[Descriptor Computation]
    C --> E[Graph Construction]
    D --> F[DescriptorVector]
    E --> G[MolecularGraph]
    G --> H[Model Training]
    H --> I[ModelArtifact]
    H --> J[Predictions]
    J --> K[Interpretability (SHAP)]
    K --> L[Validation (Correlation with F)]
```

## 2. Core Entities

### ReactionRecord
Represents a single SN2 reaction instance with normalized kinetic data.
*   `record_id`: Unique string identifier.
*   `nucleophile_smiles`: SMILES string of the amine reactant.
*   `electrophile_smiles`: SMILES string of the substrate.
*   `product_smiles`: SMILES string of the product.
*   `rate_constant`: Float, normalized to standard conditions (298K).
*   `log_rate`: Float, $\log_{10}(\text{rate\_constant})$.
*   `temperature_kelvin`: Float, experimental temperature.
*   `activation_energy`: Float, $E_a$ (kJ/mol) or `null` if imputed.
*   `pKa`: Float, calculated pKa of the nucleophile.
*   `exclusion_reason`: String (if excluded, e.g., "missing_temp", "invalid_smiles").

### MolecularGraph
The heterogeneous graph representation of a reactant.
*   `graph_id`: Unique string identifier.
*   `smiles`: Original SMILES.
*   `node_features`: List of lists (N x F), where N is number of atoms.
    *   Features: `[atomic_num, hybridization, formal_charge, gasteiger_charge, pKa]`
*   `edge_index`: 2 x E tensor (source, target).
*   `edge_features`: List of lists (E x F), where F is bond features.
    *   Features: `[bond_order, conjugation, ring_membership]`
*   `reaction_center_indices`: List of integers, indices of atoms involved in the reaction center.

### DescriptorVector
Computed external descriptors for validation.
*   `record_id`: Link to ReactionRecord.
*   `hammett_sigma`: Float (calculated).
*   `taft_es`: Float (calculated).
*   `verloop_b1`: Float (calculated).
*   `verloop_b5`: Float (calculated).
*   `charton_nu`: Float (calculated).
*   `molar_refractivity`: Float (calculated).

### ModelArtifact
Serialized trained model.
*   `model_id`: Unique string.
*   `type`: String (`"baseline"` or `"gnn"`).
*   `hyperparameters`: Dictionary of training config.
*   `weights_path`: Relative path to `.pt` or `.pkl` file.
*   `metrics`: Dictionary (`r2`, `mae`, `rmse`).

### FeatureImportance
Results of SHAP analysis.
*   `record_id`: Link to ReactionRecord.
*   `shap_values`: List of floats (one per atom).
*   `aggregated_importance`: Float, sum of absolute SHAP values for reaction center.
*   `correlation_score`: Float, Pearson r against descriptor vector.
*   `collinearity_flag`: Boolean (True if input pKa correlates > 0.9 with descriptor vector).

## 3. Data Flow & Transformations

1.  **Ingestion**: Raw Parquet -> Filtered JSON/Parquet (ReactionRecord).
    *   *Transformation*: Normalization of $k$ using Arrhenius equation.
    *   *Validation*: Check for NaN in `rate_constant`, `pKa`.
2.  **Descriptor Computation**: ReactionRecord -> DescriptorVector.
    *   *Transformation*: Calculate Hammett, Taft, Verloop descriptors using `mordred`/`rdkit`.
    *   *Validation*: Ensure no NaN in descriptors.
3.  **Graph Construction**: ReactionRecord -> PyTorch Geometric Data Object.
    *   *Transformation*: RDKit molecule generation, feature extraction.
    *   *Validation*: Ensure graph connectivity, valid feature ranges.
4.  **Training**: Graph Dataset -> ModelArtifact + Predictions.
    *   *Transformation*: Forward pass, loss calculation, backpropagation.
5.  **Interpretability**: ModelArtifact + Test Graphs -> FeatureImportance.
    *   *Transformation*: SHAP value calculation, aggregation.
    *   *Validation*: Check collinearity flag.

## 4. Storage Strategy

*   **Raw Data**: `data/raw/` (Read-only, checksummed).
*   **Processed Data**: `data/processed/` (Parquet files for ReactionRecord, PyG Data objects, DescriptorVector).
*   **Artifacts**: `artifacts/` (Model weights, prediction CSVs, plots).
*   **Logs**: `logs/` (Audit logs of exclusions, training metrics).

## 5. Versioning

*   All data files will be named with a hash of the source data and processing script version (e.g., `reaction_record_v1_<hash>.parquet`).
*   Model artifacts will include the git commit hash of the training script.
*   The `state` YAML file will be updated with these hashes immediately after generation.