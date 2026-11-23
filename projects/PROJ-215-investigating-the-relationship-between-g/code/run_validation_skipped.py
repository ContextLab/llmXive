"""
Implementation for T032b: Validation Skipped Scenario.

This module handles the case where no independent cohort is accessible.
It logs the skip reason and writes a specific status report to satisfy
the Single Source of Truth requirement.
"""
import logging
import os
import json
from pathlib import Path
from code.config import get_output_path
from code.utils.logging import get_logger

def write_skipped_validation_report(logger: logging.Logger, output_dir: Path) -> dict:
    """
    Writes the validation report indicating that validation was skipped
    due to lack of accessible independent cohorts.
    
    Args:
        logger: The logger instance to record the action.
        output_dir: The directory where the report should be saved.
        
    Returns:
        A dictionary containing the status details.
    """
    # Ensure the results directory exists
    results_dir = output_dir / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    
    report_path = results_dir / "validation_report.txt"
    
    status_message = "Validation Skipped: No independent cohort available"
    sc003_status = "Not Applicable"
    
    # Write the text report (Single Source of Truth)
    try:
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(f"Status: {status_message}\n")
            f.write(f"SC-003 (Validation Threshold): {sc003_status}\n")
            f.write(f"Reason: Independent cohort (e.g., UK Biobank, MetaHIT) not accessible.\n")
            f.write(f"Action: Proceeding without external validation.\n")
        
        logger.info(f"Validation skipped report written to: {report_path}")
    except IOError as e:
        logger.error(f"Failed to write validation report: {e}")
        raise
    
    # Also write a JSON status file for programmatic consumption
    json_path = results_dir / "validation_skipped_status.json"
    status_data = {
        "status": "skipped",
        "message": status_message,
        "sc003_status": sc003_status,
        "reason": "Independent cohort not accessible",
        "timestamp": None # Timestamp handled by caller if needed, or left as None for this static report
    }
    
    try:
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(status_data, f, indent=2)
        logger.info(f"Validation skipped JSON status written to: {json_path}")
    except IOError as e:
        logger.error(f"Failed to write validation JSON status: {e}")
        raise
        
    return status_data

def main():
    """
    Entry point for T032b execution.
    """
    logger = get_logger("validation_skipped")
    logger.info("Starting T032b: Validation Skipped Scenario")
    
    # Get output path based on project config
    output_dir = get_output_path()
    
    try:
        result = write_skipped_validation_report(logger, output_dir)
        logger.info("T032b completed successfully.")
        print(f"Validation status: {result['status']}")
        print(f"SC-003 Status: {result['sc003_status']}")
        return 0
    except Exception as e:
        logger.error(f"T032b failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())