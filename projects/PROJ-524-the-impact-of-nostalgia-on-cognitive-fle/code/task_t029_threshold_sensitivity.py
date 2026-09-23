"""
T029: Borderline Flag Implementation
Adds logic to flag 'sensitive to threshold choice' if p-value falls in the range 0.04 <= p <= 0.06.
Updates data/results/sensitivity_report.json with the binary flag is_sensitive_to_threshold.
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List
from config import get_config, get_env_float
from utils import setup_logging, log_info, log_warning, log_error, load_json, save_json

# Constants
BORDERLINE_LOW = 0.04
BORDERLINE_HIGH = 0.06
TOLERANCE = 1e-9
SENSITIVITY_REPORT_PATH = "data/results/sensitivity_report.json"

def is_borderline(p_value: float) -> bool:
    """
    Check if a p-value falls within the borderline range [0.04, 0.06].
    
    Args:
        p_value: The p-value to check.
        
    Returns:
        True if 0.04 <= p_value <= 0.06 (with float tolerance), False otherwise.
    """
    if p_value is None:
        return False
    return (p_value >= BORDERLINE_LOW - TOLERANCE) and (p_value <= BORDERLINE_HIGH + TOLERANCE)

def analyze_threshold_sensitivity(report_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze the sensitivity report and update the is_sensitive_to_threshold flag
    for each threshold result based on the primary p-values.
    
    Args:
        report_data: The loaded sensitivity report dictionary.
        
    Returns:
        Updated report data with is_sensitive_to_threshold flags set.
    """
    summary = report_data.get("summary", {})
    primary_pe_p = summary.get("primary_pe_p_value")
    primary_cc_p = summary.get("primary_cc_p_value")
    
    results = report_data.get("results", [])
    
    for result in results:
        threshold = result.get("threshold")
        
        # Determine if the specific threshold result is borderline based on the primary p-values
        # The flag indicates if the significance status is sensitive to this specific threshold choice
        # i.e., if the p-value is in the borderline range, the result is sensitive to threshold choice.
        
        is_pe_borderline = is_borderline(primary_pe_p) if primary_pe_p is not None else False
        is_cc_borderline = is_borderline(primary_cc_p) if primary_cc_p is not None else False
        
        # The task requires a binary flag per result row. 
        # If either primary metric is borderline, the result is considered sensitive to threshold choice.
        result["is_sensitive_to_threshold"] = is_pe_borderline or is_cc_borderline
        
    return report_data

def run_threshold_sensitivity(report_path: str = SENSITIVITY_REPORT_PATH) -> Dict[str, Any]:
    """
    Main entry point for T029. Loads the sensitivity report, applies the borderline flag logic,
    and saves the updated report.
    
    Args:
        report_path: Path to the sensitivity report JSON file.
        
    Returns:
        The updated report data.
    """
    if not os.path.exists(report_path):
        log_error(f"Sensitivity report not found at {report_path}")
        raise FileNotFoundError(f"Report file not found: {report_path}")
        
    report_data = load_json(report_path)
    
    log_info(f"Analyzing threshold sensitivity for {report_path}")
    
    updated_report = analyze_threshold_sensitivity(report_data)
    
    save_json(updated_report, report_path)
    log_info(f"Updated sensitivity report saved to {report_path}")
    
    return updated_report

def main():
    """Main entry point for script execution."""
    setup_logging(level=logging.INFO)
    
    try:
        run_threshold_sensitivity()
        log_info("T029 completed successfully.")
    except Exception as e:
        log_error(f"Error during T029 execution: {str(e)}")
        raise

if __name__ == "__main__":
    main()
