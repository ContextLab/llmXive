# Data Model: Predicting Yield Strength of BCC Alloys

## Entity Definitions

### 1. AlloyRecord
Represents a single alloy entry from the raw dataset.
- **Attributes**:
  - `system_id`: String (Unique identifier, e.g., "MPEA-001")
  - `elemental_composition`: Dictionary (Key: Element Symbol, Value: Atomic Fraction)
  - `yield_strength`: Float (MPa)
  - `crystal_structure`: String (e.g., "BCC", "FCC", "HCP", "Mixed")
  - `source_reference`: String (DOI or citation)
  - `yield_strength_source`: String (e.g., "Experimental", "CALPHAD", "Calculated") - **Critical for Circular Validation**
  - `is_bcc`: Boolean (Derived: True if `crystal_structure` matches BCC patterns)
  - `is_valid`: Boolean (True if yield_strength is numeric and > 0)

### 2. CompositionalDescriptor
Represents derived features for a single alloy.
- **Attributes**:
  - `alloy_id`: String (FK to AlloyRecord)
  - `delta_radius`: Float (Atomic radius mismatch, δ)
  - `vec`: Float (Valence Electron Concentration)
  - `mixing_entropy`: Float (Configurational entropy)
  - `mixing_enthalpy`: Float (Enthalpy of mixing)
  - `electronegativity_diff`: Float (Standard deviation of electronegativity)
  - `ilr_features`: List[Float] (ILR-transformed coordinates, length = num_elements - 1)
  - `feature_set_type`: String ("scalar_descriptors" OR "ilr_transformed")

### 3. ModelPerformance
Represents the evaluation results of a trained model.
- **Attributes**:
  - `model_type`: String ("RandomForest", "GradientBoosting", "Ridge")
  - `feature_set_used`: String ("scalar_descriptors" OR "ilr_transformed")
  - `r_squared`: Float
  - `r_squared_ci_lower`: Float (95% CI lower bound)
  - `r_squared_ci_upper`: Float (95% CI upper bound)
  - `mae`: Float (Mean Absolute Error)
  - `rmse`: Float (Root Mean Squared Error)
  - `feature_importance`: Dict (Feature name -> Importance score)
  - `cv_repetitions`: Integer (Default 10)
  - `n_samples`: Integer (Dataset size used)
  - `feature_stability_spearman`: Float (Median Spearman correlation of importance across CV reps)
  - `mae_vs_uncertainty`: Boolean (True if MAE <= 50 MPa, False otherwise)
  - `statistical_significance`: String (Result of Friedman/Nemenyi test)

## Data Flow

1. **Raw Input**: `data/raw/mpea_raw.csv` (or similar).
2. **Filtering**: `01_download.py` -> `data/processed/bcc_filtered.csv` (only BCC, valid yield, raw only).
3. **Normalization**: `01_download.py` -> Compositions normalized to sum=1.0.
4. **Feature Engineering**: `02_engineer.py` -> `data/processed/features_[type].csv` (Descriptive OR ILR).
5. **Modeling**: `03_train.py` -> `data/processed/model_results.json`.
6. **Evaluation**: `04_evaluate.py` -> `data/processed/performance_report.csv`.

## Constraints & Rules

- **Composition Sum**: All `elemental_composition` rows MUST sum to 1.0 (±1e-6).
- **BCC Filter**: Only entries where `crystal_structure` contains "BCC" (case-insensitive) are processed.
- **Feature Exclusivity**: A single model run MUST use either `delta_radius`, `vec`, etc., OR `ilr_features`, never both.
- **Missing Data**: Any row with missing `yield_strength` or missing elemental data is excluded and logged.
- **Duplicate Handling**: Duplicate compositions (same elements, same fractions) are averaged for yield strength; SD is recorded.
- **Circular Validation**: Rows with `yield_strength_source` == "CALPHAD" (if using mixing enthalpy) are flagged or excluded.