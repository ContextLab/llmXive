# Quickstart Guide

## Prerequisites

- Python 3.11+
- pip

## Installation

1. Clone the repository.
2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```
3. Set environment variables:
 ```bash
 cp.env.example.env
 # Edit.env with your API keys
 ```

## Running the Pipeline

Execute the full pipeline:
```bash
python code/run_pipeline_timing.py
```

This will:
1. Ingest raw data.
2. Compute descriptors.
3. Train models.
4. Generate reports.

## Output Artifacts

- `data/processed/step_final_cleaned.csv`: Cleaned dataset.
- `data/models/best_model.pkl`: Trained model.
- `data/reports/final_report.md`: Final analysis report.
