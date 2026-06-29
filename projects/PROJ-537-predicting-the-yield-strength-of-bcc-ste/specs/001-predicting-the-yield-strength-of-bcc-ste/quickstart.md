# Quickstart: Predicting the Yield Strength of BCC Steels

## Prerequisites
- Python 3.11+
- `pip` or `conda`
- Access to the project repository
- Internet access (to download datasets from HuggingFace)

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-537-predicting-the-yield-strength-of-bcc-ste
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```
   *Note: `requirements.txt` will pin versions of `pandas`, `scikit-learn`, `numpy`, `matplotlib`, `seaborn`, `shap`, `datasets`, `pytest`.*

## Running the Pipeline

The pipeline is orchestrated via `code/main.py`.

1. **Download Datasets**:
   ```bash
   python code/data/fetch_experimental.py
   python code/data/fetch_dft.py
   ```
   *This step downloads verified datasets from HuggingFace and saves them to `data/raw/`.*

2. **Run the Full Pipeline**:
   ```bash
   python code/main.py
   ```
   This script will:
   - Load and merge data.
   - Filter for BCC structure.
   - Check sample size (n >= 20). If n < 20, it will log a warning and switch to "Exploratory Mode" (omit t-test, report effect sizes). If n = 0, it will raise `DataAvailabilityError`.
   - Train the Random Forest models (with and without DFT).
   - Perform 5-fold cross-validation.
   - Run statistical tests (Pearson correlation; paired t-test **only if n >= 20**).
   - Generate SHAP values, sensitivity analysis, and feature importance plots.
   - Save results to `data/processed/`.

3. **Verify Results**:
   Check `data/processed/model_results.json` for R², MAE, p-values (if applicable), and SHAP values.
   Check `data/processed/feature_importance.csv` for stability metrics.

## Testing

Run unit and integration tests:
```bash
pytest tests/ -v
```

## Troubleshooting
- **Error: "Data Availability Failure"**: The merged dataset has n = 0. This means no BCC Fe-alloys were found in the overlap of the verified datasets. The study cannot proceed.
- **Error: "Power Warning"**: The merged dataset has n < 20. The study will proceed in "Exploratory Mode", reporting effect sizes and confidence intervals instead of p-values. The paired t-test will be omitted.
- **Error: "No BCC entries found"**: The filter logic is strict. Ensure the datasets contain BCC entries.
- **Memory Error**: The dataset is small (<1GB). If this occurs, check for memory leaks.