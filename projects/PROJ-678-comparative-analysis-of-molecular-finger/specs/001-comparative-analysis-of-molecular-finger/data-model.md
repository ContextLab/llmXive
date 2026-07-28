# Data Model: Comparative Analysis of Molecular Fingerprints for Pesticide Toxicity Prediction

This document defines the core entities, schemas, and relationships used throughout the `PROJ-678` pipeline. It serves as the foundational specification for data acquisition, processing, modeling, and evaluation tasks (T011, T012, T017, T019, T025).

## 1. Entity: Compound

Represents a single chemical entity derived from the Tox21 dataset. This is the primary unit of analysis.

**Source**: HuggingFace `deepchem/tox` dataset.

**Schema**:
| Column Name | Type | Description | Constraints |
|:--- |:--- |:--- |:--- |
| `smiles` | str | Canonical SMILES string representing the molecular structure. | Unique, non-empty. |
| `compound_id` | str | Unique identifier (e.g., DSSTox ID or internal hash). | Unique, non-empty. |
| `has_phosphorus` | bool | Flag indicating if the compound contains a phosphorus atom. | Derived from SMARTS match. |
| `n_tox_endpoints` | int | Number of toxicity endpoints measured for this compound. | >= 0. |
| `labels` | dict | Dictionary mapping endpoint names to binary labels (0, 1, or -1 for missing). | Keys: `['NR-AR', 'NR-AR-LBD',...]`. Values: `{0, 1, -1}`. |

**Derived Attributes**:
- `molecular_weight`: Calculated via RDKit.
- `num_atoms`: Count of atoms in the molecule.

**Relationships**:
- One-to-Many with `Fingerprint` (a compound can have multiple fingerprint representations).
- One-to-Many with `Model` (predictions are made per compound).

---

## 2. Entity: Fingerprint

Represents a specific bit-vector or structural representation of a `Compound`.

**Types**:
1. **Morgan (ECFP)**: Circular fingerprint.
 - Parameters: `radius=2`, `n_bits=2048`.
2. **MACCS**: Key-based fingerprint.
 - Parameters: `n_bits=166`.

**Schema**:
| Field Name | Type | Description | Constraints |
|:--- |:--- |:--- |:--- |
| `compound_id` | str | Foreign key referencing `Compound.compound_id`. | Not null. |
| `fingerprint_type` | str | Enum: `['morgan', 'maccs']`. | Not null. |
| `parameters` | dict | Configuration used to generate the fingerprint (e.g., `{'radius': 2, 'nBits': 2048}`). | Not null. |
| `bit_vector` | np.ndarray | Binary array of length `n_bits`. | Dtype: `bool` or `int8`. |
| `bit_info` | dict (optional) | Mapping of bit index to list of atom indices contributing to that bit (for Morgan). | Used for SC-003 analysis. |

**Relationships**:
- Many-to-One with `Compound`.
- One-to-Many with `Model` (used as input features).

---

## 3. Entity: Model

Represents a trained machine learning model instance used for toxicity prediction.

**Types**:
- **Random Forest**: `sklearn.ensemble.RandomForestClassifier`.
 - Hyperparameters: `n_estimators=100`, `max_depth=15`, `random_state=42`.

**Schema**:
| Field Name | Type | Description | Constraints |
|:--- |:--- |:--- |:--- |
| `model_id` | str | Unique identifier for the model instance. | Unique. |
| `model_type` | str | Enum: `['random_forest']`. | Not null. |
| `fingerprint_type` | str | The type of fingerprint used for training (`morgan` or `maccs`). | Not null. |
| `hyperparameters` | dict | JSON-serializable dict of model hyperparameters. | Not null. |
| `training_set_id` | str | Reference to the specific split or fold used for training. | Not null. |
| `feature_importance` | np.ndarray | Array of Gini importance scores (length = `n_bits`). | Only for tree-based models. |
| `artifact_path` | str | Relative path to the serialized model file (`.pkl`). | Valid file path. |

**Relationships**:
- Many-to-One with `Fingerprint` (trained on a specific fingerprint type).
- One-to-Many with `PerformanceMetric`.

---

## 4. Entity: PerformanceMetric

Represents the evaluation results of a `Model` on a specific dataset split.

**Schema**:
| Field Name | Type | Description | Constraints |
|:--- |:--- |:--- |:--- |
| `metric_id` | str | Unique identifier. | Unique. |
| `model_id` | str | Foreign key to `Model.model_id`. | Not null. |
| `split_type` | str | Enum: `['held_out_test', 'k_fold_cv']`. | Not null. |
| `fold_index` | int | Index of the fold (0-4) if `split_type` is `k_fold_cv`. -1 otherwise. | >= -1. |
| `roc_auc` | float | Area Under the Receiver Operating Characteristic Curve. | Range: [0, 1]. |
| `pr_auc` | float | Area Under the Precision-Recall Curve. | Range: [0, 1]. |
| `accuracy` | float | Classification accuracy. | Range: [0, 1]. |
| `precision` | float | Precision score. | Range: [0, 1]. |
| `recall` | float | Recall score. | Range: [0, 1]. |

**Aggregates**:
- **K-Fold Scores**: A list of `roc_auc` floats used for the Corrected Resampled t-test.
- **Descriptive Metrics**: Single float values for the held-out test set.

---

## 5. Data Flow & Contracts

### 5.1. Input Data (T011)
- **Source**: `datasets.load_dataset("deepchem/tox")`
- **Format**: Pandas DataFrame with columns `smiles`, `compound_id`, and toxicity endpoint columns.

### 5.2. Filtered Data (T012)
- **Output**: `data/processed/organophosphates_filtered.csv`
- **Schema**: Matches `Compound` schema (SMILES, ID, Labels).
- **Filter**: `SMARTS_PATTERN = "[P](=O)([O,SC])[O,SC]"`

### 5.3. Fingerprint Data (T017)
- **Output**: `data/processed/fingerprints.pkl`
- **Structure**: Dictionary `{ compound_id: { 'morgan': array, 'maccs': array } }`.

### 5.4. Split Indices (T018a)
- **Output**: `data/processed/split_indices.json`
- **Schema**:
 ```json
 {
 "status": "VALID" | "INVALID",
 "test_indices": [int],
 "train_indices": [int],
 "tanimoto_min": float,
 "tanimoto_max": float
 }
 ```

### 5.5. Model Scores (T019)
- **Output**: `data/processed/kfold_scores.json`
- **Schema**:
 ```json
 {
 "morgan": { "roc_auc": [float, float, float, float, float] },
 "maccs": { "roc_auc": [float, float, float, float, float] }
 }
 ```

### 5.6. Final Metrics (T020, T024)
- **Output**: `data/processed/final_test_metrics.json`
- **Schema**:
 ```json
 {
 "morgan": { "roc_auc": float, "pr_auc": float },
 "maccs": { "roc_auc": float, "pr_auc": float }
 }
 ```

---

## 6. Constraints & Assumptions

1. **Binary Labels**: Toxicity endpoints are treated as binary (0/1). Missing labels are encoded as -1 and excluded from metric calculation.
2. **No Measurement Uncertainty**: As per Spec Assumptions, toxicity labels are treated as ground truth. No standard deviation or calibration data is available or required for the statistical model.
3. **Reproducibility**: All random seeds are fixed to `42`.
4. **Memory Safety**: Fingerprint generation must support chunked processing if the dataset exceeds available RAM.
5. **Statistical Validity**: The Corrected Resampled t-test (Nadeau & Bengio) is applied strictly to the K-Fold ROC-AUC scores, not PR-AUC.