# Quickstart: llmXive follow-up: extending "Self-Distilled Agentic Reinforcement Learning"

## Prerequisites

- Python 3.11+
- 8GB RAM (minimum for CPU quantization)
- Git

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-825-llmxive-follow-up-extending-self-distill/code/
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Running the Experiments

### 1. GRPO Baseline (ALFWorld)

Run the standard GRPO baseline:

```bash
python main.py \
  --variant grpo \
  --env alfworld \
  --seed 42 \
  --max-steps 1000 \
  --output-dir data/processed/grpo-alfworld
```

### 2. Baseline SDAR Variant (ALFWorld)

Run the dual-model baseline for comparison (Same Architecture Teacher/Student):

```bash
python main.py \
  --variant baseline \
  --env alfworld \
  --seed 42 \
  --max-steps 1000 \
  --output-dir data/processed/baseline-alfworld
```

### 3. Student-Only Variant (ALFWorld)

Run the training loop with the student-only gating mechanism:

```bash
python main.py \
  --variant student-only \
  --env alfworld \
  --seed 42 \
  --max-steps 1000 \
  --output-dir data/processed/student-only-alfworld
```

### 4. Paired Trajectory Replay (For Correlation Analysis)

After running Baseline, replay its trajectories through the Student-Only agent:

```bash
python main.py \
  --variant student-only-replay \
  --env alfworld \
  --input-trajectories data/processed/baseline-alfworld/trajectories.jsonl \
  --output-dir data/processed/student-only-replay-alfworld
```

### 5. Statistical Analysis

After completing 5 runs for each variant, run the analysis script:

```bash
python metrics/statistical_test.py \
  --grpo-dir data/processed/grpo-alfworld \
  --baseline-dir data/processed/baseline-alfworld \
  --student-only-dir data/processed/student-only-alfworld \
  --replay-dir data/processed/student-only-replay-alfworld \
  --output data/processed/comparison_report.json
```

## Expected Outputs

- `data/processed/<variant>-<env>.jsonl`: Step-level metrics.
- `data/processed/episode_metrics.parquet`: Episode-level metrics for bootstrapping.
- `data/processed/comparison_report.json`: Statistical summary (p-value, cost reduction, performance retention, effect size).
- `data/processed/correlation_analysis.csv`: Correlation between heuristics and teacher gaps on paired data.

## Troubleshooting

- **OOM Error**: If you encounter "Out of Memory", reduce the context window size in `config.py` or use a smaller retriever model.
- **NaN Gating Scores**: Check `data/processed/` for `is_valid=False` entries. This may indicate unstable context retrieval.
- **Slow Execution**: Ensure you are running on a CPU with AVX support. If using Kaggle GPU, the `device="cuda"` flag is automatically set if the CPU run fails.
- **Early Stopping**: If runs finish too quickly, check the `--max-steps` flag or the reward threshold in `config.py`.