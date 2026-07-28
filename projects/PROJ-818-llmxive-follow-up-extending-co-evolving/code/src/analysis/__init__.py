"""
Analysis module for Co-Evolving Policy Distillation.

Contains validation, metrics, and statistical analysis components.
"""

from .validate_dataset import validate_dataset, main
from .forgetting_metrics import calculate_accuracy_drop, calculate_retention_rate
from .statistical_tests import perform_mixed_design_anova, perform_tukey_hsd
from .data_aggregator import aggregate_batch_results
from .report_generator import generate_final_report

__all__ = [
    'validate_dataset', 'main',
    'calculate_accuracy_drop', 'calculate_retention_rate',
    'perform_mixed_design_anova', 'perform_tukey_hsd',
    'aggregate_batch_results',
    'generate_final_report'
]
