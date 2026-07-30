# Quickstart Guide: llmXive Follow-up Pipeline

This guide provides explicit steps to reproduce the full pipeline for the
**llmXive Follow-up: Teacher Entanglement vs. Scalar Distillation Loss** project.

## Prerequisites

- Python 3.9+
- pip (Python package manager)
- At least 7GB RAM for data processing

## Step 1: Install Dependencies

```bash
cd projects/PROJ-967-llmxive-follow-up-extending-beyond-scala
pip install -r code/requirements.txt
```

## Step 2: Download Dataset

Download the Z-Reward evaluation dataset using the dedicated script:

```bash
python code/download_zreward.py \
 --output data/raw/zreward_dataset.parquet \
 --log-level INFO
```

This script attempts to load the dataset from:
1. Primary: `z-reward/z-reward-v1`
2. Secondary: `z-reward/z-reward-v2`
3. Tertiary: Local archive specified by `Z_REWARD_ARCHIVE_PATH` environment variable

If all sources fail, the script will raise a `RuntimeError` and exit.

## Step 3: Ingest and Align Data

Load the dataset, align teacher/student outputs with human annotations,
and identify the primary quality dimension:

```bash
python code/ingest.py \
 --input data/raw/zreward_dataset.parquet \
 --output data/processed/raw_data.parquet \
 --summary-output data/processed/ingestion_summary.json \
 --log-level INFO
```

## Step 4: Calculate Features

Compute statistical descriptors (variance, entropy, skewness, kurtosis)
and Mahalanobis distance for entanglement analysis:

```bash
python code/features.py \
 --input data/processed/raw_data.parquet \
 --output data/processed/features.json \
 --log-level INFO
```

## Step 5: Calculate Fidelity Loss

Compute dimensional fidelity loss and filter the dataset:

```bash
python code/fidelity_loss.py \
 --input data/processed/raw_data.parquet \
 --output data/processed/cleaned_data.parquet \
 --summary-output data/processed/fidelity_loss_summary.json \
 --log-level INFO
```

## Step 6: Train Model

Train a Random Forest regressor with cross-validation and permutation test:

```bash
python code/train.py \
 --features data/processed/cleaned_data.parquet \
 --split-output data/processed/split_config.json \
 --model-output results/model_temp.pkl \
 --results-output results/train_results.json \
 --n-permutations 1000 \
 --log-level INFO
```

## Step 7: Save Model Artifact

Save the trained model to the final location:

```bash
python code/save_model.py \
 --model-input results/model_temp.pkl \
 --output results/model.pkl \
 --log-level INFO
```

## Step 8: Evaluate with Null Baseline

Compare the Random Forest against a mean predictor baseline:

```bash
python code/null_baseline.py \
 --features data/processed/cleaned_data.parquet \
 --rf-results results/train_results.json \
 --split-config data/processed/split_config.json \
 --output results/null_baseline_comparison.json \
 --log-level INFO
```

## Step 9: Validate Results

Check that all required artifacts are present and results are valid:

```bash
python code/validate_quickstart.py \
 --project-root projects/PROJ-967-llmxive-follow-up-extending-beyond-scala \
 --log-level INFO
```

## Expected Output Files

After successful execution, the following files should exist:

- `data/raw/zreward_dataset.parquet` - Raw downloaded dataset
- `data/processed/raw_data.parquet` - Ingested and aligned data
- `data/processed/features.json` - Computed features
- `data/processed/cleaned_data.parquet` - Filtered dataset with fidelity loss
- `data/processed/fidelity_loss_summary.json` - Fidelity loss statistics
- `data/processed/split_config.json` - Train/test split configuration
- `results/model.pkl` - Trained Random Forest model
- `results/train_results.json` - Training metrics and cross-validation results
- `results/null_baseline_comparison.json` - Null baseline comparison results
- `results/results.json` - Final integrated results (if using integration script)

## Troubleshooting

### Dataset Download Fails

If the dataset download fails, check:
1. Internet connectivity
2. Hugging Face account authentication (if required)
3. Environment variable `Z_REWARD_ARCHIVE_PATH` for local fallback

### Memory Issues

If you encounter memory errors:
1. Reduce the dataset size by sampling
2. Increase available RAM
3. Use chunked processing (if supported)

### Linting Errors

Run the linter and formatter to fix code style issues:

```bash
ruff check code/ tests/
black code/ tests/
```

## Reproducibility

This pipeline is designed to be reproducible. All random operations use
`random_state=42` for deterministic results. The exact versions of dependencies
are pinned in `code/requirements.txt`.
