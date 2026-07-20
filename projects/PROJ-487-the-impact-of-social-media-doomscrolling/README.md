# The Impact of Aggregate Negative News Publication Volume on Anticipatory Anxiety

This project investigates the causal relationship between aggregate negative news publication volume (sourced from GDELT) and anticipatory anxiety levels (proxied by Google Trends search volume for "anticipatory anxiety" and "worry about future").

## Project Structure

```
projects/PROJ-487-the-impact-of-social-media-doomscrolling/
├── code/
│ ├── data/ # Data fetching, preprocessing, and analysis scripts
│ ├── tests/ # Unit and integration tests
│ ├── utils/ # Utility functions (logging, validation)
│ ├── config.py # Configuration management
│ └── logging_config.py # Logging setup
├── data/
│ ├── raw/ # Raw data from GDELT and Google Trends
│ ├── processed/ # Cleaned, aligned, and normalized time-series data
│ └── reports/ # Generated analysis reports and visualizations
├── specs/ # Feature specifications and design docs
├── tests/ # (Legacy/Top-level tests if any)
├── venv/ # Python virtual environment
├──.flake8 # Linting configuration
├── pyproject.toml # Black/Formatting configuration
├── requirements.txt # Python dependencies
├── README.md # This file
└── quickstart.md # Environment setup and execution guide
```

## Prerequisites

- Python 3.8+
- pip
- Virtual environment tools (`venv`)

## Quickstart

1. **Clone and setup environment**:
 ```bash
 cd projects/PROJ-487-the-impact-of-social-media-doomscrolling
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 pip install -r requirements.txt
 ```

2. **Run the Pipeline**:
 The pipeline consists of three main stages: Data Acquisition, Preprocessing, and Analysis.

 - **Step 1: Fetch Data**
 ```bash
 python code/data/fetch_gdelt.py
 python code/data/fetch_google_trends.py
 ```
 *Outputs*: `data/raw/gdelt_events.csv`, `data/raw/google_trends.csv`

 - **Step 2: Preprocess Data**
 ```bash
 python code/data/preprocess.py
 ```
 *Outputs*: `data/processed/aligned_timeseries.csv`, `data/processed/stationarity_check.csv`

 - **Step 3: Analyze Data**
 ```bash
 python code/data/analyze.py
 ```
 *Outputs*: `data/reports/analysis_report.pdf`, `data/processed/granger_results.csv`

3. **Validation**:
 Run the integrity checks and validation scripts to ensure data quality.
 ```bash
 python code/data/validate_integrity.py
 python code/data/post_interpolation_check.py
 python code/data/verify_cpu_compliance.py
 ```

## CLI Usage

Most scripts support standard CLI arguments for configuration (e.g., date ranges, output paths). Run `python code/data/<script>.py --help` for specific options.

### Example: Fetching GDELT Data with Custom Date Range
```bash
python code/data/fetch_gdelt.py --start-date 2023-01-01 --end-date 2023-12-31
```

## Testing

Run the test suite using `pytest` (installed via requirements.txt):
```bash
pytest code/tests/ -v
```

## Dependencies

See `requirements.txt` for the full list of dependencies, including:
- `pandas`, `numpy` (Data manipulation)
- `statsmodels` (Statistical tests, Granger Causality)
- `pytrends` (Google Trends API)
- `requests` (HTTP requests for GDELT)
- `matplotlib`, `seaborn` (Visualization)
- `pyyaml` (Configuration/Validation)

## Statistical Methodology

- **Correlation**: Pearson and Spearman coefficients.
- **Causality**: Granger Causality test with a fixed-sweep of lags {1, 2, 3, 7, 14}.
- **Validity**: Bonferroni correction applied (α = 0.01) for statistical significance.
- **Stationarity**: Augmented Dickey-Fuller (ADF) test with differencing if non-stationary.

## License

This project is for research purposes only.
