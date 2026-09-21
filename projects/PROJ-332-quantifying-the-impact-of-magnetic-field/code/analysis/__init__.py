"""
Analysis module for the llmXive project.

This module provides functionality for:
- Calculating topological metrics (q-profile, magnetic shear, resonant surface density).
- Deriving island widths using the Rutherford equation.
- Performing statistical correlation analysis (Spearman rank).
- Conducting power analysis and multicollinearity checks.
- Generating reports and visualizations.
"""
from .metrics import extract_q_profile, calculate_local_magnetic_shear, calculate_resonant_surface_density, derive_island_width, detect_outliers, validate_metric_ranges, validate_metric_ranges_for_output, process_metrics_for_discharges
from .correlation import stratify_by_mode, calculate_spearman_correlation, check_multicollinearity, calculate_power_for_correlation, check_power_sufficiency, run_correlation_analysis, save_analysis_results
from .power_analysis import calculate_power_for_correlation, check_power_sufficiency, run_power_analysis
from .report_generator import load_json_file, generate_final_report
