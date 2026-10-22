# Data Model: Statistical Analysis of Code Complexity Metrics and Bug Prediction

## Core Entities

### FunctionMetric
Represents a single Java function/method together with its static‑analysis metrics and outcome label.

| Attribute | Type | Description |
|-----------|------|-------------|
| `function_id` | string (UUID) | Unique identifier for the function unit |
| `project_id` | string | Identifier of the originating repository |
| `file_path` | string | Relative path to the .java file |
| `function_name` | string | Name of the function/method |
| `start_line` | integer | Starting line number (1‑based) |
| `end_line` | integer | Ending line number (1‑based) |
| `cyclomatic_complexity` | integer | CC metric (non‑negative) |
| `loc` | integer | Lines of Code (non‑negative) |
| `token_count` | integer | Number of lexical tokens (non‑negative) |
| `nesting_depth` | integer | Maximum nesting depth (non‑negative) |
| `halstead_volume` | float | Halstead Volume |
| `bug_label` | integer (0/1) | 1 = function modified in a bug‑fix commit, 0 = otherwise |
| `split` | string (`train`/`test`) | Project‑level dataset split assignment (VIF threshold > 10 applied uniformly) |

All numeric fields are non‑negative; `cyclomatic_complexity` and `nesting_depth` are integers. Skewed continuous variables (`loc`, `token_count`, `halstead_volume`) are log‑transformed during preprocessing (FR‑004).

### ModelResult
Captures evaluation metrics and feature‑level statistics for a trained model.

| Attribute | Type | Description |
|-----------|------|-------------|
| `model_type` | string | `"LogReg_L1"` or `"RandomForest"` |
| `roc_auc` | float | ROC‑AUC on the held‑out test set |
| `pr_auc` | float | Precision‑Recall AUC on test |
| `calibration_error` | float | Brier score (lower = better) |
| `feature_importance` | array of objects | Each object: `feature_name`, `importance_score`, `p_value` (after FDR), `is_significant` |
| `stability_correlation` | float | Spearman correlation of feature importance between the two models |
| `partial_dependence` | array of objects | Top‑3 metrics with practical thresholds (`metric_name`, `threshold`, `justification`) |

## Data Flow Overview
1. **Raw Ingestion** – `download_gh.py` pulls GHTorrent archives → stored in `data/raw/`.  
2. **Extraction** – `extract_metrics.py` runs `lizard` on each pre‑fix snapshot → populates `FunctionMetric` rows (excluding bug‑fix commits).  
3. **Labeling** – `label_bugs.py` matches commit messages/issue references → sets `bug_label`.  
4. **Preprocessing** – `preprocess.py` handles missingness (< 5 %), log‑transforms skewed vars, computes VIF, drops high‑VIF predictors (> 10), and assigns `split` (project‑level stratified). Output: `data/processed/bug_complexity_dataset.csv`.  
5. **Modeling** – `train.py` fits L1 LogReg and Random Forest; `evaluate.py` computes `ModelResult` objects and writes `data/model/*.csv` and `data/model/*.pkl`.  

All artifacts are validated against the contracts in `contracts/`.

## Privacy & Hygiene (Constitutional Alignment)
- **PII**: No personal data is stored; only repository‑level identifiers.  
- **Checksums**: Every file in `data/raw/` and `data/processed/` has a cryptographic hash checksum recorded in `state/`.  
- **Versioning**: Content hashes are stored alongside each artifact (Constitution V).  

---


