# Data Model: Predicting Battery Electrolyte Decomposition Products via DFT and Machine Learning

## Overview

This document defines the data structures used throughout the pipeline, ensuring strict adherence to the schema contracts and preventing data leakage.

## Entities

### 1. Molecule (Input)
Represents a single electrolyte species with ground-state properties.
-   `molecule_id`: Unique string identifier (e.g., "lit-001-EC").
-   `species`: Chemical formula (e.g., "C3H4O3").
-   `hom`: HOMO energy (eV).
-   `lum`: LUMO energy (eV).
-   `band_gap`: Calculated as `lum - hom` (eV).
-   `bond_lengths`: Dictionary of bond type to length (Å) or flattened columns (e.g., `c_o_len`, `c_c_len`).
-   `reactant_energy`: Total energy of the reactant (eV). **Used ONLY for target calculation. Excluded from feature matrix.**
-   `product_energy`: Total energy of the decomposition products (eV). **Used ONLY for target calculation. Excluded from feature matrix.**
-   `potential_phi`: Applied electrochemical potential (V).
-   `decomp_energy`: Calculated label: `product_energy - reactant_energy - n * F * potential_phi` (eV). **Target variable.**
-   `experimental_onset`: Experimental decomposition onset potential (eV) (optional, for validation).

### 2. FeatureSet (Processed)
The feature set used for training, **excluding** identity features.
-   `feature_name`: Name of the feature (e.g., "hom", "bond_c_o_len").
-   `value`: Feature value.
-   `is_rejected`: Boolean flag. `True` if the feature was rejected due to Partial Correlation > 0.9 or VIF ≥ 10.
-   `rejection_reason`: String describing why the feature was rejected (e.g., "Partial Correlation > 0.9 with target").
-   **Constraint**: `reactant_energy` and `product_energy` are **never** present in this set.

### 3. ModelOutput (Intermediate)
Results from the Random Forest training.
-   `model_id`: UUID for the specific model run.
-   `feature_importance`: Dictionary mapping feature name to importance score.
-   `cv_score`: Mean R² score from 5-fold cross-validation.
-   `vif_scores`: Dictionary mapping feature name to VIF value.
-   `rejected_features`: List of feature names rejected during Phase 1.3.
-   `residual_correlation`: Float. Partial correlation of remaining features with target (must be < 0.9).

### 4. ValidationResult (Final)
Comparison against experimental data.
-   `experiment_id`: Reference to the experimental measurement.
-   `predicted_energy`: Model prediction (eV).
-   `experimental_onset`: Experimental onset potential (eV).
-   `residual`: `predicted - experimental`.
-   `correlation_coefficient`: R² score for the correlation study.
-   `bias_corrected`: **False** (Bias correction is not applied).

### 5. SensitivityAnalysis (Final)
Output of the threshold sweep analysis.
-   `threshold_eV`: The specific threshold value tested (e.g., -0.05, 0.0, +0.05).
-   `false_positive_rate`: Calculated rate at this threshold.
-   `false_negative_rate`: Calculated rate at this threshold.
-   `total_samples`: Number of samples evaluated.

## Data Flow

1.  **Ingestion**: Raw CSV (Literature Subset) → `data/raw/literature_subset.csv`.
2.  **Contract Validation**: Validate against `dataset.schema.yaml`.
3.  **Cleaning**: Drop rows with missing HOMO/LUMO; calculate `decomp_energy` for each `Molecule` instance.
4.  **Feature Engineering**:
    -   **Drop Identity**: **Explicitly remove** `reactant_energy` and `product_energy` from the feature matrix.
    -   Calculate VIF.
    -   Calculate Partial Correlation between features and `decomp_energy`.
    -   **Reject** features with Partial Correlation > 0.9.
    -   **Residual Check**: Verify remaining features have partial correlation < 0.9.
    -   Output `data/derived/features_cleaned.csv` (only non-rejected features).
5.  **Training**: Input `features_cleaned.csv` → Output `data/derived/model_artifact.pkl` + `data/derived/importance.json`.
6.  **Validation**: Compare `model_artifact.pkl` predictions with `experimental_onset` (if available) → `data/derived/validation_report.json`.
7.  **Sensitivity Analysis**: Sweep thresholds → `data/derived/sensitivity_analysis.csv`.

## Constraints

-   **No NaNs**: Feature matrix must have zero NaN values.
-   **No Leakage**: `decomp_energy` is never used as an input feature. `reactant_energy` and `product_energy` are **excluded from the feature matrix entirely** before any model training or leakage check.
-   **VIF Limit**: Features with VIF ≥ 10 are flagged but retained only if Partial Correlation < 0.9 (unlikely for energy terms).
-   **Residual Correlation**: The remaining feature set must have partial correlation < 0.9 with the target.
-   **Empty Feature Set**: If all features are rejected, the pipeline halts with a "No viable features" report.
-   **Data Intersection**: The validation step requires the intersection of training molecules and experimental onset molecules to be non-empty.