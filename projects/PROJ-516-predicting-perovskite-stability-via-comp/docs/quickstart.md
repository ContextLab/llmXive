# Quickstart

## Project overview
A minimal, reproducible workflow for predicting perovskite thermal stability from composition alone. The pipeline downloads experimental data, generates compositional fingerprints, trains baseline regression models, and evaluates performance on an external literature set.

## Installation
```bash
pip install -r code/requirements.txt
```

## Running the pipeline
```bash
# Step 1: Data ingestion (fetches NREL and Materials Project data)
python code/data_ingestion.py

# Step 2: Compute compositional descriptors
python code/feature_engineering.py

# Step 3: Train baseline models with cross‑validation
python code/model_training.py

# Step 4: Perform validation and generate reports
python code/validation.py
```

These commands are sufficient to generate all intermediate artifacts under `data/processed/` and the final validation report in `docs/validation_report.md`.