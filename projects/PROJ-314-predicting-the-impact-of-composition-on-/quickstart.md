# Quick Start Guide

## Prerequisites

- Python 3.11+
- pip

## Installation

```bash
python -m venv.venv
source.venv/bin/activate
pip install -r requirements.txt
```

## Verify Data Sources

```bash
python code/verify_hf_dataset.py
```

## Generate Test Data (Optional)

```bash
python code/scripts/create_test_n_dataset.py
```

## Run Full Pipeline

```bash
python code/run_pipeline_timing.py
```

## Outputs

- `data/processed/step_final_cleaned.csv`: Cleaned dataset
- `data/results/model_metrics.json`: Model performance metrics
- `data/artifacts/shap_summary.png`: SHAP summary plot
- `data/reports/final_report.md`: Final project report

## Troubleshooting

- If `verify_hf_dataset.py` fails, check internet connection and HuggingFace access.
- If `run_pipeline_timing.py` fails, check `logs/pipeline_timing.log` for details.