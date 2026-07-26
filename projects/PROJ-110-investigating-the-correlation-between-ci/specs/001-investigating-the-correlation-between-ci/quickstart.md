# Quickstart: Investigating the Correlation Between Circadian Gene Expression and Metabolic Syndrome Risk

## Prerequisites

- Python 3.11+
- `pip` (Python package manager)
- Git (for cloning the repository)
- Access to Hugging Face (public datasets do not require a token, but a free account is recommended for rate limits).
- Access to GTEx v8 data (via official portal or verified mirror).

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd projects/PROJ-110-investigating-the-correlation-between-ci
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

   *Note: `requirements.txt` includes `pandas`, `numpy`, `scipy`, `scikit-learn`, `statsmodels`, `datasets`, `matplotlib`, `seaborn`, `pyyaml`.*

## Running the Pipeline

The pipeline is orchestrated via `code/main.py`.

### 1. Download Data
Fetches the GTEx v8 dataset from the verified source.
```bash
python code/data/download_gtex.py
```
*Output*: `data/raw/gtex_data.parquet` (or similar).

### 2. Validate Phenotype (NEW)
Checks for the presence of all required clinical variables.
```bash
python code/data/validate_phenotype.py
```
*Output*: `data/processed/validation_report.json`.
*Logs*: Warnings if variables are missing or unreliable.

### 3. Classify Metabolic Status
Applies ATP-III criteria to label donors.
```bash
python code/data/classify_metabolic.py
```
*Output*: `data/processed/baseline_labels.csv`.
*Logs*: Warnings for excluded samples and low-power tissues.

### 4. Run Analysis
Executes differential expression, correlation, and logistic regression.
```bash
python code/main.py
```
*Output*:
- `data/processed/model_results.json`
- `data/processed/figures/` (Heatmaps, ROC curves, Scatters)

### 5. Sensitivity Analysis (NEW)
Runs the threshold variation test (SC-005).
```bash
python code/sensitivity/sensitivity_analysis.py
```
*Output*: `data/processed/sensitivity_results.json`.

### 6. Validate Results
Run unit and integration tests to ensure reproducibility.
```bash
pytest tests/
```

## Troubleshooting

- **Missing Data**: If the log reports "Insufficient GTEx sample size (N < 100)", the study is running in `exploratory` mode. Results should be interpreted with caution.
- **Memory Error**: If the process runs out of memory, ensure the `streaming=True` flag is used in the download script, or reduce the sample size in `config.yaml`.
- **Tissue Exclusion**: Tissues with < 20 samples per group are automatically excluded. Check `stderr` for the specific list of excluded tissues.
- **Variable Validation**: If `validate_phenotype.py` reports missing "Fasting Glucose", the study cannot proceed with strict ATP-III classification.

## Expected Outputs

- **baseline_labels.csv**: A CSV with columns `donor_id`, `metabolic_status`, `criteria_count`, `validation_status`.
- **model_results.json**: A JSON file containing:
  - `differential_expression`: List of genes with p-values, FDR, and effect sizes.
  - `correlation`: List of gene-trait correlations with coefficients and p-values.
  - `logistic_regression`: AUC, Odds Ratios, and 95% CIs for each gene (Binary, Severity, Trait-Specific).
  - `sensitivity`: Stability metrics for threshold variations.
- **figures/**: PNG files for ROC curves, heatmaps, and scatter plots.