# Data Model: Comparative Analysis of Molecular Fingerprints for Pesticide Toxicity Prediction

This document defines the core data entities, their schemas, and relationships used throughout the research pipeline. These definitions serve as the contract for data exchange between `code/download.py`, `code/filter.py`, `code/fingerprints.py`, `code/split.py`, `code/train.py`, and `code/evaluate.py`.

## 1. Compound

Represents a single chemical entity derived from the Tox21 dataset.

**Source**: `data/raw/tox21.csv` (via `code/download.py`)
**Processed Output**: `data/processed/organophosphates_filtered.csv` (via `code/filter.py`)

**Schema**:
| Column Name | Type | Description | Constraints |
|:--- |:--- |:--- |:--- |
| `smiles` | string | Canonical SMILES string representing the molecular structure. | Primary Key, Not Null |
| `mol_id` | string | Unique identifier for the molecule. | Not Null |
| `nr-ah` | integer | Toxicity label for Nuclear Receptor - AhR (0=Inactive, 1=Active, -1=Missing). | [-1, 0, 1] |
| `nr-ar` | integer | Toxicity label for Nuclear Receptor - AR. | [-1, 0, 1] |
| `nr-ar-lbd` | integer | Toxicity label for Nuclear Receptor - AR ligand binding domain. | [-1, 0, 1] |
| `nr-aur` | integer | Toxicity label for Nuclear Receptor - Aromatase. | [-1, 0, 1] |
| `nr-er` | integer | Toxicity label for Nuclear Receptor - ER. | [-1, 0, 1] |
| `nr-er-lbd` | integer | Toxicity label for Nuclear Receptor - ER ligand binding domain. | [-1, 0, 1] |
| `nr-ppar-gamma` | integer | Toxicity label for Nuclear Receptor - PPAR-gamma. | [-1, 0, 1] |
| `nr-tr` | integer | Toxicity label for Nuclear Receptor - TR. | [-1, 0, 1] |
| `nr-vdr` | integer | Toxicity label for Nuclear Receptor - VDR. | [-1, 0, 1] |
| `bp-1.4.1.1` | integer | Toxicity label for Biological Process - 1.4.1.1. | [-1, 0, 1] |
| `bp-1.4.1.2` | integer | Toxicity label for Biological Process - 1.4.1.2. | [-1, 0, 1] |
| `bp-2.7.1.1` | integer | Toxicity label for Biological Process - 2.7.1.1. | [-1, 0, 1] |
| `bp-2.7.1.2` | integer | Toxicity label for Biological Process - 2.7.1.2. | [-1, 0, 1] |
| `bp-3.1.1.1` | integer | Toxicity label for Biological Process - 3.1.1.1. | [-1, 0, 1] |
| `bp-3.1.1.2` | integer | Toxicity label for Biological Process - 3.1.1.2. | [-1, 0, 1] |
| `bp-3.4.1.1` | integer | Toxicity label for Biological Process - 3.4.1.1. | [-1, 0, 1] |
| `bp-3.4.1.2` | integer | Toxicity label for Biological Process - 3.4.1.2. | [-1, 0, 1] |
| `bp-3.4.2.1` | integer | Toxicity label for Biological Process - 3.4.2.1. | [-1, 0, 1] |
| `bp-3.4.2.2` | integer | Toxicity label for Biological Process - 3.4.2.2. | [-1, 0, 1] |
| `bp-3.5.1.1` | integer | Toxicity label for Biological Process - 3.5.1.1. | [-1, 0, 1] |
| `bp-3.5.1.2` | integer | Toxicity label for Biological Process - 3.5.1.2. | [-1, 0, 1] |
| `bp-3.5.1.3` | integer | Toxicity label for Biological Process - 3.5.1.3. | [-1, 0, 1] |
| `bp-3.5.1.4` | integer | Toxicity label for Biological Process - 3.5.1.4. | [-1, 0, 1] |
| `bp-3.5.1.5` | integer | Toxicity label for Biological Process - 3.5.1.5. | [-1, 0, 1] |
| `bp-3.5.1.6` | integer | Toxicity label for Biological Process - 3.5.1.6. | [-1, 0, 1] |
| `bp-3.5.1.7` | integer | Toxicity label for Biological Process - 3.5.1.7. | [-1, 0, 1] |
| `bp-3.5.1.8` | integer | Toxicity label for Biological Process - 3.5.1.8. | [-1, 0, 1] |
| `bp-3.5.1.9` | integer | Toxicity label for Biological Process - 3.5.1.9. | [-1, 0, 1] |
| `bp-3.5.1.10` | integer | Toxicity label for Biological Process - 3.5.1.10. | [-1, 0, 1] |
| `bp-3.5.1.11` | integer | Toxicity label for Biological Process - 3.5.1.11. | [-1, 0, 1] |
| `bp-3.5.1.12` | integer | Toxicity label for Biological Process - 3.5.1.12. | [-1, 0, 1] |
| `bp-3.5.1.13` | integer | Toxicity label for Biological Process - 3.5.1.13. | [-1, 0, 1] |
| `bp-3.5.1.14` | integer | Toxicity label for Biological Process - 3.5.1.14. | [-1, 0, 1] |
| `bp-3.5.1.15` | integer | Toxicity label for Biological Process - 3.5.1.15. | [-1, 0, 1] |
| `bp-3.5.1.16` | integer | Toxicity label for Biological Process - 3.5.1.16. | [-1, 0, 1] |
| `bp-3.5.1.17` | integer | Toxicity label for Biological Process - 3.5.1.17. | [-1, 0, 1] |
| `bp-3.5.1.18` | integer | Toxicity label for Biological Process - 3.5.1.18. | [-1, 0, 1] |
| `bp-3.5.1.19` | integer | Toxicity label for Biological Process - 3.5.1.19. | [-1, 0, 1] |
| `bp-3.5.1.20` | integer | Toxicity label for Biological Process - 3.5.1.20. | [-1, 0, 1] |
| `bp-3.5.1.21` | integer | Toxicity label for Biological Process - 3.5.1.21. | [-1, 0, 1] |
| `bp-3.5.1.22` | integer | Toxicity label for Biological Process - 3.5.1.22. | [-1, 0, 1] |
| `bp-3.5.1.23` | integer | Toxicity label for Biological Process - 3.5.1.23. | [-1, 0, 1] |
| `bp-3.5.1.24` | integer | Toxicity label for Biological Process - 3.5.1.24. | [-1, 0, 1] |
| `bp-3.5.1.25` | integer | Toxicity label for Biological Process - 3.5.1.25. | [-1, 0, 1] |
| `bp-3.5.1.26` | integer | Toxicity label for Biological Process - 3.5.1.26. | [-1, 0, 1] |
| `bp-3.5.1.27` | integer | Toxicity label for Biological Process - 3.5.1.27. | [-1, 0, 1] |
| `bp-3.5.1.28` | integer | Toxicity label for Biological Process - 3.5.1.28. | [-1, 0, 1] |
| `bp-3.5.1.29` | integer | Toxicity label for Biological Process - 3.5.1.29. | [-1, 0, 1] |
| `bp-3.5.1.30` | integer | Toxicity label for Biological Process - 3.5.1.30. | [-1, 0, 1] |
| `bp-3.5.1.31` | integer | Toxicity label for Biological Process - 3.5.1.31. | [-1, 0, 1] |
| `bp-3.5.1.32` | integer | Toxicity label for Biological Process - 3.5.1.32. | [-1, 0, 1] |
| `bp-3.5.1.33` | integer | Toxicity label for Biological Process - 3.5.1.33. | [-1, 0, 1] |
| `bp-3.5.1.34` | integer | Toxicity label for Biological Process - 3.5.1.34. | [-1, 0, 1] |
| `bp-3.5.1.35` | integer | Toxicity label for Biological Process - 3.5.1.35. | [-1, 0, 1] |
| `bp-3.5.1.36` | integer | Toxicity label for Biological Process - 3.5.1.36. | [-1, 0, 1] |
| `bp-3.5.1.37` | integer | Toxicity label for Biological Process - 3.5.1.37. | [-1, 0, 1] |
| `bp-3.5.1.38` | integer | Toxicity label for Biological Process - 3.5.1.38. | [-1, 0, 1] |
| `bp-3.5.1.39` | integer | Toxicity label for Biological Process - 3.5.1.39. | [-1, 0, 1] |
| `bp-3.5.1.40` | integer | Toxicity label for Biological Process - 3.5.1.40. | [-1, 0, 1] |
| `bp-3.5.1.41` | integer | Toxicity label for Biological Process - 3.5.1.41. | [-1, 0, 1] |
| `bp-3.5.1.42` | integer | Toxicity label for Biological Process - 3.5.1.42. | [-1, 0, 1] |
| `bp-3.5.1.43` | integer | Toxicity label for Biological Process - 3.5.1.43. | [-1, 0, 1] |
| `bp-3.5.1.44` | integer | Toxicity label for Biological Process - 3.5.1.44. | [-1, 0, 1] |
| `bp-3.5.1.45` | integer | Toxicity label for Biological Process - 3.5.1.45. | [-1, 0, 1] |
| `bp-3.5.1.46` | integer | Toxicity label for Biological Process - 3.5.1.46. | [-1, 0, 1] |
| `bp-3.5.1.47` | integer | Toxicity label for Biological Process - 3.5.1.47. | [-1, 0, 1] |
| `bp-3.5.1.48` | integer | Toxicity label for Biological Process - 3.5.1.48. | [-1, 0, 1] |
| `bp-3.5.1.49` | integer | Toxicity label for Biological Process - 3.5.1.49. | [-1, 0, 1] |
| `bp-3.5.1.50` | integer | Toxicity label for Biological Process - 3.5.1.50. | [-1, 0, 1] |
| `bp-3.5.1.51` | integer | Toxicity label for Biological Process - 3.5.1.51. | [-1, 0, 1] |
| `bp-3.5.1.52` | integer | Toxicity label for Biological Process - 3.5.1.52. | [-1, 0, 1] |
| `bp-3.5.1.53` | integer | Toxicity label for Biological Process - 3.5.1.53. | [-1, 0, 1] |
| `bp-3.5.1.54` | integer | Toxicity label for Biological Process - 3.5.1.54. | [-1, 0, 1] |
| `bp-3.5.1.55` | integer | Toxicity label for Biological Process - 3.5.1.55. | [-1, 0, 1] |
| `bp-3.5.1.56` | integer | Toxicity label for Biological Process - 3.5.1.56. | [-1, 0, 1] |
| `bp-3.5.1.57` | integer | Toxicity label for Biological Process - 3.5.1.57. | [-1, 0, 1] |
| `bp-3.5.1.58` | integer | Toxicity label for Biological Process - 3.5.1.58. | [-1, 0, 1] |
| `bp-3.5.1.59` | integer | Toxicity label for Biological Process - 3.5.1.59. | [-1, 0, 1] |
| `bp-3.5.1.60` | integer | Toxicity label for Biological Process - 3.5.1.60. | [-1, 0, 1] |
| `bp-3.5.1.61` | integer | Toxicity label for Biological Process - 3.5.1.61. | [-1, 0, 1] |
| `bp-3.5.1.62` | integer | Toxicity label for Biological Process - 3.5.1.62. | [-1, 0, 1] |
| `bp-3.5.1.63` | integer | Toxicity label for Biological Process - 3.5.1.63. | [-1, 0, 1] |
| `bp-3.5.1.64` | integer | Toxicity label for Biological Process - 3.5.1.64. | [-1, 0, 1] |
| `bp-3.5.1.65` | integer | Toxicity label for Biological Process - 3.5.1.65. | [-1, 0, 1] |
| `bp-3.5.1.66` | integer | Toxicity label for Biological Process - 3.5.1.66. | [-1, 0, 1] |
| `bp-3.5.1.67` | integer | Toxicity label for Biological Process - 3.5.1.67. | [-1, 0, 1] |
| `bp-3.5.1.68` | integer | Toxicity label for Biological Process - 3.5.1.68. | [-1, 0, 1] |
| `bp-3.5.1.69` | integer | Toxicity label for Biological Process - 3.5.1.69. | [-1, 0, 1] |
| `bp-3.5.1.70` | integer | Toxicity label for Biological Process - 3.5.1.70. | [-1, 0, 1] |
| `bp-3.5.1.71` | integer | Toxicity label for Biological Process - 3.5.1.71. | [-1, 0, 1] |
| `bp-3.5.1.72` | integer | Toxicity label for Biological Process - 3.5.1.72. | [-1, 0, 1] |
| `bp-3.5.1.73` | integer | Toxicity label for Biological Process - 3.5.1.73. | [-1, 0, 1] |
| `bp-3.5.1.74` | integer | Toxicity label for Biological Process - 3.5.1.74. | [-1, 0, 1] |
| `bp-3.5.1.75` | integer | Toxicity label for Biological Process - 3.5.1.75. | [-1, 0, 1] |
| `bp-3.5.1.76` | integer | Toxicity label for Biological Process - 3.5.1.76. | [-1, 0, 1] |
| `bp-3.5.1.77` | integer | Toxicity label for Biological Process - 3.5.1.77. | [-1, 0, 1] |
| `bp-3.5.1.78` | integer | Toxicity label for Biological Process - 3.5.1.78. | [-1, 0, 1] |
| `bp-3.5.1.79` | integer | Toxicity label for Biological Process - 3.5.1.79. | [-1, 0, 1] |
| `bp-3.5.1.80` | integer | Toxicity label for Biological Process - 3.5.1.80. | [-1, 0, 1] |
| `bp-3.5.1.81` | integer | Toxicity label for Biological Process - 3.5.1.81. | [-1, 0, 1] |
| `bp-3.5.1.82` | integer | Toxicity label for Biological Process - 3.5.1.82. | [-1, 0, 1] |
| `bp-3.5.1.83` | integer | Toxicity label for Biological Process - 3.5.1.83. | [-1, 0, 1] |
| `bp-3.5.1.84` | integer | Toxicity label for Biological Process - 3.5.1.84. | [-1, 0, 1] |
| `bp-3.5.1.85` | integer | Toxicity label for Biological Process - 3.5.1.85. | [-1, 0, 1] |
| `bp-3.5.1.86` | integer | Toxicity label for Biological Process - 3.5.1.86. | [-1, 0, 1] |
| `bp-3.5.1.87` | integer | Toxicity label for Biological Process - 3.5.1.87. | [-1, 0, 1] |
| `bp-3.5.1.88` | integer | Toxicity label for Biological Process - 3.5.1.88. | [-1, 0, 1] |
| `bp-3.5.1.89` | integer | Toxicity label for Biological Process - 3.5.1.89. | [-1, 0, 1] |
| `bp-3.5.1.90` | integer | Toxicity label for Biological Process - 3.5.1.90. | [-1, 0, 1] |
| `bp-3.5.1.91` | integer | Toxicity label for Biological Process - 3.5.1.91. | [-1, 0, 1] |
| `bp-3.5.1.92` | integer | Toxicity label for Biological Process - 3.5.1.92. | [-1, 0, 1] |
| `bp-3.5.1.93` | integer | Toxicity label for Biological Process - 3.5.1.93. | [-1, 0, 1] |
| `bp-3.5.1.94` | integer | Toxicity label for Biological Process - 3.5.1.94. | [-1, 0, 1] |
| `bp-3.5.1.95` | integer | Toxicity label for Biological Process - 3.5.1.95. | [-1, 0, 1] |
| `bp-3.5.1.96` | integer | Toxicity label for Biological Process - 3.5.1.96. | [-1, 0, 1] |
| `bp-3.5.1.97` | integer | Toxicity label for Biological Process - 3.5.1.97. | [-1, 0, 1] |
| `bp-3.5.1.98` | integer | Toxicity label for Biological Process - 3.5.1.98. | [-1, 0, 1] |
| `bp-3.5.1.99` | integer | Toxicity label for Biological Process - 3.5.1.99. | [-1, 0, 1] |
| `bp-3.5.1.100` | integer | Toxicity label for Biological Process - 3.5.1.100. | [-1, 0, 1] |

