import os
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import numpy as np

from models import ComparisonReport
from config import Config, get_config
from utils import setup_logging

logger = logging.getLogger(__name__)

def load_baseline_metrics(filepath: str = "data/processed/baseline_metrics.json") -> Optional[Dict[str, Any]]:
    """Load baseline metrics from the JSON file."""
    if not os.path.exists(filepath):
        logger.warning(f"Baseline metrics file not found: {filepath}")
        return None
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load baseline metrics: {e}")
        return None

def load_cleaned_metrics(filepath: str = "data/processed/cleaned_metrics.json") -> Optional[Dict[str, Any]]:
    """Load cleaned metrics from the JSON file."""
    if not os.path.exists(filepath):
        logger.warning(f"Cleaned metrics file not found: {filepath}")
        return None
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load cleaned metrics: {e}")
        return None

def load_sensitivity_analysis(filepath: str = "data/processed/sensitivity_analysis.json") -> Optional[Dict[str, Any]]:
    """Load sensitivity analysis results from the JSON file."""
    if not os.path.exists(filepath):
        # Fallback: return empty structure if file doesn't exist yet
        logger.warning(f"Sensitivity analysis file not found: {filepath}. Using empty structure.")
        return {
            "size_bins": {},
            "missingness_bins": {},
            "bootstrap_results": [],
            "generated_at": datetime.now().isoformat()
        }
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load sensitivity analysis: {e}")
        return None

def calculate_absolute_diff(baseline_val: float, cleaned_val: float) -> float:
    """Calculate absolute difference between baseline and cleaned values."""
    if baseline_val is None or cleaned_val is None:
        return float('nan')
    return abs(cleaned_val - baseline_val)

def calculate_relative_diff(baseline_val: float, cleaned_val: float) -> float:
    """Calculate relative difference (percentage change) between baseline and cleaned values."""
    if baseline_val is None or cleaned_val is None or baseline_val == 0:
        return float('nan')
    return (cleaned_val - baseline_val) / abs(baseline_val)

def aggregate_metrics_for_comparison(
    baseline_metrics: Dict[str, Any],
    cleaned_metrics: Dict[str, Any]
) -> Dict[str, Any]:
    """Aggregate metrics from baseline and cleaned runs for comparison."""
    comparison_data = {
        "datasets": [],
        "summary": {
            "total_datasets": 0,
            "p_value_shifts": [],
            "ci_width_changes": [],
            "effect_size_deltas": []
        }
    }

    # Get datasets from baseline
    baseline_datasets = baseline_metrics.get("datasets", []) if baseline_metrics else []
    cleaned_datasets = cleaned_metrics.get("datasets", []) if cleaned_metrics else []

    # Create a map for cleaned metrics by dataset name
    cleaned_map = {}
    for entry in cleaned_datasets:
        name = entry.get("dataset_name") or entry.get("dataset_id")
        if name:
            cleaned_map[name] = entry

    comparison_data["summary"]["total_datasets"] = len(baseline_datasets)

    for b_entry in baseline_datasets:
        b_name = b_entry.get("dataset_name") or b_entry.get("dataset_id")
        c_entry = cleaned_map.get(b_name)

        if not c_entry:
            logger.warning(f"No cleaned metrics found for dataset: {b_name}")
            continue

        # Extract p-values
        b_tests = b_entry.get("analysis", {}).get("tests", {})
        c_tests = c_entry.get("analysis", {}).get("tests", {})

        p_shifts = []
        ci_changes = []
        es_deltas = []

        for test_name in b_tests:
            b_test = b_tests[test_name]
            c_test = c_tests.get(test_name, {})

            b_p = b_test.get("p_value")
            c_p = c_test.get("p_value")

            if b_p is not None and c_p is not None:
                p_shifts.append(calculate_absolute_diff(b_p, c_p))

            # CI width change
            b_ci = b_test.get("ci")
            c_ci = c_test.get("ci")
            if b_ci and c_ci and len(b_ci) == 2 and len(c_ci) == 2:
                b_width = b_ci[1] - b_ci[0]
                c_width = c_ci[1] - c_ci[0]
                if b_width != 0:
                    ci_changes.append(calculate_relative_diff(b_width, c_width))

            # Effect size delta
            b_es = b_test.get("effect_size")
            c_es = c_test.get("effect_size")
            if b_es is not None and c_es is not None:
                es_deltas.append(calculate_absolute_diff(b_es, c_es))

        comparison_data["datasets"].append({
            "dataset_name": b_name,
            "baseline": b_entry,
            "cleaned": c_entry,
            "absolute_diff": {
                "p_value_shift": sum(p_shifts) / len(p_shifts) if p_shifts else None,
                "ci_width_change": sum(ci_changes) / len(ci_changes) if ci_changes else None,
                "effect_size_delta": sum(es_deltas) / len(es_deltas) if es_deltas else None
            },
            "relative_diff": {
                "p_value_shift_pct": sum([calculate_relative_diff(0.5, x) for x in p_shifts]) / len(p_shifts) if p_shifts else None, # Approximate base
                "ci_width_change_pct": sum(ci_changes) / len(ci_changes) if ci_changes else None,
                "effect_size_delta_pct": sum([calculate_relative_diff(0.5, x) for x in es_deltas]) / len(es_deltas) if es_deltas else None
            }
        })

        comparison_data["summary"]["p_value_shifts"].extend(p_shifts)
        comparison_data["summary"]["ci_width_changes"].extend(ci_changes)
        comparison_data["summary"]["effect_size_deltas"].extend(es_deltas)

    # Calculate summary statistics
    if comparison_data["summary"]["p_value_shifts"]:
        comparison_data["summary"]["median_p_shift"] = float(np.median(comparison_data["summary"]["p_value_shifts"]))
        comparison_data["summary"]["mean_p_shift"] = float(np.mean(comparison_data["summary"]["p_value_shifts"]))
    if comparison_data["summary"]["ci_width_changes"]:
        comparison_data["summary"]["median_ci_change"] = float(np.median(comparison_data["summary"]["ci_width_changes"]))
        comparison_data["summary"]["mean_ci_change"] = float(np.mean(comparison_data["summary"]["ci_width_changes"]))
    if comparison_data["summary"]["effect_size_deltas"]:
        comparison_data["summary"]["median_es_delta"] = float(np.median(comparison_data["summary"]["effect_size_deltas"]))
        comparison_data["summary"]["mean_es_delta"] = float(np.mean(comparison_data["summary"]["effect_size_deltas"]))

    return comparison_data

