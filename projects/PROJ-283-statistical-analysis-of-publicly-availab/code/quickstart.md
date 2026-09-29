# Quickstart Guide

## Installation

```bash
pip install -r requirements.txt
```

## Running the Pipeline

Execute the main pipeline with sample mode:

```bash
python code/src/main.py --sample
```

Expected output on success:
```
Pipeline completed successfully
```

## Running T036: Print Statement Check

To verify no print statements remain in the codebase (Task T036):

```bash
python code/scripts/ruff_check.py
```

This will check for any `print` statements (T20 rule) and report violations if found.

## Output Artifacts

The pipeline produces the following artifacts:
- `data/processed/games.parquet` - Processed game records
- `data/results/model_metrics.json` - Model performance metrics
- `data/results/diagnostics.json` - Diagnostic report
- `data/results/*.png` - Diagnostic plots
