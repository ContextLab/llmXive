# Quickstart Guide: Investigating the Validity of the Equipartition Theorem

## Prerequisites

1. Ensure you have Python 3.11+ installed.
2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Setup

1. Generate test parameters:
 ```bash
 python code/generate_test_params.py
 ```

2. Generate test data:
 ```bash
 python code/generate_test_data.py
 ```

3. (Optional) Fetch real data from Zenodo:
 ```bash
 python code/ingestion.py --data-source zenodo: --streaming
 ```
 Note: Replace `` with the actual Zenodo ID from `research.md` or `data/config.yaml`.

## Run the Pipeline

Execute the full analysis pipeline:
```bash
python code/main.py --stage all --seed 42
```

## Verify Results

Check the generated artifacts:
- `data/derived/energy_samples.csv`: Final energy data
- `artifacts/statistical_results.json`: Statistical test results
- `artifacts/sensitivity_analysis_report.json`: Sensitivity analysis results
- `artifacts/regression_results.json`: Regression analysis results

## Troubleshooting

- If you encounter a `FileNotFoundError` for `logs/pipeline.log`, ensure the `logs/` directory exists.
- If data fetching fails, verify your Zenodo ID and internet connection.
- For large datasets, use the `--streaming` flag to avoid memory issues.