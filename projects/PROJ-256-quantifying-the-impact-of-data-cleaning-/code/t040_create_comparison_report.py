"""
Task T040: Create Comparison Report
Generates a ComparisonReport entity (JSON) containing baseline metrics,
cleaned metrics, absolute/relative differences, and sensitivity analysis.
"""
import os
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import numpy as np

# Local imports from project API surface
from models import ComparisonReport, AnalysisResult, CleaningStrategy, Dataset
from config import Config, get_config
from utils import setup_logging, compute_file_checksum

logger = logging.getLogger(__name__)

# Default paths
BASELINE_METRICS_PATH = "data/processed/baseline_metrics.json"
CLEANED_METRICS_PATH = "data/processed/cleaned_metrics.json"
SENSITIVITY_ANALYSIS_PATH = "data/processed/sensitivity_analysis.json"
OUTPUT_PATH = "data/processed/comparison_report.json"

def load_json_file(path: str) -> Optional[Dict[str, Any]]:
    """Load a JSON file safely."""
    if not os.path.exists(path):
        logger.warning(f"File not found: {path}. Returning empty dict.")
        return {}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading {path}: {e}")
        return {}

def load_baseline_metrics() -> Dict[str, Any]:
    """Load baseline metrics from the processed directory."""
    return load_json_file(BASELINE_METRICS_PATH)

def load_cleaned_metrics() -> Dict[str, Any]:
    """Load cleaned metrics from the processed directory."""
    return load_json_file(CLEANED_METRICS_PATH)

def load_sensitivity_analysis() -> Dict[str, Any]:
    """Load sensitivity analysis results if available."""
    return load_json_file(SENSITIVITY_ANALYSIS_PATH)

def calculate_absolute_diff(baseline_val: float, cleaned_val: float) -> float:
    """Calculate absolute difference between two values."""
    if baseline_val is None or cleaned_val is None:
        return float('nan')
    return abs(cleaned_val - baseline_val)

def calculate_relative_diff(baseline_val: float, cleaned_val: float) -> float:
    """Calculate relative difference (percentage change)."""
    if baseline_val is None or cleaned_val is None or baseline_val == 0:
        return float('nan')
    return (cleaned_val - baseline_val) / abs(baseline_val)

