# Quickstart Guide

## Prerequisites
- Python 3.9+
- pip
- HuggingFace token (optional, for rate limits)

## Setup
1. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```
2. Set HF_TOKEN (optional):
 ```bash
 export HF_TOKEN=your_token_here
 ```

## Running the Pipeline
Execute the full pipeline:
```bash
python code/run_pipeline.py
```

This will:
1. Ingest FDA-approved drugs data
2. Calculate molecular descriptors
3. Perform correlation analysis
4. Generate reports and visualizations

## Outputs
- `data/processed/structural_subset.csv`: Processed structural data
- `data/gate_status.json`: Data availability gate status
- `data/processed/analysis_results.json`: Analysis results
- `results_report.md`: Final report
- `data/checksums.txt`: Data integrity checksums