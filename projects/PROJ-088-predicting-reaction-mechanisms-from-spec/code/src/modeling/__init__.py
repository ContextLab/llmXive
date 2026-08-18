"""
Modeling module for training and evaluating machine learning models.

This package handles:
- Training Random Forest and XGBoost classifiers
- Stratified cross-validation
- Metric calculation (accuracy, F1, confusion matrices)
- Feature importance extraction
- Model reporting with associational framing
"""

from .train import train_random_forest, train_xgboost, run_cross_validation
from .metrics import calculate_accuracy, calculate_f1_scores, generate_confusion_matrix
from .report import generate_training_report, validate_report_schema

__all__ = [
    "train_random_forest",
    "train_xgboost",
    "run_cross_validation",
    "calculate_accuracy",
    "calculate_f1_scores",
    "generate_confusion_matrix",
    "generate_training_report",
    "validate_report_schema",
]