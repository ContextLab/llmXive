"""
Report generation module for the network topology influence study.

This module aggregates results from structural metrics, dynamic metrics,
and correlation analysis to produce the final research report.
It ensures strict adherence to the "associational" framing requirement
and includes sensitivity analysis comparisons.
"""

import os
import json
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime

# Import configuration
from code.config import CONFIG

# Constants for output paths
DATA_DIR = Path("data")
PROCESSED_DIR = DATA_DIR / "processed"
LOGS_DIR = DATA_DIR / "logs"
REPORTS_DIR = DATA_DIR / "reports"

# Ensure output directories exist
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)


def load_metrics_data() -> Dict[str, pd.DataFrame]:
    """
    Load processed structural and dynamic metrics from CSV files.

    Returns:
        Dict containing 'structural' and 'dynamic' DataFrames.
    """
    structural_path = PROCESSED_DIR / "structural_metrics.csv"
    dynamic_path = PROCESSED_DIR / "dynamic_metrics.csv"

    structural_df = pd.DataFrame()
    dynamic_df = pd.DataFrame()

    if structural_path.exists():
        structural_df = pd.read_csv(structural_path)
    else:
        raise FileNotFoundError(f"Structural metrics file not found: {structural_path}")

    if dynamic_path.exists():
        dynamic_df = pd.read_csv(dynamic_path)
    else:
        raise FileNotFoundError(f"Dynamic metrics file not found: {dynamic_path}")

    return {
        "structural": structural_df,
        "dynamic": dynamic_df
    }


def load_correlation_results() -> Optional[pd.DataFrame]:
    """
    Load correlation analysis results if available.

    Returns:
        DataFrame with correlation results or None if not found.
    """
    corr_path = PROCESSED_DIR / "correlation_results.csv"
    if corr_path.exists():
        return pd.read_csv(corr_path)
    return None


def load_exclusion_log() -> Dict[str, Any]:
    """
    Load the subject exclusion log.

    Returns:
        Dict with exclusion data or empty dict if not found.
    """
    log_path = LOGS_DIR / "exclusion_log.json"
    if log_path.exists():
        with open(log_path, 'r') as f:
            return json.load(f)
    return {"excluded_subjects": [], "reasons": []}


def calculate_sensitivity_metrics() -> Dict[str, float]:
    """
    Calculate sensitivity metrics for the report.

    Specifically calculates the absolute difference between 30 TR and 20 TR
    correlation coefficients as mandated by SC-002.

    Returns:
        Dict with sensitivity metrics.
    """
    # Note: In a full implementation, this would load results from a
    # sensitivity analysis run. For now, we return a placeholder structure
    # that expects the data to be present if the analysis was run.
    # If the sensitivity analysis data exists, we compute the difference.

    sensitivity_path = PROCESSED_DIR / "sensitivity_analysis.csv"
    if sensitivity_path.exists():
        sens_df = pd.read_csv(sensitivity_path)
        # Expect columns: 'metric', 'tr_30', 'tr_20'
        if 'tr_30' in sens_df.columns and 'tr_20' in sens_df.columns:
            # Calculate absolute difference for the primary correlation metric
            # Assuming the first row or a specific metric is the primary one
            primary_row = sens_df.iloc[0] if len(sens_df) > 0 else None
            if primary_row is not None:
                diff = abs(float(primary_row['tr_30']) - float(primary_row['tr_20']))
                return {
                    "absolute_diff_30_20_tr": diff,
                    "tr_30_value": float(primary_row['tr_30']),
                    "tr_20_value": float(primary_row['tr_20'])
                }

    # Default return if sensitivity data is missing
    return {
        "absolute_diff_30_20_tr": None,
        "tr_30_value": None,
        "tr_20_value": None,
        "note": "Sensitivity analysis data not found. Run robustness analysis first."
    }


