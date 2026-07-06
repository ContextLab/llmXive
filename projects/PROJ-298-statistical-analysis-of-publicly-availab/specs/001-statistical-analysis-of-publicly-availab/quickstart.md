# Quickstart: Statistical Analysis of Publicly Available Stack Overflow Question Tags

## Prerequisites

- Python 3.11+
- Git
- Access to a GitHub Actions runner (for CI) or local environment with ≥7 GB RAM.

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-org/your-repo.git
   cd projects/PROJ-298-statistical-analysis-of-publicly-availab
   ```

2. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```

3. **Verify environment**:
   ```bash
   python -c "import pandas, scipy, statsmodels; print('OK')"
   ```

## Running the Pipeline

### Option A: Full Pipeline (Requires Data)
*Note: If `data/raw/posts_tags.csv` is missing or the `archive.org` fetch fails, the pipeline will generate synthetic data for testing.*

```bash
# Download data (if available) or generate synthetic
python code/download.py

# Preprocess
python code/preprocess.py

# Run Analysis
python code/analysis/trend_analysis.py
python code/analysis/decomposition.py
python code/analysis/clustering.py

# External Validation
python code/validation.py

# Generate Reports & Hashes
python code/report.py
python code/hasher.py
```

### Option B: Unit Tests
```bash
pytest tests/unit/ -v
```

### Option C: Jupyter Notebook
```bash
jupyter notebook code/notebooks/01_full_pipeline.ipynb
```

## Expected Outputs

- `artifacts/trend_results.json`: Growth/Decline classifications (including "Insufficient Power").
- `artifacts/decomposition_results.json`: ADF, Ljung-Box, and method selection results.
- `artifacts/clusters.json`: Technology clusters with t-test validation.
- `artifacts/validation_status.json`: External correlation results or "Absent" status.
- `artifacts/reports/`: PDF/PNG visualizations with mandatory limitation headers.
- `state/projects/PROJ-298-statistical-analysis-of-publicly-availab.yaml`: Updated with artifact hashes.

## Troubleshooting

- **Missing Data**: If `PostsTags` is unavailable, the pipeline uses synthetic data. Check logs for `WARNING: Using synthetic data`.
- **Memory Error**: Reduce the `TOP_N_TAGS` constant in `code/preprocess.py` (default 50).
- **Rate Limits**: If GitHub API fails, wait 60 seconds and retry.
- **URL Fetch Failure**: If the `archive.org` URL is unreachable, the system logs the error and proceeds with synthetic data for CI only.