# Quickstart: Predicting the Effect of Alloying on the Poisson's Ratio of Aluminum Alloys

## Prerequisites

-   Python 3.11+
-   `pip`
-   Access to the internet (for downloading `matminer` data)

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
    *Note: `requirements.txt` includes `matminer`, `pandas`, `scikit-learn`, `compositional`, `statsmodels`, `pyyaml`, `joblib`, `chemparse`.*

## Running the Pipeline

The entire pipeline can be executed via the main orchestration script:

```bash
python code/main.py
```

This script performs the following steps in order:
1.  **Download**: Fetches data from `matminer` and verified NIST sources.
2.  **Clean**: Filters for monolithic Al alloys, normalizes units, excludes incomplete records.
3.  **Transform**: Applies ILR transformation and calculates VIF on raw data.
4.  **Train**: Trains Random Forest with 5-fold CV and evaluates on test set.
5.  **Interpret**: Back-transforms feature importance and generates the final report.

## Output Artifacts

After successful execution, check the following directories:

-   `data/processed/alloys_clean.parquet`: The cleaned dataset.
-   `data/processed/alloys_ilr.parquet`: The dataset with ILR features.
-   `results/model_metrics.json`: MAE and sample counts.
-   `results/feature_importance.json`: Ranked alloying elements (includes `ranked_elements` array).
-   `results/final_report.md`: The associational findings report.
-   `data/checksums.json`: SHA-256 checksums for all data files.

## Troubleshooting

-   **No Data Found**: If the dataset is empty, check the `data/logs/app.log` for filtering reasons (e.g., "Sum of elements < 0.95").
-   **VIF Flag**: If `is_flagged` is True in `collinearity_diagnostic.json`, the raw data is highly collinear (expected), but the model uses ILR so this is a diagnostic only.
-   **Matminer Error**: Ensure you have an internet connection. `matminer` fetches data from the Materials Project API.

## Validation

To validate the output against the contract schemas:

```bash
pytest tests/test_contracts.py
```

This ensures that `results/*.json` files match the defined YAML schemas.