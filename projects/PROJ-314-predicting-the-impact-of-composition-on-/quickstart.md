# Quickstart Guide: Predicting the Impact of Composition on the Weibull Modulus of Ceramics

## 1. Prerequisites & Install

Ensure you have Python 3.11+ installed.

```bash
# Create virtual environment
python -m venv.venv
source.venv/bin/activate # On Windows:.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## 2. Data Fetch

The pipeline fetches data from three sources. Ensure network access is available.

```bash
# Run ingestion pipeline (fetches MP, NIST, ArXiv, and Curated data)
python code/ingestion.py
```

This step produces:
- `data/raw/materials_project_raw.json`
- `data/raw/nist_raw.json`
- `data/raw/arxiv_raw.json`
- `data/raw/curated_literature_raw.json`
- `data/processed/step4_final.csv`
- `data/reports/data_availability_report.json` (if data < 30 rows)

## 3. Running the Pipeline

Execute the full pipeline with timeout enforcement.

```bash
# Run the full pipeline with timing and timeout enforcement
python code/run_pipeline_timing.py
```

This command:
1. Runs data ingestion
2. Trains models (with 6-hour timeout)
3. Runs permutation tests (with 6-hour timeout)
4. Generates SHAP analysis and reports

## 4. Verifying Outputs

Check that all required artifacts are generated:

```bash
# Verify data files
ls data/processed/step4_final.csv
ls data/reports/data_availability_report.json
ls data/results/baseline_metrics.json
ls data/results/model_metrics.json
ls data/results/feature_ranking_table.csv
ls data/results/leakage_report.json
ls data/results/stability_metrics.json
ls data/artifacts/shap_summary.png
```

If any file is missing, check `logs/` for error messages.

## Troubleshooting

- **Timeout Errors**: If a step times out, check `logs/modeling.log` for details. The default timeout is 6 hours.
- **Data Fetch Failures**: Ensure network access and verify URLs in `code/ingestion.py`.
- **Missing Dependencies**: Re-run `pip install -r requirements.txt`.
- **Memory Issues**: Check `logs/memory_monitor.log` for memory usage details.