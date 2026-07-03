# Quickstart: The Effect of Simulated Social Comparison on Self-Esteem in Virtual Reality

## Prerequisites
-   Python 3.11+
-   pip
-   Git

## Installation

1.  **Clone the Repository:**
    ```bash
    git clone <repo-url>
    cd projects/PROJ-490-the-effect-of-simulated-social-compariso
    ```

2.  **Create Virtual Environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r code/requirements.txt
    ```

## Running the Pipeline

### Step 1: Data Discovery / Generation
Run the data module to attempt real data retrieval or trigger synthetic generation.
```bash
python code/main.py --action download
```
*Output:* `data/raw/dataset.csv` (or synthetic equivalent) and a log indicating "Real Data" or "Synthetic Data (Pipeline Validation)".

### Step 2: Preprocessing
Clean data, handle missing values, and compute change scores.
```bash
python code/main.py --action preprocess
```
*Output:* `data/processed/cleaned_data.csv` and `data/processed/exclusion_report.json`.

### Step 3: Analysis
Fit the regression model, check assumptions, and run bootstrap.
```bash
python code/main.py --action analyze
```
*Output:* `data/results/regression_results.json`, `data/results/bootstrap_results.json`.

### Step 4: Validation
Validate outputs against schemas.
```bash
python code/main.py --action validate
```
*Output:* Console report of schema validation status.

## Verification
To verify the pipeline works on your machine:
1.  Ensure `data/results/regression_results.json` contains `interaction_beta`, `p_value`, and `assumptions`.
2.  Check that `assumptions.vif` values are < 5 (or flagged if not).
3.  Confirm `bootstrap_results.ci_width_variance` is < 0.01.

## Troubleshooting
-   **Missing Data Error:** If the dataset has >20% missingness in key variables, the pipeline will exclude rows and log the count. Check `data/processed/exclusion_report.json`.
-   **Model Assumption Failure:** If Shapiro-Wilk p < 0.05, the results will be marked as "Assumptions Violated". Do not interpret significance; rely on confidence intervals.
-   **Collinearity:** If VIF ≥ 5, the interpretation will be descriptive only.
