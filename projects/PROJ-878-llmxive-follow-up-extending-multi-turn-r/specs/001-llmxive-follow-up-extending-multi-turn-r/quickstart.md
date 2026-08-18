# Quickstart: llmXive follow-up: extending "Multi-Turn Reflective Masking Elicits Reasoning in Mask Diffusion Mode"

## Prerequisites

*   Python 3.11+
*   Git
*   Sufficient RAM (for model loading and dataset processing)
*   ~ GB Disk Space

## Installation

1.  **Clone the repository** (if not already done):
    ```bash
    git clone <repo-url>
    cd projects/PROJ-878-llmxive-follow-up-extending-multi-turn-r
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```

4.  **Verify environment**:
    ```bash
    python -c "import torch; print(torch.__version__); print('CPU available:', torch.cuda.is_available() == False)"
    ```

## Execution Workflow

### Step 1: Generate Synthetic Dataset

Generate a set of logical puzzles with controlled topology and orthogonalized metrics.

```bash
python code/graph_generator.py \
  --count 500 \
  --depth-min 1 \
  --depth-max 10 \
  --branch-min 1 \
  --branch-max 5 \
  --output data/raw/synthetic_puzzles.jsonl \
  --seed 42
```

*   **Output**: `data/raw/synthetic_puzzles.jsonl`
*   **Validation**: Run `python tests/test_graph_generator.py` to verify acyclicity, orthogonality, and metric accuracy.

### Step 2: Execute Reflective Masking Loop

Run the RM inference on the generated dataset (CPU-only).

```bash
python code/rm_executor.py \
  --input data/raw/synthetic_puzzles.jsonl \
  --output data/processed/execution_log.csv \
  --max-turns 50 \
  --batch-size 5 \
  --device cpu
```

*   **Note**: For the extended budget validation (FR-008), run a separate subset with `--max-turns 1000`.
*   **Output**: `data/processed/execution_log.csv`

### Step 3: Statistical Analysis

Perform correlation and sensitivity analysis using Survival Analysis and Segmented Regression.

```bash
python code/analyzer.py \
  --puzzles data/raw/synthetic_puzzles.jsonl \
  --results data/processed/execution_log.csv \
  --output results/statistical_report.json \
  --thresholds 40 50 60
```

*   **Output**: `results/statistical_report.json` and plots in `results/paper_figures/`.

## Verification

1.  **Check Data Integrity**:
    ```bash
    python -c "import json; data = [json.loads(l) for l in open('data/raw/synthetic_puzzles.jsonl')]; print(f'Count: {len(data)}'); print(f'Depth Range: {min(d[\"nesting_depth\"] for d in data)}-{max(d[\"nesting_depth\"] for d in data)}')"
    ```

2.  **Check Results**:
    ```bash
    cat results/statistical_report.json
    ```

## Troubleshooting

*   **OOM Error**: Reduce `--batch-size` in `rm_executor.py`.
*   **Slow Execution**: Ensure no other heavy processes are running; this is CPU-bound.
*   **Invalid Graphs**: If the generator reports many discards, check the `--depth` and `--branch` ranges; extreme combinations may be hard to construct.
*   **High Collinearity**: If the generator fails to find orthogonal samples, reduce the target grid density or relax the `|r| < 0.2` constraint (not recommended for primary analysis).