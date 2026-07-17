"""
Analysis module for network topology energy transfer research.
"""
from .regression import fit_linear_regression, analyze_correlation
from .anova import run_one_way_anova, apply_multiple_comparison_correction
from .sensitivity import run_sensitivity_sweep
from .plotting import generate_all_figures
from .report import generate_report
from .verify_report import verify_disclaimers
from .power import compute_power_analysis, generate_power_report
from .run_analysis import main as run_analysis_main

__all__ = [
    'fit_linear_regression',
    'analyze_correlation',
    'run_one_way_anova',
    'apply_multiple_comparison_correction',
    'run_sensitivity_sweep',
    'generate_all_figures',
    'generate_report',
    'verify_disclaimers',
    'compute_power_analysis',
    'generate_power_report',
    'run_analysis_main'
]