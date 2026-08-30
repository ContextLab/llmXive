# Predicting the Glass Forming Region of Alloy Systems with Machine Learning

## Project Overview
This project predicts the critical cooling rate (CCR) of glass-forming alloys using Random Forest regression on thermodynamic descriptors (mixing enthalpy, atomic size mismatch, electronegativity variance).

## Prerequisites
- Python 3.11
- Dependencies: `pandas`, `scikit-learn`, `numpy`, `requests`, `pyyaml`, `datasets`, `mendeleev`, `scipy`, `pydantic`, `jsonschema`, `pytest`

## Installation
```bash
pip install -r requirements.txt
```

## Data Ingestion
Downloads the `matsci/glass-forming-ability` dataset, filters for ternary alloys, and computes thermodynamic features.
```bash
python projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/ingestion.py
```
**Output**: `data/processed/processed_alloys.csv`

## Model Training
Trains a Random Forest regressor with k-fold cross-validation and evaluates against a null baseline.
```bash
python projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/train.py
```
**Output**: `data/models/random_forest_model.pkl`, `data/models/model_metrics_final.json`

## Analysis
Performs feature importance analysis, collinearity checks, and threshold sensitivity analysis.
```bash
python projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/analyze.py
```
**Output**: `data/processed/feature_importance.json`, `data/processed/sensitivity_report.csv`

## Final Report
A consolidated research report summarizing findings, performance metrics, and caveats is generated after the full pipeline run.
**Output**: `REPORT.md`

**View the Final Report**: [Link to REPORT.md](REPORT.md)

## Caveats
**FINDINGS ARE ASSOCIATIONAL**: This study uses observational data; no causal claims are made. All predictive findings are explicitly framed as associational due to the observational nature of the dataset.

## References
- Dataset: `matsci/glass-forming-ability` (Hugging Face)
- Library: `mendeleev` (Periodic Table Data)