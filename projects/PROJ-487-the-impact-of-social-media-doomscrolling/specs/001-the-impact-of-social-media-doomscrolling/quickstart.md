# Quickstart: The Impact of Aggregate Negative News Publication Volume on Anticipatory Anxiety

## Prerequisites

*   Python 3.11+
*   `pip`
*   Access to the GDELT API (public) and Google Trends (no key required, but session limits apply).

## Installation

1.  **Clone the repository** and navigate to the project directory.
2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Running the Pipeline

The pipeline is executed via the main script:

```bash
python code/main.py
```

### Configuration

The pipeline uses default parameters defined in `code/config.py`:
*   **Date Range**: 2020-01-01 to 2023-12-31
*   **Lag Windows**: [1, 2, 3, 7, 14]
*   **Alpha**: 0.05 (Bonferroni corrected to 0.01)

### Expected Outputs

*   `data/raw/news_volume.csv`: Raw GDELT event counts.
*   `data/raw/anxiety_trends.csv`: Raw Google Trends data.
*   `data/processed/aligned_timeseries.csv`: Cleaned, aligned, and stationary data.
*   `data/reports/analysis_results.json`: Statistical results.
*   `data/reports/report.html`: Final visualization and summary report.

## Troubleshooting

*   **API Rate Limits**: If Google Trends returns a 429 error, the script includes retry logic with exponential backoff.
*   **Missing Data**: If data completeness is < 95%, the script exits with a non-zero status code.
*   **Non-Stationarity**: If differencing does not achieve stationarity after 3 attempts, the script logs a warning and proceeds with caution.
