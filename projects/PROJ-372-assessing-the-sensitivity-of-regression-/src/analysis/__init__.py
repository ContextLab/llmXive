"""
Analysis module for assessing the sensitivity of regression coefficients.

This module implements User Story 3 (US3): Interaction Analysis and Sensitivity Visualization.
It provides tools for multiple regression with interaction terms, sensitivity sweeps,
and visualization of stability curves.

Key components:
- hlm_analysis: Multiple regression analysis (per Spec FR-005)
- Visualization utilities for stability curves
- Report generation for associational findings
"""

from .hlm_analysis import run_meta_analysis, sensitivity_sweep
from .visualization import plot_stability_curves, plot_interaction_effects

__all__ = [
    "run_meta_analysis",
    "sensitivity_sweep",
    "plot_stability_curves",
    "plot_interaction_effects",
]