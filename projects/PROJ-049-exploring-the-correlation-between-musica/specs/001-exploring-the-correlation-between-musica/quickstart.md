# Quickstart: Exploring the Correlation Between Musical Preference and Personality Traits

## Prerequisites
*   Python 3.11+
*   Git
*   Access to a terminal with `pip`

## Installation

1.  **Clone the repository** (or navigate to the project directory):
    ```bash
    cd projects/PROJ-049-exploring-the-correlation-between-musica
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Dependencies include: pandas, numpy, scipy, scikit-learn, matplotlib, seaborn, pytest.*

## Running the Pipeline

### 1. Data Ingestion & Preprocessing
This step generates the synthetic data (since verified sources are unavailable) and merges it.
```bash
python code/ingest.py
```
*   **Output**: `data/processed/merged_dataset.csv`
*   **Note**: If real data files are placed in `data/raw/`, this script will attempt to load them. Otherwise, it generates a deterministic synthetic dataset.

### 2. Statistical Analysis
Run the correlation and regression analysis.
```bash
python code/analysis.py
```
*   **Output**:
    *   `data/processed/analysis_results.csv` (Detailed stats)
    *   `data/processed/results_report.csv` (Summary report)
    *   `data/processed/correlation_heatmap.png`
    *   `data/processed/regression_coefficients.png`

### 3. Verify Results
Check the generated report.
```bash
cat data/processed/results_report.csv
```
Look for rows where `is_significant` is `True` and `adjusted_p_value` < 0.05. Check `effect_size_threshold_met` for SC-001 and `beta_delta` for SC-003.

## Testing
Run the unit tests to ensure the pipeline integrity.
```bash
pytest tests/
```

## Troubleshooting
*   **Missing Data Error**: If `merged_dataset.csv` is empty, check `code/ingest.py` logs. The script may have failed to generate synthetic data if the random seed was corrupted (unlikely).
*   **Memory Error**: The synthetic dataset is capped at 10k rows. If you replace it with a larger real dataset, ensure it fits in < 7GB RAM.
*   **No Significant Results**: This is expected if the synthetic data is random. The pipeline is validated by the *presence* of the output files and the correct application of FDR, not the existence of a specific correlation.