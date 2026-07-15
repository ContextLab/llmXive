# Quickstart Guide for PROJ-475

This guide outlines the steps to run the full pipeline end-to-end.

## Prerequisites

- Python 3.11+
- `requirements.txt` installed: `pip install -r requirements.txt`

## Execution Order

The pipeline consists of several stages. Run them in the following order:

1. **Setup & Validation** (Optional but recommended)
 ```bash
 python code/scripts/validate_quickstart.py
 ```

2. **Data Ingestion** (T010-T012)
 Fetches or generates raw data.
 ```bash
 python code/scripts/generate_mock_data.py
 # Note: This script generates the raw JSON files required for downstream steps.
 # In a real scenario, this would call code/data/ingestion.py with verified URLs.
 ```

3. **Data Validation** (T013-T014)
 Merges and validates data integrity.
 ```bash
 python code/data/validation.py
 ```

4. **Preprocessing** (T015-T016)
 Handles missing data imputation and exclusion.
 **Produces:** `data/processed/filtered.csv`
 ```bash
 python code/scripts/run_preprocessing.py
 ```

5. **Feature Engineering & Training** (T019-T026)
 Calculates metrics, VIF, and trains models.
 ```bash
 python code/models/training.py
 ```

6. **Evaluation** (T029-T033)
 Permutation tests, sensitivity analysis, and statistics.
 ```bash
 python code/models/evaluation.py
 ```

7. **Manifest Update** (T041)
 Updates the manifest with new artifacts.
 ```bash
 python code/scripts/update_manifest.py
 ```

## Full Pipeline Run

To run the entire sequence automatically (for CI or quick validation):

```bash
python code/main.py
```

## Verification

Check that the following files exist after a successful run:
- `data/raw/genomic_vcf.json`
- `data/raw/env_data.json`
- `data/raw/compound_data.json`
- `data/processed/merged.csv`
- `data/processed/filtered.csv`
- `state/PROJ-475-predicting-plant-defense-compound-produc.yaml`