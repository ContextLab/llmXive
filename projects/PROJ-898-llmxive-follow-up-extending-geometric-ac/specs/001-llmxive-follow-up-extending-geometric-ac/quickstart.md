# Quickstart: llmXive follow-up: extending "Geometric Action Model for Robot Policy Learning"

## Prerequisites

- **Python**: 3.11+
- **Dependencies**: `pybullet`, `diff-taichi`, `torch`, `scipy`, `statsmodels`, `pandas`, `numpy`, `pytest`
- **Hardware**: 2+ CPU cores, 7+ GB RAM (no GPU required)
- **Storage**: 10+ GB free disk space (for datasets and generated logs)

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-898-llmxive-follow-up-extending-geometric-ac
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

4. **Initialize Data Directories**:
   ```bash
   mkdir -p data/raw data/generated data/results
   touch data/raw/.gitkeep data/generated/.gitkeep data/results/.gitkeep
   ```

5. **Install pre-commit hooks** (to ensure code quality):
   ```bash
   pre-commit install
   ```

## Pre-commit Configuration

The `.pre-commit-config.yaml` file should contain:

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.6
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
      - id: ruff-format
```

## Running the Pipeline

### 1. Generate Synthetic Test Set

Run the topology-shift generator to create a diverse set of unique tasks.:

```bash
python code/data/generator.py --num-trials 300 --output data/generated/test_set.json
```

This script will:
- Load the `training-topology-manifest.json` (if available).
- Generate novel kinematic chains and deformable materials using PyBullet.
- Verify zero overlap with the training distribution.
- Save the test set to `data/generated/test_set.json`.

### 2. Execute Symbolic & Baseline Trials

Run the evaluation pipeline to execute both methods on the generated test set:

```bash
python code/evaluation/runner.py --test-set data/generated/test_set.json --output data/results/trial_logs.jsonl
```

This script will:
- Load the frozen GFM weights.
- Execute the symbolic solver and baseline GAM for each trial.
- Record `task_success`, `solver_feasibility`, `decoder_reconstruction_error`, latency, and latent drift.
- Save results to `data/results/trial_logs.jsonl`.

### 3. Analyze Results

Run the statistical analysis script to compare the methods:

```bash
python code/evaluation/stats.py --input data/results/trial_logs.jsonl --output data/results/analysis_report.md
```

This script will:
- Validate the input data against `contracts/trial_log.schema.yaml`.
- Perform McNemar's test for `task_success` rates.
- Perform Wilcoxon Signed-Rank test for latency (pre-registered, no Shapiro-Wilk pre-test).
- Check if total execution time exceeded 6 hours (SC-005).
- Generate a report with p-values, confidence intervals, and effect sizes.

## Validation

To ensure the pipeline is working correctly, run the unit tests:

```bash
pytest tests/ -v
```

To check the code style and formatting:

```bash
pre-commit run --all-files
```

## Troubleshooting

- **PyBullet Errors**: Ensure you have the correct version of `pybullet` installed. Check the `requirements.txt` for the pinned version.
- **Solver Timeout**: If the symbolic solver exceeds the 300s timeout, the trial will be recorded as a "timeout failure". Check the `error` field in the `trial_log`.
- **Latent Drift**: If the latent drift is high, the GFM encoder may be struggling with the novel topology. Check the `latent_drift` field in the `trial_log`.