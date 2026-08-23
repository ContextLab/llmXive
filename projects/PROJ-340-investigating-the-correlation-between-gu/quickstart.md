# Quick Start Guide: Gut Microbiome & Sleep Architecture Pipeline

This guide provides the commands to execute the full analysis pipeline.

## Environment Setup

1. **Install Dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

2. **Configure Data Sources**:
 Edit `data/config/real_data_sources.yaml` to point to your real dataset.
 ```yaml
 # data/config/real_data_sources.yaml
 sources:
 - name: "Primary_Cohort"
 type: "csv"
 url: ""
 checksum: "sha256:..."
 ```
 *Note: The pipeline will **fail** if this file is missing or the URL is invalid. Do not use synthetic data for final results.*

## Execution Steps

### Step 1: Data Ingestion & Validation
Load the data, validate required variables, and detect outliers.

**Option A: Real Data (Production)**
```bash
python code/ingest.py
```
*Output*: `data/processed/filtered_data.parquet`, `data/results/outlier_report.json`

**Option B: Synthetic Data (Testing Only)**
```bash
python code/ingest.py --mode synthetic --output data/raw/synthetic_data.csv
python code/main.py --input data/raw/synthetic_data.csv --output data/results/
```

### Step 2: Main Analysis Pipeline
Execute the full correlation analysis, diagnostics, and report generation.

```bash
python code/main.py
```
*This command performs:*
1. Ingestion (if input not provided via CLI)
2. Method Selection (ZINB vs Pearson/Spearman)
3. Correlation Analysis with FDR correction
4. Sensitivity & Power Analysis
5. Report Generation

*Outputs*:
- `data/results/correlation_matrix.json`
- `data/results/sensitivity_analysis.csv`
- `data/results/power_analysis_report.json`
- `data/results/report_draft.md`
- `data/results/timing_evidence.json`

### Step 3: Verification
Validate the integrity of the run.

```bash
python scripts/verify_integrity.py
python scripts/final_validation.py
```

## Troubleshooting

- **Error: "No required variables loaded"**
 - Check `data/config/required_variables.yaml`. Ensure your input CSV columns match the required predictors and outcomes exactly.

- **Error: "Real data fetch failed"**
 - Verify `data/config/real_data_sources.yaml`. The pipeline does not support synthetic fallbacks in production.

- **Error: "Pipeline execution exceeded 6-hour limit"**
 - This is a hard timeout. If the dataset is too large, consider reducing the sample size or optimizing the correlation method selection.

## Output Artifacts

| Artifact | Description |
|----------|-------------|
| `data/processed/filtered_data.parquet` | Cleaned dataset with outliers removed |
| `data/results/outlier_report.json` | Details of excluded data points |
| `data/results/correlation_matrix.json` | Final correlation results with p-values |
| `data/results/sensitivity_analysis.csv` | Stability of results across p-value thresholds |
| `data/results/power_analysis_report.json` | Statistical power assessment |
| `data/results/report_draft.md` | Human-readable interpretation |
| `data/results/timing_evidence.json` | Execution timing metrics |
