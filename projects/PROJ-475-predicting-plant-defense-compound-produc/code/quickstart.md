# Quickstart Guide: Predicting Plant Defense Compound Production

This guide validates the end-to-end pipeline for predicting plant defense compound production from genomic and environmental data.

## Prerequisites

- Python 3.11+
- Required packages (install via `pip install -r requirements.txt`)

## Setup

1. Clone the repository
2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```
3. Ensure you are in the project root directory.

## Running the Pipeline

The pipeline can be run in two ways:

### Option 1: Run the Full Pipeline

```bash
python code/main.py
```

This will:
1. Ingest genomic, environmental, and compound data
2. Validate data integrity
3. Preprocess and engineer features
4. Train a regularized regression model
5. Evaluate model performance and significance

### Option 2: Run Individual Steps

Each step can be run independently:

```bash
# Data Ingestion
python -m code.data.ingestion

# Data Validation
python -m code.data.validation

# Preprocessing
python -m code.data.preprocessing

# Model Training
python -m code.models.training

# Model Evaluation
python -m code.models.evaluation
```

## Validation

To validate that the quickstart guide works correctly:

```bash
python code/scripts/validate_quickstart.py
```

This script will:
1. Generate mock data (if real data is not available)
2. Run the full pipeline
3. Verify all output files are created
4. Validate the manifest and state files

## Expected Outputs

After running the pipeline, the following files should be generated:

- `data/raw/genomic_vcf.json` - Genomic data
- `data/raw/env_data.json` - Environmental data
- `data/raw/compound_data.json` - Compound data
- `data/processed/filtered.csv` - Filtered dataset
- `data/processed/features_vif.csv` - Features with VIF
- `data/processed/features_normalized.csv` - Normalized features
- `models/model.pkl` - Trained model
- `models/predictors.json` - Top predictors
- `results/permutation_results.json` - Permutation test results
- `results/sensitivity_analysis.json` - Sensitivity analysis results
- `data/manifest.yaml` - Artifact manifest with checksums
- `state/PROJ-475-predicting-plant-defense-compound-produc.yaml` - Pipeline state

## Troubleshooting

- If you encounter disk space errors, ensure you have at least 1.5x the estimated data size available.
- If data validation fails, check that all required columns are present in the input files.
- For model training issues, verify that the number of samples meets the CV strategy requirements.

## Next Steps

- Review the `README.md` for detailed project documentation
- Check `docs/api.md` for API reference
- Run the test suite: `pytest code/tests/`
