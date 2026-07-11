# Data Model: llmXive follow-up: extending "MiniMax Sparse Attention"

## Overview
This document defines the data structures for the RULER benchmark evaluation, heuristic scoring, and result aggregation. All data is stored in `data/` (raw and processed) and `code/` (in-memory structures).

## Entity Definitions

### 1. RulerTask
Represents a single evaluation instance from the RULER benchmark.

| Field | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `task_id` | `str` | Unique identifier for the task (e.g., "NIAH-128k-1"). | RULER JSONL |
| `task_type` | `str` | Type of task: "NeedleInAHaystack" or "MultiHop". | RULER JSONL |
| `context_length` | `int` | Total number of tokens in the context. | RULER JSONL |
| `context_text` | `str` | The full context string (haystack). | RULER JSONL |
| `needle_text` | `str` | The hidden "needle" string to retrieve. | RULER JSONL |
| `needle_position` | `int` | Token index where the needle starts. | RULER JSONL |
| `query` | `str` | The question asked about the context. | RULER JSONL |
| `expected_answer` | `str` | Ground truth answer for EM/F1 calculation. | RULER JSONL |
| `block_size` | `int` | Fixed block size used for chunking (e.g., 512). | Config |
| `blocks` | `List[str]` | List of block strings derived from `context_text`. | Derived |

### 2. HeuristicScore
Represents the importance score calculated for a specific block by a heuristic.

| Field | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `task_id` | `str` | Reference to the RulerTask. | RulerTask |
| `block_index` | `int` | Index of the block in the sequence. | Derived |
| `heuristic_name` | `str` | Name of the heuristic: "GradientMagnitude", "Entropy", "RecencyBias". | Config |
| `score` | `float` | The scalar importance score. | Heuristic Logic |
| `gradient_norm` | `float` | (Optional) L2 norm of input gradients for this block. | Heuristic Logic |
| `entropy_value` | `float` | (Optional) Shannon entropy of the block. | Heuristic Logic |

### 3. EvaluationResult
Aggregated result for a single task run with a specific heuristic.

| Field | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `run_id` | `str` | Unique identifier for the run (timestamp + config hash). | System |
| `task_id` | `str` | Reference to the RulerTask. | RulerTask |
| `heuristic_name` | `str` | Heuristic used. | Config |
| `k_value` | `int` | The Top-k selection cutoff used. | Config |
| `selected_blocks` | `List[int]` | Indices of the selected blocks. | Heuristic Logic |
| `generated_text` | `str` | Model output for the query. | Model Inference |
| `exact_match` | `float` | 1.0 if `generated_text` == `expected_answer`, else 0.0. | Metrics |
| `f1_score` | `float` | F1 score for Multi-Hop tasks. | Metrics |
| `cpu_time_ms` | `float` | Total CPU time for the task (inference + heuristic). | System |
| `heuristic_time_ms` | `float` | Time spent only on heuristic calculation (isolated). | System |
| `inference_time_ms` | `float` | Time spent only on model inference (isolated). | System |
| `memory_peak_mb` | `float` | Peak memory usage during the task. | System |

### 4. StatisticalSummary
Aggregated statistics for the final report.

| Field | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `heuristic_name` | `str` | Heuristic name. | Config |
| `baseline_name` | `str` | Baseline name (e.g., "Dense"). | Config |
| `mean_accuracy` | `float` | Mean Exact Match/F1 across all tasks. | Aggregation |
| `std_accuracy` | `float` | Standard deviation of accuracy. | Aggregation |
| `delta_accuracy` | `float` | `mean_accuracy` (Heuristic) - `mean_accuracy` (Baseline). | Aggregation |
| `tost_p_value` | `float` | P-value from TOST equivalence test. | Stats |
| `tost_ci_lower` | `float` | Lower bound of 90% CI for mean difference. | Stats |
| `tost_ci_upper` | `float` | Upper bound of 90% CI for mean difference. | Stats |
| `is_equivalent` | `bool` | True if CI is within [-0.02, +0.02]. | Stats |
| `avg_cpu_time_ms` | `float` | Mean CPU time. | Aggregation |
| `avg_memory_mb` | `float` | Mean memory usage. | Aggregation |

## Data Flow

1.  **Ingestion**: `ruler_loader.py` reads RULER JSONL, validates fields, and splits `context_text` into `blocks` based on `block_size`.
2.  **Heuristic Calculation**: For each task, `gradient_magnitude.py` or `block_entropy.py` calculates scores for all blocks, producing `HeuristicScore` objects.
3.  **Selection**: The top-k blocks are selected based on `HeuristicScore`.
4.  **Inference**: The model runs inference using only the selected blocks (sparse attention).
5.  **Scoring**: `metrics.py` calculates `exact_match` and `f1_score`, populating `EvaluationResult`.
6.  **Aggregation**: `stats.py` aggregates `EvaluationResult` into `StatisticalSummary`.

## Constraints

-   **Block Alignment**: `context_text` must be divisible by `block_size`. If not, the last block is padded or truncated (logged).
-   **Memory**: `context_text` and `blocks` are processed in a streaming fashion to avoid loading the entire dataset into RAM.
-   **Precision**: All floating-point scores are stored as `float64` for statistical accuracy.