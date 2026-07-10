# Data Model: Identifying Structure-Property Relationships in Polymer Blends

## 1. Overview

This document defines the data models for the project, including the raw dataset schema, the processed feature schema, and the output schema for predictions and metrics. All models are designed to be validated against `contracts/*.schema.yaml` files.

## 2. Entity-Relationship Diagram

```mermaid
erDiagram
    PolymerBlend ||--|{ MolecularDescriptor : "has"
    PolymerBlend ||--|{ InteractionFeature : "has"
    PolymerBlend {
        string blend_id PK
        string source "e.g., NIST, PolymerDB"
        json components "List of {SMILES, weight_fraction}"
        float Tg_K "Glass Transition Temperature (Kelvin)"
        float Modulus_GPa "Young's Modulus (GPa)"
        bool is_valid "Passes all validation checks"
        bool has_target "True if Tg_measured and Tg_1, Tg_2 exist for residual calculation"
    }
    MolecularDescriptor {
        string monomer_id PK
        string smiles
        float MW
        float TPSA
        float rotatable_bonds
        float fractional_free_volume "Optional: Requires external lib"
        float h_bond_donor
        float h_bond_acceptor
        float ... "Other 15+ descriptors"
    }
    InteractionFeature {
        string blend_id FK
        float weighted_avg_MW
        float diff_TPSA
        float Tg_Fox_predicted "Optional: Requires Tg_1, Tg_2"
        float Tg_residual "Optional: Tg_measured - Tg_Fox"
        float ... "Other interaction features"
    }
```

## 3. Data Flows

1.  **Raw Data Ingestion**:
    -   Input: Raw CSV/JSON from verified sources (if available).
    -   Process: Unit harmonization (Tg → Kelvin, Modulus → GPa), SMILES validation, weight-fraction check.
    -   Output: `data/processed/harmonized_raw.parquet`.

2.  **Feature Engineering**:
    -   Input: `harmonized_raw.parquet`.
    -   Process: Generate molecular descriptors (RDKit), compute interaction features (Fox, Gordon-Taylor) **only if targets exist**, VIF analysis.
    -   Output: `data/processed/features.parquet`.

3.  **Model Training**:
    -   Input: `features.parquet`.
    -   Process: Train RF/XGBoost models, hyperparameter tuning, cross-validation.
    -   Output: `data/processed/model_artifacts.pkl`.

4.  **Evaluation & Reporting**:
    -   Input: `model_artifacts.pkl`, `features.parquet`.
    -   Process: Paired t-test, SHAP analysis, feature importance stability.
    -   Output: `data/processed/final_report.json`.

## 4. Data Validation Rules

-   **SMILES**: Must be parseable by RDKit; exclude if invalid.
-   **Weight Fractions**: Sum must be 1.0 ± 0.02; exclude if not.
-   **Units**: Tg in Kelvin, Modulus in GPa; convert if necessary.
-   **Descriptors**: ≥15 non-null descriptors per monomer; exclude if not.
-   **Physical Bounds**: Tg > 0 K, Modulus ≥ 0 GPa; flag if violated.
-   **Target Availability**: `Tg_residual` is only computed if `Tg_measured`, `Tg_1`, and `Tg_2` are present.

## 5. Versioning & Checksums

-   All `data/` files are checksummed (SHA-256) and recorded in `state/projects/PROJ-122-identifying-structure-property-relations.yaml`.
-   Raw data is immutable; derivations are new files.
-   `state/projects/PROJ-122-identifying-structure-property-relations.yaml` tracks:
    ```yaml
    artifact_hashes:
      data/raw/nist.jsonl: "sha256:abc123..."
      data/processed/harmonized_raw.parquet: "sha256:def456..."
      data/processed/features.parquet: "sha256:ghi789..."
    updated_at: "2024-05-21T12:00:00Z"
    ```