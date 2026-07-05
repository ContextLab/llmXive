# Data Model: Investigating the Impact of Code Complexity on LLM Code Understanding

## 1. Entity Relationship Overview

The data model consists of three primary entities linked by `function_id`:
1.  **CodeFunction**: The raw code unit and metadata.
2.  **ComplexityMetric**: Derived static analysis scores.
3.  **InferenceResult**: LLM outputs and accuracy scores.

These are merged into a single **AnalysisDataset** for statistical modeling.

## 2. Entity Definitions

### 2.1 CodeFunction
Represents a single function from the source dataset.

| Field | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `function_id` | `string` | Unique identifier (hash of code + dataset source). | Generated |
| `source_dataset` | `string` | Name of the source dataset (e.g., "codesearchnet"). | Metadata |
| `source_code` | `string` | The raw Python source code. | Raw Data |
| `ground_truth_summary` | `string` | Human-written summary (if available). | Raw Data |
| `ground_truth_solution` | `string` | Canonical solution (if available). | Raw Data |
| `task_type` | `string` | "summarization", "completion". (Bug Detection removed). | Derived |

### 2.2 ComplexityMetric
Derived static analysis scores for a `function_id`.

| Field | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `function_id` | `string` | FK to `CodeFunction`. | Join |
| `cyclomatic_complexity` | `integer` | McCabe Cyclomatic Complexity. | `radon` |
| `halstead_volume` | `float` | Halstead Volume. | `radon` |
| `cognitive_complexity` | `integer` | Cognitive Complexity score. | `radon` |
| `line_count` | `integer` | Number of lines of code. | `radon` |
| `parse_error` | `boolean` | True if code could not be parsed. | `radon` |

### 2.3 InferenceResult
Results from LLM inference.

| Field | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `function_id` | `string` | FK to `CodeFunction`. | Join |
| `model_id` | `string` | Identifier of the model used (e.g., "starcoder-1b-gguf"). | Config |
| `task_type` | `string` | Task performed. | Config |
| `generated_output` | `string` | LLM generated text. | Inference |
| `accuracy_score` | `float` | Normalized score (0.0 to 1.0). | Calculated |
| `metric_type` | `string` | "ROUGE-L", "BLEU". | Calculated |
| `hallucination_flag` | `boolean` | True if output was invalid/hallucinated. | Logic |
| `timeout_flag` | `boolean` | True if inference timed out. | Logic |

### 2.4 AnalysisDataset (Merged)
The final table used for `03_analyze_results.py`. This entity is created by **merging** `ComplexityMetric` and `InferenceResult` on `function_id`.

| Field | Type | Description |
| :--- | :--- | :--- |
| `function_id` | `string` | Primary Key |
| `source_dataset` | `string` | Used as a fixed effect covariate. |
| `cyclomatic_complexity` | `integer` | From `ComplexityMetric` |
| `halstead_volume` | `float` | From `ComplexityMetric` |
| `cognitive_complexity` | `integer` | From `ComplexityMetric` |
| `complexity_index` | `float` | PCA-derived composite complexity score. |
| `accuracy_score` | `float` | From `InferenceResult` |
| `task_type` | `string` | From `InferenceResult` |
| `model_id` | `string` | From `InferenceResult` |
| `valid_for_analysis` | `boolean` | True if no parse/timeout errors. |

## 3. Data Flow

1.  **Raw Data** (Parquet) -> **CodeFunction** (CSV) via `00_download_data.py`
2.  **CodeFunction** -> **ComplexityMetric** (CSV) via `01_compute_metrics.py`
3.  **CodeFunction** + **Model Config** -> **InferenceResult** (CSV) via `02_run_inference.py`
4.  **ComplexityMetric** + **InferenceResult** -> **AnalysisDataset** (CSV) via `03_analyze_results.py` (Merge Step)

## 4. Data Constraints

- **Uniqueness**: `function_id` must be unique within `ComplexityMetric` and `InferenceResult`.
- **Non-Negative**: `cyclomatic_complexity`, `cognitive_complexity`, `line_count` >= 0.
- **Range**: `accuracy_score` in [0.0, 1.0].
- **Not Null**: `function_id`, `accuracy_score`, `cyclomatic_complexity` in `AnalysisDataset`.