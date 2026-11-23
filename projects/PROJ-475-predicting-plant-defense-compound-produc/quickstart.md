# Quickstart Guide for Plant Defense Compound Prediction Pipeline

## Prerequisites

- Python 3.11+
- pip
- Git

## Setup

1. Clone the repository:
 ```bash
 git clone <repo-url>
 cd PROJ-475-predicting-plant-defense-compound-produc
 ```

2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

3. Configure the pipeline (optional):
 ```bash
 python code/setup_project.py
 ```

## Run the Pipeline

Execute the full pipeline from ingestion to evaluation:

```bash
python code/main.py
```

This will:
1. Ingest genomic, environmental, and compound data
2. Validate and merge datasets
3. Perform feature engineering
4. Train models
5. Run evaluation and sensitivity analysis

## Generate Mock Data (for CI/Testing)

If verified URLs are not configured, the pipeline will automatically use mock data.
To explicitly generate mock data:

```bash
python code/scripts/generate_mock_data.py
```

## Validate Quickstart

Run the validation script to ensure all artifacts are produced:

```bash
python code/scripts/validate_quickstart.py
```

## Outputs

The pipeline produces the following artifacts:

- `data/raw/genomic_vcf.json` - Genomic variant data
- `data/raw/env_data.json` - Environmental metadata
- `data/raw/compound_data.json` - Defense compound profiles
- `data/processed/filtered.csv` - Cleaned dataset
- `data/processed/features_vif.csv` - Features with VIF
- `models/model.pkl` - Trained model
- `results/permutation_results.json` - Permutation test results
- `results/sensitivity_analysis.json` - Sensitivity analysis results

## Troubleshooting

- **Disk Space Error**: Ensure you have at least 1.5x the estimated data size available.
- **Missing URLs**: If verified URLs are not configured, the pipeline will use mock data.
- **Network Errors**: Check your internet connection and firewall settings.

## Next Steps

- Review `README.md` for detailed documentation
- Check `docs/api.md` for API reference
- Run `python code/tests/test_ingestion.py` for unit tests