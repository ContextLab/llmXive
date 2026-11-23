# Quickstart Guide

## Prerequisites
- Python 3.11+
- GitHub API token (set as `GITHUB_TOKEN` environment variable)

## Installation

1. **Clone and Setup**:
 ```bash
 git clone <repo-url>
 cd projects/PROJ-430-the-impact-of-asynchronous-communication
 python -m venv venv
 source venv/bin/activate
 pip install -r requirements.txt
 ```

2. **Linting & Formatting**:
 Ensure `pyproject.toml` and `.pre-commit-config.yaml` are present.
 ```bash
 pre-commit install
 ```

3. **Environment Variables**:
 Create a `.env` file in the project root:
 ```
 GITHUB_TOKEN=your_token_here
 ```

## Running the Pipeline

### Step 1: Data Ingestion
Fetch data for a small sample (e.g., 5 projects) to verify connectivity and logic.
```bash
python code/data_ingestion.py --sample-size 5 --output data/raw/sample_events.json
```

### Step 2: Metric Derivation (Pair‑Level)
Calculate temporal metrics per pair.
```bash
python code/metrics.py --input data/raw/sample_events.json --output data/derived/pair_metrics.parquet
```

### Step 3: Project‑Level Aggregation (T015)
Aggregate pair‑level metrics to project‑level statistics.
```bash
python code/aggregate_project_metrics.py
```

### Step 4: Sentiment Analysis (Pair‑Level)
Compute cohesion proxy per pair.
```bash
python code/sentiment.py --input data/raw/sample_events.json --output data/derived/pair_sentiment.parquet
```

### Step 5: Statistical Analysis
Run HLM and OLS.
```bash
python code/analysis.py --metrics data/derived/pair_metrics.parquet --sentiment data/derived/pair_sentiment.parquet --output data/derived/statistical_results.json
```

### Step 6: Validation (Manual Ground Truth)
If manual ground truth data is available:
```bash
python code/validation.py --vader data/derived/pair_sentiment.parquet --manual data/validation/manual_ground_truth.csv --output data/validation/validity_report.json
```
*If manual data is missing, the script will run in "Synthetic Mode" and flag the results.*

## Expected Outputs
- `data/derived/pair_metrics.parquet`: Pair‑level temporal metrics.
- `data/derived/project_metrics.csv`: Project‑level aggregated metrics (produced by T015).
- `data/derived/pair_sentiment.parquet`: Pair‑level sentiment scores.
- `data/derived/statistical_results.json`: HLM and OLS results.
- `data/derived/fdr_corrected_results.json`: FDR‑corrected stratified results.
- `data/logs/vif_halt_warning.log`: (If VIF > 5).
- `plots/delay_cohesion_scatter.png`: Visualization of the relationship.