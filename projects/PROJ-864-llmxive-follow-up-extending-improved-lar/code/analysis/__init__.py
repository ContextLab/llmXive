"""
Analysis module for llmXive Follow-up: Extending Improved Large Language Diffusion Models.

This module contains scripts for statistical analysis, evaluation, and reporting
of model training results.
"""

# Analysis scripts
from .statistical_test import run_anova_analysis, compute_generalization_gap
from .evaluate_human_eval import run_human_eval_benchmark, check_exclusion
from .evaluate_wikitext2 import evaluate_wikitext2_perplexity
from .compute_metrics import compute_gap_correlation, compute_gap_slope
from .power_analysis import perform_power_analysis
from .report_generator import generate_markdown_report, generate_final_report

__all__ = [
    'run_anova_analysis',
    'compute_generalization_gap', 
    'run_human_eval_benchmark',
    'check_exclusion',
    'evaluate_wikitext2_perplexity',
    'compute_gap_correlation',
    'compute_gap_slope',
    'perform_power_analysis',
    'generate_markdown_report',
    'generate_final_report'
]