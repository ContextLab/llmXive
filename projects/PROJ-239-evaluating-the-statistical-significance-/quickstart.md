# Quickstart Guide: Evaluating Statistical Significance with Non-Independent Observations

This guide walks you through running the complete analysis pipeline.

## Prerequisites

- Python 3.11
- Install dependencies: `pip install -r requirements.txt`

## Running the Pipeline

The pipeline consists of several stages. Run them in order:

### 1. Generate Synthetic Cluster Structure

This script generates synthetic cluster sizes based on UCI Online Retail summary statistics.

```bash
python code/synthetic_cluster_params.py
```

**Output**: `data/derived/synthetic_cluster_structure.csv`

### 2. Run Baseline Simulation

Runs the naive t-test simulation (violates cluster-aware inference for baseline comparison).

```bash
python code/run_simulation_baseline.py
```

**Output**: `data/derived/baseline_results.csv`

### 3. Run Robust Simulation

Runs the cluster-robust and block permutation test simulations.

```bash
python code/run_simulation_robust.py
```

**Output**: `data/derived/robustResults.csv`

### 4. Merge Results and Generate Final Report

Combines baseline and robust results, computes error rates, and generates the final report.

```bash
python code/scripts/merge_results.py
```

**Output**: `data/derived/final_report.csv`

### 5. Generate Research Report

Creates the final research report with visualizations.

```bash
python code/generate_report.py
```

**Outputs**:
- `specs/001-evaluating-the-statistical-significance/research.md`
- `data/derived/error_rate_vs_icc.png`

## Full Pipeline Execution

To run the entire pipeline from start to finish:

```bash
# 1. Generate cluster structure
python code/synthetic_cluster_params.py

# 2. Run baseline simulation
python code/run_simulation_baseline.py

# 3. Run robust simulation
python code/run_simulation_robust.py

# 4. Merge results
python code/scripts/merge_results.py

# 5. Generate final report
python code/generate_report.py
```

## Running Tests

```bash
pytest tests/ -v
```

## Configuration

Most scripts accept CLI arguments for customization:

- `--icc`: Specific ICC value to test
- `--icc-range`: Comma-separated list of ICC values
- `--icc-step`: Step size for ICC range
- `--alpha`: Significance level (default: 0.05)
- `--alpha-list`: Comma-separated significance levels
- `--iterations`: Number of simulation iterations
- `--seed`: Random seed
- `--n-clusters`: Number of clusters
- `--n-obs-per-cluster`: Observations per cluster

Example:
```bash
python code/run_simulation_baseline.py --icc 0.1 --iterations 100 --seed 42
```