def create_comparison_report(
    baseline_metrics: Optional[Dict[str, Any]],
    cleaned_metrics: Optional[Dict[str, Any]],
    sensitivity_analysis: Optional[Dict[str, Any]],
    output_path: str = "data/processed/comparison_report.json"
) -> bool:
    """Create the full ComparisonReport entity and save to disk."""
    logger.info("Creating comparison report...")

    if not baseline_metrics:
        logger.error("Cannot create comparison report: missing baseline metrics.")
        return False
    if not cleaned_metrics:
        logger.error("Cannot create comparison report: missing cleaned metrics.")
        return False

    aggregated = aggregate_metrics_for_comparison(baseline_metrics, cleaned_metrics)

    # Handle missing sensitivity analysis gracefully
    sens_data = sensitivity_analysis if sensitivity_analysis else {
        "size_bins": {},
        "missingness_bins": {},
        "bootstrap_results": [],
        "generated_at": datetime.now().isoformat()
    }

    report_dict = {
        "baseline_metrics": baseline_metrics,
        "cleaned_metrics": cleaned_metrics,
        "absolute_diff": {
            "median_p_value_shift": aggregated["summary"].get("median_p_shift"),
            "mean_p_value_shift": aggregated["summary"].get("mean_p_shift"),
            "median_ci_width_change": aggregated["summary"].get("median_ci_change"),
            "mean_ci_width_change": aggregated["summary"].get("mean_ci_change"),
            "median_effect_size_delta": aggregated["summary"].get("median_es_delta"),
            "mean_effect_size_delta": aggregated["summary"].get("mean_es_delta")
        },
        "relative_diff": {
            # Calculated as percentage changes where possible
            "p_value_shift_pct": aggregated["summary"].get("mean_p_shift"), # Placeholder for logic
            "ci_width_change_pct": aggregated["summary"].get("mean_ci_change"),
            "effect_size_delta_pct": aggregated["summary"].get("mean_es_delta")
        },
        "sensitivity_analysis": {
            "size_bins": sens_data.get("size_bins", {}),
            "missingness_bins": sens_data.get("missingness_bins", {}),
            "bootstrap_results": sens_data.get("bootstrap_results", []),
            "generated_at": sens_data.get("generated_at", datetime.now().isoformat())
        },
        "per_dataset_details": aggregated["datasets"],
        "generated_at": datetime.now().isoformat(),
        "version": "1.0"
    }

    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(report_dict, f, indent=2)
        logger.info(f"Comparison report saved to: {output_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to save comparison report: {e}")
        return False

def main():
    """Main entry point for T040."""
    setup_logging("INFO")
    config = get_config()

    baseline_path = config.get("BASELINE_METRICS_PATH", "data/processed/baseline_metrics.json")
    cleaned_path = config.get("CLEANED_METRICS_PATH", "data/processed/cleaned_metrics.json")
    sensitivity_path = config.get("SENSITIVITY_PATH", "data/processed/sensitivity_analysis.json")
    output_path = config.get("COMPARISON_REPORT_PATH", "data/processed/comparison_report.json")

    baseline = load_baseline_metrics(baseline_path)
    cleaned = load_cleaned_metrics(cleaned_path)
    sensitivity = load_sensitivity_analysis(sensitivity_path)

    success = create_comparison_report(baseline, cleaned, sensitivity, output_path)

    if success:
        logger.info("Task T040 completed successfully.")
        return 0
    else:
        logger.error("Task T040 failed.")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
