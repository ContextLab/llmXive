import os
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import numpy as np

from models import ComparisonReport, AnalysisResult, Dataset, CleaningStrategy
from config import Config, get_config
from utils import setup_logging

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
        logger.error(f"Failed to parse JSON in {filepath}: {e}")
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
        return float('nan')
    return abs(cleaned_val - baseline_val)

def calculate_relative_diff(baseline_val: float, cleaned_val: float) -> float:
    """Calculate relative difference (percentage change) between baseline and cleaned values."""
    if baseline_val is None or cleaned_val is None or baseline_val == 0:
        return float('nan')
    return (cleaned_val - baseline_val) / abs(baseline_val)

def aggregate_metrics_for_comparison(baseline_metrics: Dict[str, Any], cleaned_metrics: Dict[str, Any]) -> Dict[str, Any]:
    """Aggregate metrics from baseline and cleaned datasets for comparison."""
    if not baseline_metrics or not cleaned_metrics:
        return {}

    comparison_data = {
        "baseline_summary": {},
        "cleaned_summary": {},
        "differences": {}
    }

    # Extract baseline stats
    if "datasets" in baseline_metrics:
        baseline_datasets = baseline_metrics["datasets"]
        p_values = [d.get("t_test", {}).get("p_value") for d in baseline_datasets if d.get("t_test", {}).get("p_value") is not None]
        ci_widths = []
        for d in baseline_datasets:
            ci = d.get("t_test", {}).get("ci")
            if ci and len(ci) == 2:
                ci_widths.append(abs(ci[1] - ci[0]))
        
        comparison_data["baseline_summary"] = {
            "count": len(baseline_datasets),
            "mean_p_value": float(np.mean(p_values)) if p_values else None,
            "mean_ci_width": float(np.mean(ci_widths)) if ci_widths else None
        }

    # Extract cleaned stats
    if "datasets" in cleaned_metrics:
        cleaned_datasets = cleaned_metrics["datasets"]
        p_values = [d.get("t_test", {}).get("p_value") for d in cleaned_datasets if d.get("t_test", {}).get("p_value") is not None]
        ci_widths = []
        for d in cleaned_datasets:
            ci = d.get("t_test", {}).get("ci")
            if ci and len(ci) == 2:
                ci_widths.append(abs(ci[1] - ci[0]))

        comparison_data["cleaned_summary"] = {
            "count": len(cleaned_datasets),
            "mean_p_value": float(np.mean(p_values)) if p_values else None,
            "mean_ci_width": float(np.mean(ci_widths)) if ci_widths else None
        }

    # Calculate differences
    if comparison_data["baseline_summary"]["mean_p_value"] and comparison_data["cleaned_summary"]["mean_p_value"]:
        comparison_data["differences"]["p_value_abs_diff"] = calculate_absolute_diff(
            comparison_data["baseline_summary"]["mean_p_value"],
            comparison_data["cleaned_summary"]["mean_p_value"]
        )
        comparison_data["differences"]["p_value_rel_diff"] = calculate_relative_diff(
            comparison_data["baseline_summary"]["mean_p_value"],
            comparison_data["cleaned_summary"]["mean_p_value"]
        )

    if comparison_data["baseline_summary"]["mean_ci_width"] and comparison_data["cleaned_summary"]["mean_ci_width"]:
        comparison_data["differences"]["ci_width_abs_diff"] = calculate_absolute_diff(
            comparison_data["baseline_summary"]["mean_ci_width"],
            comparison_data["cleaned_summary"]["mean_ci_width"]
        )
        comparison_data["differences"]["ci_width_rel_diff"] = calculate_relative_diff(
            comparison_data["baseline_summary"]["mean_ci_width"],
            comparison_data["cleaned_summary"]["mean_ci_width"]
        )

    return comparison_data

def create_comparison_report(
    baseline_metrics: Optional[Dict[str, Any]],
    cleaned_metrics: Optional[Dict[str, Any]],
    sensitivity_analysis: Optional[Dict[str, Any]],
    output_path: str = "data/processed/comparison_report.json"
) -> Optional[Dict[str, Any]]:
    """Create a comprehensive comparison report."""
    logger.info("Creating comparison report...")

    if not baseline_metrics:
        logger.error("Baseline metrics not found. Cannot create comparison report.")
        return None
    
    if not cleaned_metrics:
        logger.error("Cleaned metrics not found. Cannot create comparison report.")
        return None

    aggregated = aggregate_metrics_for_comparison(baseline_metrics, cleaned_metrics)

    report_data = {
        "report_id": f"comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "generated_at": datetime.now().isoformat(),
        "baseline_metrics_summary": aggregated.get("baseline_summary", {}),
        "cleaned_metrics_summary": aggregated.get("cleaned_summary", {}),
        "absolute_diff": aggregated.get("differences", {}).get("p_value_abs_diff", None),
        "relative_diff": aggregated.get("differences", {}).get("p_value_rel_diff", None),
        "ci_width_changes": {
            "absolute": aggregated.get("differences", {}).get("ci_width_abs_diff", None),
            "relative": aggregated.get("differences", {}).get("ci_width_rel_diff", None)
        },
        "sensitivity_analysis": sensitivity_analysis if sensitivity_analysis else {},
        "raw_baseline_metrics": baseline_metrics,
        "raw_cleaned_metrics": cleaned_metrics
    }

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(report_data, f, indent=2)

    logger.info(f"Comparison report saved to {output_path}")
    return report_data

def main():
    """Main entry point for the comparison report generation."""
    setup_logging("INFO")
    config = get_config()
    
    baseline_path = config.get("BASELINE_METRICS_PATH", "data/processed/baseline_metrics.json")
    cleaned_path = config.get("CLEANED_METRICS_PATH", "data/processed/cleaned_metrics.json")
    sensitivity_path = config.get("SENSITIVITY_ANALYSIS_PATH", "data/processed/sensitivity_analysis.json")
    output_path = config.get("COMPARISON_REPORT_PATH", "data/processed/comparison_report.json")

    baseline_metrics = load_baseline_metrics(baseline_path)
    cleaned_metrics = load_cleaned_metrics(cleaned_path)
    sensitivity_analysis = load_sensitivity_analysis(sensitivity_path)

    report = create_comparison_report(
        baseline_metrics,
        cleaned_metrics,
        sensitivity_analysis,
        output_path
    )

    if report:
        logger.info("Comparison report generated successfully.")
        return 0
    else:
        logger.error("Failed to generate comparison report.")
        return 1

if __name__ == "__main__":
    exit(main())
