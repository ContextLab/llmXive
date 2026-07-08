# Quickstart: Predicting Molecular Properties from Open Babel Fingerprints

## Prerequisites

*   Python 3.10+
*   `pip`
*   `openbabel` (system package) or `pybel`
*   `rdkit` (via conda or pip)
*   Sufficient disk space (for raw data and derived artifacts)

## Installation

1.  **Clone the repository** and navigate to the project directory.
2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```
    *Note: Ensure `openbabel` is installed on the system (e.g., `sudo apt-get install openbabel` on Linux).*

## Running the Pipeline

The pipeline is orchestrated via `code/main.py`. It executes in the following order:
1.  **Download**: Fetches verified datasets.
2.  **Preprocess**: Cleans data, computes Crippen baseline.
3.  **Fingerprint**: Generates MACCS, ECFP4, FP2 (priority order).
4.  **Train**: Trains Random Forest with k-fold cross-validation..
5.  **Analyze**: Computes SHAP interactions and statistical tests.

### Execute Full Run
```bash
python code/main.py
```

### Output Artifacts
After completion, check the `data/` directory:
*   `data/derived/predictions_baseline.csv`: Baseline errors.
*   `data/derived/predictions_rf.csv`: RF errors.
*   `data/derived/shap_interactions.parquet`: Interaction maps.
*   `data/derived/interaction_contexts.csv`: Mapped chemical contexts.
*   `data/quality_report.csv`: List of excluded molecules/missing variables.

## Verification

To verify the run:
1.  Check `data/quality_report.csv` for `missing_covariate` flags.
2.  Run the unit tests:
    ```bash
    pytest tests/unit/
    ```
3.  Run contract tests (schema validation):
    ```bash
    pytest tests/contract/
    ```

## Troubleshooting

*   **Runtime Exceeded**: If the process hits the 6h limit, it will automatically skip lower-priority fingerprints (FP2) and reduce dataset size. Check `logs/runtime.log`.
*   **Memory Error**: Reduce `n_estimators` in `code/config.py` or further sample the dataset.
*   **Missing OpenBabel**: Ensure `obabel` is in your system PATH.
