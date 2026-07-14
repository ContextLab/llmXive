import os
import sys
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from utils import setup_logging
from config import Config, get_config
from models import ComparisonReport, AnalysisResult, Dataset, CleaningStrategy

# Ensure setup_logging is tolerant of all call signatures
# (Already handled in utils.py, but we ensure import is correct here)

def load_json_file(filepath: str) -> Dict[str, Any]:
    """Load a JSON file and return its contents as a dictionary."""
    with open(filepath, 'r') as f:
        return json.load(f)

def load_baseline_metrics(filepath: str = "data/processed/baseline_metrics.json") -> Dict[str, Any]:
    """Load baseline metrics from the specified file."""
    if not os.path.exists(filepath):
        logging.warning(f"Baseline metrics file not found: {filepath}")
        return {}
    return load_json_file(filepath)

def load_cleaned_metrics(filepath: str = "data/processed/cleaned_metrics.json") -> Dict[str, Any]:
    """Load cleaned metrics from the specified file."""
    if not os.path.exists(filepath):
        logging.warning(f"Cleaned metrics file not found: {filepath}")
        return {}
    return load_json_file(filepath)

def load_sensitivity_analysis(filepath: str = "data/processed/sensitivity_analysis.json") -> Optional[Dict[str, Any]]:
    """Load sensitivity analysis data if it exists."""
    if not os.path.exists(filepath):
        logging.info(f"Sensitivity analysis file not found: {filepath}. Skipping.")
        return None
    return load_json_file(filepath)

def calculate_absolute_diff(base_val: float, clean_val: float) -> float:
    """Calculate the absolute difference between two values."""
    return abs(clean_val - base_val)

def calculate_relative_diff(base_val: float, clean_val: float) -> float:
    """Calculate the relative difference (percentage change) between two values."""
    if base_val == 0:
        return float('inf') if clean_val != 0 else 0.0
    return (clean_val - base_val) / base_val

