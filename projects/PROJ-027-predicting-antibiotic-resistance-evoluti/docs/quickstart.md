# Quick Start Guide

Get up and running with the antibiotic resistance prediction pipeline in under 15 minutes.

## Step 1: Environment Setup

```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
pip install -r code/requirements.txt
```

## Step 2: Create Directory Structure

```bash
python code/setup_directories.py
```

## Step 3: Run the Full Pipeline

The canonical entry point for the pipeline is **`code/main.py`**.

```bash
# Ingest data, run contract validation, train models, validate, and version
python code/main.py --stage full --n-isolates 1000 --bio_project PRJNA528852 --antibiotic ciprofloxacin
```

### Running Individual Stages

```bash
# Only ingestion
python code/main.py --stage ingest --n-isolates 1000 --bio_project PRJNA528852

# Only training (requires previous ingestion)
python code/main.py --stage train --antibiotic ciprofloxacin

# Validation only
python code/main.py --stage validate --antibiotic ciprofloxacin --permutations 1000

# Visualization
python code/main.py --stage viz --antibiotic ciprofloxacin

# Versioning (hash artifacts)
python code/main.py --stage hash
```

## Step 4: Verify Outputs

```bash
ls -la data/processed/feature_matrix.csv
ls -la data/models/
ls -la data/processed/permutation_results.json
ls -la data/processed/sensitivity_sweep.csv
ls -la figures/
```

## Troubleshooting

- **OOM Error**: Reduce `--n-isolates` to 500.
- **NCBI Rate Limiting**: Add delays between requests or reduce `MAX_ISOLATES`.
- **Phylogeny Error**: Ensure `dendropy` and `statsmodels` are installed.