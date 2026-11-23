"""
T026a Implementation: Critical Guardrail for Sample Size Sufficiency.

Reads the derived power analysis CSV, filters for valid records,
and enforces the minimum sample size (SC-004: >= 30 studies).
If the count is insufficient, it halts execution and writes an error artifact.
"""
import csv
import json
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
MIN_STUDY_COUNT = 30  # SC-004 requirement
INPUT_FILE = Path("data/derived/power_analysis.csv")
ERROR_OUTPUT_DIR = Path("results/error")
ERROR_OUTPUT_FILE = ERROR_OUTPUT_DIR / "sample_size_insufficient.json"

def load_power_analysis(csv_path: Path) -> List[Dict[str, Any]]:
    """Load the power analysis CSV and return a list of records."""
    if not csv_path.exists():
        raise FileNotFoundError(f"Input file not found: {csv_path}")
    
    records = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(row)
    
    logger.info(f"Loaded {len(records)} total records from {csv_path}")
    return records

def filter_valid_records(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filter records to include only those with valid power calculations.
    
    A record is considered 'valid' if:
    1. 'sensitivity_power' is present and is a valid float (not NaN/Inf).
    2. 'power_gap' is present and is a valid float.
    3. No critical calculation errors are flagged (e.g., 'calculation_error' is False or missing).
    
    We assume the CSV columns 'sensitivity_power' and 'power_gap' exist.
    """
    valid_records = []
    
    for i, record in enumerate(records):
        try:
            # Check for sensitivity_power
            sp_val = record.get('sensitivity_power')
            if sp_val is None or sp_val == '':
                continue
              
            sp_float = float(sp_val)
            if not (0.0 <= sp_float <= 1.0):
                # Power must be a probability
                logger.warning(f"Record {i}: Invalid sensitivity_power value {sp_val}")
                continue

            # Check for power_gap
            pg_val = record.get('power_gap')
            if pg_val is None or pg_val == '':
                continue
              
            pg_float = float(pg_val)
            # Power gap can be negative or positive, just needs to be a number
            if pg_float != pg_float: # Check for NaN
                logger.warning(f"Record {i}: Invalid power_gap value (NaN)")
                continue

            # Check for explicit error flags if they exist
            if record.get('calculation_error', 'false').lower() in ['true', 'yes', '1']:
                logger.warning(f"Record {i}: Marked as having a calculation error")
                continue

            valid_records.append(record)
            
        except (ValueError, TypeError) as e:
            logger.warning(f"Record {i}: Failed to parse numeric values ({e})")
            continue

    logger.info(f"Filtered to {len(valid_records)} valid records")
    return valid_records

def write_error_artifact(count: int, reason: str, output_path: Path) -> None:
    """Write the error artifact JSON if the sample size is insufficient."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    error_doc = {
        "status": "HALTED",
        "reason": reason,
        "details": {
            "required_minimum": MIN_STUDY_COUNT,
            "actual_count": count,
            "threshold_met": count >= MIN_STUDY_COUNT
        },
        "action": "Review data extraction pipeline. Insufficient valid studies found for statistical validity assessment.",
        "timestamp": str(Path(__file__).parent.stat().st_mtime) # Placeholder for actual timestamp logic
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(error_doc, f, indent=2)
    
    logger.error(f"Error artifact written to {output_path}")

def main() -> int:
    """
    Main entry point for the guardrail check.
    
    Returns:
        0 if the sample size is sufficient (>= 30).
        1 if the sample size is insufficient (halts execution).
    """
    logger.info(f"Starting guardrail check for {INPUT_FILE}")
    
    if not INPUT_FILE.exists():
        logger.error(f"Input file {INPUT_FILE} does not exist. Cannot proceed.")
        return 1
    
    try:
        all_records = load_power_analysis(INPUT_FILE)
        valid_records = filter_valid_records(all_records)
        count = len(valid_records)
        
        logger.info(f"Valid study count: {count} (Required: >= {MIN_STUDY_COUNT})")
        
        if count < MIN_STUDY_COUNT:
            reason = f"Insufficient valid studies for statistical power validity assessment. Found {count}, required {MIN_STUDY_COUNT}."
            write_error_artifact(count, reason, ERROR_OUTPUT_FILE)
            logger.error("GUARDRAIL TRIGGERED: Execution halted due to insufficient sample size.")
            return 1
        
        logger.info("GUARDRAIL PASSED: Sample size is sufficient. Proceeding to next stage.")
        return 0
        
    except Exception as e:
        logger.exception(f"Guardrail check failed with unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
