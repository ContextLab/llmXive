"""
Task T041: Generate final report with all metrics aggregated and visualizations referenced.

This script aggregates results from all previous US3 tasks (T027-T040) into a single
comprehensive JSON report and generates a summary text file. It references the
visualization files generated in T034 and T035.
"""
import os
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import numpy as np

from config import get_config
from utils import setup_logging, compute_file_checksum
from t040_create_comparison_report import load_json, create_comparison_report

# Setup logging
logger = setup_logging("INFO")

def load_json_file(filepath: str) -> Optional[Dict[str, Any]]:
    """Safely load a JSON file, returning None if it doesn't exist."""
    if not os.path.exists(filepath):
        logger.warning(f"File not found: {filepath}")
        return None
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON in {filepath}: {e}")
        return None

def aggregate_artifacts() -> Dict[str, Any]:
    """
    Load all intermediate artifacts and aggregate them into a final report structure.
    """
    config = get_config()
    processed_dir = config.get('OUTPUT_PATH', 'data/processed')
    figures_dir = config.get('FIGURES_PATH', 'figures')

    # Ensure directories exist
    os.makedirs(processed_dir, exist_ok=True)
    os.makedirs(figures_dir, exist_ok=True)

    # 1. Load Baseline Metrics (from T012/T013)
    baseline_metrics = load_json_file(os.path.join(processed_dir, 'baseline_metrics.json'))
    if baseline_metrics is None:
        logger.error("Critical: baseline_metrics.json not found. Cannot generate final report.")
        return {}

    # 2. Load Cleaned Metrics (from T023)
    cleaned_metrics = load_json_file(os.path.join(processed_dir, 'cleaned_metrics.json'))
    if cleaned_metrics is None:
        logger.error("Critical: cleaned_metrics.json not found. Cannot generate final report.")
        return {}

    # 3. Load Sensitivity Analysis (from T030/T031)
    # Note: T030 and T031 might produce separate files or a combined one depending on implementation.
    # We look for a combined sensitivity file first, then fallback.
    sensitivity_file = os.path.join(processed_dir, 'sensitivity_analysis.json')
    sensitivity_analysis = load_json_file(sensitivity_file)
    if sensitivity_analysis is None:
        # Fallback: Try to load individual components if the combined file doesn't exist
        # For this task, we assume T030/T031 produced a consolidated file or we aggregate them here.
        # If T030/T031 produced separate files, we would load them here.
        # Since T040 expects 'sensitivity_analysis', we assume T030/T031 logic is encapsulated or
        # we create a placeholder if missing to prevent crash, though ideally T030 runs first.
        logger.warning("sensitivity_analysis.json not found. Creating empty structure.")
        sensitivity_analysis = {
            "size_bins": [],
            "missingness_bins": [],
            "bootstrap_results": [],
            "warnings": ["Sensitivity analysis artifacts missing. Check T030/T031 execution."]
        }

    # 4. Load Null FPR Metrics (from T032)
    null_fpr_metrics = load_json_file(os.path.join(processed_dir, 'null_fpr_metrics.json'))
    if null_fpr_metrics is None:
        logger.warning("null_fpr_metrics.json not found. FPR analysis will be marked as incomplete.")
        null_fpr_metrics = {"status": "missing", "fpr_estimates": []}

    # 5. Load Threshold Sweep Results (from T033)
    threshold_sweep = load_json_file(os.path.join(processed_dir, 'threshold_sweep_results.json'))
    if threshold_sweep is None:
        logger.warning("threshold_sweep_results.json not found.")
        threshold_sweep = {"status": "missing", "results": []}

    # 6. Load Per-Dataset Reports (from T036-T038)
    pvalue_report = load_json_file(os.path.join(processed_dir, 'pvalue_shift_report.json'))
    ci_width_report = load_json_file(os.path.join(processed_dir, 'ci_width_report.json'))
    effect_size_report = load_json_file(os.path.join(processed_dir, 'effect_size_report.json'))

    # 7. Load Excluded Datasets Log (from T039)
    excluded_log = load_json_file(os.path.join(processed_dir, 'excluded_datasets_log.json'))
    if excluded_log is None:
        excluded_log = {"excluded": [], "reasons": []}

    # 8. Reference Visualizations (from T034, T035)
    forest_plot_path = os.path.join(figures_dir, 'forest_plot.png')
    ci_heatmap_path = os.path.join(figures_dir, 'ci_width_heatmap.png')

    visualizations = {
        "forest_plot": {
            "path": forest_plot_path,
            "exists": os.path.exists(forest_plot_path),
            "description": "Forest plot of p-value shifts across datasets"
        },
        "ci_heatmap": {
            "path": ci_heatmap_path,
            "exists": os.path.exists(ci_heatmap_path),
            "description": "Heatmap of CI-width changes across strategies and bins"
        }
    }

    # Construct the final report
    final_report = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "task_id": "T041",
            "feature": "Quantifying the Impact of Data Cleaning on Statistical Inference",
            "version": "1.0.0"
        },
        "summary": {
            "datasets_analyzed": len(baseline_metrics.get('datasets', [])) if baseline_metrics else 0,
            "cleaning_strategies_applied": len(cleaned_metrics.get('strategies', [])) if cleaned_metrics else 0,
            "total_comparisons": len(baseline_metrics.get('datasets', [])) * (len(cleaned_metrics.get('strategies', [])) if cleaned_metrics else 0),
            "excluded_datasets_count": len(excluded_log.get('excluded', []))
        },
        "metrics": {
            "baseline": baseline_metrics,
            "cleaned": cleaned_metrics,
            "sensitivity_analysis": sensitivity_analysis,
            "null_fpr": null_fpr_metrics,
            "threshold_sweep": threshold_sweep
        },
        "per_dataset_reports": {
            "p_value_shifts": pvalue_report,
            "ci_width_changes": ci_width_report,
            "effect_size_changes": effect_size_report
        },
        "exclusions": excluded_log,
        "visualizations": visualizations,
        "status": "complete"
    }

    return final_report

