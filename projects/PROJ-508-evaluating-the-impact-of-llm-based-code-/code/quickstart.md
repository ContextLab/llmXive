# Quickstart Guide

This guide walks you through running the full pipeline to generate the master dataset, analysis results, and final report.

## Prerequisites

- Python 3.11+
- `pip install -r requirements.txt`

## Execution Order

1. **Ingest Data**: Fetch repository data and generate the master dataset.
 ```bash
 python code/ingest.py
 ```
 *Output*: `data/derived/master_dataset.csv`, `data/manifest.json`

2. **Analyze Data**: Run statistical models and sensitivity analysis.
 ```bash
 python code/analyze.py
 ```
 *Output*: `data/derived/analysis_results.json`, `data/derived/sensitivity_analysis.json`, `data/derived/stratified_results.json`

3. **Generate Report**: Create the final PDF report.
 ```bash
 python code/report.py
 ```
 *Output*: `docs/output/final_report.pdf`

## Verification

Run the validation script to ensure all outputs are present and correct.
```bash
python code/validate_quickstart.py
```

## Troubleshooting

- **Missing Data**: Ensure `data/raw/repo_list.txt` exists and contains valid repository names.
- **API Errors**: Check your `GITHUB_TOKEN` environment variable.
- **Empty Results**: Verify that the input data contains non-null values for the required columns.