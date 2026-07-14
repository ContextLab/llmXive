"""
T040: Create comparison report (ComparisonReport entity) with baseline_metrics, cleaned_metrics, absolute_diff, relative_diff, sensitivity_analysis.

This script aggregates metrics from baseline and cleaned analyses, calculates differences,
and generates a structured ComparisonReport artifact.
"""
import os
import sys
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

# Import from local modules
from utils import setup_logging
from models import ComparisonReport
from reporting import load_json_file, save_json_file, calculate_p_value_shift, compute_ci_width_change, compute_effect_size_delta
from utils import setup_logging

# Configure logging
logger = setup_logging("INFO")

def load_baseline_metrics(filepath: str) -> Dict[str, Any]:
    """Load baseline metrics from JSON file."""
    if not os.path.exists(filepath):
        logger.warning(f"Baseline metrics file not found: {filepath}")
        return None
    return load_json_file(filepath)

def load_cleaned_metrics(filepath: str) -> Dict[str, Any]:
    """Load cleaned metrics from JSON file."""
    if not os.path.exists(filepath):
        logger.warning(f"Cleaned metrics file not found: {filepath}")
        return None
    return load_json_file(filepath)

def load_sensitivity_analysis(filepath: str) -> Dict[str, Any]:
    """Load sensitivity analysis results from JSON file."""
    if not os.path.exists(filepath):
        logger.warning(f"Sensitivity analysis file not found: {filepath}. Proceeding with empty analysis.")
        return {}
    return load_json_file(filepath)

def calculate_absolute_diff(base_val: float, clean_val: float) -> float:
    """Calculate absolute difference between two values."""
    return abs(clean_val - base_val)

def calculate_relative_diff(base_val: float, clean_val: float) -> float:
    """Calculate relative difference (percentage change) between two values."""
    if base_val == 0:
        return 0.0 if clean_val == 0 else float('inf')
    return (clean_val - base_val) / base_val

