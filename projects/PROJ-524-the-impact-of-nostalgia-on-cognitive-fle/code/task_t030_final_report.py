"""
T030: FINAL SENSITIVITY SUMMARY

Updates the final report to include sensitivity analysis summary and stability metrics.
Depends on: T028 (sensitivity_report.json), T029 (threshold sensitivity flags).

This task consolidates the sensitivity analysis results into a final summary,
calculating stability metrics across the threshold sweep and comparing robustness
between primary and MMSE-excluded analyses.
"""

import os
import json
import logging
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Path constants (relative to project root)
PROJECT_ROOT = Path(__file__).parent.parent
DATA_RESULTS_DIR = PROJECT_ROOT / "data" / "results"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

# Output file paths
SENSITIVITY_REPORT_PATH = DATA_RESULTS_DIR / "sensitivity_report.json"
ROBUSTNESS_COMPARISON_PATH = DATA_RESULTS_DIR / "sensitivity_comparison.json"
STATISTICAL_REPORT_PATH = DATA_RESULTS_DIR / "statistical_report.json"
FINAL_SENSITIVITY_SUMMARY_PATH = DATA_RESULTS_DIR / "final_sensitivity_summary.json"

# Thresholds for sensitivity analysis
THRESHOLD_RANGE = [0.04, 0.05, 0.06, 0.10]
BORDERLINE_MIN = 0.04
BORDERLINE_MAX = 0.06


def load_json_file(file_path: Path) -> Optional[Dict[str, Any]]:
    """
    Load a JSON file and return its contents.
    
    Args:
        file_path: Path to the JSON file.
        
    Returns:
        Dictionary containing the JSON data, or None if file doesn't exist.
    """
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        return None
        
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON file {file_path}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error reading {file_path}: {e}")
        return None


