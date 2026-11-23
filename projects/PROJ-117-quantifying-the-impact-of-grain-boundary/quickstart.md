# Quickstart Guide

This guide explains how to run the full pipeline for PROJ-117.

## Prerequisites

- Python 3.11+
- Install dependencies: `pip install -r requirements.txt`
- Set environment variables: `MP_API_KEY`, `OPENKIM_API_KEY` (if using those sources)

## Execution Order

The pipeline must be run in the following order:

1. **Download**: Fetch raw data
 ```bash
 python code/download.py
 ```
2. **Geometry Parsing**: Extract features
 ```bash
 python code/geometry_parser.py
 ```
3. **Preprocessing**: Clean and validate data
 ```bash
 python code/preprocess.py
 ```
4. **Diagnostics**: Check collinearity
 ```bash
 python code/diagnostics.py
 ```
5. **Tuning**: Hyperparameter search
 ```bash
 python code/train_tuning.py
 ```
6. **Training**: Final model training
 ```bash
 python code/train_final.py
 ```
7. **Validation**: Cross-validation and bias test
 ```bash
 python code/validate.py
 ```
8. **Interpretability**: SHAP and sensitivity analysis (T021)
 ```bash
 python code/interpret.py
 ```

## Expected Outputs

- `data/processed/cleaned_dataset.parquet`
- `models/best_model.json`
- `artifacts/reports/training_metrics.json`
- `artifacts/reports/validation_report.json`
- `artifacts/reports/interpretability_report.json`
- `artifacts/figures/shap_summary.png`
- `artifacts/reports/threshold_sensitivity_table.csv`

## Troubleshooting

- **Data Insufficiency**: Ensure you have valid API keys and network access. The pipeline requires at least 500 valid records.
- **Missing Files**: Check that previous steps completed successfully.
- **Logging**: Check `logs/` for detailed error messages.