import os
import sys
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import numpy as np

# Import shared utilities
from utils import setup_logging
from config import Config
from models import ComparisonReport

# Configure logger
logger = logging.getLogger(__name__)

def load_json_file(filepath: str) -> Optional[Dict[str, Any]]:
    """Load a JSON file and return its contents as a dictionary."""
    if not os.path.exists(filepath):
        logger.warning(f"File not found: {filepath}")
        return None
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON in {filepath}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error reading {filepath}: {e}")
        return None

def load_baseline_metrics(filepath: str = "data/processed/baseline_metrics.json") -> Optional[Dict[str, Any]]:
    """Load baseline metrics from the specified file."""
    return load_json_file(filepath)

def load_cleaned_metrics(filepath: str = "data/processed/cleaned_metrics.json") -> Optional[Dict[str, Any]]:
    """Load cleaned metrics from the specified file."""
    return load_json_file(filepath)

def load_sensitivity_analysis(filepath: str = "data/processed/sensitivity_analysis.json") -> Optional[Dict[str, Any]]:
    """Load sensitivity analysis results from the specified file."""
    return load_json_file(filepath)

def calculate_absolute_diff(baseline_val: float, cleaned_val: float) -> float:
    """Calculate absolute difference between baseline and cleaned values."""
    if baseline_val is None or cleaned_val is None:
        return 0.0
    return abs(cleaned_val - baseline_val)

def calculate_relative_diff(baseline_val: float, cleaned_val: float) -> float:
    """Calculate relative difference (percentage change) between baseline and cleaned values."""
    if baseline_val is None or cleaned_val is None or baseline_val == 0:
        return 0.0
    return (cleaned_val - baseline_val) / abs(baseline_val)

def aggregate_metrics_for_comparison(
    baseline_metrics: Dict[str, Any],
    cleaned_metrics: Dict[str, Any],
    sensitivity_analysis: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Aggregate metrics from baseline, cleaned, and optional sensitivity analysis
    into a structure suitable for the ComparisonReport.
    """
    comparison_data = {
        "generated_at": datetime.now().isoformat(),
        "baseline_summary": {},
        "cleaned_summary": {},
        "absolute_diff": {},
        "relative_diff": {},
        "sensitivity_analysis": sensitivity_analysis or {}
    }

    # Process datasets
    baseline_datasets = baseline_metrics.get("datasets", []) if baseline_metrics else []
    cleaned_datasets = cleaned_metrics.get("datasets", []) if cleaned_metrics else []

    # Create lookup for cleaned metrics by dataset name
    cleaned_map = {}
    for entry in cleaned_datasets:
        name = entry.get("dataset_name") or entry.get("dataset_id")
        if name:
            cleaned_map[name] = entry

    for b_entry in baseline_datasets:
        name = b_entry.get("dataset_name") or b_entry.get("dataset_id")
        if not name:
            continue

        c_entry = cleaned_map.get(name)

        # Extract key metrics
        base_tests = b_entry.get("analysis", {}).get("tests", {})
        clean_tests = c_entry.get("analysis", {}).get("tests", {}) if c_entry else {}

        # Calculate diffs for t-test
        base_p = base_tests.get("t_test", {}).get("p_value") if base_tests else None
        clean_p = clean_tests.get("t_test", {}).get("p_value") if clean_tests else None

        if base_p is not None and clean_p is not None:
            comparison_data["absolute_diff"][f"{name}_p_value"] = calculate_absolute_diff(base_p, clean_p)
            comparison_data["relative_diff"][f"{name}_p_value"] = calculate_relative_diff(base_p, clean_p)

        # Calculate diffs for regression R^2
        base_r2 = base_tests.get("regression", {}).get("r_squared") if base_tests else None
        clean_r2 = clean_tests.get("regression", {}).get("r_squared") if clean_tests else None

        if base_r2 is not None and clean_r2 is not None:
            comparison_data["absolute_diff"][f"{name}_r2"] = calculate_absolute_diff(base_r2, clean_r2)
            comparison_data["relative_diff"][f"{name}_r2"] = calculate_relative_diff(base_r2, clean_r2)

        # Summarize baseline and cleaned
        comparison_data["baseline_summary"][name] = {
            "p_value": base_p,
            "r_squared": base_r2
        }
        if c_entry:
            comparison_data["cleaned_summary"][name] = {
                "p_value": clean_p,
                "r_squared": clean_r2,
                "strategy": c_entry.get("strategy", "unknown")
            }

    return comparison_data

def create_comparison_report(
    baseline_metrics: Dict[str, Any],
    cleaned_metrics: Dict[str, Any],
    sensitivity_analysis: Optional[Dict[str, Any]] = None,
    output_path: str = "data/processed/comparison_report.json"
) -> ComparisonReport:
    """
    Create a ComparisonReport entity aggregating baseline, cleaned, and sensitivity analysis.
    """
    logger.info("Creating comparison report...")

    if not baseline_metrics:
        logger.error("Baseline metrics are missing. Cannot create comparison report.")
        raise ValueError("Baseline metrics are missing.")
    if not cleaned_metrics:
        logger.error("Cleaned metrics are missing. Cannot create comparison report.")
        raise ValueError("Cleaned metrics are missing.")

    aggregated = aggregate_metrics_for_comparison(baseline_metrics, cleaned_metrics, sensitivity_analysis)

    # Construct the ComparisonReport model
    report = ComparisonReport(
        baseline_metrics=baseline_metrics,
        cleaned_metrics=cleaned_metrics,
        absolute_diff=aggregated["absolute_diff"],
        relative_diff=aggregated["relative_diff"],
        sensitivity_analysis=aggregated["sensitivity_analysis"]
    )

    # Write to file
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report.model_dump(), f, indent=2, default=str)

    logger.info(f"Comparison report written to {output_path}")
    return report

def main():
    """Main entry point for T040."""
    # Setup logging with a default level if not provided
    try:
        logger = setup_logging()
    except TypeError:
        # Fallback if setup_logging requires args but none provided
        logger = setup_logging("INFO")

    logger.info("Starting T040: Create Comparison Report")

    config = Config()

    # Define paths
    baseline_path = "data/processed/baseline_metrics.json"
    cleaned_path = "data/processed/cleaned_metrics.json"
    sensitivity_path = "data/processed/sensitivity_analysis.json"
    output_path = "data/processed/comparison_report.json"

    # Load data
    baseline_metrics = load_baseline_metrics(baseline_path)
    cleaned_metrics = load_cleaned_metrics(cleaned_path)
    sensitivity_analysis = load_sensitivity_analysis(sensitivity_path)

    if not baseline_metrics:
        logger.error(f"Failed to load baseline metrics from {baseline_path}")
        sys.exit(1)

    if not cleaned_metrics:
        logger.error(f"Failed to load cleaned metrics from {cleaned_path}")
        sys.exit(1)

    # Create report
    try:
        report = create_comparison_report(
            baseline_metrics=baseline_metrics,
            cleaned_metrics=cleaned_metrics,
            sensitivity_analysis=sensitivity_analysis,
            output_path=output_path
        )
        logger.info("Comparison report created successfully.")
    except Exception as e:
        logger.error(f"Failed to create comparison report: {e}")
        sys.exit(1)

    return 0

if __name__ == "__main__":
    sys.exit(main())