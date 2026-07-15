# Quickstart Guide: Plant Defense Compound Prediction Pipeline

## Prerequisites
- Python 3.11+
- pip
- At least 5GB free disk space

## Setup
```bash
pip install -r requirements.txt
```

## Run the Pipeline
Execute the full pipeline from ingestion to evaluation:

```bash
# Step 1: Generate mock data (for testing/CI)
python code/scripts/generate_mock_data.py

# Step 2: Run ingestion pipeline
python code/data/ingestion.py

# Step 3: Run validation pipeline
python code/data/validation.py

# Step 4: Run preprocessing (includes VIF analysis for T020)
python code/data/preprocessing.py

# Step 5: Run model training
python code/models/training.py

# Step 6: Run evaluation
python code/models/evaluation.py

# Step 7: Update manifest
python code/scripts/update_manifest.py
```

## Verify Outputs
Check that the following files exist:
- `data/raw/genomic_vcf.json`
- `data/raw/env_data.json`
- `data/raw/compound_data.json`
- `data/processed/filtered.csv`
- `data/processed/features_vif.csv`

## Run Tests
```bash
pytest code/tests/
```
