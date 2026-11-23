# Data Model: Machine Learning Prediction of Glass Transition Temperature from Composition

## Data Entities

### 1. GlassSample
Represents a single glass composition entry.

| Attribute | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `id` | string | Unique identifier (UUID or row hash) | Required |
| `formula` | string | Chemical formula (e.g., "SiO2") | Valid pymatgen syntax |
| `Tg` | float | Glass transition temperature (Kelvin) | > 0, No NaN |
| `source` | string | Origin of the data (e.g., "Zenodo") | Required |
| `atomic_fractions` | dict | Map of element -> fraction (e.g., `{"Si": 0.3, "O": 0.7}`) | Sum = 1.0 |
| `oxide_mole_fractions` | dict | Map of oxide -> fraction (e.g., `{"SiO2": 0.6, "Na2O": 0.4}`) | Calculated via Stoichiometric Conversion |
| `descriptors` | dict | Map of feature name -> value (e.g., `{"avg_electronegativity": 3.4}`) | Calculated |

### 2. ModelResult
Represents the outcome of a model training run.

| Attribute | Type | Description |
| :--- | :--- | :--- |
| `model_type` | string | e.g., "RandomForest", "GradientBoosting", "LinearBaseline" |
| `hyperparameters` | dict | e.g., `{"n_estimators": 300, "max_depth": 20}` |
| `metrics` | dict | `{"R2": 0.85, "MAE": 15.2, "RMSE": 18.1}` |
| `feature_importance` | list | List of importance objects (see schema) |
| `seed` | int | Random seed used for reproducibility |

### 3. Dataset
The aggregated collection of `GlassSample` objects.

| Attribute | Type | Description |
| :--- | :--- | :--- |
| `source` | string | Primary data source (Zenodo DOI) |
| `total_samples` | int | Total rows in raw data |
| `train_size` | int | Number of samples in training set |
| `test_size` | int | Number of samples in test set |
| `removed_rows` | list | List of reasons for exclusion (e.g., "Invalid Formula", "Domain Mismatch") |

## Data Flow

1.  **Raw Input**: CSV file from Zenodo.
    *   Columns: `formula`, `Tg`, `source`.
2.  **Parsing & Cleaning**:
    *   Input: Raw CSV.
    *   Process: `pymatgen` parsing, validation.
    *   Output: `GlassSample` objects (in memory or intermediate JSON).
    *   Side Effect: Log of excluded rows.
3.  **Featurization**:
    *   Input: `GlassSample` list.
    *   Process: Calculate atomic fractions, descriptors, and **oxide mole fractions** (via Stoichiometric Conversion).
    *   Output: `processed/featurized.csv`.
4.  **Model Training**:
    *   Input: `featurized.csv`.
    *   Process: Split, Train (RF, GB, Baseline), Cross-Validate.
    *   Output: `artifacts/model_performance.json`.
5.  **Evaluation**:
    *   Input: `model_performance.json`.
    *   Process: T-test (if N >= 50) or Bootstrap (if N < 50), Robustness check.
    *   Output: Final report.

## Data Constraints & Validations

*   **Formula Validity**: Must be parsable by `pymatgen`. If not, row is dropped.
*   **Tg Validity**: Must be a positive float. If missing, row is dropped.
*   **Feature Sum**: Atomic fractions must sum to 1.0 (within floating point tolerance).
*   **No Structural Features**: The feature set must strictly exclude coordination numbers, bond valence sums, or any structural descriptors.
*   **Stoichiometric Conversion**: Must successfully map elements to oxides. If conversion fails (e.g., impossible oxygen balance), the row is flagged and excluded.

## Storage Schema

*   **Raw Data**: `data/raw/glass_data.csv` (Checksummed).
*   **Processed Data**: `data/processed/featurized_data.csv` (Derived, no checksum needed as it is reproducible).
*   **Models**: `artifacts/model_<type>_<params>.pkl` (Pickled models).
*   **Results**: `artifacts/model_performance.json` (JSON).
