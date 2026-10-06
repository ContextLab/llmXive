"""
Data Gap Report Generator

Implements T017b: Checks if valid_subject_count is zero. If so, generates
data/data_gap_report.json with reason populated from data/exclusions.csv
and logs the error to logs/processing.log.

This script is invoked by the main pipeline (code/main.py) after T017 completes.
"""
import json
import os
import sys
import csv
from pathlib import Path
from datetime import datetime

# Ensure we can import from the project root
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from synchrony import get_logger

# Initialize logger
logger = get_logger("data_gap_report_generator")

# Paths
EXCLUSIONS_PATH = PROJECT_ROOT / "data" / "exclusions.csv"
DATA_GAP_REPORT_PATH = PROJECT_ROOT / "data" / "data_gap_report.json"
LOGS_DIR = PROJECT_ROOT / "logs"
LOG_FILE = LOGS_DIR / "processing.log"

def load_schema():
    """Load the schema from contracts if available, otherwise return default structure."""
    schema_path = PROJECT_ROOT / "contracts" / "data_gap_report.schema.yaml"
    if schema_path.exists():
        # In a real implementation, we'd parse YAML here.
        # For now, we return the expected structure based on the spec.
        return {
            "required": ["dataset_id", "reason", "timestamp"],
            "optional": ["fallback_id"]
        }
    return None

def generate_data_gap_report_from_exclusions(valid_subject_count: int) -> dict:
    """
    Generate a data gap report if valid_subject_count is zero.
    
    Args:
        valid_subject_count: The count of valid subjects from T017.
        
    Returns:
        A dictionary representing the data gap report, or None if no report is needed.
    """
    if valid_subject_count > 0:
        # No gap, no report needed
        return None

    # If we are here, valid_subject_count is zero.
    # We need to generate the report.
    
    reason = "all_subjects_excluded"
    
    # Try to read exclusions.csv to determine the specific reason
    if EXCLUSIONS_PATH.exists():
        try:
            with open(EXCLUSIONS_PATH, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                reasons = set()
                for row in reader:
                    if 'reason' in row and row['reason']:
                        reasons.add(row['reason'])
                
                if reasons:
                    reason = ", ".join(sorted(reasons))
        except Exception as e:
            logger.log("error_reading_exclusions", error=str(e))
    else:
        reason = "no_exclusions_file_found"

    report = {
        "dataset_id": "unknown",  # Will be overwritten if we can read selected_dataset_id.txt
        "reason": reason,
        "timestamp": datetime.utcnow().isoformat(),
        "fallback_id": None
    }

    # Try to read the selected dataset ID if it exists
    dataset_id_file = PROJECT_ROOT / "data" / "selected_dataset_id.txt"
    if dataset_id_file.exists():
        try:
            with open(dataset_id_file, 'r', encoding='utf-8') as f:
                ds_id = f.read().strip()
                if ds_id:
                    report["dataset_id"] = ds_id
        except Exception:
            pass

    return report

def write_report(report: dict):
    """Write the report to data/data_gap_report.json."""
    # Ensure data directory exists
    DATA_GAP_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    with open(DATA_GAP_REPORT_PATH, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    logger.log("report_written", path=str(DATA_GAP_REPORT_PATH))

def log_error(reason: str):
    """Log the error to logs/processing.log."""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    
    log_entry = f"[{datetime.utcnow().isoformat()}] ERROR: No verified task-switching dataset found. Reason: {reason}\n"
    
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(log_entry)

def main():
    """
    Main entry point for T017b.
    
    This function is expected to be called by code/main.py with the valid_subject_count.
    For standalone execution, it expects the count to be passed via environment variable
    or command line argument (for testing purposes).
    """
    # Try to get valid_subject_count from command line or environment
    # In the real pipeline, main.py will call this function directly or pass the count
    valid_subject_count = 0
    
    if len(sys.argv) > 1:
        try:
            valid_subject_count = int(sys.argv[1])
        except ValueError:
            print("Invalid argument. Usage: python data_gap_report_generator.py <valid_subject_count>")
            sys.exit(1)
    elif os.environ.get('VALID_SUBJECT_COUNT'):
        try:
            valid_subject_count = int(os.environ['VALID_SUBJECT_COUNT'])
        except ValueError:
            print("Invalid environment variable VALID_SUBJECT_COUNT")
            sys.exit(1)
    else:
        # Default to 0 for safety if called standalone without args
        print("No valid_subject_count provided. Assuming 0 (generating report).")
        valid_subject_count = 0

    logger.log("check_valid_subject_count", count=valid_subject_count)

    if valid_subject_count == 0:
        report = generate_data_gap_report_from_exclusions(valid_subject_count)
        if report:
            write_report(report)
            log_error(report["reason"])
            print(f"Data Gap Report generated: {DATA_GAP_REPORT_PATH}")
            print(f"Reason: {report['reason']}")
            # HALT execution with code 1 as per T017b spec
            sys.exit(1)
    else:
        print(f"Valid subject count is {valid_subject_count}. No data gap report needed.")
        sys.exit(0)

if __name__ == "__main__":
    main()