*Note: The Tox21 dataset contains 12 endpoints. The table above lists the standard 12 endpoints found in the `deepchem/tox21` dataset. The `smiles` column is the primary key.*

**Filtering Logic**:
- Only rows where the `smiles` string matches the SMARTS pattern `[P](=O)([O,SC])[O,SC]` are retained.
- Rows with invalid SMILES (cannot be parsed by RDKit) are dropped.

## 2. Fingerprint

Represents the binary vector representation of a compound's molecular structure.

**Source**: `data/processed/organophosphates_filtered.csv` (via `code/fingerprints.py`)
**Output**: `data/processed/fingerprints_morgan.pkl`, `data/processed/fingerprints_maccs.pkl`

**Schema**:
| Field | Type | Description |
|:--- |:--- |:--- |
| `mol_id` | string | Foreign Key to `Compound.mol_id`. |
| `morgan_fp` | list[int] | Morgan fingerprint bit vector (length=2048, radius=2). |
| `maccs_fp` | list[int] | MACCS key bit vector (length=166). |
| `smiles` | string | Original SMILES string for reference. |

**Constants**:
- `MORGAN_RADIUS`: 2
- `MORGAN_BITS`: 2048
- `MACCS_BITS`: 166

## 3. Model

Represents a trained Random Forest classifier.

