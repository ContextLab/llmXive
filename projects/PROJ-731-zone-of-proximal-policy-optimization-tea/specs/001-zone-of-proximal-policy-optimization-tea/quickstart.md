# Quickstart: Zone of Proximal Policy Optimization

## Prerequisites

- Python 3.11+
- Git
- Access to a GitHub Actions runner (or local environment with 7GB+ RAM, 2+ CPU cores).

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-731-zone-of-proximal-policy-optimization-tea
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```

## Running the Training Loop

To run a single training experiment (e.g., 10k prompts, seed 42):

```bash
python code/train_ppo.py \
  --prompt-size 10000 \
  --seed 42 \
  --max-steps 1000 \
  --output-dir results/
```

**Arguments**:
- `--prompt-size`: Number of teacher demonstrations (0, 10000, 50000, 200000).
- `--seed`: Random seed for reproducibility.
- `--max-steps`: Maximum PPO iterations (default 1000).
- `--output-dir`: Directory to save logs and checkpoints.

## Evaluating Benchmarks

To evaluate a specific checkpoint on all three benchmarks:

```bash
python code/eval_benchmarks.py \
  --checkpoint results/checkpoints/checkpoint_200 \
  --benchmarks lambada_openai truthful_qa mmlu \
  --output results/benchmarks/eval_200.csv
```

## Analyzing Results

After running multiple seeds (e.g., 3 per condition), aggregate the data:

```bash
python code/analyze.py \
  --input results/analysis/aggregated.csv \
  --output results/analysis/regression_results.json
```

This will compute the piecewise-linear regression breakpoint and confidence intervals for the diminishing returns hypothesis.

## Troubleshooting

- **Memory Error**: If you encounter OOM, reduce `--prompt-size` or `--batch-size`. The system will automatically log `MEMORY_FALLBACK` if it samples the buffer.
- **Dataset Access**: Ensure you have internet access to download `oasst1` and benchmarks.
- **Timeout**: If the job exceeds 6 hours, the process will be terminated. The last checkpoint will be saved.
