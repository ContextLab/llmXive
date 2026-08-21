"""
Modeling package for training and evaluating machine learning models.

This package handles:
- Model training (Random Forest, XGBoost)
- Cross-validation with stratified splits
- Metrics calculation (accuracy, F1, confusion matrices)
- Feature importance analysis
- Permutation testing and statistical significance
- Report generation with associational framing
"""

from .train import train_models, evaluate_model, main as train_main
from .metrics import calculate_accuracy, calculate_f1_scores, compute_confusion_matrix, generate_metrics_report
from .importance import extract_feature_importance, calculate_importance_variance, run_permutation_test, apply_benjamini_hochberg
from .report import generate_training_report, generate_importance_report, validate_report_schema

__all__ = [
    # Training functions
    'train_models',
    'evaluate_model',
    'train_main',
    
    # Metrics functions
    'calculate_accuracy',
    'calculate_f1_scores',
    'compute_confusion_matrix',
    'generate_metrics_report',
    
    # Importance analysis
    'extract_feature_importance',
    'calculate_importance_variance',
    'run_permutation_test',
    'apply_benjamini_hochberg',
    
    # Report generation
    'generate_training_report',
    'generate_importance_report',
    'validate_report_schema'
]

__version__ = "0.1.0"