# Documentation: Consciousness Bootstrapping Project

Welcome to the documentation for the `PROJ-558-consciousness-bootstrapping`
project. This repository contains the implementation of a self-referential
AI model designed to bootstrap meta-cognitive awareness through recursive
introspection.

## Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Metrics Reference](#metrics-reference)
4. [Statistical Report Schema](#statistical-report-schema)
5. [Running the Pipeline](#running-the-pipeline)

## Project Overview

This project investigates whether recursive self-modeling can lead to emergent
self-awareness in small language models. By training a model to predict its own
confidence and correctness via internal consistency checks, we aim to measure
improvements in calibration and error detection.

## Architecture

The pipeline consists of three main phases:
1. **Training**: Generates both baseline and recursive checkpoints using the
 `code/training/train.py` script.
2. **Evaluation**: Runs benchmarks (GSM8K, MMLU) to generate reasoning paths
 and compute meta-cognitive metrics (`code/evaluation/run_benchmarks.py`).
3. **Analysis**: Performs statistical testing and sensitivity analysis to
 validate significance (`code/analysis/stats.py`).

## Metrics Reference

Detailed definitions of all computed metrics can be found in:
- [`metrics_reference.md`](metrics_reference.md): Covers Self-Consistency,
 Calibration (Brier, ECE, ROC-AUC), and Statistical Significance.

## Statistical Report Schema

The format and field definitions for the final statistical report are documented in:
- [`statistical_report_schema.md`](statistical_report_schema.md)

## Running the Pipeline

Ensure all dependencies are installed:
```bash
pip install -r requirements.txt
```

### 1. Data Preparation
```bash
python code/data_loader.py
```

### 2. Training
```bash
python code/training/train.py --config code/config.py
```

### 3. Evaluation
```bash
python code/evaluation/run_benchmarks.py --checkpoint artifacts/checkpoints/recursive.pt
```

### 4. Analysis
```bash
python code/analysis/stats.py --input data/evaluation_results/*.json
```

## License

This project is part of the llmXive research initiative.