# Quick Start Guide

This guide walks you through setting up and running the SLR Equivalence Principle pipeline.

## 1. Environment Setup

```bash
# Create a virtual environment
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## 2. Configuration

Ensure `config.yaml` exists in the project root.
- **Required**: `benchmark_values.etvos_limit` must be set (see `docs/research/benchmark_selection.md`).
- **Optional**: Override default paths for `data/raw` or `data/results`.

```yaml
# Example config.yaml
paths:
 raw_data: "data/raw"
 processed_data: "data/processed"
 results: "data/results"
 logs: "data/logs"

benchmark_values:
 etvos_limit: 1.1e-13
 citation: "Williams et al. (2016)"

hyperparameters:
 residual_threshold_m: 0.02
 min_arc_days: 30
```

## 3. Running the Pipeline

### Full Run
Execute the main entry point:
```bash
python code/cli/main.py
```
This will:
1. Check resource limits (Memory < 6GB, Time < 6h).
2. Fetch data for LAGEOS-1 and LAGEOS-2 (if not already present).
3. Preprocess and clean the data.
4. Run separate orbit fits.
5. Compute $\eta$ and validate against the benchmark.
6. Generate reports and plots.

### Step-by-Step (Debugging)
You can run individual stages:
```bash
# Ingestion
python code/scripts/run_ingestion_pipeline.py

# Analysis (requires pre-processed data)
python code/analysis/eotvos.py
```

## 4. Verifying Results

Check the generated artifacts:
- `data/results/eotvos_metrics.json`: Contains the calculated $\eta$ and confidence interval.
- `data/results/sensitivity_analysis.png`: Visual check of model sensitivity.
- `data/logs/resource_monitor.log`: Verify no memory/time limits were exceeded.

## 5. Troubleshooting

- **Error: "Benchmark value missing"**: Ensure `config.yaml` has `benchmark_values.etvos_limit` set.
- **Error: "Memory limit exceeded"**: Reduce the dataset size (e.g., use a shorter time range) or increase the limit in `--memory-limit`.
- **Error: "Data unavailable"**: Check network connectivity to ILRS or verify `data/verified_datasets.yaml`.
