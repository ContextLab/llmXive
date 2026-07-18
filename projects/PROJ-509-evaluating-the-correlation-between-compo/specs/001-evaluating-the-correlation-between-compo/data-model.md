# Data Model: Evaluating the Correlation Between Compositional Features and Predicted Formation Energy in Inorganic Materials

## Overview

This document defines the data structures, schemas, and relationships for the project. It ensures that all data artifacts are consistent, versioned, and traceable.

## Entities

### Compound

Represents an inorganic material with a specific chemical formula, formation energy, and crystal system.

*   **Attributes**:
    *   `material_id`: Unique identifier (string).
    *   `formula`: Chemical formula (string).
    *   `formation_energy_per_atom`: Target variable (float).
    *   `crystal_system`: Structural classification (string).
    *   `elements`: List of constituent elements (list of strings).
    *   `element_counts`: List of element counts (list of integers).

### DescriptorSet

A collection of computed features associated with a specific Compound.

*   **Attributes**:
    *   `material_id`: Foreign key to Compound.
    *   `mean_electronegativity`: Average electronegativity (float).
    *   `variance_electronegativity`: Variance of electronegativity (float).
    *   `mean_atomic_radius`: Average atomic radius (float).
    *   `variance_atomic_radius`: Variance of atomic radius (float).
    *   `mean_valence_electrons`: Average valence electron count (float).
    *   `variance_valence_electrons`: Variance of valence electron count (float).
    *   `mean_melting_point`: Average melting point (float).
    *   `variance_melting_point`: Variance of melting point (float).
    *   `mean_ionization_energy`: Average first ionization energy (float).
    *   `variance_ionization_energy`: Variance of first ionization energy (float).

### ModelOutput

The result of training a regression model.

*   **Attributes**:
    *   `model_type`: "RandomForest" or "GradientBoosting".
    *   `r2_train`: Training R² score (float).
    *   `r2_val`: Validation R² score (float).
    *   `mae_val`: Validation MAE (float).
    *   `rmse_val`: Validation RMSE (float).
    *   `overfitting_ratio`: `train_r2 / val_r2` (float or null).
    *   `feature_importances`: Dictionary of feature name to importance score (dict).

## Data Flow

1.  **Raw Data**: `data/raw/mp_2020_12_1.csv` (Downloaded from Zenodo).
2.  **Filtered Data**: `data/processed/computed_descriptors.csv` (Inorganic, complete data; descriptors computed).
3.  **Train/Val Split**: `data/processed/train_set.csv`, `data/processed/val_set.csv` (Stratified by Chemical Family).
4.  **Model Artifacts**: `data/evaluation/trained_models.pkl`, `data/evaluation/metrics.json`.
5.  **Analysis Artifacts**: `data/evaluation/permutation_importance.json`, `data/evaluation/feature_ranking.json`, `data/evaluation/ale_plots/*.png`, `data/evaluation/vif_scores.json`.

## Storage & Versioning

*   **Raw Data**: Stored in `data/raw/` with checksums recorded in `state/projects/PROJ-509-evaluating-the-correlation-between-compo.yaml`.
*   **Processed Data**: Stored in `data/processed/` with new filenames and checksums.
*   **Evaluation Data**: Stored in `data/evaluation/` with JSON format for metrics and CSV for rankings.
*   **Versioning**: Every file under `data/` carries a content hash. Changes trigger updates to the state file.
