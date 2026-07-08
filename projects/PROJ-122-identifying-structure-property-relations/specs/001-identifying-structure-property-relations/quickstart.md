# Quickstart: Identifying Structure-Property Relationships in Polymer Blends

## Prerequisites

*   Python 3.11+
*   Access to a GitHub Actions runner (or local environment with multiple CPU cores and sufficient RAM).
*   API keys for Materials Project (if required by the spec's assumed sources).

## Installation

1.  Clone the repository and navigate to the project root.
2.  Create a virtual environment:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  Install dependencies:
    ```bash
    pip install -r code/requirements.txt
    ```

## Running the Pipeline

Execute the full pipeline end-to-end:
```bash
bash code/run_pipeline.sh
```

This script performs the following steps in order:
1.  **Ingest**: Fetches data, harmonizes units, validates weight fractions.
2.  **Features**: Generates RDKit descriptors and computes baseline physical models (Fox/GT).
3.  **Train**: Trains RF, XGB, and Linear models; performs cross-validation and t-tests; runs VIF sensitivity analysis.
4.  **Stability**: Executes **5 independent training runs** with different random seeds to measure feature stability.
5.  **Report**: Generates SHAP plots, summary statistics, and the `data_quality_report.json`.

**Note**: If the data fetch fails to return polymer blend data with Tg/Modulus, the pipeline will halt with a "Data Insufficiency" error.

## Verifying Results

*   **Check Data Quality**: Review `data/processed/cleaned.csv` to ensure weight fractions sum to ~1.0. Check `results/data_quality_report.json` for the pass rate (SC-004).
*   **Check Descriptors**: Verify `data/features/descriptors.csv` has $\ge 15$ columns per monomer.
*   **Check Model Performance**: Look for `results/model_metrics.json` containing MAE and p-values.
*   **Check VIF**: Review `results/vif_analysis.txt` for collinearity flags and sensitivity results.
*   **Check Stability**: Review `results/stability_analysis.json` for feature importance consistency across 5 independent runs.

## Troubleshooting

*   **Data Insufficiency**: If the dataset has < 100 samples or missing target variables, the pipeline will halt. Check the logs for "Data Insufficiency" error.
*   **API Rate Limits**: The script implements exponential backoff. If it fails after multiple retries, check network connectivity or API status.
*   **Memory Error**: If running out of RAM, reduce the dataset size in `code/01_ingest.py` (sampling strategy).
*   **No Verified Source**: If NIST/Materials Project APIs do not return the required data, the pipeline halts. This is expected behavior per the research strategy.