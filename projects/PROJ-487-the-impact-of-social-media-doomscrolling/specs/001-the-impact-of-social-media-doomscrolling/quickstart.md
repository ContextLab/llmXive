# Quickstart: The Impact of Aggregate Negative News Publication Volume on Anticipatory Anxiety

## Prerequisites

- Python 3.11+
- `pip`
- Access to GDELT API (no authentication required for basic queries) or AWS S3 (public bucket)
- Access to Google Trends (via `pytrends`)

## Installation

1. Clone the repository and navigate to the project directory:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-487-the-impact-of-social-media-doomscrolling
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r code/requirements.txt
   ```

## Data Fetching

Run the data fetching scripts to retrieve raw data:

```bash
# For pilot validation (API)
python code/data/fetch_gdelt.py --start 2020-01-01 --end 2020-01-31 --mode pilot
# For full dataset (S3 Bulk)
python code/data/fetch_gdelt.py --start 2020-01-01 --end 2023-12-31 --mode bulk
python code/data/fetch_trends.py --start 2020-01-01 --end 2023-12-31
```

This will generate:
- `data/raw/gdelt_events.csv`
- `data/raw/google_trends.csv`

## Preprocessing

Run the preprocessing script to align, check stationarity, and normalize data:

```bash
python code/data/alignment.py
```

This will generate:
- `data/processed/aligned_timeseries.csv`
- `data/processed/stationarity_check.csv`

## Analysis

Run the analysis script to compute correlations, Granger causality, and sensitivity analysis:

```bash
python code/analysis/granger.py
```

This will generate:
- `data/reports/analysis_results.json`
- `data/reports/plots/` (directory with generated plots)

## Reporting

Generate the final report:

```bash
python code/main.py --generate-report
```

This will produce:
- `data/reports/final_report.pdf` (or `.html`)

## Validation

Run the test suite to ensure everything is working correctly:

```bash
pytest code/tests/ -v
```

## Troubleshooting

- **API Errors**: If GDELT API returns errors, the script will retry up to 3 times with exponential backoff. If it still fails, check your internet connection or the GDELT API status.
- **Data Completeness**: If data completeness is < 95%, the pipeline will exit with an error. Check the raw data files for missing dates.
- **Stationarity**: If the data is non-stationary, the pipeline will apply detrending and differencing until it is stationary. If it cannot be made stationary, check the data for anomalies.
- **Keyword Volatility**: If the pilot correlation check fails (r < 0.7), the script will automatically switch to fallback keywords.