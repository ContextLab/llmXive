# Quick Start Guide: Gut Microbiome & Sleep Architecture Pipeline

This guide walks you through setting up and running the analysis pipeline for PROJ-340.

## 1. Environment Setup

Ensure you have Python 3.11+ installed.

**Option A: Real Data (Production)**
```bash
# Create virtual environment
python -m venv.venv
source.venv/bin/activate # On Windows:.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## 2. Data Configuration

The pipeline is configured to run **only on real data** by default. You must specify a real data source.

1. Open `data/config/real_data_sources.yaml`.
2. Update the `source_url` to a valid, programmatically accessible URL or local path.
3. Ensure the `expected_checksum` matches the file (optional but recommended).

Example:
```yaml
real_data:
 source_url: ""
 expected_checksum: "sha256:a1b2c3..."
 source_type: "public_dataset"
```

## 3. Running the Pipeline

### Option A: Real Data Execution (Production)
This mode will fetch data from the configured source, validate it, and run the full analysis.
```bash
# Step 1: Fetch and validate data (ingest.py handles this internally if --input is not provided)
# Step 2: Run the main pipeline
python code/main.py --output data/results/
```
*Note*: If `--input` is not provided, `main.py` will attempt to fetch data from `real_data_sources.yaml`. If the fetch fails, the pipeline halts.

### Option B: Synthetic Data Execution (Testing)
Use this for local validation of the pipeline logic without real data.
```bash
# Generate synthetic test data
python code/generate_synthetic_data.py --output data/raw/synthetic_test_data.csv

# Run the pipeline on synthetic data
python code/main.py --input data/raw/synthetic_test_data.csv --output data/results/
```
*This command performs:*
1. Ingestion (if input not provided via CLI)
2. Method Selection (ZINB vs Pearson/Spearman)
3. Correlation Analysis with FDR correction
4. Sensitivity & Power Analysis
5. Report Generation

## 4. Expected Outputs

After a successful run, check the `data/results/` directory for:
- `correlation_results.csv`: Primary statistical outputs.
- `power_analysis_report.json`: Power metrics.
- `sensitivity_analysis.csv`: Threshold stability.
- `report_draft.md`: Final report draft.
- `causal_scan_report.json`: Causal language verification.

## 5. Verification

Verify the integrity of all generated artifacts:
```bash
python scripts/verify_integrity.py
```

## 6. Troubleshooting

- **Error: "No required variables loaded"**: Check `data/config/required_variables.yaml` to ensure your input data contains the expected columns.
- **Error: "RealDataFetchError"**: The configured data source in `real_data_sources.yaml` is unreachable or invalid.
- **Error: "Causal language detected"**: The report generation step found prohibited terms. Review `data/results/causal_scan_report.json` for details.
