import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from utils import setup_logging, log_info, log_warning, log_error, load_json, save_json

# Constants
PRIMARY_REPORT_PATH = Path("data/results/statistical_report.json")
ROBUSTNESS_REPORT_PATH = Path("data/results/robustness_report.json")
OUTPUT_PATH = Path("data/results/sensitivity_comparison.json")

def load_report(path: Path) -> Optional[Dict[str, Any]]:
    """Load a JSON report file."""
    if not path.exists():
        log_error(f"Report file not found: {path}")
        return None
    try:
        return load_json(path)
    except Exception as e:
        log_error(f"Failed to load report {path}: {e}")
        return None

def compare_metrics(
    primary_val: Optional[float],
    robust_val: Optional[float],
    metric_name: str
) -> Dict[str, Any]:
    """Compare a specific metric between primary and robustness analysis."""
    result = {
        "metric": metric_name,
        "primary_value": primary_val,
        "robustness_value": robust_val,
        "difference": None,
        "percent_change": None,
        "significance_changed": False,
        "effect_size_changed": False
    }

    if primary_val is None and robust_val is None:
        result["status"] = "both_missing"
        return result

    if primary_val is None:
        result["status"] = "primary_missing"
        return result

    if robust_val is None:
        result["status"] = "robustness_missing"
        return result

    # Calculate differences
    diff = robust_val - primary_val
    result["difference"] = diff

    if abs(primary_val) > 1e-9:
        pct_change = (diff / abs(primary_val)) * 100
        result["percent_change"] = pct_change
    else:
        result["percent_change"] = float('inf') if diff != 0 else 0.0

    # Determine if significance changed (p-value threshold 0.05)
    # We assume the metric is a p-value for significance checks
    # For effect sizes, we check if the sign or magnitude changed significantly
    if metric_name.endswith("p_value") or "p_value" in metric_name:
        primary_sig = primary_val < 0.05
        robust_sig = robust_val < 0.05
        result["significance_changed"] = primary_sig != robust_sig
        result["status"] = "significant_change" if result["significance_changed"] else "stable"
    else:
        # For effect sizes (Cohen's d), check if the interpretation changed
        # Small: |d| < 0.2, Medium: 0.2 <= |d| < 0.5, Large: |d| >= 0.5
        def interpret_effect(d):
            if abs(d) < 0.2:
                return "small"
            elif abs(d) < 0.5:
                return "medium"
            else:
                return "large"

        primary_interp = interpret_effect(primary_val)
        robust_interp = interpret_effect(robust_val)
        result["effect_size_changed"] = primary_interp != robust_interp
        result["status"] = "interpretation_change" if result["effect_size_changed"] else "stable"

    return result

def compare_reports(
    primary_report: Dict[str, Any],
    robustness_report: Dict[str, Any]
) -> Dict[str, Any]:
    """Compare primary and robustness analysis reports."""
    comparison = {
        "summary": {
            "primary_analysis_source": str(PRIMARY_REPORT_PATH),
            "robustness_analysis_source": str(ROBUSTNESS_REPORT_PATH),
            "comparison_timestamp": "N/A", # Will be set by caller if needed
            "overall_stability": "unknown"
        },
        "metrics": {}
    }

    # Extract relevant metrics for comparison
    # We expect keys like: 'perseverative_errors', 'categories_completed'
    # Each containing 'p_value', 'cohens_d', etc.

    primary_metrics = primary_report.get("metrics", {})
    robust_metrics = robustness_report.get("metrics", {})

    all_metric_names = set(primary_metrics.keys()) | set(robust_metrics.keys())

    stability_count = 0
    change_count = 0

    for metric_name in all_metric_names:
        primary_data = primary_metrics.get(metric_name, {})
        robust_data = robust_metrics.get(metric_name, {})

        metric_comparison = {
            "perseverative_errors": {},
            "categories_completed": {}
        }.get(metric_name, {}) # Default to empty if not one of expected

        # Compare p-values
        p_comp = compare_metrics(
            primary_data.get("p_value"),
            robust_data.get("p_value"),
            f"{metric_name}_p_value"
        )
        metric_comparison["p_value"] = p_comp

        # Compare Cohen's d
        d_comp = compare_metrics(
            primary_data.get("cohens_d"),
            robust_data.get("cohens_d"),
            f"{metric_name}_cohens_d"
        )
        metric_comparison["cohens_d"] = d_comp

        comparison["metrics"][metric_name] = metric_comparison

        # Update stability counters
        if p_comp["status"] == "stable" and d_comp["status"] == "stable":
            stability_count += 1
        else:
            change_count += 1

    # Overall stability assessment
    total = stability_count + change_count
    if total == 0:
        comparison["summary"]["overall_stability"] = "no_data"
    elif stability_count == total:
        comparison["summary"]["overall_stability"] = "highly_stable"
    elif change_count <= 1:
        comparison["summary"]["overall_stability"] = "mostly_stable"
    else:
        comparison["summary"]["overall_stability"] = "sensitive_to_mmse_exclusion"

    return comparison

def main():
    """Main entry point for T027c: Compare Robustness Analysis."""
    setup_logging()
    log_info("Starting T027c: Compare Primary vs. Robustness Analysis")

    # Load reports
    primary_report = load_report(PRIMARY_REPORT_PATH)
    robustness_report = load_report(ROBUSTNESS_REPORT_PATH)

    if primary_report is None:
        log_error("Primary statistical report missing. Cannot proceed with comparison.")
        return 1

    if robustness_report is None:
        log_error("Robustness report missing. Cannot proceed with comparison.")
        return 1

    log_info("Reports loaded successfully.")

    # Perform comparison
    comparison_result = compare_reports(primary_report, robustness_report)

    # Save result
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    save_json(comparison_result, OUTPUT_PATH)

    log_info(f"Comparison result saved to {OUTPUT_PATH}")
    log_info(f"Overall Stability: {comparison_result['summary']['overall_stability']}")

    return 0

if __name__ == "__main__":
    exit(main())
