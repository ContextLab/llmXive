"""
Analysis module for llmXive.

This package provides interfaces for:
- Calculating topological metrics (q-profile, resonant surface density)
- Computing statistical correlations (Spearman, bootstrap)
- Generating diagnostic visualizations
"""
from .metrics import calculate_resonant_surface_density, extract_q_profile, detect_outliers
from .correlation import compute_spearman_correlation, bootstrap_resample, perform_power_analysis
from .viz import plot_topology_vs_confinement

__all__ = [
    "calculate_resonant_surface_density",
    "extract_q_profile",
    "detect_outliers",
    "compute_spearman_correlation",
    "bootstrap_resample",
    "perform_power_analysis",
    "plot_topology_vs_confinement",
]