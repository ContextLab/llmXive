# Quickstart Guide

This guide walks you through the llmXive pipeline to reproduce the MIPU gap analysis.

## 1. Setup

```bash
# Create directories
python code/scripts/setup_data_dirs.py
```

## 2. Generate Dataset

```bash
python code/src/cli/generate_dataset.py
```
Output: `data/processed/training_sample.parquet`

## 3. Validate Features

```bash
python code/src/cli/validate_features_diagnostic.py
```

## 4. Train Predictor

```bash
python code/src/cli/prepare_data_split.py
python code/src/cli/train_predictor.py
```
Output: `data/models/gap_predictor.pkl`

## 5. Evaluate

```bash
python code/src/cli/evaluate_on_test.py
```
Output: `data/processed/test_metrics.json`

## 6. Verify Bounds & Statistics

```bash
python code/src/cli/synchronize_inputs.py
python code/src/cli/orchestrate_baseline_proxy.py
python code/src/cli/verify_bound_consistency.py
python code/src/cli/aggregate_bound_results.py
```

## 7. Latency Analysis

```bash
python code/src/cli/run_latency_analysis.py
```
Output: `data/processed/latency_metrics.json`

## 8. Final Report

```bash
python code/src/cli/generate_report.py
```
Output: `docs/reports/001-llmxive-mipu-gap-bounds.md`
