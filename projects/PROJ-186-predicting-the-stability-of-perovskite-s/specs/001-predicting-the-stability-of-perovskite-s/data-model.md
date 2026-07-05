# Data Model: Predicting the Stability of Perovskite Structures Using Machine Learning

## 1. Overview
This document defines the data entities, schemas, and relationships for the perovskite stability prediction pipeline. All data artifacts must adhere to these schemas to ensure reproducibility and contract compliance.

## 2. Core Entities

### 2.1 CompositionRecord
Represents a single ABX₃ entry from the training dataset.
- **Attributes**:
  - `formula` (str): Chemical formula (e.g., "CsPbI3").
  - `source_id` (str): Unique identifier from Materials Project or OQMD.
  - `space_group` (int): Space group number (e.g., 221, 148).
  - `tolerance_factor` (float): Goldschmidt tolerance factor ($t$).
  - `octahedral_factor` (float): Octahedral factor ($\mu$).
  - `ionic_radius_mismatch` (float): Calculated mismatch metric.
  - `electronegativity_diff` (float): Electronegativity difference.
  - `decomposition_energy` (float): Target variable (eV/atom).
  - `source` (str): "MP" or "OQMD".

### 2.2 TrainedModel
Represents the serialized model artifact.
- **Attributes**:
  - `hyperparameters` (dict): Best parameters from grid search.
  - `feature_importances` (dict): Feature importance scores (from permutation analysis).
  - `cross_validation_rmse` (float): RMSE from inner 5-fold CV.
  - `test_set_rmse` (float): RMSE on the held-out test set.
  - `training_samples` (int): Number of samples used for training.
  - `random_seed` (int): Seed used for reproducibility.
  - `dft_functional` (str): DFT functional used (e.g., "PBE").

### 2.3 ScreeningCandidate
Represents a hypothetical composition generated for screening.
- **Attributes**:
  - `formula` (str): Hypothetical formula.
  - `tolerance_factor` (float): Calculated $t$.
  - `predicted_stability_score` (float): Predicted decomposition energy.
  - `descriptor_values` (dict): Full set of descriptors.
  - `rank` (int): Rank in the sorted list.
  - `flagged` (bool): True if predicted energy < -0.1 eV/atom.

## 3. Data Flow

1.  **Ingestion**: Raw data from MP/OQMD → `CompositionRecord` (raw).
2.  **Filtering**: Filter by Space Group → `CompositionRecord` (filtered).
3.  **Feature Engineering**: Calculate descriptors → `CompositionRecord` (enriched).
4.  **Splitting**: 80/20 split → `train_set` and `test_set`.
5.  **Training**: Train on `train_set` (with inner CV) → `TrainedModel`.
6.  **Evaluation**: Evaluate on `test_set` → `TrainedModel` (updated with test RMSE).
7.  **Screening**: Generate hypothetical library → Predict → `ScreeningCandidate`.

## 4. Constraints & Validation
- **Null Handling**: `decomposition_energy` must not be null. If null, the record is excluded.
- **Range Checks**:
  - `tolerance_factor`: Must be > 0.
  - `decomposition_energy`: No hard bounds, but extreme outliers may be flagged.
- **Uniqueness**: `source_id` + `source` must be unique.

## 5. File Formats
- **Input/Intermediate**: CSV (comma-separated) with headers matching `CompositionRecord`.
- **Model**: Pickle (`.pkl`) containing the `TrainedModel` object.
- **Output**: Markdown table for `ScreeningCandidate` list; PNG for plots.
