"""
Task T040: Create comparison report (ComparisonReport entity) with baseline_metrics,
cleaned_metrics, absolute_diff, relative_diff, sensitivity_analysis.

This script aggregates the results from baseline analysis and cleaned variants,
computes differences, and generates a structured ComparisonReport artifact.
"""
import os
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import numpy as np

# Import models to construct the report entity
from models import ComparisonReport, Dataset, CleaningStrategy, AnalysisResult
from reporting import load_json_file, calculate_p_value_shift, compute_ci_width_change, compute_effect_size_delta
from utils import setup_logging, compute_file_checksum

logger = logging.getLogger(__name__)

def load_baseline_metrics(filepath: str = "data/processed/baseline_metrics.json") -> Optional[Dict[str, Any]]:
    """Load baseline metrics from the generated JSON file."""
    if not os.path.exists(filepath):
        logger.warning(f"Baseline metrics file not found at {filepath}. Skipping comparison report generation.")
        return None
    return load_json_file(filepath)

def load_cleaned_metrics(filepath: str = "data/processed/cleaned_metrics.json") -> Optional[Dict[str, Any]]:
    """Load cleaned metrics from the generated JSON file."""
    if not os.path.exists(filepath):
        logger.warning(f"Cleaned metrics file not found at {filepath}. Skipping comparison report generation.")
        return None
    return load_json_file(filepath)

def load_sensitivity_analysis(filepath: str = "data/processed/sensitivity_analysis.json") -> Optional[Dict[str, Any]]:
    """Load sensitivity analysis results if available."""
    if not os.path.exists(filepath):
        logger.info(f"Sensitivity analysis file not found at {filepath}. Proceeding without it.")
        return None
    return load_json_file(filepath)

def calculate_absolute_diff(base_val: float, clean_val: float) -> float:
    """Calculate absolute difference between baseline and cleaned values."""
    if base_val is None or clean_val is None:
        return 0.0
    return abs(clean_val - base_val)

def calculate_relative_diff(base_val: float, clean_val: float) -> float:
    """Calculate relative difference (percentage change) between baseline and cleaned values."""
    if base_val is None or clean_val is None or base_val == 0:
        return 0.0
    return (clean_val - base_val) / abs(base_val)

