# Quickstart Guide

This guide walks you through running the statistical analysis pipeline end-to-end.

## Prerequisites

- Python 3.11+
- pip

## Installation

```bash
pip install -r requirements.txt
```

## Running the Pipeline

The pipeline consists of several stages. Run them in order:

### 1. Download Data

```bash
python code/src/data/download.py --sample-size 100 --output data/raw/sample_games.pgn
```

### 2. Parse and Process Data

```bash
python code/src/data/parse.py --input data/raw/sample_games.pgn --output data/processed/games.parquet
```

### 3. Fit Models

```bash
python code/src/models/fit.py --input data/processed/games.parquet --output data/results/model_metrics.json
```

### 4. Validate Models (Cross-Validation)

```bash
python code/src/models/validate.py --input data/processed/games.parquet --results data/results/model_metrics.json --output data/results/cv_summary.json
```

### 5. Generate Diagnostic Report

This command generates plots and the final diagnostic report:

```bash
python code/src/reports/generate_plots.py \
 --cv-summary data/results/cv_summary.json \
 --significant-predictors data/results/significant_predictors.json \
 --model-results data/results/model_metrics.json \
 --processed-data data/processed/games.parquet \
 --output-dir data/results
```

## Expected Outputs

After running the full pipeline, you should see:

- `data/processed/games.parquet` - Processed game records
- `data/results/model_metrics.json` - Model coefficients and metrics
- `data/results/cv_summary.json` - Cross-validation summary
- `data/results/diagnostics.json` - Final diagnostic report with plot paths
- `data/results/predicted_vs_actual.png` - Predicted vs actual plot
- `data/results/residuals.png` - Residual plot
- `data/results/feature_importance.png` - Feature importance plot (if coefficients available)

## Validation

Verify the pipeline completed successfully by checking:

```bash
python code/src/validation/validate_contracts.py --data data/processed/games.parquet --contracts specs/contracts/game_record.schema.yaml
```

The pipeline should exit with code 0 if all validations pass.
