"""
Modeling package for machine learning training and evaluation.

This module orchestrates:
1. Data splitting (Stratified + Scaffold grouping)
2. Model training (Random Forest, SVM) with hyperparameter optimization
3. Model evaluation (R², RMSE, MAE, Permutation Importance)
4. Generalization analysis and feature importance mapping
"""
from .split import create_scaffold_split, extract_validation_set
from .train import train_random_forest, train_svm, run_grid_search
from .evaluate import evaluate_model, compute_per_class_metrics, compute_permutation_importance, map_bits_to_substructures

__all__ = [
    "create_scaffold_split",
    "extract_validation_set",
    "train_random_forest",
    "train_svm",
    "run_grid_search",
    "evaluate_model",
    "compute_per_class_metrics",
    "compute_permutation_importance",
    "map_bits_to_substructures",
]