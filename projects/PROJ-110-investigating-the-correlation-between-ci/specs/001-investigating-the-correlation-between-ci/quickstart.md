# Quickstart: Investigating the Correlation Between Circadian Gene Expression and Metabolic Syndrome Risk

## Prerequisites

- Python 3.11+
- Git
- Access to a terminal with internet connectivity (for downloading datasets).

## Installation

1. **Clone the repository** (if not already done):
   ```bash
   git clone <repo-url>
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

## Data Preparation

The pipeline automatically downloads data from verified Hugging Face sources.
**Note**: Ensure you have sufficient disk space (~5-10GB) for the downloaded data.

1. **Run the data download script**:
   ```bash
   python code/data_loader.py --download
   ```
   This script will:
   - Stream data from the verified URLs.
   - Verify the schema (check for required clinical variables).
   - Save raw data to `data/raw/`.
   - Log any missing variables or access errors.

2. **Verify data integrity**:
   Check the log output for `ERROR` or `WARNING` messages. If the required clinical variables (BMI, Glucose, etc.) are missing, the pipeline will halt.

## Running the Analysis

1. **Execute the main pipeline**:
   ```bash
   python code/main.py
   ```
   This will:
   - Classify donors into MetS/Control.
   - Perform differential expression analysis (Wilcoxon).
   - Fit logistic regression models.
   - Generate diagnostic plots.
   - Save results to `data/processed/`.

2. **Expected Outputs**:
   - `data/processed/baseline_labels.csv`: Classification results.
   - `data/processed/statistical_results.csv`: P-values, FDR, Odds Ratios.
   - `data/processed/plots/`: Heatmaps, ROC curves, scatter plots.
   - `output/report.md`: Summary of findings.

## Testing

Run the test suite to verify correctness:
```bash
pytest tests/
```

## Troubleshooting

- **Missing Clinical Variables**: If the script fails with "Missing required columns", check the `research.md` for the "Critical Data Gap Analysis". The verified GTEx URLs may not contain the necessary phenotype data.
- **Memory Error**: If you encounter OOM errors, ensure `streaming=True` is used in `data_loader.py`. Do not load the full dataset into memory.
- **Permission Denied**: Ensure you have write access to `data/` and `code/`.

## Cleanup

To remove generated data (keep raw data):
```bash
rm -rf data/processed/*
```
