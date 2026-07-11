# Data Model: llmXive follow-up: extending "MiniMax Sparse Attention"

## 1. Conceptual Model

The data model revolves around the evaluation of a `HeuristicSelector` against a `DenseBaseline` on a `RulerTask` instance.

- **RulerTask**: A single sample from the RULER dataset, containing a long context, a "needle" (target), and a question.
- **ContextBlock**: A chunk of the context window (e.g., 4k tokens) with associated metadata (position, entropy, gradient norm).
- **SelectionResult**: The set of blocks selected by a specific heuristic or the full set (for Dense Baseline).
- **EvaluationMetric**: The computed scores (EM, F1, PPL) for a specific `SelectionResult` on a `RulerTask`.
- **ExperimentRun**: A record of a full pass over the dataset with a specific configuration (heuristic, threshold).

## 2. Physical Data Model (JSON Schema)

The system outputs results to JSON files. The primary artifact is `benchmark_report.json`.

### 2.1 `benchmark_report.json` Structure

```json
{
  "experiment_id": "uuid",
  "timestamp": "ISO8601",
  "config": {
    "model": "MiniMax-M3",
    "device": "cpu",
    "context_window": 4096,
    "heuristics": ["entropy", "gradient", "recency"],
    "thresholds": [0.01, 0.05, 0.1],
    "baseline_type": "dense_attention"
  },
  "results": [
    {
      "task_id": "ruler_niah_001",
      "heuristic": "entropy",
      "threshold": 0.05,
      "metrics": {
        "exact_match": 0.0,
        "f1": 0.85,
        "perplexity": 12.5,
        "selected_blocks_count": 10,
        "execution_time_ms": 1200,
        "false_positive_rate": 0.05
      },
      "baseline_metrics": {
        "f1": 0.88,
        "perplexity": 11.2
      }
    }
  ],
  "statistics": {
    "paired_t_test": {
      "statistic": 150.0,
      "p_value": 0.04,
      "significant": true,
      "correction": "holm_bonferroni"
    },
    "wilcoxon_test": {
      "statistic": 150.0,
      "p_value": 0.06,
      "significant": false
    },
    "sensitivity_analysis": [
      {
        "threshold": 0.01,
        "mean_f1": 0.82,
        "false_positive_rate": 0.05
      }
    ]
  }
}
```

## 3. Data Processing Pipeline

1. **Ingestion**: `RulerTask` objects are streamed from `data/raw/ruler.jsonl`.
2. **Transformation**:
   - `ContextBlock` objects are generated via `preprocess.py` (chunking).
   - Heuristic scores are computed and attached to blocks.
3. **Selection**: `HeuristicSelector` filters blocks to produce `SelectionResult`.
4. **Evaluation**: `EvaluationMetric` is computed by comparing model output to the ground truth needle.
5. **Aggregation**: `ExperimentRun` aggregates metrics per task and heuristic.
6. **Output**: Final `benchmark_report.json` is written to `results/`.

## 4. Constraints & Validation

- **Max Context**: 4096 tokens per block (to fit RAM).
- **Max Batch Size**: 4 (for gradient computation).
- **Data Integrity**: All raw files must match checksums recorded in `state/`.
- **Null Handling**: If a needle is missing, the task is skipped and logged.
- **Baseline Definition**: `baseline_metrics` must always reflect **Dense Attention** (Full Context) performance.