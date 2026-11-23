# llmXive Quickstart Guide

This guide provides step-by-step instructions to set up and run the llmXive research pipeline for evaluating static sparsification against full attention baselines.

## Prerequisites

- Python 3.10+
- 7GB+ RAM (for streaming dataset processing)
- 14GB+ disk space
- pip and virtualenv

## Setup

### 1. Clone and Initialize

```bash
git clone <repository-url>
cd llmXive
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r code/requirements.txt
```

### 3. Create Directory Structure

Run the initialization script:

```bash
python code/setup/create_directories.py
```

This creates all required directories under `code/`, `data/`, `tests/`, etc.

## Data Preparation

The pipeline streams the RULER dataset. No manual download is required.

### Ground Truth Extraction

Run the ground truth extraction pipeline:

```bash
python code/data/extract_ground_truth.py
```

This generates:
- `data/intermediate/rtpurbo_labels.parquet`
- `data/intermediate/attention_maps.h5`
- `data/logs/anomalies.csv`

### Feature Computation

Compute static linguistic features:

```bash
python code/data/compute_features.py
```

This generates `data/intermediate/features.csv`.

### Merge Datasets

Merge ground truth with features:

```bash
python code/data/merge_datasets.py
```

Output: `data/intermediate/merged_dataset.csv`

## Model Training

### Train Static Predictor

```bash
python code/models/train_static.py
```

This trains multiple models with different seeds and saves them to `data/intermediate/models/`.

### Evaluate Static Models

```bash
python code/models/evaluate_static.py
```

Output: `data/intermediate/static_eval_scores.json`

### Derive Heuristic Rules

```bash
python code/models/derive_rules.py
```

Output: `data/intermediate/rules.json`

## Evaluation

### Run Baselines

Execute full attention and static heuristic baselines:

```bash
python code/evaluation/run_baselines.py
```

Output: `data/results/full_baseline_metrics.json`

### Run Learned Baseline

```bash
python code/evaluation/run_learned_baseline.py
```

Output: Per-seed results in `data/intermediate/baseline_seeds/`

### Statistical Analysis

Perform paired t-tests:

```bash
python code/evaluation/stats_analysis.py
```

Output: `data/results/statistical_report.txt`

### Falsifiability Check

```bash
python code/evaluation/falsifiability_check.py
```

### Generate Final Report

```bash
python code/evaluation/generate_final_report.py
```

Output: `data/results/final_report.md`

## Validation

### Quickstart Validation

Verify reproducibility:

```bash
python code/scripts/run_quickstart_validation.py
```

### Timing Check

Ensure pipeline completes within 6 hours:

```bash
python code/evaluation/check_timing.py
```

## Testing

Run all tests:

```bash
pytest tests/ -v
```

Run specific test suites:

```bash
pytest tests/unit/ -v
pytest tests/integration/ -v
pytest tests/contract/ -v
```

## Troubleshooting

### Memory Issues

If you encounter OOM errors, ensure you have at least 7GB of available RAM and that streaming is enabled in `code/data/download.py`.

### KenLM Errors

If KenLM fails to load, the pipeline will skip perplexity computation and log errors to `data/logs/compute_errors.log`.

### Anomaly Exclusion

Documents with zero RTPurbo tokens are automatically excluded. Check `data/logs/anomalies.csv` for excluded document IDs.

## Next Steps

- Review `research.md` for detailed methodology and statistical analysis.
- Explore `data/results/final_report.md` for the complete evaluation summary.
- Contribute improvements by following the contribution guidelines.