def generate_summary_statistics(metrics: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
    """
    Generate summary statistics for structural and dynamic metrics.

    Args:
        metrics: Dict with 'structural' and 'dynamic' DataFrames.

    Returns:
        Dict with summary statistics.
    """
    summary = {}

    # Structural metrics summary
    struct_df = metrics["structural"]
    summary["structural"] = {
        "total_subjects": len(struct_df),
        "mean_global_efficiency": float(struct_df["global_efficiency"].mean()) if "global_efficiency" in struct_df.columns else None,
        "mean_clustering": float(struct_df["clustering_coefficient"].mean()) if "clustering_coefficient" in struct_df.columns else None,
        "mean_modularity": float(struct_df["modularity"].mean()) if "modularity" in struct_df.columns else None,
    }

    # Dynamic metrics summary
    dyn_df = metrics["dynamic"]
    summary["dynamic"] = {
        "total_subjects": len(dyn_df),
        "mean_dwell_time": float(dyn_df["mean_dwell_time"].mean()) if "mean_dwell_time" in dyn_df.columns else None,
        "mean_visited_states": float(dyn_df["visited_states"].mean()) if "visited_states" in dyn_df.columns else None,
    }

    return summary


def generate_final_report(
    output_path: Optional[str] = None,
    include_sensitivity: bool = True
) -> str:
    """
    Generate the final research report in JSON format.

    The report includes:
    - Summary statistics
    - Correlation results (if available)
    - Exclusion log
    - Sensitivity analysis (if requested)
    - Explicit "associational" framing

    Args:
        output_path: Optional path for the output file. Defaults to generated name.
        include_sensitivity: Whether to include sensitivity analysis data.

    Returns:
        Path to the generated report file.
    """
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = str(REPORTS_DIR / f"final_report_{timestamp}.json")

    report_data = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "project_id": "PROJ-128",
            "version": "1.0",
            "framing": "associational",
            "description": "This report presents associational findings between structural and dynamic brain network metrics. No causal claims are made."
        },
        "summary": generate_summary_statistics(load_metrics_data()),
        "exclusion_log": load_exclusion_log(),
        "correlation_results": None,
        "sensitivity_analysis": None
    }

    # Add correlation results if available
    corr_results = load_correlation_results()
    if corr_results is not None:
        report_data["correlation_results"] = corr_results.to_dict(orient="records")

    # Add sensitivity analysis if requested
    if include_sensitivity:
        report_data["sensitivity_analysis"] = calculate_sensitivity_metrics()

    # Write report to file
    with open(output_path, 'w') as f:
        json.dump(report_data, f, indent=2, default=str)

    return output_path


def main():
    """
    Main entry point for report generation.
    """
    print("Starting report generation...")

    try:
        report_path = generate_final_report()
        print(f"Report successfully generated at: {report_path}")

        # Print a brief summary to stdout
        with open(report_path, 'r') as f:
            data = json.load(f)
            print(f"\nReport Summary:")
            print(f"  - Subjects (Structural): {data['summary']['structural']['total_subjects']}")
            print(f"  - Subjects (Dynamic): {data['summary']['dynamic']['total_subjects']}")
            if data['correlation_results']:
                print(f"  - Correlation findings included: {len(data['correlation_results'])} pairs")
            else:
                print("  - No correlation results found (US2 not completed or data missing)")

            if data['sensitivity_analysis'] and data['sensitivity_analysis'].get('absolute_diff_30_20_tr') is not None:
                print(f"  - Sensitivity (30TR vs 20TR diff): {data['sensitivity_analysis']['absolute_diff_30_20_tr']:.4f}")
            else:
                print("  - Sensitivity analysis: Not available or not run")

    except FileNotFoundError as e:
        print(f"Error: Missing required data files. {e}")
        print("Please ensure Tasks T015-T019 (US1) are completed and data is generated.")
        raise
    except Exception as e:
        print(f"Error generating report: {e}")
        raise


if __name__ == "__main__":
    main()