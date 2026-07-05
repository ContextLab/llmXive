# Quickstart: Traffic-Weather Severity Analysis

## Prerequisites

- Python 3.11+
- `pip`
- Access to the internet (for downloading datasets)
- Sufficient disk space (for raw data and processing)

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
    *Note: `requirements.txt` is generated during the implementation phase and will pin `statsmodels`, `pandas`, `numpy`, `scikit-learn`, `geopy`, `matplotlib`, `seaborn`, `pyyaml`, `pyarrow`, `h3`.*

## Data Setup

The project requires two datasets. Due to potential mismatches in the provided URLs, the script includes a fallback mechanism with **pinned sources**.

1.  **Run the ingestion script**:
    ```bash
    python code/ingest.py
    ```
    - This script will:
        - Invoke the Reference-Validator Agent to verify the pinned URLs (NHTSA 2022, HuggingFace `noaa/isd-hourly`).
        - If invalid, abort and flag the spec for update.
        - **Pre-filter** NOAA data to reduce memory footprint (using H3/geohash).
        - Merge the data based on location and time.
        - **Validate** the output against `merged_dataset.schema.yaml`, ensuring `match_method` is populated correctly.
        - Generate `data/processed/excluded_records_summary.csv` for bias quantification.
        - Save the result to `data/processed/merged_dataset.csv`.
        - Generate a checksum file `data/raw/checksums.json`.

2.  **Verify the data**:
    Ensure `data/processed/merged_dataset.csv` exists and contains at least 85% of records with valid weather data. Check `data/processed/excluded_records_summary.csv` for bias analysis.

## Running the Analysis

Execute the full pipeline:

```bash
python code/main.py
```

This will:
1.  Load the merged dataset.
2.  Fit the Ordinal Logistic Regression model (`model.py`).
3.  Run diagnostics (VIF, Brant test) (`diagnostics.py`).
4.  Perform the **Primary Robustness Check** (Subset-based Continuous Coefficient Stability) and **Secondary Hypothesis** (Binary Threshold Sweep).
5.  Generate plots and a summary report in `data/reports/`.

## Testing

Run the unit tests to verify logic:

```bash
pytest tests/ -v
```

## Output

- **Model Summary**: `data/reports/model_summary.txt` (Coefficients, Odds Ratios, AIC/BIC).
- **Diagnostics**: `data/reports/diagnostics.csv` (VIF values, Brant test p-value, PPO feasibility status).
- **Bias Report**: `data/reports/bias_quantification.txt` (Chi-square results).
- **Plots**: `data/reports/coefficient_plot.png`, `data/reports/spline_plot.png`, `data/reports/binary_sweep_plot.png`.
- **Final Report**: `paper/analysis_findings.md` (Generated from the above artifacts).