# Quickstart: The Impact of Network Efficiency on Age-Related Changes in Resting-State EEG

## Prerequisites
- Python 3.11+
- Git
- Substantial RAM (recommended for full dataset)

## Installation

1. **Clone and Setup**:
 ```bash
 git clone <repo-url>
 cd projects/PROJ-429-the-impact-of-network-efficiency-on-age-/
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 pip install -r code/requirements.txt
 ```

2. **Verify Data Sources**:
 Ensure you have internet access to fetch the verified datasets. The script will attempt to download from:
 - ` (TUH EEG Corpus)
 - *Note*: If the TUH EEG Corpus does not contain linked cognitive scores, the pipeline will run in "EEG-Only" mode.

## Running the Pipeline

Execute the full pipeline sequentially. Parameters (thresholds, bands) are loaded from `code/config.yaml`.

```bash
# 1. Download Data (or skip if already present)
# This step converts raw TUH data (EDF/JSON) to Parquet for batch processing
python code/01_download_data.py

# 2. Preprocess EEG (Filter, ICA, Epoch)
python code/02_preprocess_eeeg.py

# 3. Compute Graph Metrics (using Imaginary Coherence)
python code/03_compute_graph_metrics.py

# 4. Run Power Analysis & Correlation Analysis
python code/04_correlation_analysis.py

# 5. Run Regression & Stratification
python code/05_regression_analysis.py

# 6. Generate Visualizations
python code/06_visualization.py
```

## Expected Outputs

- `data/processed/metrics.csv`: Network metrics per participant.
- `results/correlations.json`: Spearman correlations and p-values (Age only if Cognition missing).
- `results/power_analysis.json`: Simulation-based power analysis results.
- `results/fwer_check.json`: Family-Wise Error Rate measurement.
- `results/regression_summary.json`: Regression coefficients and warnings (e.g., "Missing Cognitive Data").
- `results/plots/`: Age-stratified network efficiency plots.

## Testing

Run unit tests to verify graph metric calculations:
```bash
pytest tests/test_graph_metrics.py -v
```

Run integration test on a small subset:
```bash
python tests/test_pipeline.py --subset 5
```