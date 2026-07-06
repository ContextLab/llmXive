"""
Analysis module for brain network dynamics research.

This package contains modules for:
- Network metric computation
- Statistical analysis
- Visualization
- Report generation
"""

from .network import load_preprocessed_data, extract_roi_timeseries, calculate_connectivity_matrix
from .network import calculate_network_metrics, save_metrics_to_csv, run_analysis as run_network_analysis
from .network import main as network_main

from .plots import generate_scatter_plot, generate_regression_line_plot, generate_residual_plot
from .plots import run_analysis as run_plots_analysis
from .plots import main as plots_main

from .stats import calculate_vif, apply_fdr_correction, run_ancova_analysis
from .stats import run_analysis as run_stats_analysis
from .stats import main as stats_main

from .report import determine_framing, generate_report, save_report, run_analysis as run_report_analysis
from .report import main as report_main

__all__ = [
    # Network analysis
    'load_preprocessed_data',
    'extract_roi_timeseries',
    'calculate_connectivity_matrix',
    'calculate_network_metrics',
    'save_metrics_to_csv',
    'run_network_analysis',
    'network_main',
    
    # Plots
    'generate_scatter_plot',
    'generate_regression_line_plot',
    'generate_residual_plot',
    'run_plots_analysis',
    'plots_main',
    
    # Statistics
    'calculate_vif',
    'apply_fdr_correction',
    'run_ancova_analysis',
    'run_stats_analysis',
    'stats_main',
    
    # Report
    'determine_framing',
    'generate_report',
    'save_report',
    'run_report_analysis',
    'report_main',
]
