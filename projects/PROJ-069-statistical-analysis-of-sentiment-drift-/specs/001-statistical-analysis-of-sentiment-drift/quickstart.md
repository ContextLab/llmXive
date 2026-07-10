# Quickstart: Sentiment Drift Analysis

## Prerequisites

- Python 3.10+
- Valid FRED API Key (optional, if using direct API; otherwise use HF datasets).
- Access to HuggingFace datasets (free tier).

## Installation

1.  Clone the repository.
2.  Create a virtual environment:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  Install dependencies:
    ```bash
    pip install -r code/requirements.txt
    ```

## Running the Analysis

The analysis is orchestrated via a single Jupyter Notebook which calls the modular scripts.

1.  **Start the notebook**:
    ```bash
    jupyter notebook notebooks/analysis_master.ipynb
    ```
2.  **Execute all cells**:
    - The notebook will automatically:
        - Call `code/01_ingest_align.py` to download data from verified sources (GDELT, FRED) and align to **monthly** frequency.
        - Call `code/02_stationarity_test.py` to perform ADF tests and interpolation.
        - Call `code/03_granger_analysis.py` to run Granger tests (using 3 sentiment variables).
        - Call `code/04_validation.py` to execute MBB (block=1 month) and sensitivity analysis.
        - Call `code/05_visualization.py` to generate plots with NBER shading.
3.  **Output**:
    - Check `data/processed/` for intermediate CSVs and JSONs.
    - The notebook will display final plots and a summary table of p-values.

## Verification

To verify the run:
- Check that `data/processed/aligned_monthly.csv` exists and has no missing values (or documented interpolation/exclusion).
- Verify that `data/processed/model_results.json` contains p-values for all variable pairs.
- Confirm that plots in the notebook have shaded recession periods.
- Ensure `sentiment_low_confidence` flags are set correctly based on the A threshold value will be established to determine the removal or generalization criteria..

## Troubleshooting

- **Memory Error**: Reduce the GDELT dataset sample size in `code/01_ingest_align.py` (default a large-scale dataset).
- **FRED API Error**: Ensure API key is set in environment variable `FRED_API_KEY` or use the verified HF dataset wrapper.
- **Stationarity Failure**: Check logs in `code/02_stationarity_test.py` for fallback transformation details.