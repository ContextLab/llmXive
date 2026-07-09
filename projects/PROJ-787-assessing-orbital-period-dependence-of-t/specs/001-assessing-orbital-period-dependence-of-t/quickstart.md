# Quickstart: Assessing Orbital Period Dependence of the Exoplanet Radius Gap

## Prerequisites
-   Python 3.11+
-   Git
-   Access to the internet (for downloading Kepler data)

## Installation

1.  **Clone the repository** (if not already done):
    ```bash
    git clone <repo-url>
    cd projects/PROJ-787-assessing-orbital-period-dependence-of-t
    ```

2.  **Create and activate a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Running the Pipeline

The pipeline is executed via the main entry point. It handles data download, cleaning, analysis, and report generation.

```bash
python code/main.py
```

### Configuration
-   **Random Seeds**: Set in `code/config.py` (default: 42).
-   **Data Paths**: Default to `data/raw/` and `data/processed/`.
-   **Thresholds**: Configurable in `code/config.py` (e.g., min planets per bin, uncertainty limits).

### Expected Output
Upon successful completion:
1.  `data/processed/cleaned_planets.csv`: The filtered dataset.
2.  `data/processed/binned_results.csv`: Gap locations per period bin.
3.  `data/processed/final_analysis_results.json`: Measured slope, p-values, and validation status.
4.  `reports/summary.md`: Human-readable summary of findings.

## Testing

Run the test suite to verify data cleaning and statistical logic:

```bash
pytest tests/ -v
```

## Troubleshooting
-   **Data Download Fails**: Ensure internet connectivity. The script retries 3 times with exponential backoff.
-   **Memory Error**: The script processes data in chunks. If issues persist, check RAM usage (limit ~7GB).
-   **GMM Convergence**: If GMM fails to converge, check the `binned_results.csv` for "UNRESOLVED" bins.
