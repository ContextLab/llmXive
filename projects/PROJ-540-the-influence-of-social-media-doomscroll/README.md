# The Influence of Social Media "Doomscrolling" on Anticipatory Anxiety

**Project ID**: PROJ-540

## Overview

This project investigates the relationship between social media doomscrolling (high-frequency news exposure) and anticipatory anxiety. Using public survey data, we perform statistical modeling to estimate associations while rigorously checking for construct validity and statistical assumptions.

## Repository Structure

```
.
├── code/ # Source code for ingestion, cleaning, modeling, and visualization
│ ├── __init__.py
│ ├── config.py # Configuration management, seeds, and environment
│ ├── exceptions.py # Custom exceptions (PowerLimitationError, etc.)
│ ├── ingest.py # Data download and schema validation
│ ├── clean.py # Data cleaning and listwise deletion
│ ├── models.py # Data classes (SurveyResponse, RegressionModel)
│ ├── model.py # Statistical modeling (OLS, correlations)
│ ├── validity.py # Construct validity checks
│ ├── robustness.py # Robustness checks on high-engagement subsets
│ ├── viz.py # Visualization generation
│ └── report_generator.py # Final report generation
├── data/
│ ├── raw/ # Downloaded raw datasets
│ └── processed/ # Cleaned analysis-ready datasets
├── outputs/ # Generated results, plots, and reports
│ ├── analysis.log # Execution logs
│ ├── regression_results.json
│ ├── correlation_results.json
│ ├── robustness_results.json
│ ├── plot.png
│ └── final_report.md
├── tests/ # Unit and integration tests
├── docs/ # Detailed documentation
│ └── api.md
├── requirements.txt # Python dependencies
└── README.md
```

## Prerequisites

- Python 3.11+
- pip

## Installation

1. Clone the repository.
2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Configuration

Create a `.env` file in the root directory (optional) or modify `code/config.py` defaults:
- `DATASET_URL`: URL to the source dataset (e.g., GSS or Pew Research API).
- `RANDOM_SEED`: Integer for reproducibility.

## Usage

Run the pipeline sequentially:

```bash
# 1. Ingest and Clean Data
python code/ingest.py
python code/clean.py

# 2. Statistical Modeling
python code/model.py

# 3. Robustness Checks
python code/robustness.py

# 4. Visualization
python code/viz.py

# 5. Generate Final Report
python code/report_generator.py
```

Or run the full pipeline via the main entry point (if configured):
```bash
python code/pipeline.py
```

## Output Artifacts

- `data/processed/analysis_data.csv`: Cleaned dataset ready for analysis.
- `outputs/regression_results.json`: OLS model coefficients and diagnostics.
- `outputs/correlation_results.json`: Pearson/Spearman correlation matrices.
- `outputs/robustness_results.json`: Comparison of full vs. high-engagement models.
- `outputs/plot.png`: Scatter plot with regression line and 95% CI.
- `outputs/final_report.md`: Comprehensive summary of findings.

## Testing

Run tests using pytest:
```bash
pytest tests/ -v
```

## Data Sources

This project uses real public survey data. The specific dataset URL is configured in `code/config.py`. If the download fails, the script will raise an error rather than using synthetic data.

## License

MIT License
