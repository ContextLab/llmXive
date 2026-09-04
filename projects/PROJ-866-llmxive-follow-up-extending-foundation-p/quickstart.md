# Quickstart Guide: llmXive Foundation Protocol

This guide walks you through generating a synthetic workflow baseline, executing them with full and compressed context, and analyzing the trade-off between context reduction and policy violation rates.

## Prerequisites

- Python 3.9+
- Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## 1. Generate Synthetic Workflows (500 Workflows)

Generate a deterministic set of 500 synthetic workflows with varying depths (1-20) and complexities. These are saved to `data/raw/`.

```bash
python code/main.py generate --count 500 --output-dir data/raw/
```

**Output**:
- `data/raw/workflows_*.json`: Individual workflow definitions.
- `data/raw/workflow_manifest.json`: Summary of generated IDs, depths, and metadata.

## 2. Execute with Full Context (Ground Truth)

Run the generated workflows through the Oracle Policy Engine and Full Context Engine to establish ground-truth validity and execution logs.

```bash
python code/main.py execute-full --input-dir data/raw/ --output-dir data/processed/
```

**Output**:
- `data/processed/full_context_log_*.json`: Execution logs with ground-truth validity flags.

## 3. Execute with Compressed Context

Run the same workflows using compressed context (BFS/DFS truncation) at various depth levels to measure token reduction and violation rates.

```bash
python code/main.py execute-compressed --input-dir data/raw/ --output-dir data/processed/ --depths 1 2 3 5 10
```

**Output**:
- `data/processed/compressed_context_log_depth_*.json`: Execution logs for each compression depth.

## 4. Analyze Trade-off and Identify Safe Threshold

Perform statistical analysis to model the trade-off curve and identify the maximum context reduction that keeps error rates ≤ 1%.

```bash
python code/main.py analyze --input-dir data/processed/ --output-dir data/results/
```

**Output**:
- `data/results/tradeoff_curve.csv`: Regression data points (token reduction % vs. error rate).
- `data/results/threshold_ci.json`: The calculated safe threshold with 95% confidence intervals.
- `data/results/analysis_summary.json`: High-level summary of the safe operating zone.

## 5. Verify Results

Ensure the generated artifacts match the expected schemas:

```bash
python -m pytest tests/
```

## Full Pipeline Execution

To run the entire pipeline from generation to analysis in one step:

```bash
python code/main.py full-pipeline --count 500 --depths 1 2 3 5 10
```

This command executes steps 1 through 4 sequentially, saving all artifacts to their respective directories.