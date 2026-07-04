# Quickstart: Exploring the Statistical Relationship Between Solar Wind Composition and Geomagnetic Indices

## Prerequisites

*   Python 3.11+
*   `git`
*   Access to a GitHub Actions runner (or local environment with sufficient RAM).

## Installation

1.  **Clone the Repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-505-exploring-the-statistical-relationship-b
    ```

2.  **Create Virtual Environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Data Preparation

*Note: Due to the absence of verified sources for ACE SWICS and NOAA Dst/Kp in the provided list, this step generates synthetic data for pipeline validation.*

1.  **Generate Synthetic Data**:
    ```bash
    python code/ingestion/generate_synthetic_data.py --output data/processed/synthetic_aligned.parquet
    ```
    *This script creates a multi-year hourly dataset with realistic distributions for bulk parameters and simulated composition ratios/geomagnetic indices. It also attempts to fetch real data, but falls back to synthetic if fetch fails.*

2.  **Verify Data**:
    ```bash
    python code/utils/verify_data.py --input data/processed/synthetic_aligned.parquet
    ```

## Running the Analysis

1.  **Execute Full Pipeline**:
    ```bash
    python code/main.py
    ```
    *This runs ingestion (with fallback to synthetic), coupling function derivation, regression, cross-validation, permutation tests, and sensitivity analysis.*

2.  **View Results**:
    Results are saved to `data/artifacts/`:
    *   `regression_results.csv`: Coefficients, p-values, R², VIF.
    *   `permutation_results.csv`: Null distributions and significance flags.
    *   `sensitivity_analysis.csv`: Results across $\alpha$ thresholds.
    *   `plots/`: Visualizations of coefficients and null distributions.

## Testing

Run the test suite to ensure pipeline integrity:
```bash
pytest tests/
```

## Troubleshooting

*   **Memory Error**: If running on real data (future), ensure data is processed in chunks. The current synthetic dataset is small (<10MB).
*   **Import Error**: Ensure `venv` is activated and `requirements.txt` is up to date.
*   **Data Fetch Failure**: If the real data fetch fails (expected), the script will automatically switch to synthetic data generation. Check the logs for the fallback message.