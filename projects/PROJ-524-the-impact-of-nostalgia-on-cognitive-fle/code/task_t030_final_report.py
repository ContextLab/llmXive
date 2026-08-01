"""
T030: Update final report to include sensitivity analysis summary and stability metrics.

This module loads the statistical report, the sensitivity report, and the robustness
check results. It aggregates them into a comprehensive final report that includes
stability metrics (e.g., how often the result is significant across thresholds)
and a summary of the sensitivity analysis.
"""
import os
import json
import logging
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional

# Imports from project API surface
from config import get_config, get_env_float
from utils import setup_logging, log_info, log_warning, log_error, get_timestamp

# Constants
RESULTS_DIR = "data/results"
FINAL_REPORT_PATH = os.path.join(RESULTS_DIR, "final_report.json")
STATISTICAL_REPORT_PATH = os.path.join(RESULTS_DIR, "statistical_report.json")
SENSITIVITY_REPORT_PATH = os.path.join(RESULTS_DIR, "sensitivity_report.json")
ROBUSTNESS_REPORT_PATH = os.path.join(RESULTS_DIR, "robustness_report.json")

def load_json_file(path: str) -> Optional[Dict[str, Any]]:
    """Load a JSON file if it exists, return None otherwise."""
    if not os.path.exists(path):
        log_warning(f"File not found: {path}")
        return None
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        log_error(f"Failed to parse JSON in {path}: {e}")
        return None

def calculate_stability_metrics(sensitivity_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate stability metrics based on the sensitivity analysis results.
    
    Metrics:
    - stability_score: Proportion of tested thresholds where the result is significant.
    - borderline_count: Number of thresholds where p-value is near 0.05 (within 0.01).
    - stability_rating: 'High', 'Medium', or 'Low' based on stability_score.
    """
    if not sensitivity_data or "thresholds" not in sensitivity_data:
        return {
            "stability_score": 0.0,
            "borderline_count": 0,
            "stability_rating": "Unknown",
            "reason": "No sensitivity data available"
        }

    thresholds = sensitivity_data.get("thresholds", [])
    if not thresholds:
        return {
            "stability_score": 0.0,
            "borderline_count": 0,
            "stability_rating": "Unknown",
            "reason": "Empty threshold list"
        }

    significant_count = 0
    borderline_count = 0
    total_count = len(thresholds)

    for entry in thresholds:
        is_sig = entry.get("is_significant", False)
        p_val = entry.get("p_value", 1.0)
        
        if is_sig:
            significant_count += 1
        
        # Check if borderline (p-value within 0.01 of 0.05)
        if abs(p_val - 0.05) <= 0.01:
            borderline_count += 1

    stability_score = significant_count / total_count if total_count > 0 else 0.0

    if stability_score >= 0.8:
        rating = "High"
    elif stability_score >= 0.5:
        rating = "Medium"
    else:
        rating = "Low"

    return {
        "stability_score": round(stability_score, 3),
        "borderline_count": borderline_count,
        "stability_rating": rating,
        "total_thresholds_tested": total_count
    }

def generate_sensitivity_summary(sensitivity_data: Dict[str, Any]) -> str:
    """Generate a human-readable summary of the sensitivity analysis."""
    if not sensitivity_data:
        return "Sensitivity analysis data is missing."

    thresholds = sensitivity_data.get("thresholds", [])
    if not thresholds:
        return "No thresholds were tested in the sensitivity analysis."

    sig_count = sum(1 for t in thresholds if t.get("is_significant", False))
    total = len(thresholds)
    
    summary = f"Sensitivity analysis tested {total} significance thresholds. "
    summary += f"The result was significant in {sig_count} of them ({round(sig_count/total*100, 1)}%)."
    
    if sensitivity_data.get("is_sensitive_to_threshold", False):
        summary += " The result is SENSITIVE to the choice of threshold (borderline p-values detected)."
    else:
        summary += " The result is STABLE across different threshold choices."
        
    return summary

def compile_final_report() -> Dict[str, Any]:
    """
    Compile the final report by merging statistical, sensitivity, and robustness results.
    """
    timestamp = get_timestamp()
    
    # Load source reports
    stat_report = load_json_file(STATISTICAL_REPORT_PATH)
    sens_report = load_json_file(SENSITIVITY_REPORT_PATH)
    robust_report = load_json_file(ROBUSTNESS_REPORT_PATH)

    # Calculate stability metrics
    stability_metrics = calculate_stability_metrics(sens_report)
    
    # Generate sensitivity summary
    sens_summary = generate_sensitivity_summary(sens_report)

    # Construct the final report structure
    final_report = {
        "metadata": {
            "generated_at": timestamp,
            "task_id": "T030",
            "version": "1.0.0"
        },
        "sensitivity_analysis": {
            "summary": sens_summary,
            "stability_metrics": stability_metrics,
            "raw_data": sens_report
        },
        "statistical_results": {
            "summary": {
                "primary_metric": "perseverative_errors",
                "comparison": "nostalgia vs control (Welch's t-test)",
                "significance": stat_report.get("is_significant", False) if stat_report else False,
                "p_value": stat_report.get("p_value", None) if stat_report else None,
                "effect_size": stat_report.get("cohens_d", None) if stat_report else None
            },
            "raw_data": stat_report
        },
        "robustness_check": {
            "summary": robust_report.get("summary", "No robustness check performed.") if robust_report else "No robustness check performed.",
            "raw_data": robust_report
        },
        "overall_conclusion": {
            "stability": stability_metrics.get("stability_rating", "Unknown"),
            "recommendation": "Results are robust" if stability_metrics.get("stability_rating") in ["High", "Medium"] else "Results are sensitive to threshold choice; interpret with caution."
        }
    }

    return final_report

def save_report(report: Dict[str, Any], path: str) -> None:
    """Save the report to a JSON file."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    log_info(f"Final report saved to {path}")

def main():
    """Main entry point for T030."""
    setup_logging()
    log_info("Starting T030: Final Report Generation with Sensitivity Summary")
    
    try:
        report = compile_final_report()
        save_report(report, FINAL_REPORT_PATH)
        log_info("T030 completed successfully.")
    except Exception as e:
        log_error(f"Failed to generate final report: {e}")
        raise

if __name__ == "__main__":
    main()
