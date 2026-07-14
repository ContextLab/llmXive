import os
import sys
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from utils import setup_logging
from models import ComparisonReport
from reporting import load_json_file, save_json_file

logger = setup_logging("INFO")

BASELINE_PATH = "data/processed/baseline_metrics.json"
CLEANED_PATH = "data/processed/cleaned_metrics.json"
SENSITIVITY_PATH = "data/processed/sensitivity_analysis.json"
OUTPUT_PATH = "data/processed/comparison_report.json"

def load_baseline_metrics() -> Optional[Dict[str, Any]]:
    if not os.path.exists(BASELINE_PATH):
        logger.warning(f"Baseline metrics not found at {BASELINE_PATH}")
        return None
    return load_json_file(BASELINE_PATH)

def load_cleaned_metrics() -> Optional[Dict[str, Any]]:
    if not os.path.exists(CLEANED_PATH):
        logger.warning(f"Cleaned metrics not found at {CLEANED_PATH}")
        return None
    return load_json_file(CLEANED_PATH)

def load_sensitivity_analysis() -> Optional[Dict[str, Any]]:
    if not os.path.exists(SENSITIVITY_PATH):
        logger.warning(f"Sensitivity analysis not found at {SENSITIVITY_PATH}. Proceeding without it.")
        return None
    return load_json_file(SENSITIVITY_PATH)

def calculate_absolute_diff(baseline_val: float, cleaned_val: float) -> float:
    return abs(cleaned_val - baseline_val)

def calculate_relative_diff(baseline_val: float, cleaned_val: float) -> float:
    if baseline_val == 0:
        return 0.0 if cleaned_val == 0 else float('inf')
    return (cleaned_val - baseline_val) / baseline_val

def aggregate_metrics_for_comparison(
    baseline_metrics: Dict[str, Any],
    cleaned_metrics: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Aggregates metrics from baseline and cleaned runs into a structure suitable for the report.
    Handles the case where metrics might be stored as a list of datasets or a dict.
    """
    comparison_data = {
        "baseline": {},
        "cleaned": {},
        "differences": []
    }

    # Normalize baseline data to a list of entries
    baseline_entries = baseline_metrics.get("datasets", []) if isinstance(baseline_metrics.get("datasets"), list) else []
    if not baseline_entries and isinstance(baseline_metrics, dict) and "datasets" not in baseline_metrics:
        # Fallback if structure is just a list at root or single dict
        baseline_entries = [baseline_metrics] if not isinstance(baseline_metrics, list) else baseline_metrics

    # Normalize cleaned data
    cleaned_entries = cleaned_metrics.get("datasets", []) if isinstance(cleaned_metrics.get("datasets"), list) else []
    if not cleaned_entries and isinstance(cleaned_metrics, dict) and "datasets" not in cleaned_metrics:
        cleaned_entries = [cleaned_metrics] if not isinstance(cleaned_metrics, list) else cleaned_metrics

    # Map by dataset name for comparison
    baseline_map = {d.get("dataset_name", d.get("name", "")): d for d in baseline_entries if d.get("dataset_name") or d.get("name")}
    cleaned_map = {d.get("dataset_name", d.get("name", "")): d for d in cleaned_entries if d.get("dataset_name") or d.get("name")}

    all_names = set(baseline_map.keys()) | set(cleaned_map.keys())

    for name in all_names:
        b_entry = baseline_map.get(name, {})
        c_entry = cleaned_map.get(name, {})

        # Extract p-values (assuming structure like: analysis -> t_test -> p_value)
        b_p = None
        c_p = None
        
        # Attempt to find p-value in various common structures
        if "analysis" in b_entry and "t_test" in b_entry["analysis"]:
            b_p = b_entry["analysis"]["t_test"].get("p_value")
        elif "t_test" in b_entry:
            b_p = b_entry["t_test"].get("p_value")
        elif "p_value" in b_entry:
            b_p = b_entry["p_value"]

        if "analysis" in c_entry and "t_test" in c_entry["analysis"]:
            c_p = c_entry["analysis"]["t_test"].get("p_value")
        elif "t_test" in c_entry:
            c_p = c_entry["t_test"].get("p_value")
        elif "p_value" in c_entry:
            c_p = c_entry["p_value"]

        # Extract effect sizes (Cohen's d)
        b_eff = None
        c_eff = None
        if "analysis" in b_entry and "effect_size" in b_entry["analysis"]:
            b_eff = b_entry["analysis"]["effect_size"].get("cohens_d")
        elif "effect_size" in b_entry:
            b_eff = b_entry["effect_size"].get("cohens_d")
        elif "cohens_d" in b_entry:
            b_eff = b_entry["cohens_d"]

        if "analysis" in c_entry and "effect_size" in c_entry["analysis"]:
            c_eff = c_entry["analysis"]["effect_size"].get("cohens_d")
        elif "effect_size" in c_entry:
            c_eff = c_entry["effect_size"].get("cohens_d")
        elif "cohens_d" in c_entry:
            c_eff = c_entry["cohens_d"]

        diff_entry = {
            "dataset_name": name,
            "baseline": {
                "p_value": b_p,
                "effect_size": b_eff
            },
            "cleaned": {
                "p_value": c_p,
                "effect_size": c_eff
            },
            "absolute_diff": {
                "p_value": calculate_absolute_diff(b_p, c_p) if b_p is not None and c_p is not None else None,
                "effect_size": calculate_absolute_diff(b_eff, c_eff) if b_eff is not None and c_eff is not None else None
            },
            "relative_diff": {
                "p_value": calculate_relative_diff(b_p, c_p) if b_p is not None and c_p is not None else None,
                "effect_size": calculate_relative_diff(b_eff, c_eff) if b_eff is not None and c_eff is not None else None
            }
        }
        comparison_data["differences"].append(diff_entry)

    return comparison_data

def create_comparison_report(
    baseline_metrics: Dict[str, Any],
    cleaned_metrics: Dict[str, Any],
    sensitivity_analysis: Optional[Dict[str, Any]]
) -> ComparisonReport:
    """
    Creates the ComparisonReport entity as defined in models.py.
    """
    aggregated = aggregate_metrics_for_comparison(baseline_metrics, cleaned_metrics)
    
    report = ComparisonReport(
        baseline_metrics=baseline_metrics,
        cleaned_metrics=cleaned_metrics,
        absolute_diff=aggregated["differences"],
        relative_diff=aggregated["differences"], # Reusing structure, or could flatten if needed
        sensitivity_analysis=sensitivity_analysis,
        created_at=datetime.now().isoformat()
    )
    return report

def main():
    logger.info("Starting comparison report generation (T040).")
    
    baseline = load_baseline_metrics()
    cleaned = load_cleaned_metrics()
    sensitivity = load_sensitivity_analysis()

    if not baseline:
        logger.error("Cannot generate comparison report: Baseline metrics missing.")
        return 1
    if not cleaned:
        logger.error("Cannot generate comparison report: Cleaned metrics missing.")
        return 1

    try:
        report = create_comparison_report(baseline, cleaned, sensitivity)
        
        # Convert to dict for JSON serialization
        report_dict = report.model_dump(mode='json')
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
        
        save_json_file(report_dict, OUTPUT_PATH)
        logger.info(f"Comparison report successfully written to {OUTPUT_PATH}")
        return 0
    except Exception as e:
        logger.error(f"Failed to create comparison report: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
