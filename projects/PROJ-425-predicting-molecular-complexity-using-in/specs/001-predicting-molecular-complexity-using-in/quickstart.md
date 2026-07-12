# Quickstart: Predicting Molecular Complexity Using Information Theory

## Prerequisites

- Python 3.11+
- pip (package manager)
- Git

## Setup

1. **Clone the repository** (if not already done):
   ```bash
   git clone <repo-url>
   cd projects/PROJ-425-predicting-molecular-complexity-using-in
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   *Note: `requirements.txt` includes `rdkit`, `pandas`, `numpy`, `scipy`, `scikit-learn`, `matplotlib`, `seaborn`, `datasets`.*

## Running the Analysis

Execute the full pipeline (download, compute, analyze, visualize):

```bash
python code/main.py
```

### What this does:
1. **Downloads** a stratified random sample of [deferred] molecules from the verified HuggingFace dataset.
2. **Computes** Shannon Entropy (raw and per-atom), LZ Length, SA Score, and QED Score for each.
3. **Performs** Pearson and Spearman correlation, 1,000-iteration bootstrap resampling, and multiple-comparison correction.
4. **Generates** plots and a JSON report.

## Expected Outputs

- **Console**: Progress logs, summary statistics.
- **`data/processed/metrics.csv`**: Full dataset with all metrics (including `smiles` and `lz_length`).
- **`reports/stats.json`**: Correlation coefficients, p-values, CIs, and partial correlations.
- **`reports/figures/`**: Four scatter plots with regression lines.

## Troubleshooting

- **Memory Error**: Ensure you are not running other heavy processes. The script uses chunked processing during the initial load.
- **RDKit Import Error**: Ensure `rdkit` is installed correctly. On some systems, it may require `conda` or specific wheel installation.
- **Dataset Load Error**: Verify internet connection. The script fetches data from HuggingFace. If the download fails, it will retry with exponential backoff.
- **Timeout Errors**: If many molecules timeout, check for network issues or extremely complex structures. These are logged and skipped.

## Verification

To verify the results manually:
1. Check `reports/stats.json` for the correlation coefficients (both Pearson and Spearman).
2. Open `reports/figures/entropy_sa.png` to visually inspect the relationship.
3. Ensure the `adjusted_p_value` in the JSON is below the Bonferroni-corrected threshold for significant findings.
4. Verify the `smiles` and `lz_length` columns in `data/processed/metrics.csv` to confirm they are stored side-by-side.
