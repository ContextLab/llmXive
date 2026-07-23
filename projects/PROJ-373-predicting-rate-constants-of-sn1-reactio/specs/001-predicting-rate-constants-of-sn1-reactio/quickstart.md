# Quickstart Guide: Predicting SN1 Rate Constants

## Project Overview

This project implements a machine learning pipeline to predict rate constants of SN1 reactions from molecular structure using Graph Neural Networks (MPNN).

## Prerequisites

- Python 3.11+
- pip package manager
- 64-bit operating system

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd PROJ-373-predicting-rate-constants-of-sn1-reactio
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Data Preparation

The pipeline automatically downloads and processes SN1 kinetic data from public sources.

1. Run the ingestion stage:
```bash
python code/main.py --stage ingest
```

2. Clean and filter the dataset:
```bash
python code/data/clean.py --input data/raw/sn1_raw.csv --output data/processed/cleaned_sn1.csv
```

3. Compute molecular descriptors:
```bash
python code/data/descriptors.py --input data/processed/cleaned_sn1.csv --output data/processed/descriptors.csv
```

4. Split the dataset:
```bash
python code/data/split.py --input data/processed/descriptors.csv --output data/processed/
```

## Model Training

Train the MPNN model with hyperparameter optimization:

```bash
python code/models/train.py --config config.yaml --data data/processed/train.csv --output artifacts/
```

This will:
- Run random search over 50 hyperparameter configurations
- Train models on the training set
- Evaluate on the validation set
- Save the best model to `artifacts/best_model.pt`
- Log results to `artifacts/metrics.json` and `artifacts/hyperparameter_search.csv`

## Evaluation

Evaluate the trained model:

```bash
python code/models/evaluate.py --model artifacts/best_model.pt --data data/processed/test.csv
```

This will:
- Calculate R² and MAE metrics
- Compare against linear regression baseline
- Save results to `artifacts/evaluation_results.csv`

## Interpretability Analysis

Generate feature importance and sensitivity analysis:

```bash
python code/analysis/interpret.py --model artifacts/best_model.pt --data data/processed/test.csv --output artifacts/
```

This will:
- Compute SHAP values for feature importance
- Generate `artifacts/feature_importance.png`
- Perform perturbation studies
- Save `artifacts/perturbation_results.csv`

## Full Pipeline Execution

Run the complete pipeline from data ingestion to analysis:

```bash
python code/main.py --stage all
```

## Expected Artifacts

After successful execution, the following artifacts should be present:

### Data Artifacts
- `data/raw/sn1_raw.csv` - Raw ingested data
- `data/processed/cleaned_sn1.csv` - Cleaned and filtered dataset
- `data/processed/descriptors.csv` - Dataset with computed descriptors
- `data/processed/train.csv`, `data/processed/val.csv`, `data/processed/test.csv` - Split datasets
- `data/processed/exclusion_report.csv` - Log of excluded samples

### Model Artifacts
- `artifacts/best_model.pt` - Trained MPNN model weights
- `artifacts/metrics.json` - Model performance metrics
- `artifacts/hyperparameter_search.csv` - Hyperparameter search results

### Analysis Artifacts
- `artifacts/feature_importance.png` - SHAP summary plot
- `artifacts/sensitivity_report.csv` - Sensitivity analysis results
- `artifacts/perturbation_results.csv` - Perturbation study results
- `artifacts/collinearity_report.csv` - VIF and correlation analysis

## Troubleshooting

### Common Issues

1. **Missing dependencies**: Ensure all packages in `requirements.txt` are installed.
2. **Data download failures**: Check internet connection and firewall settings.
3. **Memory errors**: Reduce dataset size or batch size in `config.yaml`.
4. **CUDA errors**: The pipeline is CPU-only; ensure no GPU-specific code is invoked.

### Validation

Validate the quickstart guide against actual execution:

```bash
python code/validation/validate_quickstart.py --quickstart specs/001-predict-sn1-rate-constants/quickstart.md --evidence artifacts/integration_test_report.md
```

## Next Steps

- Review the model performance metrics
- Analyze feature importance from SHAP values
- Explore sensitivity to descriptor thresholds
- Extend the dataset with additional SN1 reaction data

## References

- Original spec: `specs/001-predict-sn1-rate-constants/plan.md`
- Data schema: `specs/001-predict-sn1-rate-constants/contracts/dataset.schema.yaml`
- Model output schema: `specs/001-predict-sn1-rate-constants/contracts/model_output.schema.yaml`