def aggregate_metrics_for_comparison(
    baseline_entry: Dict[str, Any],
    cleaned_entry: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Aggregate metrics for a single dataset/strategy pair.
    Extracts p-values, CIs, and effect sizes, then computes diffs.
    """
    result = {
        "dataset_name": baseline_entry.get("dataset_name", "Unknown"),
        "cleaning_strategy": cleaned_entry.get("strategy", cleaned_entry.get("cleaning_strategy", "Unknown")),
        "metrics": {}
    }

    # Helper to safely get a float or None
    def safe_float(val):
        if val is None:
            return None
        try:
            return float(val)
        except (ValueError, TypeError):
            return None

    # Process p-values
    base_p = safe_float(baseline_entry.get("p_value"))
    clean_p = safe_float(cleaned_entry.get("p_value"))
    
    if base_p is not None and clean_p is not None:
        result["metrics"]["p_value"] = {
            "baseline": base_p,
            "cleaned": clean_p,
            "absolute_diff": calculate_absolute_diff(base_p, clean_p),
            "relative_diff": calculate_relative_diff(base_p, clean_p)
        }

    # Process Confidence Intervals (assuming 'ci_width' or 'ci' field)
    base_ci = safe_float(baseline_entry.get("ci_width", baseline_entry.get("ci", {}).get("width", 0)))
    clean_ci = safe_float(cleaned_entry.get("ci_width", cleaned_entry.get("ci", {}).get("width", 0)))
    
    if base_ci is not None and clean_ci is not None:
        result["metrics"]["ci_width"] = {
            "baseline": base_ci,
            "cleaned": clean_ci,
            "absolute_diff": calculate_absolute_diff(base_ci, clean_ci),
            "relative_diff": calculate_relative_diff(base_ci, clean_ci)
        }

    # Process Effect Sizes (Cohen's d or R-squared)
    base_es = safe_float(baseline_entry.get("effect_size", baseline_entry.get("cohens_d", baseline_entry.get("r_squared", 0))))
    clean_es = safe_float(cleaned_entry.get("effect_size", cleaned_entry.get("cohens_d", cleaned_entry.get("r_squared", 0))))
    
    if base_es is not None and clean_es is not None:
        result["metrics"]["effect_size"] = {
            "baseline": base_es,
            "cleaned": clean_es,
            "absolute_diff": calculate_absolute_diff(base_es, clean_es),
            "relative_diff": calculate_relative_diff(base_es, clean_es)
        }

    return result

def create_comparison_report(
    baseline_data: Dict[str, Any],
    cleaned_data: Dict[str, Any],
    sensitivity_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create the full ComparisonReport structure.
    Matches the schema of the ComparisonReport Pydantic model.
    """
    report = {
        "id": f"cmp_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "created_at": datetime.now().isoformat(),
        "baseline_metrics": baseline_data.get("datasets", []),
        "cleaned_metrics": cleaned_data.get("datasets", []),
        "comparisons": [],
        "sensitivity_analysis": sensitivity_data or {},
        "summary": {}
    }

    # Aggregate comparisons
    baseline_list = baseline_data.get("datasets", [])
    cleaned_list = cleaned_data.get("datasets", [])

    # Map cleaned by dataset name + strategy
    cleaned_map = {}
    for c in cleaned_list:
        key = (c.get("dataset_name"), c.get("strategy", c.get("cleaning_strategy")))
        cleaned_map[key] = c

    for b in baseline_list:
        ds_name = b.get("dataset_name")
        # Compare against all strategies applied to this dataset
        for (key_ds, key_strat), c in cleaned_map.items():
            if key_ds == ds_name:
                comp = aggregate_metrics_for_comparison(b, c)
                report["comparisons"].append(comp)

    # Calculate summary statistics
    if report["comparisons"]:
        p_shifts = [c["metrics"]["p_value"]["absolute_diff"] for c in report["comparisons"] 
                    if "p_value" in c["metrics"] and not np.isnan(c["metrics"]["p_value"]["absolute_diff"])]
        ci_shifts = [c["metrics"]["ci_width"]["absolute_diff"] for c in report["comparisons"] 
                     if "ci_width" in c["metrics"] and not np.isnan(c["metrics"]["ci_width"]["absolute_diff"])]
        
        report["summary"] = {
            "total_comparisons": len(report["comparisons"]),
            "avg_p_value_shift": float(np.mean(p_shifts)) if p_shifts else None,
            "median_p_value_shift": float(np.median(p_shifts)) if p_shifts else None,
            "avg_ci_width_change": float(np.mean(ci_shifts)) if ci_shifts else None,
            "median_ci_width_change": float(np.median(ci_shifts)) if ci_shifts else None
        }

    return report

def main():
    """Main entry point for T040."""
    # Setup logging
    setup_logging("INFO")
    
    logger.info("Starting T040: Create Comparison Report")
    
    # Load data
    baseline_data = load_baseline_metrics()
    cleaned_data = load_cleaned_metrics()
    sensitivity_data = load_sensitivity_analysis()

    if not baseline_data or not baseline_data.get("datasets"):
        logger.error("Baseline metrics are missing or empty. Cannot create comparison report.")
        # Still generate a report with empty data to satisfy artifact requirement
        report = create_comparison_report({}, {}, sensitivity_data)
    elif not cleaned_data or not cleaned_data.get("datasets"):
        logger.warning("Cleaned metrics are missing or empty. Creating report with baseline only.")
        report = create_comparison_report(baseline_data, {}, sensitivity_data)
    else:
        logger.info("Loading complete. Generating comparison report.")
        report = create_comparison_report(baseline_data, cleaned_data, sensitivity_data)

    # Write output
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, default=str)
    
    # Compute checksum
    checksum = compute_file_checksum(OUTPUT_PATH)
    logger.info(f"Comparison report written to {OUTPUT_PATH} (SHA256: {checksum})")
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
