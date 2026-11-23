# Quickstart Guide for llmXive Co-Evolving Policy Distillation

This guide provides the essential commands to run the pipeline end-to-end.

## Prerequisites

- Python 3.11+
- pip and virtualenv

## Setup

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Pipeline Commands

The pipeline consists of three main stages: generate, train, and analyze.

### 1. Generate Synthetic Data

Generate propositional logic proofs and grid-world navigation tasks.

```bash
python src/cli.py generate --logic 100 --grid 50 --seed 42 --output data/synthetic_dataset.json
```

This command:
- Generates 100 logic proofs
- Generates 50 grid-world instances
- Uses seed 42 for reproducibility
- Outputs to `data/synthetic_dataset.json`

### 2. Train Agents

Train agents under three different conditions: Sequential, Mixed, and Co-evolving.

```bash
python src/cli.py train --conditions sequential,mixed,coevolving --generations 50 --runs-per-condition 30 --seed 42
```

This command:
- Runs training for all three conditions
- Each condition runs for 50 generations
- Executes 30 independent runs per condition
- Uses seed 42 as the base for all runs

### 3. Analyze Results

Perform statistical analysis on the training results.

```bash
python src/cli.py analyze --input data/results/forgetting_metrics.csv --output data/results/statistical_report.json
```

This command:
- Loads forgetting metrics from the CSV file
- Performs Mixed-Design ANOVA and Tukey HSD tests
- Outputs the statistical report to JSON

### 4. Pilot Power Estimation (T042)

Run a minimal pilot simulation to estimate the required sample size for statistical power.

```bash
python src/analysis/pilot_power_estimator.py --pilot-runs 2 --generations 10 --base-seed 42 --output data/batch_config.json
```

This command:
- Runs 2 pilot runs per condition
- Uses 10 generations for each pilot run
- Calculates the required sample size for power >= 0.8
- Generates `data/batch_config.json` with the recommended seeds

### 5. Full Batch Run

Execute the full batch of experiments using the configuration from T042.

```bash
python src/cli.py batch --config data/batch_config.json
```

This command:
- Reads the sample size and seeds from `data/batch_config.json`
- Executes the full batch of experiments
- Saves results to `data/results/`

## Output Files

The pipeline generates the following key output files:

- `data/generated_proofs.json`: Generated propositional logic proofs
- `data/generated_grids.json`: Generated grid-world instances
- `data/test_instances.json`: Held-out test instances
- `data/checksums.json`: SHA-256 checksums for data integrity
- `data/batch_config.json`: Batch configuration with seeds (from T042)
- `data/results/initial_metrics.json`: Initial single-task performance metrics
- `data/results/final_metrics.json`: Final multi-task performance metrics
- `data/results/forgetting_analysis.json`: Final forgetting and retention analysis
- `data/results/statistical_report.json`: Statistical analysis report

## Troubleshooting

- If you encounter "unrecognized arguments" errors, ensure you are using the correct command structure.
- If data generation fails, check that `sympy` and `networkx` are properly installed.
- For statistical analysis errors, verify that `scipy` and `statsmodels` are up to date.
