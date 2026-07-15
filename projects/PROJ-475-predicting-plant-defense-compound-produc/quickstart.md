# Quickstart Guide for PROJ-475

This guide outlines the steps to run the full pipeline for predicting plant defense compound production.

## Prerequisites
- Python 3.11+
- Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Running the Pipeline

The full pipeline is orchestrated by `code/main.py`. It performs:
1. Data Ingestion (fetch or generate mock data)
2. Data Validation (merge, listwise deletion)
3. Preprocessing (imputation, aggregation, VIF)
4. Model Training (LASSO/Ridge)
5. Evaluation (Permutation test, sensitivity analysis)

### Step 1: Run the Full Pipeline

```bash
python code/main.py
```

This command will:
- Generate necessary directories (`data/raw`, `data/processed`, `figures`, `state`)
- Execute ingestion (T010-T012)
- Execute validation (T013-T014)
- Execute preprocessing (T015-T016, T019-T020, T026)
- Execute training (T022-T025)
- Execute evaluation (T029-T033)
- Update state file (T034)

### Step 2: Verify Outputs

Ensure the following files are generated:
- `data/raw/genomic_vcf.json`
- `data/raw/env_data.json`
- `data/raw/compound_data.json`
- `data/processed/merged.csv`
- `data/processed/filtered.csv`
- `data/processed/features_vif.csv`
- `state/PROJ-475-predicting-plant-defense-compound-produc.yaml`

## Testing

Run unit tests:
```bash
python -m pytest code/tests/ -v
```

## Configuration

Edit `code/config.yaml` to modify paths, seeds, and hyperparameters.
Ensure `verified_urls` are set correctly if fetching real data.

## Troubleshooting

- **Disk Space**: If you encounter `DiskSpaceError`, free up space or adjust `estimated_size` in `code/utils/io.py`.
- **Missing Data**: If ingestion fails, check `verified_urls` in config or ensure `mock_generator` is working.
- **VIF Errors**: Ensure `statsmodels` is installed (`pip install statsmodels`).
