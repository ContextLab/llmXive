# Quick Start Guide

## Prerequisites
- Python 3.11+
- pip

## Installation
```bash
pip install -r requirements.txt
```

## Running the Pipeline
1. **Data Ingestion**: Fetch and preprocess experimental data
 ```bash
 python -m src.cli.ingest
 ```
 This will create `data/processed/validated_dataset.parquet`.

2. **Model Training**: Train GPR/RF models with Nested CV
 ```bash
 python -m src.cli.train
 ```
 This will generate model metrics and reports in `results/`.

3. **Interpretation**: Generate partial dependence plots and feature importance
 ```bash
 python -m src.cli.interpret
 ```
 This will save plots to `results/` and feature importance to `results/feature_importance.json`.

## Output Files
- `data/processed/validated_dataset.parquet`: Clean, analysis-ready dataset
- `results/metrics.csv`: Model performance metrics
- `results/partial_dependence_*.png`: Visualization of feature impacts
- `results/feature_importance.json`: Ranked feature importance

## Troubleshooting
- If data ingestion fails, check network connectivity and API keys in environment variables.
- If model training exceeds resource limits, it will automatically fallback to Random Forest.
