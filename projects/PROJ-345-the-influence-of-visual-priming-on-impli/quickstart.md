# Quickstart Guide

## Prerequisites
- Python 3.11+
- pip
- git

## Step 1: Clone and Setup
```bash
git clone <repo-url>
cd PROJ-345-the-influence-of-visual-priming-on-impli
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Step 2: Initialize Project Structure
```bash
python code/run_setup.py
python code/run_state_init.py
```

## Step 3: Run the Pipeline
Execute the full pipeline to ingest data, preprocess, model, and generate reports:
```bash
python code/main.py
```

## Step 4: Verify Outputs
Check the following artifacts after successful execution:
- `data/processed/linked_trials.csv`
- `data/processed/stimulus_metadata.csv`
- `state/model_convergence_metrics.json`
- `reports/output_report.pdf`

## Troubleshooting
- **Missing Data**: Ensure `data/raw` contains valid IAT datasets or run `code/data/ingest.py` manually.
- **Model Convergence**: Check `state/model_convergence_metrics.json` for convergence rates.
- **Linkage Failures**: Verify `data/processed/linked_trials.csv` for missing `stimulus_id` values.
