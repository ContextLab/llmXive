# Quickstart: The Use of Climate-Smart Agricultural Practices in Rural Areas to Improve Food Security and Livelihoods

## Prerequisites

-   Python 3.14.6 (Source: History of Python, https://en.wikipedia.org/wiki/History_of_Python).
    *Note: The Spec and Verified Facts mandate Python 3.14.6. The implementation MUST use this exact version. No fallback is permitted.*
-   `pip` and `venv`.
-   Access to Hugging Face Hub (for dataset downloads) and World Bank LSMS Portal (for LSMS microdata).

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-020-the-use-of-climate-smart-agricultural-pr
    ```

2.  **Create and activate virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Running the Pipeline

1.  **Download and Process Data**:
    ```bash
    python code/ingestion.py
    python code/preprocessing.py
    ```

2.  **Fit Models**:
    ```bash
    python code/modeling.py
    ```

3.  **Run Robustness Checks**:
    ```bash
    python code/robustness.py
    ```

4.  **Generate Visualizations**:
    ```bash
    python code/viz.py
    ```

5.  **Verify Reproducibility**:
    ```bash
    python code/verify_reproducibility.py
    ```
    *This script generates `reproducibility_report.md` confirming the pipeline ran successfully on a fresh environment.*

## Expected Output

-   `data/processed/analysis_dataset.parquet`
-   `output/model_results.json`
-   `output/figures/` (Scatter, Coefficient, Map, Distribution plots)
-   `reproducibility_report.md`

## Verification

To verify the pipeline:
1.  Run `python tests/test_ingestion.py`.
2.  Run `python tests/test_modeling.py`.
3.  Check `output/figures/` for the presence of 4 distinct plot types.
4.  Verify that `output/model_results.json` contains `p_value_corrected` and `significance` fields.
5.  Confirm that the `provenance_id` field in `analysis_dataset.parquet` maps to raw survey IDs (or composite key).
6.  **Execution Logs**: Verify that `logs/pipeline.log` contains entries confirming:
    -   Successful download of LSMS data for KEN, IND, VNM.
    -   Successful spatial merge (radius-based proximity).
    -   CSA Index construction including digital/finance variables.
    -   Fixed-Effects model fit with Country Dummies.
    -   Bonferroni correction applied.
    -   Sensitivity analysis range executed.
7.  **Reproducibility Report**: Verify that `reproducibility_report.md` exists and confirms successful end-to-end execution.

## Troubleshooting

- **Timeout**: If the model fitting exceeds 6 hours, the script will automatically reduce the sample size by [deferred] and retry. If timeout persists, reduce by [deferred] (as per FR-010).
-   **Missing Data**: If climate data gaps are > 3 months, the script will log a warning and skip imputation.
-   **VIF Warning**: If VIF > 5.0, the script will log a warning but continue (as per Constitution Principle VII).
-   **N < 5000**: If sample size < 5000, the script will log a warning and proceed (as per Spec Edge Cases).
-   **Python Version**: If Python 3.14.6 is not found, the script will raise a critical error and exit (as per Verified Facts constraint).