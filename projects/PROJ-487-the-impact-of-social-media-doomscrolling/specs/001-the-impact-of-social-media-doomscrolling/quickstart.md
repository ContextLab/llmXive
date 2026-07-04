# Quickstart: The Impact of Aggregate Negative News Publication Volume on Anticipatory Anxiety

## Prerequisites

- Python 3.11+
- pip (Python package manager)
- Internet access (for API fetching)

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-487-the-impact-of-social-media-doomscrolling/code
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Pipeline

### Step 1: Fetch Data
```bash
python data/fetch_gdelt.py --start-date 2020-01-01 --end-date 2023-12-31
python data/fetch_google_trends.py --start-date 2020-01-01 --end-date 2023-12-31
```
- Outputs: `data/raw/gdelt_events.csv`, `data/raw/google_trends.csv`

### Step 2: Preprocess Data
```bash
python data/preprocess.py
```
- Outputs: `data/processed/aligned_timeseries.csv`, `data/processed/stationarity_check.csv`
- Note: This step performs forward fill, ADF testing, cointegration testing, and ECM/differencing.

### Step 3: Run Analysis
```bash
python data/analyze.py
```
- Outputs: `analysis_results.json`, `plots/` (correlation heatmap, lag plots)
- Note: Uses AIC/BIC for lag selection and Joint F-tests.

### Step 4: Generate Report
```bash
python data/generate_report.py
```
- Outputs: `report.pdf` or `report.html`

## Verification

- **Data Completeness**: Check `data/processed/aligned_timeseries.csv` for missing values (should be 0).
- **Stationarity/Cointegration**: Verify `data/processed/stationarity_check.csv` shows appropriate status (stationary or cointegrated).
- **Significance**: Check `analysis_results.json` for p-values < 0.05 in the Joint F-test.

## Troubleshooting

- **API Rate Limits**: If fetching fails, retry with exponential backoff (max 3 attempts).
- **Non-Stationary Data**: If ADF test fails, the script will automatically check for cointegration and apply ECM or differencing.
- **Insufficient Data**: If time series length < 20 days, the script exits with "Insufficient data for Granger causality."