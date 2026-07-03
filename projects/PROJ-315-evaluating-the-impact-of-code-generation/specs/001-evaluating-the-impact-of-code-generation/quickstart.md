# Quickstart: Evaluating the Impact of Code Generation on Code Review Quality

## Prerequisites

- Python 3.11+
- Git
- GitHub Actions account (for CI testing)

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-org/your-repo.git
   cd your-repo
   ```

2. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```

3. **Set up virtual environment** (optional but recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

## Running the Pipeline

### Step 1: Fetch Dataset
```bash
python code/data/fetch.py --dataset loubnabnl/prs-v2-sample
```
- Downloads raw parquet to `data/raw/`.
- Computes checksum and records in state file.

### Step 2: Preprocess Data
```bash
python code/data/preprocess.py
```
- Filters missing fields.
- Computes review and complexity metrics.
- Classifies PRs using keyword heuristics.
- Outputs to `data/processed/`.

### Step 3: Run Analysis
```bash
python code/analysis/stats.py
```
- Performs Mann-Whitney U tests.
- Applies multiple comparison correction.
- Runs linear regression with VIF diagnostics.
- Outputs statistics to `data/processed/stats.json`.

### Step 4: Generate Visualizations
```bash
python code/analysis/viz.py
```
- Creates boxplots, histograms, and sensitivity analysis plots.
- Saves to `docs/reports/figures/`.

### Step 5: Generate Final Report
```bash
python code/report/generate.py
```
- Produces PDF/HTML report with all findings.
- Saves to `docs/reports/final_report.html`.

## Testing

### Unit Tests
```bash
pytest code/tests/test_classify.py
pytest code/tests/test_stats.py
```

### Integration Tests
```bash
pytest code/tests/test_pipeline.py
```

## Troubleshooting

- **Error: Data Completeness <95%**: Check raw data source; try fallback dataset.
- **Error: Power Insufficiency**: Ensure ≥500 PRs per group; if not, halt and report.
- **Memory Error**: Reduce dataset size or process in chunks.
- **Collinearity Warning**: Check VIF values; exclude highly collinear predictors.

## Reproducibility

- Random seeds pinned in `code/` scripts.
- Dataset fetched from canonical HuggingFace URL.
- All dependencies pinned in `requirements.txt`.
