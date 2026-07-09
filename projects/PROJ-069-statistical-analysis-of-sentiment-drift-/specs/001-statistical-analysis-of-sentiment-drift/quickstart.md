# Quickstart: Sentiment Drift Analysis

## Prerequisites

- Python 3.11+
- HuggingFace account (to access the sentiment dataset)
- FRED API key (set as environment variable `FRED_API_KEY`)
- GitHub Actions free tier (for CI reproducibility)

## Installation

```bash
git clone <repo-url>
cd projects/PROJ-069-statistical-analysis-of-sentiment-drift-/
python -m venv venv
source venv/bin/activate
pip install -r code/requirements.txt
```

## Execution Order

Run the scripts **exactly** in the order listed; each step depends on the previous output.

1. **Ingest raw data**  
   ```bash
   python code/01_ingest_data.py
   ```
   *Outputs*: `data/raw/fred_gdp.csv`, `data/raw/fred_unrate.csv`, `data/raw/fred_consumer_confidence.csv`, `data/raw/sentiment_daily.json`, `data/raw/nber_recessions.csv`

2. **Preprocess & align**  
   ```bash
   python code/02_preprocess.py
   ```
   *Outputs*: `data/processed/aligned_quarterly.csv`, `data/processed/sentiment_monthly.csv`, `data/data_quality_log.json`

3. **Stationarity tests & model fitting**  
   ```bash
   python code/03_stationarity_and_modeling.py
   ```
   *Outputs*: `results/model_stats.json`, `results/stationarity_log.txt`

4. **Robustness validation & sensitivity**  
   ```bash
   python code/04_validation_and_sensitivity.py
   ```
   *Outputs*: `results/validation_stats.json`

5. **Visualization & final report**  
   ```bash
   python code/05_visualization_and_report.py
   ```
   *Outputs*: `plots/timeseries_recession.png`, `plots/correlation_heatmap.png`, `docs/paper/report.html`, `analysis.ipynb`

## Reproducibility Checks

```bash
pytest tests/          # contract validation
pytest --nbval-lax analysis.ipynb   # notebook execution on fresh runner
```

The checksum of `data/processed/aligned_quarterly.csv` must match the hash recorded in the project state file; any mismatch indicates a data‑hygiene violation.

## Troubleshooting

- **Missing verified URLs**: The pipeline will abort with a clear message; add the missing URLs to the `# Verified datasets` block before rerunning.
- **Memory errors**: Reduce bootstrap iterations (`--iters 500`) if RAM is constrained.
- **Non‑stationary warnings**: Check `results/stationarity_log.txt` for applied transformations.
