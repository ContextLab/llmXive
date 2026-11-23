# Quickstart Guide

This guide outlines the commands to execute the full research pipeline.
Ensure you have installed dependencies via `pip install -r code/requirements.txt`.

## 1. Generate Synthetic Networks

Generates batches of graphs based on `code/config.yaml` topology targets.

```bash
python code/src/generators/batch_runner.py --config code/config.yaml --output data/raw/global_batch_manifest.json
```

## 2. Run Simulations

Executes energy propagation simulations on the generated graphs.

```bash
python code/scripts/run_simulation.py --config code/config.yaml
```

## 3. Sensitivity Analysis

Runs sensitivity sweeps on clustering thresholds.

```bash
python code/scripts/run_sensitivity_sweep.py --config code/config.yaml
```

## 4. Aggregate and Analyze

Aggregates results, performs regression/ANOVA, and generates final reports.

```bash
python code/scripts/run_analysis.py --config code/config.yaml
```

## 5. Final Serialization

Produces the final `data/analysis/final_results.json` and figures.

```bash
python code/scripts/run_final_serialization.py --config code/config.yaml
```

## Full Pipeline Execution

To run the entire pipeline sequentially:

```bash
python code/src/generators/batch_runner.py --config code/config.yaml
python code/scripts/run_simulation.py --config code/config.yaml
python code/scripts/run_sensitivity_sweep.py --config code/config.yaml
python code/scripts/run_analysis.py --config code/config.yaml
python code/scripts/run_final_serialization.py --config code/config.yaml
```

## Verification

Verify the outputs exist:

```bash
ls -lh data/raw/global_batch_manifest.json
ls -lh data/analysis/simulation_results.json
ls -lh data/analysis/sensitivity_sweep.json
ls -lh data/analysis/aggregated_results.json
ls -lh data/analysis/final_results.json
ls -lh data/run_log.json
```
