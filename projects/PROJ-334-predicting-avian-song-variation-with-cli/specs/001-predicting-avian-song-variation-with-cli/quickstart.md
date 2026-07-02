# Quickstart: Predicting Avian Song Variation with Climatic and Geographic Factors

## Prerequisites
-   Python 3.11+
-   Git
-   Access to the internet (to fetch Xeno-Canto and WorldClim data).

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-334-predicting-avian-song-variation-with-cli
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

## Data Setup

1.  **Fetch Data**: The pipeline automatically fetches data from Xeno-Canto and WorldClim v2.1.
    -   Ensure you have an internet connection.
    -   To use local cached data, place `song_record.csv` and `climate_snapshot.csv` in `data/raw/`.

2.  **Verify Checksums**:
    ```bash
    python code/utils.py --verify-checksums
    ```

## Running the Pipeline

Execute the full pipeline (Ingestion → EDA → Modeling → Sensitivity):

```bash
python code/main.py
```

### Output Artifacts
-   `data/processed/analysis_dataset.parquet`: Merged dataset.
-   `outputs/eda_report.json`: Correlation matrix and summary stats.
-   `outputs/model_summary.txt`: Regression coefficients and p-values.
-   `outputs/sensitivity_report.json`: Results of threshold sweep and FDR control.
-   `outputs/figures/`: Correlation heatmap, VIF plot, R² vs. Threshold plot.

## Testing

Run unit and integration tests:

```bash
pytest tests/ -v
```

### Specific Test Cases
-   **Ingestion**: Verify fetch logic and schema validation.
-   **EDA**: Ensure correlation matrix is symmetric and diagonal is 1.0.
-   **Modeling**: Verify FDR correction is applied and VIF > 5 is flagged.

## Troubleshooting

-   **Fetch Failed**: If the pipeline fails to fetch data, check internet connection or API rate limits.
-   **Memory Error**: If running out of RAM, reduce the sample size in `code/utils.py` or use the `--sample` flag.
-   **Coordinate Mismatch**: Ensure all coordinates are in WGS84 (decimal degrees).
