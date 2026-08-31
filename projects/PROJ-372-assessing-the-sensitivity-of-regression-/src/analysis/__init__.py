"""
Analysis module for llmXive sensitivity assessment pipeline.

This module provides functionality for:
- Theoretical baseline calculation (T044)
- Empirical vs theoretical variance comparison (T045)
- Multiple regression analysis with interaction terms (T031)
- Sensitivity sweep logic (T061, T062)
- Visualization generation (T032)
- Report generation (T033)
- Pipeline orchestration (T034)
"""

from .regression_analysis import (
    calculate_theoretical_variance,
    compare_empirical_theoretical_variance,
    run_multiple_regression_analysis,
    run_sensitivity_sweep,
    generate_stability_curves,
    generate_final_report,
    run_meta_analysis
)

__all__ = [
    'calculate_theoretical_variance',
    'compare_empirical_theoretical_variance',
    'run_multiple_regression_analysis',
    'run_sensitivity_sweep',
    'generate_stability_curves',
    'generate_final_report',
    'run_meta_analysis'
]