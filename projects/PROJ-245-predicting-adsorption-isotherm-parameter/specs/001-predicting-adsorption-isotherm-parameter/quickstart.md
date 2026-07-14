# Quickstart: Predicting Adsorption Isotherm Parameters from Molecular Features

## Prerequisites

-   Python 3.11+
-   Git
-   A POSIX-compliant shell (bash/zsh)

## Installation

1.  **Clone the Repository**
    ```bash
    git clone <repo-url>
    cd projects/PROJ-245-predicting-adsorption-isotherm-parameter
    ```

2.  **Create Virtual Environment**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```
    *Note: `requirements.txt` pins versions for `rdkit`, `scikit-learn`, `pandas`, `numpy`, `shap`.*

## Running the Pipeline

The pipeline is executed via the `main.py` script. It handles data generation (synthetic), preprocessing, training, and evaluation.

```bash
python code/main.py
```

### What happens?

1.  **Verification Audit**: Attempts to fetch NIST/MOF-1000. If failed, writes `verification_log.json`.
2.  **Data Generation**: Creates a synthetic dataset (if real data unavailable) matching `contracts/dataset.schema.yaml`.
3.  **Preprocessing**: Filters for Type I isotherms, calculates RDKit descriptors, normalizes units.
4.  **Training**: Trains Linear Regression, Random Forest, and Gradient Boosting models with 5-fold CV.
5.  **Evaluation**: Computes R², RMSE, MAE on the material-level split test set.
6.  **Interpretation**: Generates SHAP summary plots and performs FDR-corrected permutation tests.
7.  **Output**: Saves results to `data/processed/` and logs metrics to `stdout`.

## Verifying the Results

### 1. Check Output Files
Ensure the following files are generated:
-   `data/processed/train.csv`
-   `data/processed/test.csv`
-   `data/processed/model_metrics.json`
-   `data/processed/shap_summary.png`
-   `data/verification_log.json` (if real data was unavailable)

### 2. Validate Success Criteria
-   **SC-001**: Check `model_metrics.json` for the best model's R² (Pipeline check).
-   **SC-004**: Verify runtime < 6h.
-   **SC-005**: Check that adjusted p-values (q-values) are present.
-   **SC-002/SC-003**: **Note**: These criteria are **Deferred**. They will only be measured in Phase 3 (External Validation) using a real literature dataset. Do not interpret synthetic R² values as scientific proof.

## Troubleshooting

-   **ImportError: No module named 'rdkit'**: Ensure you activated the virtual environment and ran `pip install -r requirements.txt`. RDKit is large; installation may take a few minutes.
- **Memory Error**: The synthetic dataset is capped to [deferred] rows. If you modify the generator to create more data, ensure you stay within the 7GB RAM limit of the CI runner.
-   **No Verified Data**: If the script complains about missing data, it is expected. The pipeline uses the built-in synthetic generator and writes a `verification_log.json`. Do not attempt to fetch external URLs.

## Next Steps

-   **Interpretation**: Review the SHAP plots in `data/processed/` to understand which molecular features drive adsorption (Pipeline check).
-   **External Validation**: (Phase 3) Load a small, verified literature dataset (e.g., Kr on CNTs) and re-run the pipeline to validate the scientific hypothesis (SC-002/SC-003).
-   **Extension**: Replace the synthetic generator with a verified dataset (if a valid URL is found in the future) and re-run.