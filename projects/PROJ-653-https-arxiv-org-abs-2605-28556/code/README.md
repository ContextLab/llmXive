# TASTE Adaptation: Coverage & Difficulty Analysis (CPU Scaled)

## Purpose
This adaptation reproduces the **core quantitative claim** of the TASTE paper:
> "Our generated tasks more than double the number of unique tool combinations agents must execute."

Instead of running the full LLM-driven generation pipeline (which requires Vertex AI credentials, expensive API calls, and hours of compute), this script:
1.  **Loads existing artifacts** from the `artifacts/` directory (pre-computed n-gram models and task sets).
2.  **Simulates the "TASTE" process** by extracting tool sequences from:
    *   **Base Tasks**: Existing `tau2`-Bench tasks (from `artifacts/domains/*/tasks.json`).
    *   **Synthetic Tasks**: Representative sequences from the TASTE-generated clusters (from `artifacts/validated_clusters/` and `artifacts/task_sets/`).
3.  **Computes the metric**: Counts unique tool combinations (n-grams of tool names) in both sets.
4.  **Outputs**: A CSV report and a bar chart showing the "Coverage Ratio" (Synthetic vs. Base).

## Simplifications vs. Original
| Feature | Original Paper | This Adaptation |
| :--- | :--- | :--- |
| **Data Source** | Real-time LLM generation + iterative evolution | Pre-saved checkpoints & task sets (no LLM calls) |
| **Tool Sequence Extraction** | LLM parsing of generated scenarios | Direct JSON parsing of `tool_sequence` fields |
| **Scale** | Thousands of generated tasks | ~50 tasks per domain (sampled from artifacts) |
| **Complexity** | Multi-stage pipeline (N-gram → Cluster → Evolve) | Single-stage analysis (Load → Count → Compare) |
| **Compute** | GPU/TPU for LLM inference | Pure CPU (pandas, json, matplotlib) |

## Dependencies
- `pandas`
- `matplotlib`
- `numpy`
- `json` (stdlib)

## How to Run
```bash
python code/analyze_coverage.py
```
This will generate:
- `data/coverage_results.csv`: Detailed metrics per domain.
- `figures/coverage_comparison.png`: Visual comparison of tool diversity.
