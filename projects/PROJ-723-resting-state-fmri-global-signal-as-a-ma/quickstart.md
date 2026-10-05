# Quickstart Guide: Resting-State fMRI Global Signal Analysis

## Prerequisites

- Python 3.9+
- pip (Python package manager)
- HCP credentials (set `HCP_USER` and `HCP_PASS` environment variables)

## Installation

1. Install dependencies:

 ```bash
 pip install -r requirements.txt
 ```

2. Set HCP credentials (required for data download):

 ```bash
 export HCP_USER="your_username"
 export HCP_PASS="your_password"
 ```

## Running the Pipeline

Execute the full analysis pipeline:

```bash
python code/main.py
```

This will:
1. Download and validate HCP resting-state fMRI data
2. Compute global signal metrics
3. Run ridge regression models
4. Perform robustness checks
5. Generate visualizations and reports

## Output Artifacts

After successful execution, you will find:

- `data/processed/cleaned_data.csv` - Cleaned dataset with all metrics
- `data/results/full_model.json` - Primary model results
- `data/results/null_distribution.json` - Null distribution data
- `data/results/diagnostics.json` - Collinearity diagnostics
- `data/results/robustness_report.json` - Robustness analysis results
- `data/results/final_report.json` - Aggregated final report
- `data/results/*.png` - Visualization plots

## Individual Scripts

You can also run individual pipeline steps:

```bash
# Data ingestion only
python code/run_ingestion_pipeline.py

# Modeling only (requires cleaned_data.csv)
python code/modeling.py --data data/processed/cleaned_data.csv

# Diagnostics only
python code/run_diagnostics.py

# Robustness analysis only
python code/run_robustness_report.py

# Visualizations only
python code/run_visualizations.py

# Final report generation
python code/run_final_report.py
```

## Troubleshooting

- **Missing pandas/numpy**: Ensure you installed dependencies with `pip install -r requirements.txt`
- **HCP credentials error**: Set `HCP_USER` and `HCP_PASS` environment variables
- **Data download fails**: Check internet connection and HCP dataset availability
- **Memory issues**: The pipeline streams data to avoid memory overflow; ensure sufficient disk space in `data/raw/`