def aggregate_metrics_for_comparison(
    baseline_data: Dict[str, Any],
    cleaned_data: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Aggregate baseline and cleaned metrics to compute diffs.
    Returns a list of comparison entries.
    """
    comparisons = []

    # Ensure we have datasets to compare
    base_datasets = baseline_data.get('datasets', []) if baseline_data else []
    clean_datasets = cleaned_data.get('datasets', []) if cleaned_data else []

    # Create a map of cleaned datasets for easy lookup
    clean_map = {}
    for entry in clean_datasets:
        key = (entry.get('dataset_name'), entry.get('strategy'))
        clean_map[key] = entry

    for base_entry in base_datasets:
        dataset_name = base_entry.get('dataset_name')
        base_analysis = base_entry.get('analysis', {})
        
        # Extract baseline metrics
        base_p = base_analysis.get('t_test', {}).get('p_value')
        base_ci_width = base_analysis.get('t_test', {}).get('ci_width')
        base_effect_size = base_analysis.get('t_test', {}).get('effect_size')

        comparison_entry = {
            "dataset_name": dataset_name,
            "baseline": base_entry,
            "cleaned_variants": []
        }

        # Compare against each cleaning strategy applied to this dataset
        for strategy_name in ["outlier_removal", "mean_imputation", "median_imputation", "knn_imputation"]:
            key = (dataset_name, strategy_name)
            if key in clean_map:
                clean_entry = clean_map[key]
                clean_analysis = clean_entry.get('analysis', {})
                
                clean_p = clean_analysis.get('t_test', {}).get('p_value')
                clean_ci_width = clean_analysis.get('t_test', {}).get('ci_width')
                clean_effect_size = clean_analysis.get('t_test', {}).get('effect_size')

                p_shift = calculate_p_value_shift(base_p, clean_p) if base_p and clean_p else 0.0
                ci_change = compute_ci_width_change(base_ci_width, clean_ci_width) if base_ci_width and clean_ci_width else 0.0
                es_delta = compute_effect_size_delta(base_effect_size, clean_effect_size) if base_effect_size and clean_effect_size else 0.0

                comparison_entry["cleaned_variants"].append({
                    "strategy": strategy_name,
                    "metrics": {
                        "p_value_shift": p_shift,
                        "ci_width_change": ci_change,
                        "effect_size_delta": es_delta,
                        "absolute_diff_p": calculate_absolute_diff(base_p, clean_p),
                        "relative_diff_p": calculate_relative_diff(base_p, clean_p)
                    }
                })

        comparisons.append(comparison_entry)

    return comparisons

def create_comparison_report(
    baseline_metrics: Dict[str, Any],
    cleaned_metrics: Dict[str, Any],
    sensitivity_analysis: Optional[Dict[str, Any]] = None,
    output_path: str = "data/processed/comparison_report.json"
) -> ComparisonReport:
    """
    Create the ComparisonReport entity with all required fields.
    """
    logger.info("Aggregating metrics for comparison report...")
    comparisons = aggregate_metrics_for_comparison(baseline_metrics, cleaned_metrics)

    # Calculate summary statistics
    total_p_shifts = []
    total_ci_changes = []
    
    for comp in comparisons:
        for variant in comp.get("cleaned_variants", []):
            metrics = variant.get("metrics", {})
            if metrics.get("p_value_shift") is not None:
                total_p_shifts.append(metrics["p_value_shift"])
            if metrics.get("ci_width_change") is not None:
                total_ci_changes.append(metrics["ci_width_change"])

    avg_p_shift = float(np.mean(total_p_shifts)) if total_p_shifts else 0.0
    avg_ci_change = float(np.mean(total_ci_changes)) if total_ci_changes else 0.0
    max_p_shift = float(np.max(total_p_shifts)) if total_p_shifts else 0.0

    report_data = {
        "report_id": "CMP-001",
        "generated_at": datetime.now().isoformat(),
        "baseline_metrics_path": "data/processed/baseline_metrics.json",
        "cleaned_metrics_path": "data/processed/cleaned_metrics.json",
        "summary": {
            "total_datasets_analyzed": len(comparisons),
            "average_p_value_shift": avg_p_shift,
            "average_ci_width_change": avg_ci_change,
            "max_p_value_shift": max_p_shift
        },
        "detailed_comparisons": comparisons,
        "sensitivity_analysis": sensitivity_analysis
    }

    # Write to file
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report_data, f, indent=2)
    
    logger.info(f"Comparison report written to {output_path}")

    # Construct the Pydantic model for return
    # Note: We are constructing a simplified version for the return type
    # The full data is in the JSON file
    return ComparisonReport(
        report_id="CMP-001",
        baseline_metrics=baseline_metrics,
        cleaned_metrics=cleaned_metrics,
        absolute_diff=avg_p_shift, # Simplified aggregate
        relative_diff=avg_p_shift / 0.05 if avg_p_shift != 0 else 0.0, # Simplified relative to alpha
        sensitivity_analysis=sensitivity_analysis
    )

def main():
    """Main entry point for Task T040."""
    setup_logging("INFO")
    logger.info("Starting Task T040: Create Comparison Report")

    baseline = load_baseline_metrics()
    cleaned = load_cleaned_metrics()
    sensitivity = load_sensitivity_analysis()

    if not baseline:
        logger.error("Cannot proceed without baseline metrics. Ensure T012/T013 have run.")
        return 1
    
    if not cleaned:
        logger.error("Cannot proceed without cleaned metrics. Ensure T023 has run.")
        return 1

    try:
        report = create_comparison_report(baseline, cleaned, sensitivity)
        logger.info(f"Successfully created comparison report: {report.report_id}")
        return 0
    except Exception as e:
        logger.exception(f"Failed to create comparison report: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