**Source**: `code/train.py`
**Output**: `data/processed/models/fold_{i}_morgan.pkl`, `data/processed/models/fold_{i}_maccs.pkl`

**Schema**:
| Field | Type | Description |
|:--- |:--- |:--- |
| `fold_index` | int | The fold number (0-4). |
| `fingerprint_type` | string | Either "morgan" or "maccs". |
| `model_object` | object | The fitted `sklearn.ensemble.RandomForestClassifier` instance. |
| `feature_importances_` | list[float] | Gini importance scores for each bit. |
| `training_indices` | list[int] | Indices of compounds used for training. |
| `test_indices` | list[int] | Indices of compounds used for testing. |

**Hyperparameters**:
- `n_estimators`: 100
- `max_depth`: 15
- `random_state`: 42

## 4. PerformanceMetric

Represents the evaluation results for a specific model fold.

**Source**: `code/evaluate.py`
**Output**: `data/processed/metrics/fold_{i}_morgan.json`, `data/processed/metrics/fold_{i}_maccs.json`

**Schema**:
| Field | Type | Description |
|:--- |:--- |:--- |
| `fold_index` | int | The fold number (0-4). |
| `fingerprint_type` | string | Either "morgan" or "maccs". |
| `roc_auc` | float | Area Under the Receiver Operating Characteristic Curve. |
| `pr_auc` | float | Area Under the Precision-Recall Curve. |
| `balanced_accuracy` | float | Balanced Accuracy score. |
| `test_indices` | list[int] | Indices of the test set used for this evaluation. |

