# Quickstart: Investigating the Correlation Between Circadian Gene Expression and Metabolic Syndrome Risk

## Prerequisites

- Python 3.11+
- Git
- Access to GitHub Actions (for CI) or local environment.
- **GTEx v8 Phenotype and RNA-seq Data**: The pipeline requires the specific GTEx v8 files containing clinical variables (BMI, Glucose, BP, Lipids). If these are not available in the `data/raw/` directory, the pipeline will halt with a "Data Gap" error.

## Installation

1. **Clone the repository** (or navigate to the project directory):
   ```bash
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
   *Note: `requirements.txt` will pin specific versions of `pandas`, `scipy`, `scikit-learn`, etc.*

## Data Setup

The pipeline attempts to download data from the verified HuggingFace URLs defined in `research.md`. **Note**: If the verified URLs do not contain the required clinical variables, the pipeline will halt.

1. **Run the data download script**:
   ```bash
   python code/data/loader.py --download
   ```
   - This will fetch the GTEx phenotype and expression files from the verified URLs.
   - Files are saved to `data/raw/`.
   - Checksums are recorded in `state/.../artifact_hashes.yaml`.

2. **Verify Data Integrity**:
   ```bash
   python code/data/loader.py --verify
   ```
   - Ensures required columns (BMI, Glucose, BP, Lipids) are present.
   - **If columns are missing**: The script will halt and report "Data Gap - Study Invalid for Primary Hypothesis".

## Running the Analysis

Execute the full pipeline:

```bash
python code/main.py
```

This script will:
1. Load and clean data.
2. **Power Analysis**: Estimate complete case count (N) and perform formal power analysis.
3. Classify donors (ATP-III).
4. Run Differential Expression (Wilcoxon + FDR).
5. Fit Logistic Regression (5-fold CV, global model with tissue covariate).
6. **Correlation Analysis**: Compute correlations with continuous traits.
7. **Sensitivity Analysis**: Vary ATP-III thresholds.
8. Generate plots (Heatmap, ROC, Scatter).
9. Save results to `data/processed/`.
10. **Versioning**: Update state file with content hashes.

## Generating Reports

To generate the summary report (JSON/CSV) and plots:

```bash
python code/main.py --report
```

Output files:
- `data/processed/results/differential_expression.csv`
- `data/processed/results/correlation_results.csv`
- `data/processed/results/sensitivity_analysis.csv`
- `data/processed/results/model_metrics.json`
- `data/processed/plots/heatmap.png`
- `data/processed/plots/roc_curve.png`
- `data/processed/plots/correlation_scatter.png`

## Testing

Run the test suite:

```bash
pytest tests/
```

- **Unit Tests**: Verify ATP-III classification logic.
- **Integration Tests**: Verify end-to-end pipeline execution on a small sample subset.

## Troubleshooting

- **Missing Columns**: If the pipeline fails with "Missing Phenotype Variables", check `research.md` for the current status of the verified GTEx URLs. The specific files listed may not contain the required clinical data. In this case, the study cannot proceed with the primary hypothesis.
- **Memory Error**: If running out of RAM, ensure the gene filtering step (to ~15 core genes) is active. The pipeline is designed to load only these genes.
- **No Significant Genes**: This is a valid result. Check `data/processed/results/differential_expression.csv` for raw p-values.
- **Power Warning**: If N < 100, the pipeline will log a warning but proceed in "Exploratory" mode.