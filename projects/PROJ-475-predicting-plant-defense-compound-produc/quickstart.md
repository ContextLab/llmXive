# Quickstart Guide for Plant Defense Compound Prediction Pipeline

This guide provides the commands to run the full pipeline end-to-end.

## Prerequisites

- Python 3.11+
- `pip install -r requirements.txt`

## Running the Pipeline

The full pipeline is orchestrated by `code/main.py`. It executes:
1. Ingestion (T010-T012)
2. Validation (T013-T014)
3. Preprocessing (T015-T016, T019-T020, T026)
4. Training (T022-T025)
5. Evaluation (T029-T033)
6. Manifest and state update

```bash
cd code
python main.py
```

## Expected Outputs

After successful execution, the following files should exist:

- `data/raw/genomic_vcf.json`
- `data/raw/env_data.json`
- `data/raw/compound_data.json`
- `data/processed/filtered.csv`
- `data/processed/features_vif.csv`
- `data/processed/aggregated.csv`
- `state/PROJ-475-predicting-plant-defense-compound-produc.yaml`
- `data/manifest.yaml`

## Verification

To verify the pipeline ran correctly:

```bash
python scripts/validate_quickstart.py
```

This script checks for the presence of all expected artifacts and their checksums.