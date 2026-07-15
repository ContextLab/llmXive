# Data Model Specification

This document defines the core data entities, their schemas, and relationships for the comparative analysis of molecular fingerprints for pesticide toxicity prediction.

## Entity: Compound

Represents a unique chemical compound with its molecular structure and toxicity labels.

| Field | Type | Description | Constraints |
|:--- |:--- |:--- |:--- |
| `compound_id` | str | Unique identifier (e.g., Tox21 ID) | Primary Key, Non-null |
| `smiles` | str | Canonical SMILES string representation | Non-null, Valid chemical structure |
| `molecular_weight` | float | Calculated molecular weight (g/mol) | Nullable |
| `is_organophosphate` | bool | Flag indicating if compound matches the SMARTS pattern for organophosphates | Non-null (derived) |
| `labels` | dict | Dictionary of toxicity endpoints (e.g., `{"NR-AR": 1.0, "NR-AR-LBD": 0.0}`) | Non-null, Keys correspond to dataset columns |

**Schema Example (JSON):**
```json
{
 "compound_id": "TOX21_100001",
 "smiles": "CC(=O)OC1=CC=CC=C1",
 "molecular_weight": 136.08,
 "is_organophosphate": false,
 "labels": {
 "NR-AR": 0.0,
 "NR-AR-LBD": 0.0,
 "NR-AhR": 1.0
 }
}
```

## Entity: Fingerprint

Represents a vectorized representation of a compound's molecular structure used for similarity calculation and model training.

| Field | Type | Description | Constraints |
|:--- |:--- |:--- |:--- |
| `compound_id` | str | Reference to the parent Compound | Foreign Key, Non-null |
| `fingerprint_type` | str | Type of fingerprint (e.g., "Morgan", "MACCS") | Enum: ["Morgan", "MACCS"] |
| `radius` | int | Radius parameter (for Morgan fingerprints) | Nullable (0 for MACCS) |
| `n_bits` | int | Number of bits in the fingerprint vector | Non-null |
| `vector` | np.ndarray | Binary vector representation | Shape: (n_bits,), dtype: bool or int |
| `bit_info` | dict | Mapping of bit indices to atom indices (for interpretability) | Nullable |

**Relationships:**
- One Compound can have multiple Fingerprints (one per type).

## Entity: Model

Represents a trained machine learning model (Random Forest) for a specific fold and fingerprint type.

| Field | Type | Description | Constraints |
|:--- |:--- |:--- |:--- |
| `model_id` | str | Unique identifier (e.g., `fold-0_morgan_rf`) | Primary Key |
| `fold_index` | int | The cross-validation fold index (0-4) | Non-null |
| `fingerprint_type` | str | Type of fingerprint used for training | Enum: ["Morgan", "MACCS"] |
| `n_estimators` | int | Number of trees in the Random Forest | Non-null (Default: 100) |
| `max_depth` | int | Maximum depth of the tree | Non-null (Default: 15) |
| `artifact_path` | str | Filesystem path to the pickled model object | Non-null |
| `feature_importance` | np.ndarray | Gini importance of each feature (bit) | Shape: (n_bits,) |

**Relationships:**
- One Model is trained on one specific Fingerprint type.
- One Model corresponds to one specific Fold split.

## Entity: PerformanceMetric

Stores the evaluation results for a specific model on a specific fold.

| Field | Type | Description | Constraints |
|:--- |:--- |:--- |:--- |
| `metric_id` | str | Unique identifier (e.g., `fold-0_morgan_roc_auc`) | Primary Key |
| `model_id` | str | Reference to the trained Model | Foreign Key, Non-null |
| `metric_name` | str | Name of the metric | Enum: ["ROC-AUC", "PR-AUC", "Balanced Accuracy"] |
| `value` | float | The calculated metric score | Non-null, Range [0.0, 1.0] |
| `fold_index` | int | The fold index associated with this metric | Non-null |
| `confidence_interval` | dict | Bootstrap confidence interval (e.g., `{"lower": 0.75, "upper": 0.85}`) | Nullable |

**Relationships:**
- One PerformanceMetric belongs to one Model.
- One Model has multiple PerformanceMetrics (one per metric type).

## Derived Entities / Aggregates

### SplitConfiguration
Defines the parameters for the Greedy Maximal Dissimilarity Split.
- `threshold`: float (Tanimoto similarity threshold, e.g., 0.85)
- `min_test_size`: int (Minimum required test set size, e.g., 20)
- `n_folds`: int (Number of folds, e.g., 5)

### StatisticalTestResult
Aggregates the results of comparative statistical tests.
- `test_type`: str (e.g., "Paired t-test")
- `metric`: str (e.g., "ROC-AUC")
- `p_value`: float
- `significant`: bool (p < 0.05)
- `comparison`: str (e.g., "Morgan vs MACCS")

## Data Flow

1. **Ingestion**: Raw data (Tox21) -> `Compound` entities.
2. **Filtering**: `Compound` -> Filtered `Compound` (Organophosphates only).
3. **Feature Engineering**: Filtered `Compound` -> `Fingerprint` entities.
4. **Splitting**: `Fingerprint` -> `SplitConfiguration` -> Train/Test indices.
5. **Training**: Train indices + `Fingerprint` -> `Model` entities.
6. **Evaluation**: Test indices + `Model` -> `PerformanceMetric` entities.
7. **Analysis**: `PerformanceMetric` -> `StatisticalTestResult`.