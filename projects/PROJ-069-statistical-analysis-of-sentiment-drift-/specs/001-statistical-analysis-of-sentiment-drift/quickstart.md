# Quickstart: Statistical Analysis of Sentiment Drift

## Prerequisites

- Python 3.11+
- Valid FRED API Key (set as `FRED_API_KEY` environment variable).
- HuggingFace Access Token (optional, for rate limits).

## Installation

1.  **Clone the repository** and navigate to the project root.
    ```bash
    git clone <repo-url>
    cd PROJ-069-statistical-analysis-of-sentiment-drift
    ```

2.  **Create a virtual environment** and install dependencies.
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r code/requirements.txt
    ```

3.  **Set Environment Variables**.
    ```bash
    export FRED_API_KEY="your_fred_api_key_here"
    # Optional: Set HuggingFace token if needed
    export HF_TOKEN="your_hf_token_here"
    ```

## Running the Pipeline

### Option A: Full Reproducible Run (Notebook)
The recommended way to run the full analysis (Ingestion -> Modeling -> Viz) is via the Jupyter Notebook.
```bash
jupyter notebook code/analysis_notebook.ipynb
```
*Note: If running in CI or without a display, use `jupyter nbconvert --execute code/analysis_notebook.ipynb`.*

### Option B: Modular Scripts
Run the pipeline step-by-step using the Python scripts:
1.  **Ingest Data**:
    ```bash
    python code/data_ingestion.py
    ```
    *Generates `data/processed/merged_timeseries.csv`.*

2.  **Run Analysis**:
    ```bash
    python code/modeling.py
    ```
    *Generates `data/processed/model_results.json` and `data/processed/stats_log.csv`.*

3.  **Generate Visuals**:
    ```bash
    python code/visualization.py
    ```
    *Generates plots in `artifacts/figures/`.*

## Validation & Testing

1.  **Unit Tests**:
    ```bash
    pytest tests/unit/
    ```
    *Tests interpolation logic, alignment, and schema validation.*

2.  **Contract Tests**:
    ```bash
    pytest tests/contract/
    ```
    *Validates output against `contracts/` schemas.*

3.  **Reproducibility Check**:
    Run the pipeline twice and compare checksums of `data/processed/merged_timeseries.csv`.
    ```bash
    # First run
    python code/analysis_notebook.ipynb
    md5sum data/processed/merged_timeseries.csv > checksum1.txt

    # Second run
    python code/analysis_notebook.ipynb
    md5sum data/processed/merged_timeseries.csv > checksum2.txt

    diff checksum1.txt checksum2.txt # Should show no differences
    ```

## Troubleshooting

- **Missing Data**: If the pipeline flags >5% missing data, check the `data/processed/alignment_log.csv` to see which periods were excluded.
- **Non-Stationarity**: If ADF tests fail, check `data/processed/stats_log.csv` for the applied transformation (e.g., "1st_diff").
- **API Errors**: Ensure `FRED_API_KEY` is set and valid. If running in CI without keys, the pipeline will fallback to synthetic data generation (if configured).
