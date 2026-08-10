# Data Model: Comparative Analysis of Molecular Fingerprints for Pesticide Toxicity Prediction

This document defines the core data entities, their schemas, and relationships for the molecular fingerprint analysis pipeline.

## 1. Entity: Compound

Represents a chemical compound from the source dataset (Tox21).

**Schema:**
| Field Name | Type | Description | Constraints |
|:--- |:--- |:--- |:--- |
| `compound_id` | str | Unique identifier for the compound (e.g., DSSTox ID) | Primary Key, Non-null |
| `smiles` | str | Canonical SMILES string representing the molecular structure | Non-null, Valid RDKit parseable string |
| `molecular_weight` | float | Calculated molecular weight | > 0 |
| `formula` | str | Chemical formula (optional) | Nullable |
| `organophosphate` | bool | Flag indicating if the compound matches the organophosphate SMARTS pattern | Derived (via T012) |
| `labels` | dict | Dictionary of toxicity endpoints (e.g., `{"NR-AR": 0, "NR-AR-LBD": 1}`) | Values in {0, 1, -1} (0: inactive, 1: active, -1: missing) |

**Source:** `data/raw/tox21.csv` (via T011)
**Derived File:** `data/processed/organophosphates_filtered.csv` (via T012)

## 2. Entity: Fingerprint

Represents a binary or integer vector encoding the structural features of a compound.

**Schema:**
| Field Name | Type | Description | Constraints |
|:--- |:--- |:--- |:--- |
| `compound_id` | str | Reference to the parent Compound | Foreign Key |
| `fingerprint_type` | str | Type of fingerprint (e.g., "Morgan", "MACCS") | Enum: ["Morgan", "MACCS"] |
| `parameters` | dict | Configuration used for generation (e.g., `{"radius": 2, "n_bits": 2048}`) | Non-null |
| `vector` | ndarray | The actual fingerprint bit vector (uint8 or int) | Shape depends on type |
| `bit_info` | dict | Mapping of bit indices to substructure patterns (for Morgan) | Optional, derived |

**Constants (from `code/constants.py`):**
- **Morgan:** `radius=2`, `n_bits=2048`
- **MACCS:** `n_bits=166`

**Derived File:** `data/processed/fingerprints.pkl` (via T017)

## 3. Entity: Model

Represents a trained machine learning model (Random Forest) used for toxicity prediction.

**Schema:**
| Field Name | Type | Description | Constraints |
|:--- |:--- |:--- |:--- |
| `model_id` | str | Unique identifier for the model instance | Primary Key |
| `algorithm` | str | Underlying algorithm (e.g., "RandomForestClassifier") | Non-null |
| `fingerprint_type` | str | Type of fingerprint used for training | Enum: ["Morgan", "MACCS"] |
| `hyperparameters` | dict | Training parameters (e.g., `{"n_estimators": 100, "max_depth": 15}`) | Non-null |
| `training_set_id` | str | Reference to the specific data split used for training | Foreign Key |
| `artifacts` | dict | Serialized model object and feature importance vectors | Non-null |
| `feature_importances` | ndarray | Gini importance scores for each bit in the fingerprint | Shape matches fingerprint vector |

**Derived File:** `data/processed/final_models.pkl` (via T020a)

## 4. Entity: PerformanceMetric

Represents the evaluation results of a model on a specific dataset split.

**Schema:**
| Field Name | Type | Description | Constraints |
|:--- |:--- |:--- |:--- |
| `metric_id` | str | Unique identifier for the metric record | Primary Key |
| `model_id` | str | Reference to the evaluated Model | Foreign Key |
| `dataset_split` | str | Name of the split used (e.g., "test_set", "fold_0") | Non-null |
| `metric_name` | str | Name of the metric (e.g., "roc_auc", "pr_auc") | Enum: ["roc_auc", "pr_auc"] |
| `value` | float | Calculated metric value | Range: [0.0, 1.0] |
| `confidence_interval` | tuple | (lower, upper) bounds if calculated via bootstrap | Optional |
| `p_value` | float | Statistical significance value (for comparative tests) | Range: [0.0, 1.0] |

**Derived Files:**
- `data/processed/final_test_metrics.json` (Single Split, via T020b)
- `data/processed/kfold_scores.json` (K-Fold CV, via T019)
- `data/processed/test_set_descriptive.json` (via T024b)
- `data/processed/sc003_analysis.json` (Feature Importance, via T025c3)

## Relationships

1. **Compound 1..1 Fingerprint**: Each compound generates one Morgan and one MACCS fingerprint.
2. **Compound 1..* PerformanceMetric**: A compound's label is used in multiple model evaluations.
3. **Model 1..* PerformanceMetric**: A model is evaluated on multiple splits (K-Fold) or a single test set.
4. **PerformanceMetric 1..1 Model**: Each metric record belongs to exactly one model instance.

## Data Flow

1. **Raw Data** -> `Compound` (T011)
2. **Compound** -> `Fingerprint` (T017)
3. **Fingerprint + Compound Labels** -> `Model` (T019, T020a)
4. **Model + Test Data** -> `PerformanceMetric` (T020b, T019)
5. **PerformanceMetric Aggregation** -> Statistical Reports (T025a2, T025b, T029a3)