def aggregate_metrics_for_comparison(
    baseline_metrics: Dict[str, Any],
    cleaned_metrics: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Aggregate metrics from baseline and cleaned datasets for comparison.
    Returns a list of comparison records.
    """
    comparisons = []

    baseline_datasets = baseline_metrics.get("datasets", [])
    cleaned_datasets = cleaned_metrics.get("datasets", [])

    # Create a map of cleaned datasets by name
    cleaned_map = {}
    for entry in cleaned_datasets:
        name = entry.get("dataset_name") or entry.get("dataset_id")
        if name:
            cleaned_map[name] = entry

    for base_entry in baseline_datasets:
        name = base_entry.get("dataset_name") or base_entry.get("dataset_id")
        if not name:
            continue

        clean_entry = cleaned_map.get(name)
        if not clean_entry:
            logger.warning(f"No cleaned metrics found for baseline dataset: {name}")
            continue

        # Extract p-values
        base_p = base_entry.get("t_test", {}).get("p_value") or base_entry.get("p_value")
        clean_p = clean_entry.get("t_test", {}).get("p_value") or clean_entry.get("p_value")

        # Extract CI widths
        base_ci = base_entry.get("t_test", {}).get("ci")
        clean_ci = clean_entry.get("t_test", {}).get("ci")

        base_ci_width = (base_ci[1] - base_ci[0]) if base_ci and len(base_ci) == 2 else None
        clean_ci_width = (clean_ci[1] - clean_ci[0]) if clean_ci and len(clean_ci) == 2 else None

        # Extract effect sizes
        base_es = base_entry.get("effect_size", {}).get("cohens_d") or base_entry.get("cohens_d")
        clean_es = clean_entry.get("effect_size", {}).get("cohens_d") or clean_entry.get("cohens_d")

        comparison = {
            "dataset_name": name,
            "baseline": {
                "p_value": base_p,
                "ci_width": base_ci_width,
                "effect_size": base_es
            },
            "cleaned": {
                "p_value": clean_p,
                "ci_width": clean_ci_width,
                "effect_size": clean_es
            }
        }

        # Calculate differences
        if base_p is not None and clean_p is not None:
            comparison["absolute_diff"] = {
                "p_value": calculate_absolute_diff(base_p, clean_p),
                "ci_width": calculate_absolute_diff(base_ci_width, clean_ci_width) if base_ci_width is not None and clean_ci_width is not None else None,
                "effect_size": calculate_absolute_diff(base_es, clean_es) if base_es is not None and clean_es is not None else None
            }
            comparison["relative_diff"] = {
                "p_value": calculate_relative_diff(base_p, clean_p),
                "ci_width": calculate_relative_diff(base_ci_width, clean_ci_width) if base_ci_width is not None and clean_ci_width is not None else None,
                "effect_size": calculate_relative_diff(base_es, clean_es) if base_es is not None and clean_es is not None else None
            }

        comparisons.append(comparison)

    return comparisons

def create_comparison_report(
    baseline_metrics: Dict[str, Any],
    cleaned_metrics: Dict[str, Any],
    sensitivity_analysis: Dict[str, Any],
    output_path: str
) -> bool:
    """
    Create a ComparisonReport entity containing all comparison data.
    Writes the report to the specified JSON path.
    """
    comparisons = aggregate_metrics_for_comparison(baseline_metrics, cleaned_metrics)

    # Calculate summary statistics
    total_datasets = len(comparisons)
    significant_changes = 0
    p_value_shifts = []
    ci_width_changes = []
    effect_size_changes = []

    for comp in comparisons:
        abs_diff = comp.get("absolute_diff", {})
        p_shift = abs_diff.get("p_value")
        if p_shift is not None:
            p_value_shifts.append(p_shift)
            # Consider significant if p-value changed order of magnitude or crossed 0.05 threshold
            base_p = comp["baseline"]["p_value"]
            clean_p = comp["cleaned"]["p_value"]
            if (base_p < 0.05 and clean_p >= 0.05) or (base_p >= 0.05 and clean_p < 0.05):
                significant_changes += 1

        ci_change = abs_diff.get("ci_width")
        if ci_change is not None:
            ci_width_changes.append(ci_change)

        es_change = abs_diff.get("effect_size")
        if es_change is not None:
            effect_size_changes.append(es_change)

    report_data = {
        "report_metadata": {
            "created_at": datetime.now().isoformat(),
            "version": "1.0",
            "description": "Comparison of baseline vs cleaned dataset statistical metrics"
        },
        "summary": {
            "total_datasets_analyzed": total_datasets,
            "significant_significance_changes": significant_changes,
            "average_p_value_shift": sum(p_value_shifts) / len(p_value_shifts) if p_value_shifts else None,
            "average_ci_width_change": sum(ci_width_changes) / len(ci_width_changes) if ci_width_changes else None,
            "average_effect_size_change": sum(effect_size_changes) / len(effect_size_changes) if effect_size_changes else None
        },
        "sensitivity_analysis": sensitivity_analysis,
        "comparisons": comparisons
    }

    try:
        save_json_file(report_data, output_path)
        logger.info(f"Comparison report successfully written to: {output_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to write comparison report: {e}")
        return False

def main():
    """Main entry point for T040: Create comparison report."""
    logger.info("Starting T040: Create comparison report")

    # Configuration paths
    baseline_path = os.getenv("BASELINE_METRICS_PATH", "data/processed/baseline_metrics.json")
    cleaned_path = os.getenv("CLEANED_METRICS_PATH", "data/processed/cleaned_metrics.json")
    sensitivity_path = os.getenv("SENSITIVITY_ANALYSIS_PATH", "data/processed/sensitivity_analysis.json")
    output_path = os.getenv("COMPARISON_REPORT_PATH", "data/processed/comparison_report.json")

    # Load data
    logger.info(f"Loading baseline metrics from: {baseline_path}")
    baseline_metrics = load_baseline_metrics(baseline_path)

    logger.info(f"Loading cleaned metrics from: {cleaned_path}")
    cleaned_metrics = load_cleaned_metrics(cleaned_path)

    logger.info(f"Loading sensitivity analysis from: {sensitivity_path}")
    sensitivity_analysis = load_sensitivity_analysis(sensitivity_path)

    # Validate inputs
    if not baseline_metrics or not baseline_metrics.get("datasets"):
        logger.error("Baseline metrics are missing or empty. Cannot generate comparison report.")
        sys.exit(1)

    if not cleaned_metrics or not cleaned_metrics.get("datasets"):
        logger.error("Cleaned metrics are missing or empty. Cannot generate comparison report.")
        sys.exit(1)

    # Create report
    logger.info("Generating comparison report...")
    success = create_comparison_report(
        baseline_metrics,
        cleaned_metrics,
        sensitivity_analysis,
        output_path
    )

    if success:
        logger.info("T040 completed successfully.")
        sys.exit(0)
    else:
        logger.error("T040 failed to generate report.")
        sys.exit(1)

if __name__ == "__main__":
    main()