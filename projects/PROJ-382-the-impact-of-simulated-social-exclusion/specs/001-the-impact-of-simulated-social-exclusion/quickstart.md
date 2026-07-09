# Quickstart: The Impact of Simulated Social Exclusion on Subsequent Prosocial Behavior

## Prerequisites

*   Python 3.11+
*   `pip`
*   Git

## Installation

1.  **Clone the repository** (or navigate to the project root):
    ```bash
    cd projects/PROJ-382-the-impact-of-simulated-social-exclusion
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

## Running the Pipeline

The pipeline is executed via the `main.py` script. It will attempt to ingest the verified datasets, validate schemas, and run the analysis.

**Note**: As per the research findings in `research.md`, the current set of verified datasets does not contain the required social exclusion data. Running this script will likely result in a "Insufficient Data" halt, which is the expected and correct behavior.

```bash
python code/main.py
```

### Expected Output

*   **Success**: If valid datasets are found, the script will output:
    *   `data/processed/cleaned_data.csv`
    *   `data/processed/analysis_results.json`
    *   Console logs with effect sizes (both zero-inflation and gamma components) and confidence intervals.
*   **Halt**: If <3 valid datasets are found (current state), the script will:
    *   Log: `ERROR: Insufficient Data: <3 valid datasets found`.
    *   Exit with code `1`.

## Verification

To verify the pipeline logic without needing real data, run the unit tests with synthetic data:

```bash
pytest tests/ -v
```

This will test:
*   Schema validation (pass/fail logic).
*   Zero-inflation handling (structural zeros preserved).
*   Model fitting on synthetic ZIG data.
*   Sensitivity analysis sweep (link function/distribution).

## Troubleshooting

*   **Missing Columns**: If a dataset is rejected, check `logs/ingestion.log` for the specific missing column.
*   **Memory Error**: If running on a local machine with <8GB RAM, reduce the batch size in `ingestion.py` (though unlikely for this dataset size).
*   **Model Convergence**: If ZIG fails to converge, the script falls back to Hurdle or logs a warning.