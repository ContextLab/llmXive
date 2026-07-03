# Quickstart: Network Module Dynamics in Predicting Working Memory

## Prerequisites

- Python 3.11+
- Git
- Sufficient free disk space (for data download and processing)
- Sufficient RAM for execution

## Setup

1. **Clone the Repository**:
   ```bash
   git clone <repo-url>
   cd <repo-dir>
   ```

2. **Create Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```

## Execution

### 1. Data Ingestion & Preprocessing
Run the ingestion script to download and preprocess data from **OpenNeuro ds001734** (verified public source).
```bash
python code/ingestion/download_hcp.py --dataset ds001734 --limit 100 --output data/processed/cleaned_timeseries.parquet
python code/ingestion/preprocess.py --input data/processed/cleaned_timeseries.parquet --output data/processed/cleaned_timeseries_scrubbed.parquet
```
*Note: The script is hardcoded to use a designated dataset. If this dataset is not available in the verified list, the script will abort with a "Dataset Mismatch Error".*

### 2. Compute Flexibility Metrics
Run the dynamic connectivity analysis using Multilayer Modularity Optimization (MMO).
```bash
python code/analysis/dynamic_connectivity.py \
  --input data/processed/cleaned_timeseries_scrubbed.parquet \
  --window-lengths 30 60 90 \
  --output data/processed/flexibility_scores.parquet
```
*This may take several hours. Monitor memory usage.*

### 3. Statistical Analysis
Run the correlation and permutation tests with Bonferroni correction.
```bash
python code/analysis/statistics.py \
  --flexibility data/processed/flexibility_scores.parquet \
  --behavior data/raw_behavior/2back_scores.csv \
  --output data/results/correlation_results.parquet
```

### 4. Generate Report
Generate the final results summary.
```bash
python code/results/generate_report.py --input data/results/correlation_results.parquet --output docs/report.md
```

## Verification

- Check `data/results/correlation_results.parquet` for `p_value_perm` < 0.0167 (Bonferroni-corrected alpha).
- Check `docs/report.md` for the "Associational" framing statement.
- Verify `psutil` logs in `logs/` for peak RAM < 7 GB.

## Troubleshooting

- **OOM Error**: Reduce `--limit` in ingestion script to a manageable subset of subjects.
- **Runtime > 6h**: Reduce `--window-step` in `dynamic_connectivity.py` or reduce subject count.
- **Data Not Found**: The script is hardcoded to use `ds001734`. If this fails, verify the "Verified datasets" block. If the required HCP data is missing, the project cannot proceed.
