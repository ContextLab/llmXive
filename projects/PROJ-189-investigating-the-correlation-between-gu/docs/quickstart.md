# Quickstart Guide: Gut Microbiome and Cognitive Decline Analysis

This guide validates the end-to-end reproducibility of the research pipeline.

## Prerequisites

- Python 3.11+
- Dependencies installed: `pip install -r code/requirements.txt`

## Execution

To run the full validation pipeline:

```bash
python code/quickstart_validation.py
```

This script will:
1. Execute `01_data_ingestion.py` to fetch and merge AGP/HRS data.
2. Execute `02_preprocessing.py` to rarefy and clean data.
3. Execute `03_correlation_analysis.py` to compute Spearman correlations.
4. Execute `04_predictive_modeling.py` to train models and verify significance.
5. Execute `05_sensitivity_analysis.py` to test robustness.
6. Verify all output artifacts exist and contain valid data.

## Output

A validation report is generated at `data/processed/quickstart_validation_report.json`.
A log file is generated at `data/processed/quickstart_validation.log`.

## Troubleshooting

- If data fetch fails, check your internet connection and API keys in `code/.env`.
- If memory errors occur, ensure you are running in an environment with >= 7GB RAM.
- If specific steps fail, check `data/processed/run.log` for detailed error messages.
