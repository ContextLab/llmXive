import os
import sys
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from utils import setup_logging
from config import Config
from models import ComparisonReport
from reporting import load_json_file, save_json_file

logger = setup_logging("INFO")

def load_baseline_metrics(filepath: str = "data/processed/baseline_metrics.json") -> Dict[str, Any]:
    if not os.path.exists(filepath):
        logger.error(f"Baseline metrics file not found: {filepath}")
        return {}
    return load_json_file(filepath)

def load_cleaned_metrics(filepath: str = "data/processed/cleaned_metrics.json") -> Dict[str, Any]:
    if not os.path.exists(filepath):
        logger.error(f"Cleaned metrics file not found: {filepath}")
        return {}
    return load_json_file(filepath)

def load_sensitivity_analysis(filepath: str = "data/processed/sensitivity_analysis.json") -> Optional[Dict[str, Any]]:
    if not os.path.exists(filepath):
        logger.warning(f"Sensitivity analysis file not found: {filepath}. Proceeding without it.")
        return None
    return load_json_file(filepath)

def calculate_absolute_diff(baseline_val: float, cleaned_val: float) -> float:
    if baseline_val is None or cleaned_val is None:
        return 0.0
    return abs(cleaned_val - baseline_val)

def calculate_relative_diff(baseline_val: float, cleaned_val: float) -> float:
    if baseline_val is None or baseline_val == 0:
        return 0.0
    return (cleaned_val - baseline_val) / abs(baseline_val)

def aggregate_metrics_for_comparison(
    baseline_metrics: Dict[str, Any],
    cleaned_metrics: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Aggregates metrics from baseline and cleaned datasets to calculate diffs.
    Handles both dict and list structures for 'datasets'.
    """
    baseline_datasets = baseline_metrics.get("datasets", [])
    cleaned_datasets = cleaned_metrics.get("datasets", [])

    # Normalize to list if it's a single dict
    if isinstance(baseline_datasets, dict):
        baseline_datasets = [baseline_datasets]
    if isinstance(cleaned_datasets, dict):
        cleaned_datasets = [cleaned_datasets]

    comparison_results = []

    # Create a map for cleaned metrics by dataset name for easier lookup
    cleaned_map = {}
    for cd in cleaned_datasets:
        name = cd.get("dataset_name") or cd.get("dataset_id")
        if name:
            cleaned_map[name] = cd

    for bd in baseline_datasets:
        name = bd.get("dataset_name") or bd.get("dataset_id")
        cd = cleaned_map.get(name)

        if not cd:
            logger.warning(f"No cleaned metrics found for baseline dataset: {name}")
            continue

        # Extract p-values (assuming first test for simplicity if multiple exist)
        # Structure check: bd['analysis']['t_test']['p_value']
        baseline_p = None
        cleaned_p = None

        try:
            baseline_tests = bd.get("analysis", {}).get("t_test", {})
            if isinstance(baseline_tests, dict):
                baseline_p = baseline_tests.get("p_value")
            elif isinstance(baseline_tests, list) and len(baseline_tests) > 0:
                baseline_p = baseline_tests[0].get("p_value")

            cleaned_tests = cd.get("analysis", {}).get("t_test", {})
            if isinstance(cleaned_tests, dict):
                cleaned_p = cleaned_tests.get("p_value")
            elif isinstance(cleaned_tests, list) and len(cleaned_tests) > 0:
                cleaned_p = cleaned_tests[0].get("p_value")
        except Exception as e:
            logger.warning(f"Error extracting p-values for {name}: {e}")

        abs_diff = calculate_absolute_diff(baseline_p, cleaned_p)
        rel_diff = calculate_relative_diff(baseline_p, cleaned_p)

        comparison_results.append({
            "dataset_name": name,
            "baseline_p_value": baseline_p,
            "cleaned_p_value": cleaned_p,
            "absolute_diff": round(abs_diff, 6),
            "relative_diff": round(rel_diff, 6),
            "baseline_metrics": bd.get("analysis", {}),
            "cleaned_metrics": cd.get("analysis", {})
        })

    return {
        "timestamp": datetime.now().isoformat(),
        "comparison_results": comparison_results,
        "total_comparisons": len(comparison_results)
    }

def create_comparison_report(
    baseline_metrics: Dict[str, Any],
    cleaned_metrics: Dict[str, Any],
    sensitivity_analysis: Optional[Dict[str, Any]]
) -> ComparisonReport:
    logger.info("Generating comparison report...")

    aggregated = aggregate_metrics_for_comparison(baseline_metrics, cleaned_metrics)

    report_data = {
        "baseline_metrics": baseline_metrics,
        "cleaned_metrics": cleaned_metrics,
        "absolute_diff": [r["absolute_diff"] for r in aggregated["comparison_results"]],
        "relative_diff": [r["relative_diff"] for r in aggregated["comparison_results"]],
        "sensitivity_analysis": sensitivity_analysis or {},
        "aggregated_details": aggregated
    }

    # Save raw JSON
    save_json_file(report_data, output_path)
    logger.info(f"Comparison report saved to {output_path}")

    # Create Pydantic model instance for type safety/return
    # Note: We map the aggregated data into the model fields.
    # Since ComparisonReport expects specific types, we adapt the dict.
    try:
        report = ComparisonReport(
            baseline_metrics=baseline_metrics,
            cleaned_metrics=cleaned_metrics,
            absolute_diff=aggregated["comparison_results"], # Storing full details
            relative_diff=aggregated["comparison_results"], # Storing full details
            sensitivity_analysis=sensitivity_analysis or {}
        )
    except Exception as e:
        logger.error(f"Failed to create ComparisonReport model instance: {e}")
        # Fallback: create a minimal valid report if model fails
        report = ComparisonReport(
            baseline_metrics={},
            cleaned_metrics={},
            absolute_diff=[],
            relative_diff=[],
            sensitivity_analysis={}
        )

    return report

def main():
    logger.info("Starting T040: Create Comparison Report")

    config = Config()
    baseline_path = config.get("BASELINE_METRICS_PATH", "data/processed/baseline_metrics.json")
    cleaned_path = config.get("CLEANED_METRICS_PATH", "data/processed/cleaned_metrics.json")
    sensitivity_path = config.get("SENSITIVITY_ANALYSIS_PATH", "data/processed/sensitivity_analysis.json")
    output_path = config.get("COMPARISON_REPORT_PATH", "data/processed/comparison_report.json")

    baseline_metrics = load_baseline_metrics(baseline_path)
    cleaned_metrics = load_cleaned_metrics(cleaned_path)
    sensitivity_analysis = load_sensitivity_analysis(sensitivity_path)

    if not baseline_metrics or not cleaned_metrics:
        logger.error("Missing baseline or cleaned metrics. Cannot generate report.")
        sys.exit(1)

    report = create_comparison_report(
        baseline_metrics,
        cleaned_metrics,
        sensitivity_analysis,
        output_path
    )

    logger.info(f"Task T040 completed successfully. Report: {output_path}")

if __name__ == "__main__":
    main()