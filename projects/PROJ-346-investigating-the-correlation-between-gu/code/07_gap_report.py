import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# Import utils
try:
    from utils import get_data_processed_path, get_data_qc_path, setup_logger, write_json_log
except ImportError:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from utils import get_data_processed_path, get_data_qc_path, setup_logger, write_json_log

logger = setup_logger("gap_report")

def generate_gap_report(reason="No common participant IDs found"):
    """
    Generate a Data Gap Report (FR-008) indicating failure to link datasets.
    This is the fallback workflow trigger.
    """
    logger.info(f"Generating Data Gap Report: {reason}")
    
    processed_dir = get_data_processed_path()
    qc_dir = get_data_qc_path()
    
    # Ensure directories exist
    processed_dir.mkdir(parents=True, exist_ok=True)
    qc_dir.mkdir(parents=True, exist_ok=True)
    
    # Define output path: data/processed/data_gap_report.json
    # The error in the execution log showed a path issue: 
    # "IsADirectoryError: [Errno 21] Is a directory: '.../data/processed/data_gap_report.json'"
    # This implies `get_data_processed_path` might have returned a path that was treated as a directory
    # or the file path construction was incorrect in the previous version.
    # We will explicitly construct the file path.
    
    report_file = processed_dir / "data_gap_report.json"
    
    report_data = {
        "report_type": "Data Gap Report (FR-008)",
        "timestamp": datetime.now().isoformat(),
        "failure_reason": reason,
        "affected_studies": ["Qiita 10313", "UK Biobank/NHANES"],
        "status": "Linkage Failed",
        "framing": "associational only - No individual-level data available",
        "message": "No individual-level linkage possible; no valid meta-analysis possible without synthetic linkage.",
        "next_steps": "Trigger meta-analysis fallback or report gap."
    }
    
    # Use the fixed write_json_log utility if it handles paths correctly, 
    # or write directly to ensure the file is created.
    # The error log indicated write_json_log was called with a path that was a directory.
    # We will write directly here to ensure correctness.
    
    try:
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        logger.info(f"Gap report written to {report_file}")
    except Exception as e:
        logger.error(f"Failed to write gap report: {e}")
        raise

def trigger_meta_analysis():
    """Trigger the meta-analysis fallback workflow."""
    logger.info("Triggering meta-analysis fallback (T017d).")
    # In a real flow, this might call code/08_meta_analysis.py
    # For now, we just log it as part of the gap report process.

def main():
    """Main entry point for gap report generation."""
    logger.info("Starting Gap Report Generation.")
    
    # Check if merge failed (simulated by checking for specific log or condition)
    # For this task, we assume the caller indicates the failure reason.
    reason = "No common participant IDs found"
    
    generate_gap_report(reason=reason)
    trigger_meta_analysis()
    
    logger.info("Gap report generation complete.")

if __name__ == "__main__":
    main()
