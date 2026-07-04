"""
Task T038: Write final results and plots to data/results/

This script orchestrates the final output generation for User Story 4.
It loads computed metrics and ground truth, calculates errors, identifies
critical thresholds, and writes the final artifacts to disk:
- data/results/error_vs_snr.png
- data/results/final_lookup.csv
- data/results/critical_threshold_report.json
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

# Ensure project root is in path for imports
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.analysis import (
    load_ground_truth_metrics, 
    calculate_metric_error, 
    identify_critical_threshold,
    analyze_results_from_files
)
from code.visualize import (
    export_metric_results_to_csv,
    generate_error_vs_snr_plot,
    generate_critical_threshold_report,
    run_visualization_pipeline
)
from code.utils.io import write_json_artifact

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_final_results_pipeline(
    metrics_file: str = "data/processed/metrics_summary.csv",
    ground_truth_dir: str = "data/processed",
    output_dir: str = "data/results",
    snr_levels: List[float] = None
) -> Dict[str, Any]:
    """
    Execute the final results pipeline for T038.
    
    Args:
        metrics_file: Path to the CSV containing all computed metrics (T032 output)
        ground_truth_dir: Directory containing ground truth JSON files (T017 output)
        output_dir: Directory to write final results
        snr_levels: List of SNR levels to include in the lookup table. 
                    If None, defaults to [0, 5, 10, 15, 20, 25, 30].
    
    Returns:
        Dictionary containing paths to generated artifacts and summary stats.
    """
    if snr_levels is None:
        snr_levels = [0.0, 5.0, 10.0, 15.0, 20.0, 25.0, 30.0]

    # Ensure output directory exists
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    logger.info(f"Output directory ensured: {output_path}")

    # 1. Load Ground Truth Metrics
    logger.info(f"Loading ground truth metrics from {ground_truth_dir}...")
    try:
        ground_truth = load_ground_truth_metrics(ground_truth_dir)
        if not ground_truth:
            raise FileNotFoundError("No ground truth metrics found.")
        logger.info(f"Loaded ground truth for {len(ground_truth)} seeds.")
    except Exception as e:
        logger.error(f"Failed to load ground truth metrics: {e}")
        raise

    # 2. Analyze Results (Compute Errors)
    # This function internally calls calculate_metric_error for each row
    logger.info("Computing errors relative to ground truth...")
    try:
        analysis_results = analyze_results_from_files(
            metrics_file_path=metrics_file,
            ground_truth_data=ground_truth
        )
    except FileNotFoundError:
        logger.error(f"Metrics file not found at {metrics_file}")
        raise
    
    if not analysis_results:
        raise ValueError("Analysis results are empty. Check input data.")

    # 3. Generate CSV Export (final_lookup.csv)
    csv_path = output_path / "final_lookup.csv"
    logger.info(f"Exporting results to {csv_path}...")
    export_metric_results_to_csv(analysis_results, str(csv_path))
    logger.info("CSV export complete.")

    # 4. Generate Plot (error_vs_snr.png)
    plot_path = output_path / "error_vs_snr.png"
    logger.info(f"Generating error vs SNR plot at {plot_path}...")
    try:
        generate_error_vs_snr_plot(
            analysis_results, 
            output_path=str(plot_path),
            snr_levels=snr_levels
        )
        logger.info("Plot generation complete.")
    except Exception as e:
        logger.error(f"Failed to generate plot: {e}")
        raise

    # 5. Identify Critical Threshold & Generate Report (critical_threshold_report.json)
    report_path = output_path / "critical_threshold_report.json"
    logger.info(f"Generating critical threshold report at {report_path}...")
    try:
        threshold_data = generate_critical_threshold_report(
            analysis_results,
            output_path=str(report_path)
        )
        # Also save the raw threshold data for reference if needed
        logger.info("Critical threshold report generated.")
    except Exception as e:
        logger.error(f"Failed to generate threshold report: {e}")
        raise

    # 6. Summary
    result_summary = {
        "csv_path": str(csv_path),
        "plot_path": str(plot_path),
        "report_path": str(report_path),
        "total_records": len(analysis_results),
        "snr_levels_used": snr_levels,
        "status": "success"
    }

    # Write a summary manifest for the task
    manifest_path = output_path / "task_t038_manifest.json"
    write_json_artifact(result_summary, str(manifest_path))
    logger.info(f"Task T038 complete. Manifest written to {manifest_path}")

    return result_summary

def main():
    """Entry point for T038 execution."""
    logger.info("Starting Task T038: Final Results Generation")
    
    # Default paths based on project conventions
    metrics_file = "data/processed/metrics_summary.csv"
    ground_truth_dir = "data/processed"
    output_dir = "data/results"
    
    try:
        results = run_final_results_pipeline(
            metrics_file=metrics_file,
            ground_truth_dir=ground_truth_dir,
            output_dir=output_dir
        )
        logger.info("T038 Execution Successful")
        print(json.dumps(results, indent=2))
    except Exception as e:
        logger.error(f"T038 Execution Failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()