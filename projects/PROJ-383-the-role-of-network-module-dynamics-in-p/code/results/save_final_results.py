"""
T030: Save final results to data/results/statistical_report.json and data/results/plots/

This script consolidates the statistical analysis results (correlation, p-values)
and sensitivity analysis results into a final JSON report, and ensures all
generated plots are saved in the correct directory.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from results.generate_report import load_json_file, generate_statistical_report
from results.generate_plots import load_statistics_results, load_sensitivity_results, ensure_plots_directory, plot_null_distribution, plot_sensitivity_analysis
from utils.logging_config import setup_logging

# Constants
RESULTS_DIR = PROJECT_ROOT / "data" / "results"
PLOTS_DIR = RESULTS_DIR / "plots"
STATISTICAL_REPORT_PATH = RESULTS_DIR / "statistical_report.json"
STATISTICS_RESULTS_PATH = RESULTS_DIR / "statistics_results.json"
SENSITIVITY_RESULTS_PATH = RESULTS_DIR / "sensitivity_analysis.json"

def main():
    """
    Main entry point for saving final results.
    1. Loads statistics and sensitivity results.
    2. Generates the final statistical report JSON.
    3. Ensures plots are generated and saved.
    4. Writes the final report to disk.
    """
    # Setup logging
    log_path = RESULTS_DIR / "save_final_results.log"
    logger = setup_logging("save_final_results", log_file=str(log_path))
    logger.info("Starting final results save process.")

    # Ensure directories exist
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured directories exist: {RESULTS_DIR}, {PLOTS_DIR}")

    # Load existing results from previous tasks (T025-T029)
    try:
        stats_results = load_statistics_results(str(STATISTICS_RESULTS_PATH))
        logger.info(f"Loaded statistics results from {STATISTICS_RESULTS_PATH}")
    except FileNotFoundError:
        logger.error(f"Statistics results file not found: {STATISTICS_RESULTS_PATH}. "
                     "Please ensure T025 (statistics) has been run.")
        sys.exit(1)

    try:
        sensitivity_results = load_sensitivity_results(str(SENSITIVITY_RESULTS_PATH))
        logger.info(f"Loaded sensitivity results from {SENSITIVITY_RESULTS_PATH}")
    except FileNotFoundError:
        logger.error(f"Sensitivity results file not found: {SENSITIVITY_RESULTS_PATH}. "
                     "Please ensure T027 (sensitivity analysis) has been run.")
        sys.exit(1)

    # Generate the final statistical report content
    # This aggregates the correlation, p-values, and sensitivity findings
    report_data = {
        "analysis_summary": {
            "metric": "Temporal Flexibility",
            "behavioral_metric": "2-back Accuracy",
            "control_variable": "Mean Framewise Displacement (FD)",
            "method": "Partial Spearman Correlation with Permutation Test"
        },
        "primary_results": {
            "correlation_coefficient": stats_results.get("correlation_coefficient"),
            "p_value_permutation": stats_results.get("p_value_permutation"),
            "n_permutations": stats_results.get("n_permutations"),
            "sample_size": stats_results.get("sample_size"),
            "mean_fd_controlled": True
        },
        "sensitivity_analysis": {
            "window_lengths_tested": sensitivity_results.get("window_lengths_tested"),
            "p_values": sensitivity_results.get("p_values"),
            "max_p_value_difference": sensitivity_results.get("max_p_value_difference"),
            "stability_threshold": 0.05,
            "is_stable": sensitivity_results.get("max_p_value_difference", float('inf')) < 0.05
        },
        "conclusion": {
            "associational_nature": True,
            "motion_control_applied": True,
            "sensitivity_confirmed": sensitivity_results.get("max_p_value_difference", float('inf')) < 0.05,
            "note": "Findings are framed as associational. Motion control was applied via regression and scrubbing."
        }
    }

    # Save the final statistical report JSON
    try:
        with open(STATISTICAL_REPORT_PATH, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2)
        logger.info(f"Saved final statistical report to {STATISTICAL_REPORT_PATH}")
    except IOError as e:
        logger.error(f"Failed to write statistical report: {e}")
        sys.exit(1)

    # Ensure plots are generated and saved (T029 dependency)
    # Although T029 is marked complete, we re-run the plot generation logic
    # here to guarantee the files exist in the expected location for this task's output.
    try:
        # Load data for plots
        stats_data = load_statistics_results(str(STATISTICS_RESULTS_PATH))
        sens_data = load_sensitivity_results(str(SENSITIVITY_RESULTS_PATH))

        # Plot Null Distribution
        plot_null_distribution(stats_data, str(PLOTS_DIR / "null_dist.png"))
        logger.info(f"Saved null distribution plot to {PLOTS_DIR / 'null_dist.png'}")

        # Plot Sensitivity Analysis
        plot_sensitivity_analysis(sens_data, str(PLOTS_DIR / "sensitivity_plot.png"))
        logger.info(f"Saved sensitivity plot to {PLOTS_DIR / 'sensitivity_plot.png'}")

    except Exception as e:
        logger.error(f"Failed to generate or save plots: {e}")
        sys.exit(1)

    logger.info("Final results save process completed successfully.")
    print(f"Final report saved to: {STATISTICAL_REPORT_PATH}")
    print(f"Plots saved to: {PLOTS_DIR}")

if __name__ == "__main__":
    main()