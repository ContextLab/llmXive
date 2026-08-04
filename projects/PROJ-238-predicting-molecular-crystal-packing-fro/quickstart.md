# Quickstart Guide: Predicting Molecular Crystal Packing

This guide provides a step-by-step walkthrough to run the full pipeline for
predicting molecular crystal packing from structural descriptors using the
Crystallography Open Database (COD).

## Prerequisites

- Python 3.11+
- pip
- Git

## 1. Setup Environment

Clone the repository and install dependencies:

```bash
git clone <repository-url>
cd PROJ-238-predicting-molecular-crystal-packing-fro
pip install -r requirements.txt
```

Ensure the following environment variables are set (optional, defaults provided):

```bash
export COD_URL=""
export RANDOM_SEED=42
export DATA_PATH="./data"
```

## 2. Ingest Data and Compute Descriptors

Download CIFs from COD, parse unit cell parameters, add missing hydrogens,
and compute molecular descriptors.

```bash
python code/01_ingest_and_descriptors.py
```

**Outputs:**
- `data/descriptors/raw_descriptors.csv`: Raw descriptor values.
- `data/processed/hydrogen_addition.log`: Log of hydrogen additions.

## 3. Impute and Filter Data

Handle missing values and filter physically impossible packing coefficients.

```bash
python code/02_impute_and_filter.py
```

**Outputs:**
- `data/processed/train.csv`, `val.csv`, `test.csv`: Stratified splits.
- `data/processed/filter_log.txt`: Exclusion log.

## 4. Train Models

Train Random Forest, Gradient Boosting, and Mean Predictor baseline models.

```bash
python code/02_train_models.py
```

**Outputs:**
- `results/models/`: Saved model artifacts.
- `results/metrics.json`: Initial performance metrics.

## 5. Evaluate and Report

Perform statistical evaluation, feature importance analysis, and sensitivity testing.

```bash
python code/03_evaluate_and_report.py
```

**Outputs:**
- `results/feature_importance.png`: Visualization of top features.
- `results/sensitivity_report.md`: LOFO analysis results.
- `results/interaction_classification.md`: Interaction type accuracy.

## 6. Verify Results

Validate the integrity of the output artifacts.

```bash
python code/verify_metrics.py
```

## Schema Reference

The dataset schema is defined in `contracts/dataset.schema.yaml`.
It specifies the required columns, data types, and metadata for all
processed datasets (raw, imputed, and split).

## Troubleshooting

- **Missing COD URL**: Ensure `COD_URL` is set or update `code/config.py`.
- **RDKit Errors**: Verify RDKit installation and version compatibility.
- **Memory Issues**: For large datasets, ensure sufficient RAM or use streaming.

## Next Steps

- Review `results/metrics.json` for model performance.
- Analyze `results/feature_importance.png` for descriptor insights.
- Read `results/sensitivity_report.md` for model robustness details.
