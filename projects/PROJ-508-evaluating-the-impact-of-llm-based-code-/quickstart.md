# Quickstart Guide

## Prerequisites
- Python 3.11+
- pip

## Setup
```bash
pip install -r requirements.txt
```

## Run the Pipeline
Execute the following commands in order:

1. **Ingestion** - Fetch and process GitHub data
```bash
python code/ingest.py
```

2. **Analysis** - Run statistical models
```bash
python code/analyze.py
```

3. **Derive Analysis Results** - Extract and format model results
```bash
python code/derive_analysis_results.py
```

4. **Sensitivity Analysis** - Generate sensitivity analysis JSON
```bash
python code/derive_sensitivity_analysis.py
```

5. **Report Generation** - Create visualizations and final report
```bash
python code/report.py
```

## Expected Outputs
- `data/derived/master_dataset.csv`
- `data/derived/analysis_results.json`
- `data/derived/sensitivity_analysis.json`
- `data/derived/stratified_results.json`
- `docs/output/final_report.pdf` (if reportlab installed) or `.md`
