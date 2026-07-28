"""
Evaluation module for model performance and statistical testing.
"""
from src.evaluate.metrics import calculate_metrics
from src.evaluate.statistical_tests import nadeau_bengio_ttest, run_model_comparison_test
from src.evaluate.power_analysis import perform_power_analysis
from src.evaluate.held_out_report import generate_held_out_report

__all__ = [
    "calculate_metrics",
    "nadeau_bengio_ttest",
    "run_model_comparison_test",
    "perform_power_analysis",
    "generate_held_out_report"
]