# Models Module

This module contains the machine learning pipeline for predicting drug-likeness scores from molecular descriptors.

## Components

- `train.py`: Model training (Linear Regression, Random Forest)
- `evaluate.py`: Model evaluation, metrics calculation, and visualization

## Usage

```bash
# Train models
python code/models/train.py

# Evaluate models
python code/models/evaluate.py
```

## Outputs

- `data/processed/model_lr.pkl`: Trained Linear Regression model
- `data/processed/model_rf.pkl`: Trained Random Forest model
- `data/processed/feature_importance.json`: Feature importance rankings
- `data/processed/plot_scatter_*.png`: Predicted vs. experimental plots
- `data/processed/plot_importance.png`: Feature importance bar chart
- `data/processed/metrics_summary.json`: Final metrics summary