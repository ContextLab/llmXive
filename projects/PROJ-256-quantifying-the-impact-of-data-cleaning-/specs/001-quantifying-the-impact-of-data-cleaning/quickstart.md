# Quickstart: Quantifying the Impact of Data Cleaning on Statistical Inference

## Prerequisites
- Python 3.11+
- `pip` or `venv`

## Installation

1. **Clone and Setup Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r code/requirements.txt
   ```

2. **Verify Datasets**
   The script will automatically download the two verified datasets (UCI HAR, UCI Shopper) on first run. No manual download required.

## Running the Analysis

Execute the main pipeline:
```bash
python code/main.py
```

This will:
1. Download and checksum raw data.
2. Run baseline analysis.
3. Apply cleaning strategies (Outlier, Imputation, Recoding).
4. Compute metrics and bootstrap variances.
5. Generate visualizations and reports in `output/`.

## Output Artifacts
- `output/reports/summary.json`: Raw metrics and comparisons.
- `output/figures/forest_plot.png`: P-value shifts.
- `output/figures/heatmap.png`: CI width changes.
- `output/reports/sensitivity_analysis.md`: Textual summary of binning results.

## Troubleshooting
- **Runtime Error**: If the job exceeds a substantial duration, the bootstrap iterations will automatically reduce to 500. Check `output/logs/runtime.log`.
- **Missing Data**: If a dataset has >80% missing outcome, it is skipped. Check `output/logs/warnings.log`.
- **Memory Error**: If RAM usage > 7 GB, the script samples rows ([deferred] random sample) and logs a warning.
