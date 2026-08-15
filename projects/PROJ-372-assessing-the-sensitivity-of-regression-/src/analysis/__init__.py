"""
Analysis module for assessing the sensitivity of regression coefficients
to dataset subset selection.

This module implements User Story 3: Interaction Analysis and Sensitivity Visualization.
It provides tools for meta-analysis, interaction modeling, and sensitivity sweeps.
"""

from .hlm_analysis import (
    run_meta_analysis,
    perform_sensitivity_sweep,
    calculate_interaction_effects,
)
from .visualizer import generate_stability_curves, plot_sensitivity_effects
from .reporter import generate_final_report

__all__ = [
    "run_meta_analysis",
    "perform_sensitivity_sweep",
    "calculate_interaction_effects",
    "generate_stability_curves",
    "plot_sensitivity_effects",
    "generate_final_report",
]