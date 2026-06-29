# Models Module

This directory contains code for training and evaluating machine learning models
for glass-forming region prediction.

## Purpose

Train Random Forest and Gradient Boosting classifiers with 5-fold cross-validation
and report performance metrics as specified in User Story 2.

## Key Files

- `train.py`: Train classification models with cross-validation
- `evaluate.py`: Evaluate models on held-out test sets
- `importance.py`: Compute permutation importance and SHAP values

## Output Files

- `models/trained_models.pkl`: Serialized trained models
- `code/models/hyperparameters.yaml`: Training hyperparameters
- `results/performance_metrics.json`: Model performance metrics
- `results/permutation_importance.csv`: Feature importance scores
- `results/shap_plots/shap_summary_<model>.png`: SHAP visualization plots

## References

- FR-004: Report ROC-AUC, precision, recall metrics
- FR-007: Respect RAM limits during training
- Constitution VII: Document all hyperparameters and validation limitations
