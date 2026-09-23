"""
T041: Strengthen Robustness - Explicitly log borderline range and set sensitivity flag.

This task ensures the sensitivity analysis explicitly logs the "borderline" range (0.04-0.06)
and outputs the binary flag `is_sensitive_to_threshold` in `data/results/sensitivity_report.json`
as required by FR-005.
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants for borderline range
BORDERLINE_LOW = 0.04
BORDERLINE_HIGH = 0.06

def load_sensitivity_report(report_path: str) -> Dict[str, Any]:
    """Load the sensitivity report from the specified path."""
    path = Path(report_path)
    if not path.exists():
        raise FileNotFoundError(f"Sensitivity report not found at {report_path}")
    
    with open(path, 'r') as f:
        return json.load(f)

def is_borderline(p_value: float, tolerance: float = 1e-9) -> bool:
    """
    Check if a p-value falls within the borderline range [0.04, 0.06].
    
    Args:
        p_value: The p-value to check.
        tolerance: Floating point comparison tolerance.
    
    Returns:
        True if the p-value is in the range [0.04, 0.06], False otherwise.
    """
    return BORDERLINE_LOW - tolerance <= p_value <= BORDERLINE_HIGH + tolerance

def calculate_stability_metrics(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate stability metrics based on sensitivity sweep results.
    
    Args:
        results: List of sensitivity sweep results containing thresholds and significance flags.
    
    Returns:
        Dictionary with stability metrics.
    """
    if not results:
        return {"stable_across_thresholds": False, "num_thresholds": 0}

    # Check if significance status is consistent across thresholds
    pe_significance = [r.get("perseverative_errors_significant", False) for r in results]
    cc_significance = [r.get("categories_completed_significant", False) for r in results]

    pe_stable = len(set(pe_significance)) == 1
    cc_stable = len(set(cc_significance)) == 1
    overall_stable = pe_stable and cc_stable

    # Count borderline results
    borderline_count = sum(1 for r in results if r.get("is_sensitive_to_threshold", False))

    return {
        "stable_across_thresholds": overall_stable,
        "pe_stable": pe_stable,
        "cc_stable": cc_stable,
        "num_thresholds": len(results),
        "borderline_count": borderline_count
    }

def update_sensitivity_flags(report: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update the sensitivity report to explicitly log borderline range and set flags.
    
    This function ensures:
    1. The borderline range [0.04, 0.06] is explicitly documented.
    2. The `is_sensitive_to_threshold` flag is set for each result based on p-values.
    3. Stability metrics are calculated and included in the summary.
    
    Args:
        report: The sensitivity report dictionary to update.
    
    Returns:
        The updated sensitivity report.
    """
    logger.info("Updating sensitivity flags and logging borderline range...")
    
    # Explicitly log the borderline range in the report metadata
    report["borderline_range"] = {
        "low": BORDERLINE_LOW,
        "high": BORDERLINE_HIGH,
        "description": "P-values in this range are considered 'borderline' and sensitive to threshold choice."
    }

    # Update each result with the is_sensitive_to_threshold flag
    updated_results = []
    for result in report.get("results", []):
        threshold = result.get("threshold")
        
        # Get p-values from the summary if available
        summary = report.get("summary", {})
        pe_p = summary.get("primary_pe_p_value")
        cc_p = summary.get("primary_cc_p_value")
        
        # Determine sensitivity based on whether the threshold is in the borderline range
        # or if the p-value falls in the borderline range
        is_sensitive = False
        if threshold is not None:
            # If the threshold itself is in the borderline range, flag it
            if is_borderline(threshold):
                is_sensitive = True
                logger.info(f"Threshold {threshold} is in borderline range [{BORDERLINE_LOW}, {BORDERLINE_HIGH}]")
        
        # Also check if p-values are borderline
        if pe_p is not None and is_borderline(pe_p):
            is_sensitive = True
            logger.info(f"Perseverative errors p-value {pe_p} is borderline")
        if cc_p is not None and is_borderline(cc_p):
            is_sensitive = True
            logger.info(f"Categories completed p-value {cc_p} is borderline")
        
        result["is_sensitive_to_threshold"] = is_sensitive
        updated_results.append(result)
    
    report["results"] = updated_results

    # Calculate and update stability metrics
    stability_metrics = calculate_stability_metrics(updated_results)
    report["summary"]["stable_across_thresholds"] = stability_metrics["stable_across_thresholds"]
    report["summary"]["borderline_results_found"] = stability_metrics["borderline_count"] > 0
    report["stability_metrics"] = stability_metrics

    logger.info(f"Stability metrics calculated: {stability_metrics}")
    logger.info("Sensitivity flags updated successfully.")
    
    return report

def save_sensitivity_report(report: Dict[str, Any], output_path: str) -> None:
    """Save the updated sensitivity report to the specified path."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Sensitivity report saved to {output_path}")

def main() -> int:
    """Main entry point for T041."""
    logger.info("Starting T041: Strengthen Robustness")
    
    # Paths
    input_path = "data/results/sensitivity_report.json"
    output_path = "data/results/sensitivity_report.json"
    
    try:
        # Load the existing sensitivity report
        report = load_sensitivity_report(input_path)
        logger.info(f"Loaded sensitivity report from {input_path}")
        
        # Update the report with explicit borderline logging and flags
        updated_report = update_sensitivity_flags(report)
        
        # Save the updated report
        save_sensitivity_report(updated_report, output_path)
        
        logger.info("T041 completed successfully")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"Input file not found: {e}")
        return 1
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in input file: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during T041 execution: {e}")
        return 1

if __name__ == "__main__":
    exit(main())