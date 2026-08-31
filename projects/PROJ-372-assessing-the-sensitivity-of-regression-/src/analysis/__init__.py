"""
Analysis module for sensitivity analysis of regression coefficients.

This module provides tools for:
- Hierarchical Linear Modeling (HLM) analysis
- Meta-analysis of stability results
- Sensitivity sweeps and visualization
- Report generation
"""

from .hlm_analysis import (
    run_meta_analysis,
    perform_sensitivity_sweep,
    calculate_interaction_model,
)
from .visualization import generate_stability_curves, plot_convergence
from .report_generator import generate_analysis_report

__all__ = [
    "run_meta_analysis",
    "perform_sensitivity_sweep",
    "calculate_interaction_model",
    "generate_stability_curves",
    "plot_convergence",
    "generate_analysis_report",
]