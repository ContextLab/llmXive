# Data Model: Predicting Molecular Properties from Open Babel Fingerprints

## Overview

This document defines the data structures used throughout the pipeline, ensuring alignment with the `contracts/` schemas. The data flows from raw datasets to processed features, model predictions, and finally, interaction contexts.

## Entity Definitions

### 1. Molecule
Represents a chemical entity.
*   **ID**: Unique identifier (e.g., PubChem CID or generated hash).
*   **SMILES**: Canonical SMILES string.
*   **Properties**:
    *   `logP_exp`: Experimental logP (float).
    *   `solubility_exp`: Experimental solubility (float, unit: g/L or logS).
    *   `bp_exp`: Experimental boiling point (float, unit: K or °C).
*   **Flags**: `is_outlier`, `missing_covariate`.

### 2. Fingerprint
Binary vector representation.
*   **Type**: `MACCS` (166 bits), `ECFP4` (1024/2048 bits), `FP2` (1024 bits).
*   **Vector**: Array of integers (0 or 1).
*   **Metadata**: Hash of the SMILES used to generate it.

### 3. Prediction
Record of model output.
*   **Model_Type**: `Additive` (Crippen) or `RandomForest`.
*   **Property**: `logP`, `solubility`, `boiling_point`.
*   **Value_Pred**: Predicted value.
*   **Value_Exp**: Experimental value.
*   **Residual**: `Value_Exp - Value_Pred`.
*   **Abs_Error**: `|Residual|`.

### 4. InteractionContext
Derived entity for SHAP analysis.
*   **Bit_Pair**: Tuple of two fingerprint bit indices `(i, j)`.
*   **Interaction_Strength**: SHAP interaction value (float).
*   **Substructure_Desc**: Description of the chemical substructures mapped to bits `i` and `j` (via RDKit).
*   **Context_Type**: e.g., "Steric", "Electronic", "Hydrophobic".

## Data Flow

1.  **Ingestion**: Raw Parquet/CSV → `data/raw/` (Checksummed).
2.  **Preprocessing**:
    *   Filter outliers (solubility > 1000 g/L).
    *   Compute Crippen values.
    *   Generate Fingerprints.
    *   Output: `data/processed/molecules_cleaned.csv`, `data/processed/fingerprints.parquet`.
3.  **Modeling**:
    *   Train Baseline → `data/derived/predictions_baseline.csv`.
    *   Train RF → `data/derived/predictions_rf.csv`.
4.  **Analysis**:
    *   SHAP Interaction → `data/derived/shap_interactions.parquet`.
    *   Mapping → `data/derived/interaction_contexts.csv`.

## Assumptions & Constraints

*   **Missing Data**: If a molecule lacks `bp_exp` but has `logP_exp`, it is included in logP analysis but excluded from BP analysis. This is tracked in `data_quality_report.csv`.
*   **Unit Standardization**: All solubility values converted to logS (mol/L) or g/L consistently before modeling.
*   **Diversity**: Dataset subset is filtered to ensure Tanimoto similarity < 0.7 between any pair in the final training set.
