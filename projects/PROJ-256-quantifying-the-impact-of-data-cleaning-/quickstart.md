# Quickstart Guide

This guide describes how to run the full analysis pipeline.

## Prerequisites

- Python 3.11+
- Dependencies installed (see requirements.txt)

## Execution

Run the main pipeline script:

```bash
python code/main.py
```

This will:
1. Download datasets (if not present)
2. Run baseline analysis
3. Apply cleaning strategies
4. Re-analyze cleaned variants
5. Generate reports

## Output Artifacts

- `data/processed/baseline_metrics.json`
- `data/processed/cleaned_metrics.json`
- `data/processed/*.csv` (cleaned datasets)
- `data/processed/*.png` (visualizations)

## Validation

To validate the outputs:

```bash
python code/run_quickstart_validation.py
```
