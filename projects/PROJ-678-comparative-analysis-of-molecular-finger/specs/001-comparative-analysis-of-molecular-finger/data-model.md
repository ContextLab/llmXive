# Data Model: Comparative Analysis of Molecular Fingerprints for Pesticide Toxicity Prediction

This document defines the core data entities, their schemas, and relationships used throughout the `PROJ-678-comparative-analysis-of-molecular-fingerprints` pipeline.

## 1. Compound

Represents a chemical entity from the source dataset (Tox21), filtered for organophosphates.

**Source**: `data/raw/tox21_raw.csv` (derived from HuggingFace `deepchem/tox`)
**Filtered Output**: `data/processed/organophosphates_filtered.csv`

### Schema

| Column Name | Type | Description | Constraints |
|:--- |:--- |:--- |:--- |
| `compound_id` | str | Unique identifier (e.g., DSSTox ID or HuggingFace index) | Primary Key, Non-null |
| `smiles` | str | Canonical SMILES string representing the molecular structure | Non-null, Valid RDKit parseable string |
| `has_phosphorus` | bool | Flag indicating if the molecule contains a Phosphorus atom | Non-null, Derived from SMARTS filter |
| `n_endpoints` | int | Count of toxicity endpoints available for this compound | Non-null, ≥ 0 |
| `labels` | dict | Dictionary mapping endpoint names to binary labels (0/1) or null | Non-null, Keys match endpoint list |
| `molecular_weight` | float | Calculated molecular weight | Nullable, ≥ 0 |

### Constraints & Validation
- **SMARTS Filter**: Must match `[P](=O)([O,SC])[O,SC]` to be included in the filtered dataset.
- **Label Integrity**: Rows with missing labels for all endpoints are excluded during `code/filter.py` validation.
- **Data Types**: All floating point values must be IEEE 754 compliant; NaNs allowed for optional metrics but not for core identifiers.

---

## 2. Fingerprint

Represents the binary bit-vector representation of a `Compound` used for similarity calculations and model input.

**Generation**: `code/fingerprints.py`
**Output**: `data/processed/fingerprints_morgan.pkl`, `data/processed/fingerprints_maccs.pkl`

### Schema

| Attribute | Type | Description | Constraints |
|:--- |:--- |:--- |:--- |
| `compound_id` | str | Reference to the `Compound` primary key | Foreign Key to Compound |
| `type` | str | Fingerprint algorithm: `"MORGAN"` or `"MACCS"` | Enum: ["MORGAN", "MACCS"] |
| `bits` | int | Total number of bits in the vector | Morgan: 2048, MACCS: 166 |
| `radius` | int | Radius parameter (only for Morgan) | Morgan: 2, MACCS: N/A |
| `vector` | ndarray | Binary vector (uint8 or bool) of length `bits` | Shape: `(bits,)`, Values: {0, 1} |
| `bit_info` | dict | Mapping of bit index to atom indices (for Morgan) | Only for Morgan; used for feature importance |

### Configuration Constants (from `code/constants.py`)
- `MORGAN_RADIUS = 2`
- `MORGAN_BITS = 2048`
- `MACCS_BITS = 166`

---

## 3. Model

Represents a trained Random Forest classifier for a specific fingerprint type and cross-validation fold.

**Training**: `code/train.py`
**Output**: `data/processed/models/fold_{fold}_{type}.pkl`

### Schema

| Attribute | Type | Description | Constraints |
|:--- |:--- |:--- |:--- |
| `model_id` | str | Unique identifier: `fold_{fold}_{type}` | Primary Key |
| `fold_index` | int | Cross-validation fold number (0-4) | Range: [0, 4] |
| `fingerprint_type` | str | Input fingerprint type: `"MORGAN"` or `"MACCS"` | Enum: ["MORGAN", "MACCS"] |
| `algorithm` | str | ML Algorithm used | Value: `"RandomForestClassifier"` |
| `n_estimators` | int | Number of trees in the forest | Value: 100 |
| `max_depth` | int | Maximum depth of the tree | Value: 15 |
| `feature_importances_` | ndarray | Gini importance of each feature | Shape: `(bits,)`, Sum = 1.0 |
| `random_state` | int | Seed for reproducibility | Value: 42 |
| `trained_at` | datetime | Timestamp of model creation | ISO 8601 format |

