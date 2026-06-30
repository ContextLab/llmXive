# Quickstart: Solar Wind and Magnetotail Reconnection Analysis

## Prerequisites

*   **Python**: 3.11 or higher.
*   **Data Access**: Internet connection to fetch data from NASA OMNIWeb and CDAWeb.
*   **Environment**: Linux (for GitHub Actions compatibility) or macOS.

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-300-exploring-the-relationship-between-solar
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```

## Running the Analysis

### 1. Define Parameters
Edit `code/config.py` or pass command-line arguments to specify:
*   **Start Date**: e.g., `2023-01-01`
*   **End Date**: e.g., `2023-01-03` (Minimum 2 days recommended)
*   **Lag Window**: Default 30-90 minutes.

### 2. Execute the Pipeline
Run the main script:
```bash
python code/main.py --start 2023-01-01 --end 2023-01-03
```

### 3. Output
The script will generate:
*   **Data**: `data/processed/cleaned_data.csv` (resampled, lag-adjusted).
*   **Plots**: `data/visualizations/scatter_plot.png`, `time_series.png`.
*   **Report**: `data/reports/analysis_summary.json` containing correlations, p-values, and optimal lag.

## Verifying Results

1.  **Check the JSON report**: Look for `optimal_lag`, `pearson_r`, and `p_value_permutation`.
2.  **Visual Inspection**: Open `scatter_plot.png` to verify the linear fit and `time_series.png` to check the alignment of Vsw and Ey.
3.  **Reproducibility**: Re-run the script with the same dates. The results should be identical (due to fixed random seeds).

## Troubleshooting

*   **Data Fetch Failures**: Ensure your internet connection is stable. OMNIWeb and CDAWeb may have rate limits; the script includes retries.
*   **Memory Errors**: If processing > 5 days of data, reduce the date range. The 5-minute resampling is designed to fit within 7 GB RAM.
*   **NaN Errors**: If the output contains NaNs, check the input data for gaps. The pipeline logs warnings for gaps > 30 minutes.

## Next Steps

*   **Sensitivity Analysis**: The pipeline automatically runs the threshold analysis (400, 500, 600 km/s). Review the `sensitivity_table.csv` in the reports.
*   **Custom Lag**: To test a specific lag, modify the `lag_window` in `config.py` to a single value.
*   **Extend Dates**: For a more robust statistical power, extend the date range to 1 week or more (if data is available).
