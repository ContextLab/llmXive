# Experiment Configuration Guide

This document details the configuration options available for running the DP-FL experiments.

## Configuration File

While most experiments are run via CLI arguments, a `config.json` can be used for complex setups.

```json
{
 "dataset": "femnist",
 "seeds": [42, 123, 456, 789, 101112],
 "alphas": [0.1, 0.5, 1.0],
 "epsilons": [0.5, 1.0, 5.0, 10.0],
 "model": "SmallCNN",
 "batch_size": 32,
 "learning_rate": 0.01,
 "num_rounds": 50,
 "num_clients": 100,
 "dp_config": {
 "noise_multiplier": 1.0,
 "max_grad_norm": 1.0,
 "target_epsilon": 1.0
 }
}
```

## CLI Arguments Reference

### Data Pipeline
- `--dataset`: Dataset name (default: `femnist`).
- `--seed`: Random seed (default: `42`).
- `--alpha`: Dirichlet parameter (default: `0.1`).

### Training
- `--dataset`: Dataset name.
- `--seeds`: Space-separated list of seeds.
- `--alphas`: Space-separated list of $\alpha$ values.
- `--epsilons`: Space-separated list of $\epsilon$ values.
- `--model`: Model architecture (`SmallCNN` or `SmallMLP`).
- `--batch_size`: Batch size (default: `32`).
- `--learning_rate`: Learning rate (default: `0.01`).
- `--num_rounds`: Number of communication rounds (default: `50`).

### Analysis
- `--input_file`: Path to raw logs CSV (default: `results/raw_logs.csv`).
- `--output_dir`: Directory for output files (default: `results/`).

## Exclusion of Shakespeare

**Important**: The Shakespeare dataset is **not supported** in this project.
- **Reason**: No verified programmatic source exists (per plan.md Gap Analysis).
- **Behavior**: Any attempt to use `shakespeare` will raise a `ValueError`.
- **Error Message**: "Shakespeare excluded per plan.md Gap Analysis (no verified source)."

This exclusion is enforced at the configuration level in `code/config.py` and propagated to all data loading and partitioning functions.

## Environment Variables

- `FEMNIST_CACHE_DIR`: Directory for caching the FEMNIST dataset.
- `HF_HOME`: Hugging Face home directory.
- `TORCH_HOME`: PyTorch home directory.

## Logging Levels

- `DEBUG`: Detailed debug information.
- `INFO`: General information (default).
- `WARNING`: Warning messages.
- `ERROR`: Error messages.
- `CRITICAL`: Critical errors.

Set logging level via `--log-level` CLI argument or `LOG_LEVEL` environment variable.
