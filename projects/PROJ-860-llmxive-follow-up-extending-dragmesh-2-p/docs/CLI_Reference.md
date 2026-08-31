# CLI Reference Guide

This document lists the command-line interfaces for all executable scripts in the project.

## 1. Data Management

### `code/data_loader.py`
Downloads the DragMesh-2 dataset.
```bash
python code/data_loader.py [--output-dir PATH]
```

### `code/verify_manifest.py`
Verifies the integrity of downloaded data.
```bash
python code/verify_manifest.py --manifest data/raw/dataset_manifest.jsonl
```

## 2. Generation

### `code/generator.py`
Generates novel object geometries.
```bash
python code/generator.py \
 --count 50 \
 --seed 42 \
 --high-friction-count 25 \
 --friction-min 0.0 \
 --friction-max 2.5 \
 --output data/generated/
```
**Arguments**:
- `--count`: Total number of objects to generate.
- `--seed`: Random seed for reproducibility.
- `--high-friction-count`: Number of objects with friction in [0.8, 1.2].
- `--friction-min`: Minimum friction coefficient.
- `--friction-max`: Maximum friction coefficient.
- `--output`: Output directory.

## 3. Training

### `code/train.py`
Trains the adaptive policy.
```bash
python code/train.py \
 --epochs 100 \
 --batch-size 32 \
 --log-file data/results/train.log
```

## 4. Evaluation

### `code/evaluate.py`
Runs inference on novel objects.
```bash
python code/evaluate.py \
 --policy adaptive \
 --policy static \
 --objects data/generated/ \
 --output data/results/eval_logs.csv
```

## 5. Analysis

### `code/aggregate.py`
Aggregates evaluation logs.
```bash
python code/aggregate.py \
 --input data/results/eval_logs.csv \
 --output data/results/aggregated.csv
```

### `code/glmm_analysis.py`
Performs statistical analysis.
```bash
python code/glmm_analysis.py \
 --input data/results/aggregated.csv \
 --output data/results/glmm_summary.json
```

### `code/analysis.py`
Generates the final validation report.
```bash
python code/analysis.py \
 --glmm data/results/glmm_summary.json \
 --output data/results/analysis_glmm.json
```

## 6. Benchmarking

### `code/run_benchmark.py`
Orchestrates the full pipeline.
```bash
python code/run_benchmark.py \
 --output data/results/benchmark_metrics.json
```

## 7. Utilities

### `code/validate_citations.py`
Validates all citations in documentation.
```bash
python code/validate_citations.py
```

### `code/audit_reproducibility.py`
Generates a reproducibility audit report.
```bash
python code/audit_reproducibility.py \
 --output data/results/audit_report.json
```