def aggregate_metrics_for_comparison(
    baseline_metrics: Dict[str, Any],
    cleaned_metrics: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Aggregate metrics from baseline and cleaned datasets to compute
    absolute and relative differences for p-values, CI widths, and effect sizes.
    """
    comparison_data = {
        "datasets": [],
        "summary": {
            "total_datasets": 0,
            "p_value_shifts": [],
            "ci_width_changes": [],
            "effect_size_changes": []
        }
    }

    baseline_datasets = baseline_metrics.get("datasets", [])
    cleaned_datasets = cleaned_metrics.get("datasets", [])

    # Create a map for cleaned metrics by dataset name
    cleaned_map = {
        entry.get("dataset_name") or entry.get("dataset_id"): entry
        for entry in cleaned_datasets
    }

    for base_entry in baseline_datasets:
        ds_name = base_entry.get("dataset_name") or base_entry.get("dataset_id")
        if not ds_name:
            continue

        clean_entry = cleaned_map.get(ds_name)
        if not clean_entry:
            logging.warning(f"No cleaned metrics found for dataset: {ds_name}")
            continue

        comparison_entry = {
            "dataset_name": ds_name,
            "baseline": {},
            "cleaned": {},
            "differences": {}
        }

        # Extract p-values
        base_p = base_entry.get("analysis", {}).get("t_test", {}).get("p_value")
        clean_p = clean_entry.get("analysis", {}).get("t_test", {}).get("p_value")

        if base_p is not None and clean_p is not None:
            abs_diff = calculate_absolute_diff(base_p, clean_p)
            rel_diff = calculate_relative_diff(base_p, clean_p)
            comparison_entry["differences"]["p_value"] = {
                "absolute": round(abs_diff, 6),
                "relative": round(rel_diff, 6) if rel_diff != float('inf') else None
            }
            comparison_entry["baseline"]["p_value"] = round(base_p, 6)
            comparison_entry["cleaned"]["p_value"] = round(clean_p, 6)
            comparison_data["summary"]["p_value_shifts"].append(abs_diff)

        # Extract CI widths
        base_ci = base_entry.get("analysis", {}).get("t_test", {}).get("ci")
        clean_ci = clean_entry.get("analysis", {}).get("t_test", {}).get("ci")

        if base_ci and clean_ci and len(base_ci) == 2 and len(clean_ci) == 2:
            base_width = base_ci[1] - base_ci[0]
            clean_width = clean_ci[1] - clean_ci[0]
            abs_diff = calculate_absolute_diff(base_width, clean_width)
            rel_diff = calculate_relative_diff(base_width, clean_width)
            comparison_entry["differences"]["ci_width"] = {
                "absolute": round(abs_diff, 6),
                "relative": round(rel_diff, 6) if rel_diff != float('inf') else None
            }
            comparison_entry["baseline"]["ci_width"] = round(base_width, 6)
            comparison_entry["cleaned"]["ci_width"] = round(clean_width, 6)
            comparison_data["summary"]["ci_width_changes"].append(abs_diff)

        # Extract Effect Sizes (Cohen's d)
        base_es = base_entry.get("analysis", {}).get("t_test", {}).get("effect_size")
        clean_es = clean_entry.get("analysis", {}).get("t_test", {}).get("effect_size")

        if base_es is not None and clean_es is not None:
            abs_diff = calculate_absolute_diff(base_es, clean_es)
            rel_diff = calculate_relative_diff(base_es, clean_es)
            comparison_entry["differences"]["effect_size"] = {
                "absolute": round(abs_diff, 6),
                "relative": round(rel_diff, 6) if rel_diff != float('inf') else None
            }
            comparison_entry["baseline"]["effect_size"] = round(base_es, 6)
            comparison_entry["cleaned"]["effect_size"] = round(clean_es, 6)
            comparison_data["summary"]["effect_size_changes"].append(abs_diff)

        comparison_data["datasets"].append(comparison_entry)
        comparison_data["summary"]["total_datasets"] += 1

    return comparison_data

def create_comparison_report(
    baseline_metrics: Dict[str, Any],
    cleaned_metrics: Dict[str, Any],
    sensitivity_analysis: Optional[Dict[str, Any]],
    output_path: str = "data/processed/comparison_report.json"
) -> ComparisonReport:
    """
    Create a ComparisonReport entity containing baseline_metrics, cleaned_metrics,
    absolute_diff, relative_diff, and sensitivity_analysis.
    """
    aggregated = aggregate_metrics_for_comparison(baseline_metrics, cleaned_metrics)

    # Construct the ComparisonReport object
    report = ComparisonReport(
        id=f"cmp_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        created_at=datetime.now().isoformat(),
        baseline_metrics=baseline_metrics,
        cleaned_metrics=cleaned_metrics,
        sensitivity_analysis=sensitivity_analysis,
        absolute_diff=aggregated.get("summary", {}).get("p_value_shifts", []),
        relative_diff=[
            {"absolute": d["absolute"], "relative": d["relative"]}
            for d in [
                item.get("differences", {}).get("p_value", {})
                for item in aggregated.get("datasets", [])
            ]
        ],
        detailed_comparison=aggregated
    )

    # Serialize to JSON and write to disk
    with open(output_path, 'w') as f:
        json.dump(report.model_dump(), f, indent=2, default=str)

    logging.info(f"Comparison report written to {output_path}")
    return report

def main():
    """Main entry point for T040: Create comparison report."""
    logger = setup_logging("INFO")
    config = get_config()

    logger.info("Starting T040: Create comparison report")

    # Load required artifacts
    baseline_metrics = load_baseline_metrics()
    cleaned_metrics = load_cleaned_metrics()
    sensitivity_analysis = load_sensitivity_analysis()

    if not baseline_metrics or not cleaned_metrics:
        logger.error("Missing required input files (baseline_metrics.json or cleaned_metrics.json).")
        sys.exit(1)

    # Create the report
    output_path = os.path.join(config.PROCESSED_DATA_PATH, "comparison_report.json")
    report = create_comparison_report(
        baseline_metrics,
        cleaned_metrics,
        sensitivity_analysis,
        output_path=output_path
    )

    logger.info(f"Successfully created comparison report: {output_path}")
    return 0

if __name__ == "__main__":
    sys.exit(main())