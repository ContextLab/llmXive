# Quickstart Guide: Social Support & Resilience Pipeline

## Prerequisites
- Python 3.9+
- pip

## Installation
1. Install dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```

## Running the Pipeline
To execute the full analysis end-to-end:
```bash
cd code
python main_pipeline.py
```

## Expected Outputs
After successful execution, the following files will be generated:
- `data/raw/cyberbullying_2021.csv` (Raw ingested data)
- `data/results/analysis_cohort.csv` (Cleaned analysis dataset)
- `data/results/regression_results.csv` (Model coefficients & stats)
- `data/results/sensitivity_analysis.csv` (Sensitivity check results)
- `data/results/regression_summary.md` (Human-readable report)
- `data/results/pipeline_run.log` (Execution log)

## Troubleshooting
- **Missing Data Source**: Ensure `code/config/data_sources.yaml` contains a valid URL/ID for the Cyberbullying Survey 2021.
- **Module Errors**: Ensure you are running from the `code/` directory or have the project root in your `PYTHONPATH`.