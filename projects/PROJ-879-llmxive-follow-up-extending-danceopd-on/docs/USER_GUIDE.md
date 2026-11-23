# User Guide

## Overview

This guide explains how to use the llmXive follow-up pipeline to extend DanceOPD.

## Quick Start

1. **Install Dependencies**:
 ```bash
 cd code
 pip install -r requirements.txt
 ```
2. **Set Up Directories**:
 ```bash
 python setup_data_dirs.py
 ```
3. **Run the Pipeline**:
 ```bash
 python main.py
 ```

## Pipeline Stages

### 1. Data Generation

The pipeline streams samples from ImageNet-1K and LAION-400M, runs teacher model inference, and extracts features.

**Output**: `data/processed/teacher_routing_dataset.parquet`

### 2. Tree Training

Decision trees are trained for various `max_depth` values to approximate the teacher's routing behavior.

**Output**: `models/trained_trees/`, `data/results/tree_accuracy.csv`

### 3. Fidelity Evaluation

Images are generated using tree-predicted and teacher baseline routing. FID and CLIP scores are computed.

**Output**: `data/results/fidelity_metrics.csv`, `data/results/statistical_tests.json`

### 4. Summary Report

A summary report is generated with degradation metrics and statistical significance statements.

**Output**: `data/results/fidelity_summary.md`

## Configuration

Edit `code/config.yaml` to customize:
- Data paths
- Hyperparameters
- Timeout settings
- Sample sizes

## Output Files

- `data/processed/teacher_routing_dataset.parquet`: Generated dataset
- `models/trained_trees/`: Trained decision tree models
- `data/results/tree_accuracy.csv`: Tree accuracy by depth
- `data/results/fidelity_metrics.csv`: FID and CLIP scores
- `data/results/statistical_tests.json`: Statistical test results
- `data/results/fidelity_summary.md`: Summary report
- `data/results/exclusion_log.json`: Log of excluded samples

## Troubleshooting

### "Statistical Power Insufficient"

Ensure the dataset has at least `N_min` samples (defined in `config.py`).

### "Undefined Route"

Check `data/results/exclusion_log.json` for details on excluded samples.

### Timeout

The pipeline will save partial results and exit cleanly if it exceeds the 6-hour limit.

## Support

For issues or questions, refer to the `docs/` directory or open an issue on the repository.
