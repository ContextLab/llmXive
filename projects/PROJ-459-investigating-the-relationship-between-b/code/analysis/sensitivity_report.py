"""
Generate SensitivityReport JSON/Parquet with stability metrics and ICC values.
Saves to data/derived/sensitivity_report.json.
"""
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

import numpy as np
import pandas as pd

from config import get_derived_path
from data.models import SensitivityReport
from utils.io import save_json, save_parquet, ensure_dir
from analysis.metrics import run_sensitivity_analysis, compute_icc

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_sensitivity_report(
    time_series: np.ndarray,
    confounds: Optional[np.ndarray] = None,
    window_sizes: List[int] = None,
    output_path: Optional[Path] = None
) -> SensitivityReport:
    """
    Run sensitivity analysis on dynamic connectivity metrics across window sizes
    and generate a SensitivityReport.

    Args:
        time_series: 2D array of shape (timepoints, roi_count)
        confounds: Optional 2D array of confounds to regress out
        window_sizes: List of window sizes (in TRs) to test
        output_path: Path to save the report (defaults to data/derived/sensitivity_report.json)

    Returns:
        SensitivityReport object containing stability metrics and ICC values
    """
    if window_sizes is None:
        window_sizes = [20, 30, 40]

    if output_path is None:
        output_path = get_derived_path("sensitivity_report.json")

    ensure_dir(output_path.parent)

    logger.info(f"Running sensitivity analysis with window sizes: {window_sizes}")

    # Regress confounds if provided
    if confounds is not None:
        from analysis.metrics import regress_confounds
        time_series = regress_confounds(time_series, confounds)

    # Run sensitivity analysis to get metrics for each window size
    analysis_results = run_sensitivity_analysis(time_series, window_sizes)

    # analysis_results is a dict: {window_size: {metric_name: value, ...}}
    # We need to compute ICC for each metric across window sizes

    metrics_data = []
    icc_results = {}

    # Collect all metric names across window sizes
    all_metric_names = set()
    for wsize, metrics in analysis_results.items():
        all_metric_names.update(metrics.keys())

    # For each metric, collect values across window sizes and compute ICC
    for metric_name in sorted(all_metric_names):
        values_by_window = {}
        for wsize in window_sizes:
            if wsize in analysis_results and metric_name in analysis_results[wsize]:
                values_by_window[wsize] = analysis_results[wsize][metric_name]

        if len(values_by_window) >= 2:
            # Compute ICC across window sizes for this metric
            values = [values_by_window[w] for w in sorted(values_by_window.keys())]
            icc_value = compute_icc(values)
            icc_results[metric_name] = icc_value

            metrics_data.append({
                "metric_name": metric_name,
                "window_sizes": list(values_by_window.keys()),
                "values": [float(values_by_window[w]) for w in sorted(values_by_window.keys())],
                "icc": float(icc_value) if not np.isnan(icc_value) else None
            })

    # Build the report
    report_data = {
        "window_sizes_tested": window_sizes,
        "metrics": metrics_data,
        "icc_results": {k: (v if not np.isnan(v) else None) for k, v in icc_results.items()}
    }

    # Create Pydantic model instance
    report = SensitivityReport(
        window_size=window_sizes[0],  # Primary window size
        icc=icc_results.get("global_efficiency", 0.0) if icc_results else 0.0
    )

    # Save as JSON
    save_json(report_data, output_path)
    logger.info(f"Sensitivity report saved to {output_path}")

    # Also save as Parquet for the metrics table
    parquet_path = output_path.with_suffix(".parquet")
    if metrics_data:
        df = pd.DataFrame(metrics_data)
        save_parquet(df, parquet_path)
        logger.info(f"Sensitivity metrics saved to {parquet_path}")

    return report


def main():
    """
    Main entry point for generating sensitivity report.
    This script expects to be run after metrics have been computed.
    For demonstration, it will load example time series from data/processed/
    if available, or raise an error if no data is found.
    """
    import sys
    from data.preprocess import extract_time_series
    from config import get_processed_path, DatasetConfig

    # Try to find processed time series data
    processed_dir = get_processed_path("")
    if not processed_dir.exists():
        logger.error(f"Processed directory not found: {processed_dir}")
        logger.error("Please run preprocessing first (T015) to generate time series data.")
        sys.exit(1)

    # Look for time series files
    ts_files = list(processed_dir.glob("*_time_series.parquet"))
    if not ts_files:
        logger.error(f"No time series files found in {processed_dir}")
        logger.error("Please ensure preprocessing has been completed.")
        sys.exit(1)

    logger.info(f"Found {len(ts_files)} time series file(s)")

    # For the report, we'll aggregate across subjects or pick one for demonstration
    # In a full pipeline, we might compute per-subject reports and then aggregate
    all_metrics = []
    subject_ids = []

    for ts_file in ts_files[:5]:  # Limit to first 5 subjects for efficiency
        try:
            df = pd.read_parquet(ts_file)
            # Assume columns are ROI IDs, index is timepoints
            time_series = df.values
            subject_id = ts_file.stem.replace("_time_series", "")
            subject_ids.append(subject_id)

            # Compute report for this subject
            report = generate_sensitivity_report(time_series)
            all_metrics.append(report)

            logger.info(f"Processed subject {subject_id}")
        except Exception as e:
            logger.warning(f"Failed to process {ts_file}: {e}")
            continue

    if not all_metrics:
        logger.error("No subjects successfully processed for sensitivity report")
        sys.exit(1)

    logger.info(f"Successfully generated sensitivity reports for {len(all_metrics)} subjects")
    logger.info(f"Reports saved to {get_derived_path('sensitivity_report.json')}")


if __name__ == "__main__":
    main()