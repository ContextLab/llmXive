# Quickstart Guide: The Impact of Incidental Music on Autobiographical Memory Retrieval

This guide provides step-by-step instructions to run the full pipeline from data ingestion to final analysis.

## Prerequisites

- Python 3.9+
- `requirements.txt` installed
- Valid internet connection for downloading datasets

## Installation

1. Clone the repository.
2. Create a virtual environment and activate it:
 ```bash
 python -m venv code/.venv
 source code/.venv/bin/activate # On Windows: code\.venv\Scripts\activate
 ```
3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Running the Pipeline

The pipeline is executed via a series of scripts defined in the `code/` directory. Run them in the following order:

### 1. Download Data
Downloads the MSD and AMT datasets from the canonical sources.
```bash
python code/01_download_data.py
```

### 2. Preprocess Data
Filters and prepares the data for analysis.
```bash
python code/02_preprocess.py
```

### 3. Aggregate Data
Joins exposure data and aggregates memory cues.
```bash
python code/03_aggregate.py
```

### 4. Calculate Exposure Scores
Computes the adolescent exposure ratio.
```bash
python code/04_exposure.py
```

### 5. Model and Analyze
Fits the mixed-effects model, runs sensitivity analysis, and performs the bootstrap test.
**This script also generates the final output CSVs.**
```bash
python code/05_model.py
```

### 6. Sensitivity Analysis (Optional/Redundant if included in 05_model.py)
*Note: If 05_model.py already runs the sensitivity loop, this step may be skipped or used for re-running with different parameters.*
```bash
python code/06_sensitivity.py
```

### 7. Selection Correction (Optional)
```bash
python code/07_selection_correction.py
```

### 8. Visualization
Generates diagnostic plots.
```bash
python code/08_visualize.py
```

## Output Artifacts

Upon successful completion, the following files will be generated in the `data/` directory:

- `data/processed/ingested_cohort.parquet`
- `data/processed/user_track_pairs.parquet`
- `data/final/regression_summary.csv`
- `data/final/sensitivity_analysis.csv`
- `data/final/bootstrap_results.csv`
- `data/final/plots/` (diagnostic plots)

## Validation

To validate the pipeline outputs, run:
```bash
python code/quickstart_validator.py
```

## Troubleshooting

- **Missing Data Files**: Ensure `code/01_download_data.py` ran successfully and that the data sources are accessible.
- **Model Fitting Errors**: Check for multicollinearity (VIF > 5) or insufficient data points.
- **Permission Errors**: Ensure you have write permissions to the `data/` directory.

## License

This project is licensed under the terms of the MIT license.