# Data Model: Comparative Analysis of Molecular Fingerprints for Pesticide Toxicity Prediction

This document defines the core data entities, their schemas, and relationships used throughout the project pipeline. These definitions align with the requirements in `spec.md` and serve as the contract between the data acquisition, processing, modeling, and evaluation stages.

## 1. Overview

The project processes chemical compounds to predict toxicity. The data flow transforms raw molecular structures into numerical fingerprints, which are then used to train machine learning models. The final output consists of performance metrics and statistical analyses.

## 2. Entity Definitions

### 2.1. Compound

Represents a single chemical entity. This is the primary unit of analysis.

| Field Name | Type | Description | Source/Notes |
|:--- |:--- |:--- |:--- |
| `compound_id` | `str` | Unique identifier for the compound (e.g., SMILES string hash or dataset ID). | Generated/External |
| `smiles` | `str` | Simplified Molecular Input Line Entry System string. | Tox21 / External |
| `is_organophosphate` | `bool` | Flag indicating if the compound matches the SMARTS pattern `[P](=O)([O,SC])[O,SC]`. | Derived via `code/filter.py` |
| `toxicity_labels` | `Dict[str, bool]` | Dictionary mapping toxicity endpoints (e.g., "NR-AR", "SR-ARE") to binary labels (1=active, 0=inactive). | Tox21 Dataset |
| `mol_obj` | `rdkit.Chem.Mol` | (Optional) RDKit molecule object used during intermediate processing. | In-memory only |

**Constraints:**
- `smiles` must be a valid RDKit-parseable string.
- `is_organophosphate` is `True` if and only if `rdkit.Chem.MolFromSmarts` matches the pattern.
- Compounds with missing toxicity labels for all endpoints are excluded from training.

### 2.2. Fingerprint

Represents the binary vector representation of a compound used for similarity calculation and model input.

| Field Name | Type | Description | Source/Notes |
|:--- |:--- |:--- |:--- |
| `compound_id` | `str` | Foreign key linking to `Compound.compound_id`. | |
| `fingerprint_type` | `str` | Type of fingerprint: `"Morgan"` or `"MACCS"`. | |
| `bits` | `int` | Number of bits in the fingerprint (2048 for Morgan, 166 for MACCS). | |
| `radius` | `int` | Radius parameter (only applicable for Morgan). Value: 2. | |
| `vector` | `np.ndarray` | Binary array of shape `(bits,)`. | Generated via `code/fingerprints.py` |
| `bit_info` | `Dict[int, List[Tuple[int, int]]]` | (Optional) Mapping of bit index to atom indices contributing to it. Used for feature importance analysis. | RDKit `GetBitInfo` |

**Constraints:**
- `vector` elements must be strictly 0 or 1.
- `fingerprint_type` must be one of the allowed enum values.
- The `vector` length must match the `bits` definition for the specific type.

### 2.3. Model

Represents a trained Random Forest classifier and its associated metadata.

| Field Name | Type | Description | Source/Notes |
|:--- |:--- |:--- |:--- |
| `model_id` | `str` | Unique identifier (e.g., `fold-<N>-<type>`). | Generated |
| `fingerprint_type` | `str` | The fingerprint type used for training (`"Morgan"` or `"MACCS"`). | |
| `fold_index` | `int` | The cross-validation fold index (0-4). | |
| `n_trees` | `int` | Number of trees in the forest. Value: 100. | |
| `max_depth` | `int` | Maximum depth of the trees. Value: 15. | |
| `train_indices` | `List[int]` | List of row indices used for training. | From `code/split.py` |
| `test_indices` | `List[int]` | List of row indices used for testing. | From `code/split.py` |
| `rf_model` | `sklearn.ensemble.RandomForestClassifier` | The trained scikit-learn model object. | Saved to `data/processed/models/` |
| `feature_importance` | `np.ndarray` | Gini importance array of shape `(bits,)`. | Derived from `rf_model` |

**Constraints:**
- `train_indices` and `test_indices` must be disjoint.
- `rf_model` must be fitted on the training data corresponding to `train_indices`.
- `feature_importance` length must match the fingerprint `bits`.

### 2.4. PerformanceMetric

Represents the evaluation results of a specific model on a specific fold.

| Field Name | Type | Description | Source/Notes |
|:--- |:--- |:--- |:--- |
| `model_id` | `str` | Foreign key linking to `Model.model_id`. | |
| `fold_index` | `int` | The cross-validation fold index. | |
| `fingerprint_type` | `str` | The fingerprint type used. | |
| `roc_auc` | `float` | Area Under the Receiver Operating Characteristic Curve. | Calculated via `code/evaluate.py` |
| `pr_auc` | `float` | Area Under the Precision-Recall Curve. | Calculated via `code/evaluate.py` |
| `balanced_accuracy` | `float` | Balanced accuracy score. | Calculated via `code/evaluate.py` |
| `confusion_matrix` | `np.ndarray` | 2x2 matrix of predictions vs. actuals. | |
| `bootstrap_ci_lower` | `float` | Lower bound of the 95% CI for the metric difference (if applicable). | From `code/evaluate.py` |
| `bootstrap_ci_upper` | `float` | Upper bound of the 95% CI for the metric difference. | From `code/evaluate.py` |

**Constraints:**
- All score fields must be in the range [0.0, 1.0].
- `confusion_matrix` shape must be (2, 2).

## 3. Relationships

- **Compound 1-to-Many Fingerprint**: A single compound can have multiple fingerprint representations (Morgan and MACCS).
- **Compound 1-to-Many Model**: A compound appears in the training or test set of multiple models (across different folds).
- **Model 1-to-1 PerformanceMetric**: Each trained model produces exactly one set of performance metrics per fold.
- **Fingerprint 1-to-1 Model**: A model is trained on a specific set of fingerprints of a specific type.

## 4. Data Storage Conventions

| Artifact | File Path | Format |
|:--- |:--- |:--- |
| Filtered Compounds | `data/processed/organophosphates_filtered.csv` | CSV |
| Fingerprints | `data/processed/fingerprints_morgan.npy`, `data/processed/fingerprints_maccs.npy` | NumPy (.npy) |
| Split Indices | `data/processed/splits/fold_<N>_indices.pkl` | Pickle |
| Trained Models | `data/processed/models/fold_<N>_<type>.pkl` | Pickle |
| Metrics | `data/processed/metrics.csv` | CSV |
| Final Report | `data/processed/research_results.md` | Markdown |

## 5. Validation Rules

1. **SMARTS Filter**: All `is_organophosphate` flags must be verified against the pattern `[P](=O)([O,SC])[O,SC]` before inclusion in the final dataset.
2. **Split Validity**: The Greedy Maximal Dissimilarity Split must ensure `Tanimoto Similarity < 0.85` between any test set compound and the training set mean.
3. **Minimum Sample Size**: If the number of valid compounds per endpoint is < 50, statistical tests (t-test) must be skipped, and a warning logged.
4. **Reproducibility**: All random seeds must be initialized to 42 as per `code/utils.py`.