def calculate_stability_metrics(
    sensitivity_results: Dict[str, Any],
    robustness_comparison: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Calculate stability metrics based on sensitivity sweep and robustness comparison.
    
    Args:
        sensitivity_results: Results from the sensitivity threshold sweep.
        robustness_comparison: Comparison between primary and MMSE-excluded analyses.
        
    Returns:
        Dictionary containing stability metrics.
    """
    metrics = {
        "threshold_stability": {},
        "robustness_stability": {},
        "overall_stability_score": 0.0,
        "stability_flags": []
    }
    
    # Analyze threshold stability
    if "threshold_analysis" in sensitivity_results:
        threshold_data = sensitivity_results["threshold_analysis"]
        significant_count = 0
        total_tests = 0
        
        for metric_name, results in threshold_data.items():
            if "significance_by_threshold" in results:
                sig_results = results["significance_by_threshold"]
                significant_count = sum(1 for is_sig in sig_results.values() if is_sig)
                total_tests = len(sig_results)
                
                if total_tests > 0:
                    stability_ratio = significant_count / total_tests
                    metrics["threshold_stability"][metric_name] = {
                        "significant_count": significant_count,
                        "total_tests": total_tests,
                        "stability_ratio": round(stability_ratio, 4)
                    }
                    
                    # Flag unstable metrics (significant in < 50% of thresholds)
                    if stability_ratio < 0.5 and significant_count > 0:
                        metrics["stability_flags"].append(
                            f"{metric_name}: unstable across thresholds ({stability_ratio:.2%} significant)"
                        )
    
    # Analyze robustness stability
    if robustness_comparison and "comparison_summary" in robustness_comparison:
        summary = robustness_comparison["comparison_summary"]
        
        # Check if significance status changed between analyses
        for metric in ["perseverative_errors", "categories_completed"]:
            if metric in summary:
                metric_summary = summary[metric]
                primary_sig = metric_summary.get("primary_significant", False)
                robust_sig = metric_summary.get("robust_significant", False)
                
                if primary_sig != robust_sig:
                    metrics["robustness_stability"][metric] = {
                        "primary_significant": primary_sig,
                        "robust_significant": robust_sig,
                        "stable": False,
                        "reason": "Significance status changed with MMSE exclusion"
                    }
                    metrics["stability_flags"].append(
                        f"{metric}: not robust to MMSE exclusion"
                    )
                else:
                    metrics["robustness_stability"][metric] = {
                        "primary_significant": primary_sig,
                        "robust_significant": robust_sig,
                        "stable": True
                    }
    
    # Calculate overall stability score (0.0 to 1.0)
    stability_scores = []
    
    # Add threshold stability scores
    for metric_data in metrics["threshold_stability"].values():
        stability_scores.append(metric_data["stability_ratio"])
    
    # Add robustness stability scores
    for metric_data in metrics["robustness_stability"].values():
        stability_scores.append(1.0 if metric_data.get("stable", False) else 0.0)
    
    if stability_scores:
        metrics["overall_stability_score"] = round(
            sum(stability_scores) / len(stability_scores), 4
        )
    
    return metrics


def generate_sensitivity_summary(
    sensitivity_results: Dict[str, Any],
    robustness_comparison: Dict[str, Any],
    statistical_report: Dict[str, Any],
    stability_metrics: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate a comprehensive sensitivity analysis summary.
    
    Args:
        sensitivity_results: Results from the sensitivity threshold sweep.
        robustness_comparison: Comparison between primary and MMSE-excluded analyses.
        statistical_report: Main statistical analysis report.
        stability_metrics: Calculated stability metrics.
        
    Returns:
        Dictionary containing the final sensitivity summary.
    """
    summary = {
        "summary_metadata": {
            "generated_at": pd.Timestamp.now().isoformat(),
            "thresholds_analyzed": THRESHOLD_RANGE,
            "borderline_range": [BORDERLINE_MIN, BORDERLINE_MAX]
        },
        "primary_findings": {},
        "sensitivity_analysis": {
            "threshold_stability": stability_metrics["threshold_stability"],
            "borderline_flags": [],
            "threshold_sensitivity_flags": []
        },
        "robustness_analysis": {
            "mmse_exclusion_impact": stability_metrics["robustness_stability"],
            "comparison_summary": robustness_comparison.get("comparison_summary", {})
            if robustness_comparison else {}
        },
        "stability_metrics": {
            "overall_stability_score": stability_metrics["overall_stability_score"],
            "stability_flags": stability_metrics["stability_flags"]
        },
        "conclusions": []
    }
    
    # Extract borderline flags from sensitivity results
    if sensitivity_results and "threshold_analysis" in sensitivity_results:
        for metric_name, results in sensitivity_results["threshold_analysis"].items():
            if "borderline_status" in results:
                summary["sensitivity_analysis"]["borderline_flags"].append({
                    "metric": metric_name,
                    "is_borderline": results["borderline_status"].get("is_borderline", False),
                    "p_value": results["borderline_status"].get("p_value"),
                    "threshold_range": results["borderline_status"].get("threshold_range")
                })
                
                # Check if sensitive to threshold choice
                if results["borderline_status"].get("is_sensitive_to_threshold", False):
                    summary["sensitivity_analysis"]["threshold_sensitivity_flags"].append({
                        "metric": metric_name,
                        "reason": "p-value falls in borderline range (0.04-0.06)"
                    })
    
    # Extract primary findings from statistical report
    if statistical_report:
        summary["primary_findings"] = {
            "perseverative_errors": statistical_report.get("perseverative_errors", {}),
            "categories_completed": statistical_report.get("categories_completed", {})
        }
    
    # Generate conclusions based on stability analysis
    conclusions = []
    
    if stability_metrics["overall_stability_score"] >= 0.8:
        conclusions.append(
            "Results demonstrate HIGH stability across sensitivity thresholds and robustness checks."
        )
    elif stability_metrics["overall_stability_score"] >= 0.5:
        conclusions.append(
            "Results demonstrate MODERATE stability, with some sensitivity to threshold choice or MMSE exclusion."
        )
    else:
        conclusions.append(
            "Results demonstrate LOW stability, indicating significant sensitivity to analysis parameters."
        )
    
    if stability_metrics["stability_flags"]:
        conclusions.append(
            f"Stability concerns identified: {'; '.join(stability_metrics['stability_flags'])}"
        )
    
    # Check for borderline results
    if summary["sensitivity_analysis"]["threshold_sensitivity_flags"]:
        conclusions.append(
            "Some metrics fall in the borderline significance range (0.04-0.06), requiring cautious interpretation."
        )
    
    summary["conclusions"] = conclusions
    
    return summary


def compile_final_report(
    sensitivity_summary: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Compile the final sensitivity summary report with all relevant metadata.
    
    Args:
        sensitivity_summary: The generated sensitivity summary.
        
    Returns:
        Complete final report dictionary.
    """
    final_report = {
        "report_type": "Final Sensitivity Analysis Summary",
        "version": "1.0",
        "task_id": "T030",
        "dependencies_completed": ["T028", "T029"],
        "report_data": sensitivity_summary,
        "status": "complete"
    }
    
    return final_report


def save_report(report: Dict[str, Any], output_path: Path) -> bool:
    """
    Save the report to a JSON file.
    
    Args:
        report: The report dictionary to save.
        output_path: Path to the output file.
        
    Returns:
        True if successful, False otherwise.
    """
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"Successfully saved report to {output_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to save report to {output_path}: {e}")
        return False


def main():
    """
    Main entry point for T030: Final Sensitivity Summary.
    """
    logger.info("Starting T030: Final Sensitivity Summary")
    
    # Load required input files
    logger.info(f"Loading sensitivity report from {SENSITIVITY_REPORT_PATH}")
    sensitivity_results = load_json_file(SENSITIVITY_REPORT_PATH)
    if sensitivity_results is None:
        logger.error("Failed to load sensitivity report. Cannot proceed.")
        return False
        
    logger.info(f"Loading robustness comparison from {ROBUSTNESS_COMPARISON_PATH}")
    robustness_comparison = load_json_file(ROBUSTNESS_COMPARISON_PATH)
    if robustness_comparison is None:
        logger.warning(
            f"Robustness comparison file not found at {ROBUSTNESS_COMPARISON_PATH}. "
            "Proceeding with available data."
        )
        robustness_comparison = {}
        
    logger.info(f"Loading statistical report from {STATISTICAL_REPORT_PATH}")
    statistical_report = load_json_file(STATISTICAL_REPORT_PATH)
    if statistical_report is None:
        logger.error("Failed to load statistical report. Cannot proceed.")
        return False
    
    # Calculate stability metrics
    logger.info("Calculating stability metrics...")
    stability_metrics = calculate_stability_metrics(
        sensitivity_results, robustness_comparison
    )
    
    # Generate sensitivity summary
    logger.info("Generating sensitivity summary...")
    sensitivity_summary = generate_sensitivity_summary(
        sensitivity_results, robustness_comparison, statistical_report, stability_metrics
    )
    
    # Compile final report
    logger.info("Compiling final report...")
    final_report = compile_final_report(sensitivity_summary)
    
    # Save the report
    logger.info(f"Saving final report to {FINAL_SENSITIVITY_SUMMARY_PATH}")
    success = save_report(final_report, FINAL_SENSITIVITY_SUMMARY_PATH)
    
    if success:
        logger.info("T030 completed successfully.")
        return True
    else:
        logger.error("T030 failed to save the final report.")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)