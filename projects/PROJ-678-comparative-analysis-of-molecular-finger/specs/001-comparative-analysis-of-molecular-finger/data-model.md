# Data Model: Comparative Analysis of Molecular Fingerprints for Pesticide Toxicity Prediction

This document defines the core entities, schemas, and relationships required for the comparative analysis of molecular fingerprints in predicting pesticide toxicity.

## Overview

The data model supports the ingestion of chemical structures, generation of molecular fingerprints, training of predictive models, and evaluation of performance metrics. All entities are designed to align with the US212 dataset (Tox21) and the SMARTS-based filtering for organophosphates.

## Entities

### 1. Compound

Represents a unique chemical entity identified by its SMILES string and associated metadata.

**Schema:**
| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `smiles` | str | Canonical SMILES representation of the molecule | Unique, Non-empty |
| `compound_id` | str | Unique identifier (e.g., Tox21 ID) | Unique |
| `is_organophosphate` | bool | Flag indicating if the compound matches the SMARTS pattern `[P](=O)([O,SC])[O,SC]` | Derived |
| `molecular_weight` | float | Calculated molecular weight (g/mol) | Nullable |
| `logP` | float | Calculated octanol-water partition coefficient | Nullable |
| `toxicity_labels` | dict | Dictionary of toxicity endpoints (e.g., `{"NR-AR": 1.0, "NR-ER": 0.0}`) | Keys: Endpoint names, Values: {0, 1, NaN} |

**Relationships:**
- One Compound generates one or more Fingerprints.
- One Compound is used to train one or more Models.

### 2. Fingerprint

Represents a binary vector encoding of a compound's structural features.

**Schema:**
| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `fingerprint_id` | str | Unique identifier (UUID) | Unique |
| `compound_id` | str | Foreign key to Compound | Required |
| `type` | str | Type of fingerprint (e.g., "Morgan", "MACCS") | Enum: ["Morgan", "MACCS"] |
| `radius` | int | Radius parameter (for Morgan) | Required if type == "Morgan" |
| `n_bits` | int | Number of bits in the vector | Required |
| `vector` | array[int] | Binary vector (0 or 1) | Length == n_bits |
| `generation_timestamp` | datetime | Time of generation | Required |

**Relationships:**
- Belongs to one Compound.
- Used as input for one or more Model training runs.

### 3. Model

Represents a trained machine learning model (Random Forest) used for toxicity prediction.

**Schema:**
| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `model_id` | str | Unique identifier (UUID) | Unique |
| `fingerprint_type` | str | Type of fingerprint used (Morgan/MACCS) | Required |
| `fold_index` | int | Index of the cross-validation fold (0-4) | Range: 0-4 |
| `algorithm` | str | Algorithm name (e.g., "RandomForestClassifier") | Required |
| `hyperparameters` | dict | Training parameters (n_estimators, max_depth, etc.) | Required |
| `artifact_path` | str | Path to the saved model file (pickle/joblib) | Required |
| `training_date` | datetime | Date of training | Required |
| `cpu_only` | bool | Flag indicating CPU-only execution | Default: True |

**Relationships:**
- Trained on a specific split of Fingerprints.
- Evaluated to produce one or more PerformanceMetrics.

### 4. PerformanceMetric

Represents the evaluation results of a Model on a test set.

**Schema:**
| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `metric_id` | str | Unique identifier (UUID) | Unique |
| `model_id` | str | Foreign key to Model | Required |
| `fold_index` | int | Corresponding CV fold index | Required |
| `roc_auc` | float | Area Under the Receiver Operating Characteristic Curve | Range: 0.0-1.0 |
| `pr_auc` | float | Area Under the Precision-Recall Curve | Range: 0.0-1.0 |
| `balanced_accuracy` | float | Balanced Accuracy score | Range: 0.0-1.0 |
| `confusion_matrix` | dict | Dictionary with keys: TN, FP, FN, TP | Required |
| `feature_importance` | dict | Mapping of bit indices to Gini importance | Optional, Size == n_bits |

**Relationships:**
- Belongs to one Model.
- Aggregated across folds for statistical analysis (t-test, bootstrap).

## Data Flow

1. **Ingestion**: Raw data from Tox21 is loaded into `Compound` entities.
2. **Filtering**: `is_organophosphate` is computed using SMARTS pattern; non-matching compounds are excluded.
3. **Fingerprinting**: `Fingerprint` vectors are generated for valid compounds.
4. **Splitting**: Data is split into 5 folds using Greedy Maximal Dissimilarity (Tanimoto < 0.85).
5. **Training**: `Model` entities are trained on training splits.
6. **Evaluation**: `PerformanceMetric` entities are generated for each test split.
7. **Aggregation**: Metrics are aggregated for statistical validation (paired t-test, bootstrap CI).

## Constraints & Assumptions

- **Data Source**: All compounds originate from the Tox21 dataset. [UNRESOLVED-CLAIM: c_43501490 — status=not_enough_info]
- **SMARTS Pattern**: Organophosphate filtering strictly uses `[P](=O)([O,SC])[O,SC]`.
- **Fingerprint Parameters**:
 - Morgan: Radius=2, n_bits=2048
 - MACCS: n_bits=166
- **Model Configuration**: Random Forest (n_estimators=100, max_depth=15).
- **Execution Environment**: CPU-only (no CUDA).
- **Measurement Uncertainty**: Toxicity labels are treated as ground truth; measurement uncertainty is not recalculated per Spec Assumptions.

## File Storage Mapping

- `data/raw/tox21.csv`: Raw source data (external).
- `data/processed/organophosphates_filtered.csv`: Filtered Compound data.
- `data/processed/splits/`: JSON/CSV files containing fold indices.
- `data/processed/models/`: Serialized Model artifacts.
- `data/processed/research_results.md`: Final report containing aggregated PerformanceMetrics.