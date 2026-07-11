# Quickstart: llmXive follow-up: extending "APPO: Agentic Procedural Policy Optimization"

## Prerequisites

- Python 3.11+
- Git
- Sufficient RAM available (free-tier runner)

The research question remains: [Research Question]
The method remains: [Method]
The references remain: [References]

## Installation

1. **Clone the repository** (if not already done):
   ```bash
   git clone <repo-url>
   cd projects/PROJ-861-llmxive-follow-up-extending-appo-agentic
   ```

2. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```
   *Note: `requirements.txt` pins `torch` to a CPU-only wheel to avoid CUDA dependencies.*

3. **Verify environment**:
   ```bash
   python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
   # Expected output: CUDA available: False
   ```

## Running the Pipeline

The full pipeline (Static -> Dynamic -> Analysis) can be run via the CLI:

```bash
python code/cli/run_pipeline.py --subset-size 85 --max-permutations 10000
```

### Parameters

- `--subset-size`: Number of tasks for dynamic scoring (default:, to account for dropouts and alignment noise).
- `--max-permutations`: Number of iterations for the permutation test (default: a sufficiently large sample size to ensure statistical power).
- `--dry-run`: Skips APPO rollout, only computes static scores (for testing).

### Output

- **Static Scores**: `data/processed/static_scores.parquet`
- **Dynamic Scores**: `data/processed/dynamic_scores.parquet`
- **Results**: `data/results/correlation_results.json`
- **Logs**: `data/logs/pipeline.log` (includes memory usage and timing)

## Verification

After running, verify the results:

1. **Check for errors**:
   ```bash
   grep "RESOURCE_LIMIT_EXCEEDED" data/logs/pipeline.log
   ```
   *Expected: No matches.*

2. **Inspect results**:
   ```bash
   cat data/results/correlation_results.json | jq .
   ```
   *Look for `threshold_met: true` if the hypothesis is supported.*

3. **Reproducibility**:
   Run the pipeline again with the same seed (set in `requirements.txt` or env var `RANDOM_SEED=42`) and verify identical `correlation_results.json`.

## Troubleshooting

- **Memory Error**: If you encounter OOM, reduce `--subset-size` or the model size.
- **Timeout**: If the job exceeds a prolonged duration, the pipeline will exit with code 1 and log `RESOURCE_LIMIT_EXCEEDED`.
- **CUDA Detected**: If `torch.cuda.is_available()` is True, ensure the `requirements.txt` does not install `torch` with CUDA support (use `torch-cpu` wheel).