### Relationships
- Associated with exactly one `Fingerprint` type.
- Evaluated against specific `PerformanceMetric` records.

---

## 4. PerformanceMetric

Represents the evaluation results of a `Model` on a specific `Fold`.

**Evaluation**: `code/evaluate.py`
**Output**: `data/processed/cv_scores.json`, `data/processed/research_results.md`

### Schema

| Attribute | Type | Description | Constraints |
|:--- |:--- |:--- |:--- |
| `metric_id` | str | Unique ID: `fold_{fold}_{type}_{metric_name}` | Primary Key |
| `model_id` | str | Reference to the trained `Model` | Foreign Key to Model |
| `fold_index` | int | The CV fold index | Range: [0, 4] |
| `fingerprint_type` | str | Input fingerprint type | Enum: ["MORGAN", "MACCS"] |
| `metric_name` | str | Type of metric | Enum: ["ROC_AUC", "PR_AUC", "BALANCED_ACC"] |
| `value` | float | Calculated metric score | Range: [0.0, 1.0] |
| `ci_lower` | float | Lower bound of 95% CI (if applicable) | Nullable |
| `ci_upper` | float | Upper bound of 95% CI (if applicable) | Nullable |

### Aggregation Schema (`cv_scores.json`)
The evaluation process aggregates these records into a structured JSON:
```json
{
 "morgan": {
 "roc_auc": [float, float, float, float, float],
 "pr_auc": [float, float, float, float, float],
 "balanced_acc": [float, float, float, float, float]
 },
 "maccs": {
 "roc_auc": [...],
 "pr_auc": [...],
 "balanced_acc": [...]
 }
}
```

---

## 5. Statistical Result (Derived Entity)

Represents the outcome of the comparative statistical analysis between Morgan and MACCS models.

**Analysis**: `code/evaluate.py` (Corrected Resampled t-test, Bootstrap)
**Output**: `data/processed/statistical_results.json`

### Schema

| Attribute | Type | Description | Constraints |
|:--- |:--- |:--- |:--- |
| `analysis_id` | str | Unique identifier: `stat_comparison_{metric}` | Primary Key |
| `metric` | str | Metric being compared | Enum: ["ROC_AUC", "PR_AUC"] |
| `p_value` | float | Result of Corrected Resampled t-test | Range: [0.0, 1.0] |
| `t_statistic` | float | t-statistic value | Nullable |
| `bootstrap_ci` | dict | 95% CI from 1000 bootstrap resamples | Keys: "lower", "upper" |
| `significant` | bool | True if p-value < 0.05 | Derived |
| `sc003_analysis` | dict | Feature importance analysis for Phosphorus | Contains "morgan_mean", "maccs_mean", "exceeds_threshold" |

### SC-003 Specific Fields
- `morgan_mean`: Mean Gini importance of bits near Phosphorus (Sum / 2048).
- `maccs_mean`: Mean Gini importance of bits near Phosphorus (Sum / 166).
- `exceeds_threshold`: Boolean indicating if `morgan_mean > maccs_mean * 1.15`.

---

## Data Flow Summary

1. **Raw Data**: `tox21` -> `code/download.py` -> `data/raw/tox21.csv`
2. **Filtering**: `tox21.csv` -> `code/filter.py` (SMARTS) -> `data/processed/organophosphates_filtered.csv` (Compound)
3. **Fingerprinting**: `filtered.csv` -> `code/fingerprints.py` -> `data/processed/fingerprints_*.pkl` (Fingerprint)
4. **Splitting**: `fingerprints` -> `code/split.py` -> `data/processed/split_fold_*.json`
5. **Training**: `splits` + `fingerprints` -> `code/train.py` -> `data/processed/models/*.pkl` (Model)
6. **Evaluation**: `models` -> `code/evaluate.py` -> `data/processed/cv_scores.json`, `research_results.md` (PerformanceMetric, Statistical Result)