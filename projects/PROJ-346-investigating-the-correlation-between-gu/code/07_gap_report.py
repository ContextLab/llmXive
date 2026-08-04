import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# Import shared utilities
from utils import (
    get_project_root_path,
    get_data_processed_path,
    get_data_qc_path,
    setup_logger,
    write_json_log
)

logger = setup_logger("gap_report")

def generate_gap_report(reason: str = "Unknown reason"):
    """
    Generate a structured Data Gap Report artifact.
    Documents the inability to link individual-level data.
    Logs the specific reason and marks SC-001/SC-004 as "Not Measurable".
    This function implements FR-008 fallback behavior.
    
    Args:
        reason: The specific reason for the data gap (e.g., "No common sample IDs").
    
    Returns:
        dict: The generated report data.
    """
    logger.warning("Generating Data Gap Report (FR-008 fallback)...")
    
    # Determine output path: The task specifies data/processed/data_gap_report.json
    processed_path = get_data_processed_path()
    report_file = processed_path / "data_gap_report.json"
    
    # Ensure the directory exists
    processed_path.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().isoformat()
    
    report_data = {
        "timestamp": timestamp,
        "status": "Data Gap Detected",
        "measureability": {
            "SC-001": "Not Measurable",
            "SC-004": "Not Measurable"
        },
        "reason": reason,
        "details": {
            "action_taken": "Skipped statistical synthesis (FR-008 fallback)",
            "next_steps": "Review data sources for individual-level linkage keys (sample_id)",
            "affected_studies": [
                "Gut Microbiome Composition Study",
                "Cognitive Flexibility Assessment"
            ],
            "pipeline_status": "TERMINATED_AT_PREPROCESSING",
            "associational_framing": "No association could be measured due to data gap.",
            "causal_claims": "None made. Pipeline halted before analysis."
        }
    }
    
    logger.info(f"Writing gap report to {report_file}")
    write_json_log(report_data, report_file)
    
    logger.info(f"Data Gap Report saved. Reason: {reason}")
    return report_data

def main():
    """
    Entry point for generating the gap report.
    Can be called directly or invoked from 02_preprocess.py when merge fails.
    This script is designed to run and produce the required artifact.
    """
    reason = "Individual-level linkage failed: No common sample IDs found between microbiome and cognitive datasets."
    generate_gap_report(reason=reason)
    logger.info("Gap report generation complete.")

if __name__ == "__main__":
    main()