def write_summary_text(report: Dict[str, Any], output_path: str):
    """Write a human-readable summary text file."""
    with open(output_path, 'w') as f:
        f.write("=" * 60 + "\n")
        f.write("FINAL REPORT: Impact of Data Cleaning on Statistical Inference\n")
        f.write("=" * 60 + "\n\n")
        
        meta = report.get('metadata', {})
        f.write(f"Generated: {meta.get('generated_at', 'N/A')}\n")
        f.write(f"Task: {meta.get('task_id', 'N/A')}\n\n")

        summary = report.get('summary', {})
        f.write("SUMMARY STATISTICS\n")
        f.write("-" * 40 + "\n")
        f.write(f"Datasets Analyzed: {summary.get('datasets_analyzed', 0)}\n")
        f.write(f"Cleaning Strategies: {summary.get('cleaning_strategies_applied', 0)}\n")
        f.write(f"Total Comparisons: {summary.get('total_comparisons', 0)}\n")
        f.write(f"Excluded Datasets: {summary.get('excluded_datasets_count', 0)}\n\n")

        viz = report.get('visualizations', {})
        f.write("VISUALIZATIONS\n")
        f.write("-" * 40 + "\n")
        for name, info in viz.items():
            status = "EXISTS" if info.get('exists') else "MISSING"
            f.write(f"- {name.replace('_', ' ').title()}: [{status}]\n")
            f.write(f"  Path: {info.get('path', 'N/A')}\n")
            f.write(f"  Desc: {info.get('description', 'N/A')}\n")
        
        f.write("\n" + "=" * 60 + "\n")
        f.write("END OF REPORT\n")
        f.write("=" * 60 + "\n")

def main():
    """Main entry point for T041."""
    logger.info("Starting T041: Generate Final Report")
    
    try:
        # Aggregate all artifacts
        final_report = aggregate_artifacts()
        
        if not final_report:
            logger.error("Failed to aggregate artifacts. Aborting report generation.")
            return 1

        # Define output paths
        config = get_config()
        processed_dir = config.get('OUTPUT_PATH', 'data/processed')
        
        report_json_path = os.path.join(processed_dir, 'final_report.json')
        report_txt_path = os.path.join(processed_dir, 'final_report_summary.txt')

        # Write JSON report
        with open(report_json_path, 'w') as f:
            json.dump(final_report, f, indent=2, default=str)
        
        logger.info(f"JSON report written to: {report_json_path}")

        # Write text summary
        write_summary_text(final_report, report_txt_path)
        logger.info(f"Text summary written to: {report_txt_path}")

        # Calculate checksum for the final report
        checksum = compute_file_checksum(report_json_path)
        logger.info(f"Final report checksum: {checksum}")

        logger.info("T041 completed successfully.")
        return 0

    except Exception as e:
        logger.exception(f"Error during T041 execution: {e}")
        return 1

if __name__ == "__main__":
    exit(main())