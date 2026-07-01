# Quickstart: The Impact of Visual Motion on Perceived Agency in Virtual Interactions

## Prerequisites

-   Python 3.11+
-   `pip` or `conda`
-   Git

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-531-the-impact-of-visual-motion-on-perceived
    ```

2.  **Create and activate virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```

## Running the Pipeline

### Step 1: Data Acquisition
Download real data (if available) or generate synthetic data.
```bash
python code/download_data.py
```
-   **Output**: `data/raw/synthetic_agency_data.csv` (or real data if found).
-   **Note**: If no real dataset meets criteria, synthetic data is generated automatically for pipeline stress-testing.

### Step 2: Preprocessing
Extract motion features and clean data.
```bash
python code/preprocess.py
```
-   **Output**: `data/processed/analysis_ready.csv`
-   **Logs**: `data/processed/preprocessing_log.txt` (includes VIF diagnostics, missing value handling).

### Step 3: Model Fitting
Fit Ridge Regression and Random Forest models.
```bash
python code/model_fitting.py
```
-   **Output**: `data/processed/model_results.json` (coefficients, p-values, feature importance, VIF).

### Step 4: Sensitivity Analysis
Sweep noise parameters to test robustness.
```bash
python code/sensitivity_analysis.py
```
-   **Output**: `data/processed/sensitivity_report.json`
-   **Description**: This script varies noise magnitude and heteroscedasticity levels to assess how model performance degrades under different data quality conditions. It does **not** sweep coefficient thresholds.

### Step 5: Visualization
Generate plots.
```bash
python code/visualization.py
```
-   **Output**: `data/processed/figures/` (scatter plots, feature importance bar chart, partial dependence plot).

## Verification

Run the test suite to ensure all components work correctly.
```bash
pytest tests/
```

## Troubleshooting

-   **Error: "Insufficient sample size"**: The pipeline aborted because fewer than a sufficient number of complete observations were found. This is expected if the synthetic data generation failed or real data was too small. Check `data/processed/preprocessing_log.txt`.
-   **Error: "Collinearity detected"**: A predictor has VIF ≥5. Ridge Regression is used to handle this without dropping variables. Check `data/processed/preprocessing_log.txt` for details.
-   **Error: "Invalid instrument"**: The dataset's agency questionnaire lacks a DOI or citations. The pipeline will skip this dataset and generate synthetic data instead.