## 5. StatisticalResult

Aggregated statistical comparison results.

**Source**: `code/evaluate.py`
**Output**: `data/processed/statistical_results.json`

**Schema**:
| Field | Type | Description |
|:--- |:--- |:--- |
| `test_name` | string | "Corrected Resampled t-test (Nadeau & Bengio)". |
| `roc_auc_p_value` | float | P-value for ROC-AUC comparison. |
| `pr_auc_p_value` | float | P-value for PR-AUC comparison. |
| `roc_auc_ci_low` | float | Lower bound of 95% CI for ROC-AUC difference. |
| `roc_auc_ci_high` | float | Upper bound of 95% CI for ROC-AUC difference. |
| `pr_auc_ci_low` | float | Lower bound of 95% CI for PR-AUC difference. |
| `pr_auc_ci_high` | float | Upper bound of 95% CI for PR-AUC difference. |
| `bootstrap_resamples` | int | Number of bootstrap resamples (1000). |

## 6. SC003Analysis

Specific analysis of phosphorus center feature importance.

**Source**: `code/evaluate.py`
**Output**: `data/processed/sc003_analysis.json`

**Schema**:
| Field | Type | Description |
|:--- |:--- |:--- |
| `morgan_p_sum` | float | Sum of Gini importance for Morgan bits within radius 2 of P atom. |
| `maccs_p_sum` | float | Sum of Gini importance for MACCS bits associated with P atom. |
| `morgan_total_importance` | float | Total Gini importance of the Morgan model. |
| `maccs_total_importance` | float | Total Gini importance of the MACCS model. |
| `improvement_ratio` | float | `morgan_p_sum / maccs_p_sum`. |
| `threshold_met` | boolean | True if `morgan_p_sum` > `maccs_p_sum` * 1.15. |
| `conclusion` | string | Human-readable summary of the SC-003 verification. |