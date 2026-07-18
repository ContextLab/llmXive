# Quickstart: Investigating the Correlation Between Circadian Gene Expression and Metabolic Syndrome Risk

## Prerequisites

*   Python 3.11+
*   Git
*   Access to a terminal with network access (for downloading datasets).

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repository-url>
    cd projects/PROJ-110-investigating-the-correlation-between-ci
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

4.  **Verify environment**:
    ```bash
    python -c "import pandas, scipy, statsmodels, sklearn; print('Dependencies OK')"
    ```

## Running the Pipeline

The pipeline is designed to run end-to-end. It will download data (if missing), classify samples, run statistical tests, and generate plots.

1.  **Execute the main script**:
    ```bash
    python code/main.py
    ```

    *   **Step 1**: Downloads GTEx/TCGA data to `data/raw/`.
    *   **Step 2**: Validates columns and classifies samples (ATP-III).
    *   **Step 3**: Runs Wilcoxon tests (Differential Expression).
    *   **Step 4**: Fits Logistic Regression with 5-fold CV.
    *   **Step 5**: Generates plots (ROC, Heatmap, Scatter) in `data/processed/figures/`.

2.  **Check outputs**:
    *   **Classification**: `data/processed/baseline_labels.csv`
    *   **DE Results**: `data/processed/results/differential_expression.csv`
    *   **Model Results**: `data/processed/results/logistic_regression.csv`
    *   **Plots**: `data/processed/figures/` (e.g., `roc_curve.png`, `heatmap_sig_genes.png`)

## Unit Testing

Run the test suite to verify logic (especially ATP-III classification and statistical methods):

```bash
pytest tests/ -v
```

*   **Key Tests**:
    *   `test_classifier_atp_iii`: Verifies correct labeling of MetS vs Control.
    *   `test_missing_data_exclusion`: Verifies that samples with missing values are excluded.
    *   `test_fdr_correction`: Verifies Benjamini-Hochberg implementation.
    *   `test_vif_detection`: Verifies collinearity flagging.

## Troubleshooting

*   **Missing Columns in Dataset**: If the script fails with "Missing column: [X]", the verified dataset URL may not contain the required phenotype data. Check `research.md` for the dataset strategy and potential power limitations.
*   **Memory Error**: If the dataset is too large, the script will automatically switch to a sampled subset (if configured) or fail with a clear message. Ensure you have at least 7 GB RAM available.
*   **Collinearity Warnings**: If VIF > 5 is detected, the model will flag the predictors. Review `data/processed/results/logistic_regression.csv` for the `VIF` column.
