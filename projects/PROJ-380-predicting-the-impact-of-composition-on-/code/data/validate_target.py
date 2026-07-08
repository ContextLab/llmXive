import os
import sys
import logging
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

def load_processed_data(input_path: str) -> List[Dict[str, Any]]:
    with open(input_path, 'r', newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))

def validate_target_no_missing(data: List[Dict[str, Any]], target_col: str = 'shear_modulus_gpa') -> bool:
    """
    Check if any rows have missing target values.
    Returns True if valid, False otherwise.
    """
    for i, row in enumerate(data):
        val = row.get(target_col)
        if val is None or val == '':
            logger.warning(f"Row {i} missing target value: {row}")
            return False
    return True

def save_validation_report(report: Dict[str, Any], output_path: str):
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=report.keys())
        writer.writeheader()
        writer.writerow(report)

def main():
    input_file = "data/processed/processed_bmg_features.csv"
    report_file = "data/processed/target_validation_report.csv"
    
    if len(sys.argv) >= 2:
        input_file = sys.argv[1]
    if len(sys.argv) >= 3:
        report_file = sys.argv[2]
        
    if not os.path.exists(input_file):
        logger.error(f"Input file not found: {input_file}")
        sys.exit(1)
        
    data = load_processed_data(input_file)
    is_valid = validate_target_no_missing(data)
    
    report = {
        "status": "valid" if is_valid else "invalid",
        "total_rows": len(data),
        "missing_targets": 0 if is_valid else "detected"
    }
    save_validation_report(report, report_file)
    logger.info(f"Validation complete: {report}")

if __name__ == "__main__":
    main()
