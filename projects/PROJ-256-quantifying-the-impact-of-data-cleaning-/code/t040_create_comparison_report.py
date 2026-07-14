import os
import sys
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

# Import from local modules
from models import ComparisonReport, Dataset, CleaningStrategy, AnalysisResult
from utils import setup_logging

logger = setup_logging("INFO")

def load_json_file(filepath: str) -> Dict[str, Any]:
    """Load a JSON file and return its contents as a dictionary."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    with open(filepath, 'r') as f:
        return json.load(f)

def load_baseline_metrics(filepath: str = "data/processed/baseline_metrics.json") -> Dict[str, Any]:
    """Load baseline metrics from the specified file."""
    logger.info(f"Loading baseline metrics from {filepath}")
    return load_json_file(filepath)

def load_cleaned_metrics(filepath: str = "data/processed/cleaned_metrics.json") -> Dict[str, Any]:
    """Load cleaned metrics from the specified file."""
    logger.info(f"Loading cleaned metrics from {filepath}")
    return load_json_file(filepath)

def load_sensitivity_analysis(filepath: str = "data/processed/sensitivity_analysis.json") -> Optional[Dict[str, Any]]:
    """Load sensitivity analysis if it exists, otherwise return None."""
    if os.path.exists(filepath):
        logger.info(f"Loading sensitivity analysis from {filepath}")
        return load_json_file(filepath)
    else:
        logger.warning(f"Sensitivity analysis file not found at {filepath}. Skipping.")
        return None

def calculate_absolute_diff(baseline_val: float, cleaned_val: float) -> float:
    """Calculate the absolute difference between two values."""
    return abs(cleaned_val - baseline_val)

def calculate_relative_diff(baseline_val: float, cleaned_val: float) -> float:
    """Calculate the relative difference between two values."""
    if baseline_val == 0:
        return float('inf') if cleaned_val != 0 else 0.0
    return abs(cleaned_val - baseline_val) / abs(baseline_val)

def aggregate_metrics_for_comparison(baseline_metrics: Dict[str, Any], cleaned_metrics: Dict[str, Any]) -> Dict[str, Any]:
    """Aggregate baseline and cleaned metrics for comparison."""
    aggregated = {
        "baseline": {},
        "cleaned": {},
        "absolute_diff": {},
        "relative_diff": {}
    }

    # Process baseline metrics
    for dataset_name, metrics in baseline_metrics.get("datasets", {}).items():
        aggregated["baseline"][dataset_name] = metrics

    # Process cleaned metrics
    for dataset_name, metrics in cleaned_metrics.get("datasets", {}).items():
        aggregated["cleaned"][dataset_name] = metrics

    # Calculate differences
    for dataset_name in set(aggregated["baseline"].keys()) & set(aggregated["cleaned"].keys()):
        baseline_entry = aggregated["baseline"][dataset_name]
        cleaned_entry = aggregated["cleaned"][dataset_name]

        # Calculate p-value differences
        if "p_value" in baseline_entry and "p_value" in cleaned_entry:
            baseline_p = baseline_entry["p_value"]
            cleaned_p = cleaned_entry["p_value"]
            aggregated["absolute_diff"][f"{dataset_name}_p_value"] = calculate_absolute_diff(baseline_p, cleaned_p)
            aggregated["relative_diff"][f"{dataset_name}_p_value"] = calculate_relative_diff(baseline_p, cleaned_p)

        # Calculate CI width differences
        if "ci_width" in baseline_entry and "ci_width" in cleaned_entry:
            baseline_ci = baseline_entry["ci_width"]
            cleaned_ci = cleaned_entry["ci_width"]
            aggregated["absolute_diff"][f"{dataset_name}_ci_width"] = calculate_absolute_diff(baseline_ci, cleaned_ci)
            aggregated["relative_diff"][f"{dataset_name}_ci_width"] = calculate_relative_diff(baseline_ci, cleaned_ci)

        # Calculate effect size differences
        if "effect_size" in baseline_entry and "effect_size" in cleaned_entry:
            baseline_es = baseline_entry["effect_size"]
            cleaned_es = cleaned_entry["effect_size"]
            aggregated["absolute_diff"][f"{dataset_name}_effect_size"] = calculate_absolute_diff(baseline_es, cleaned_es)
            aggregated["relative_diff"][f"{dataset_name}_effect_size"] = calculate_relative_diff(baseline_es, cleaned_es)

    return aggregated

def create_comparison_report(
    baseline_metrics: Dict[str, Any],
    cleaned_metrics: Dict[str, Any],
    sensitivity_analysis: Optional[Dict[str, Any]] = None,
    output_path: str = "data/processed/comparison_report.json"
) -> ComparisonReport:
    """Create a ComparisonReport entity with all required fields."""
    logger.info("Creating comparison report...")

    # Aggregate metrics
    aggregated = aggregate_metrics_for_comparison(baseline_metrics, cleaned_metrics)

    # Construct the report data
    report_data = {
        "baseline_metrics": baseline_metrics,
        "cleaned_metrics": cleaned_metrics,
        "absolute_diff": aggregated["absolute_diff"],
        "relative_diff": aggregated["relative_diff"],
        "sensitivity_analysis": sensitivity_analysis,
        "created_at": datetime.utcnow().isoformat()
    }

    # Save to file
    with open(output_path, 'w') as f:
        json.dump(report_data, f, indent=2, default=str)
    logger.info(f"Comparison report saved to {output_path}")

    # Create and return the ComparisonReport entity
    # Note: Since ComparisonReport is a Pydantic model expecting specific fields,
    # we construct it with the aggregated data.
    # The model definition in models.py expects specific structures, so we adapt.
    return ComparisonReport(
        baseline_metrics=baseline_metrics,
        cleaned_metrics=cleaned_metrics,
        absolute_diff=aggregated["absolute_diff"],
        relative_diff=aggregated["relative_diff"],
        sensitivity_analysis=sensitivity_analysis
    )

def main():
    """Main entry point for creating the comparison report."""
    logger.info("Starting comparison report generation...")

    try:
        # Load metrics
        baseline_metrics = load_baseline_metrics()
        cleaned_metrics = load_cleaned_metrics()
        sensitivity_analysis = load_sensitivity_analysis()

        # Create the report
        report = create_comparison_report(
            baseline_metrics=baseline_metrics,
            cleaned_metrics=cleaned_metrics,
            sensitivity_analysis=sensitivity_analysis,
            output_path="data/processed/comparison_report.json"
        )

        logger.info("Comparison report generated successfully.")
        return 0

    except FileNotFoundError as e:
        logger.error(f"Missing required input file: {e}")
        return 1
    except Exception as e:
        logger.error(f"Error generating comparison report: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())