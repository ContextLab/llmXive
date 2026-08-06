# Data Model: Comparative Analysis of Molecular Fingerprints for Pesticide Toxicity Prediction

This document defines the core data entities, their schemas, and relationships for the project.
These definitions serve as the contract between data acquisition, processing, modeling, and evaluation stages.

## 1. Compound

Represents a unique chemical entity derived from the Tox21 dataset, filtered for organophosphates.

| Field Name | Type | Description | Constraints |
|:--- |:--- |:--- |:--- |
| `compound_id` | string | Unique identifier (e.g., DSSTox ID or hash) | Primary Key, Non-null |
| `smiles` | string | Canonical SMILES string representing the molecular structure | Non-null, Valid RDKit parseable string |
| `inchi_key` | string | Standard InChI Key for deduplication | Unique, Non-null |
| `molecular_weight` | float | Calculated molecular weight (g/mol) | > 0 |
| `is_organophosphate` | boolean | Flag indicating if the compound matches the SMARTS pattern `[P](=O)([O,SC])[O,SC]` | True (after filtering) |
| `toxicity_labels` | dict | Dictionary mapping endpoint names to binary labels (0/1) or null | Keys: `NR-AR`, `NR-AR-LBD`, `NR-AhR`, etc. |

**Source**: `data/processed/organophosphates_filtered.csv`
**Schema Version**: 1.0

## 2. Fingerprint

Represents the binary vector encoding of a compound's molecular structure, generated via RDKit.

| Field Name | Type | Description | Constraints |
|:--- |:--- |:--- |:--- |
| `compound_id` | string | Foreign key referencing `Compound.compound_id` | Foreign Key |
| `fingerprint_type` | string | Type of fingerprint: `Morgan` or `MACCS` | Enum: ['Morgan', 'MACCS'] |
| `parameters` | dict | Configuration used for generation (e.g., radius, bits) | JSON object |
| `bit_vector` | list[int] | The binary fingerprint vector (0 or 1) | Length: 2048 (Morgan) or 166 (MACCS) |
| `generated_at` | timestamp | ISO 8601 timestamp of generation | Non-null |

**Source**: Intermediate memory objects or `data/processed/fingerprints.pkl`
**Schema Version**: 1.0

## 3. Model

Represents a trained machine learning model (Random Forest) associated with a specific fingerprint type and split configuration.

| Field Name | Type | Description | Constraints |
|:--- |:--- |:--- |:--- |
| `model_id` | string | Unique identifier for the model instance | Primary Key |
| `model_type` | string | Algorithm used (e.g., `RandomForestClassifier`) | Non-null |
| `fingerprint_type` | string | Input feature type (`Morgan` or `MACCS`) | Enum: ['Morgan', 'MACCS'] |
| `hyperparameters` | dict | Training parameters (e.g., `n_estimators`, `max_depth`) | JSON object |
| `split_config` | string | Identifier for the data split used (e.g., `single_held_out`, `kfold_0`) | Non-null |
| `artifact_path` | string | Relative path to the serialized model file (`.pkl`) | Valid file path |
| `trained_at` | timestamp | ISO 8601 timestamp of training | Non-null |

**Source**: `data/processed/final_models.pkl` (serialized object metadata)
**Schema Version**: 1.0

## 4. PerformanceMetric

Represents the quantitative evaluation results of a model on a specific dataset split.

| Field Name | Type | Description | Constraints |
|:--- |:--- |:--- |:--- |
| `metric_id` | string | Unique identifier for the metric record | Primary Key |
| `model_id` | string | Foreign key referencing `Model.model_id` | Foreign Key |
| `split_config` | string | The data split configuration used for evaluation | Non-null |
| `metric_name` | string | Name of the metric (e.g., `roc_auc`, `pr_auc`) | Enum: ['roc_auc', 'pr_auc'] |
| `value` | float | The calculated score | 0.0 <= value <= 1.0 |
| `confidence_interval` | list[float] | 95% CI bounds [lower, upper] (if applicable) | Optional |
| `p_value` | float | Statistical significance value (if applicable) | 0.0 <= value <= 1.0 |
| `evaluated_at` | timestamp | ISO 8601 timestamp of evaluation | Non-null |

**Source**: `data/processed/final_test_metrics.json`, `data/processed/kfold_scores.json`, `data/processed/sc003_analysis.json`
**Schema Version**: 1.0

## Data Flow & Relationships

1. **Compound** is the foundational entity.
2. **Fingerprint** is derived from **Compound** (1:1 or 1:N relationship depending on fingerprint types generated).
3. **Model** is trained on **Fingerprint** data partitioned by a **Split**.
4. **PerformanceMetric** is calculated by evaluating **Model** on a held-out set of **Fingerprints** and **Compound** labels.

## Constraints & Validation Rules

- **SMARTS Filter**: All `Compound` records must satisfy the pattern `[P](=O)([O,SC])[O,SC]` to be included in the analysis.
- **Fingerprint Consistency**: Morgan fingerprints must have exactly 2048 bits; MACCS must have 166 bits. [UNRESOLVED-CLAIM: c_f94f7e14 — status=not_enough_info]
- **Split Integrity**: The Tanimoto similarity between any compound in the test set and any compound in the training set must be < 0.85 (Greedy Maximal Dissimilarity constraint).
- **Statistical Rigor**: Corrected Resampled t-test (Nadeau & Bengio) is applied to `roc_auc` scores from K-Fold splits only.