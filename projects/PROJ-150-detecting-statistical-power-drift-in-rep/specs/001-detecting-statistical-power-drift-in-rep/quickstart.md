# Quickstart: Detecting Statistical Power Drift in Replicated Studies

## Prerequisites

- Python 3.11 or higher
- `pip` or `conda`
- Git (for repository access)

## Installation

1.  **Clone the Repository**:
    ```bash
    git clone <repository-url>
    cd projects/PROJ-150-detecting-statistical-power-drift-in-rep
    ```

2.  **Create Virtual Environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: `requirements.txt` pins versions for `pandas`, `statsmodels`, `scipy`, `huggingface_hub`, etc.*

4.  **Download Data**:
    The pipeline automatically downloads the OSF dataset from Hugging Face if `data/raw/` is empty. To manually download:
    ```bash
    python code/preprocess.py --download-only
    ```

## Running the Analysis

### Full Pipeline
Execute the entire analysis from data cleaning to robustness checks:
```bash
python code/main.py
```
This will:
1.  Download and clean data.
2.  Calculate power estimates.
3.  Perform residualization and fit the LMM.
4.  Run permutation tests and sensitivity analysis.
5.  Generate visualizations and JSON reports.

### Individual Tasks
You can run specific components:

- **Preprocessing & Power Calculation**:
  ```bash
  python code/preprocess.py
  ```
  Outputs: `data/derived/cleaned_data.csv`, `data/derived/grouping_validation.json`

- **Residualization & Model Fitting**:
  ```bash
  python code/models.py
  ```
  Outputs: `data/derived/residuals.csv`, `results/lmm_final_summary.json`

- **Robustness Checks**:
  ```bash
  python code/robustness.py
  ```
  Outputs: `results/permutation_pvalue.json`, `results/sensitivity_report.json`, `results/aggregated_drift.json`

- **Visualization**:
  ```bash
  python code/visualize.py
  ```
  Outputs: `results/power_drift_plot.png`

## Expected Outputs

After a successful run, the `results/` directory will contain:
- `lmm_final_summary.json`: Primary drift slope and p-values.
- `permutation_pvalue.json`: Empirical p-value from the permutation test.
- `sensitivity_report.json`: Drift significance across alpha thresholds.
- `aggregated_drift.json`: Cross-field aggregated drift estimate.
- `power_drift_plot.png`: Visualization of residual power vs. year.

## Troubleshooting

- **Memory Error**: If you encounter OOM errors, ensure `streaming=True` is used in `code/preprocess.py` or reduce the dataset size.
- **Permutation Timeout**: If the permutation test takes too long, the script will automatically fall back to [deferred] iterations and flag the result as "approximate".
- **Missing Data**: Studies with missing `year`, `effect_size`, or `sample_size` are skipped and logged in `preprocess.log`.
