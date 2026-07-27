"""
Module: verify_annotation_output

Purpose:
    Verifies the output of the annotation process to ensure data integrity
    and correctness of the generated columns.

Functions:
    - verify_annotation_output: Performs verification checks.
    - main: Entry point for the script.
"""
import csv
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Union

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_annotation_output(file_path: Path) -> Dict[str, Any]:
    """
    Verifies the annotation output file.

    Args:
        file_path (Path): Path to the annotated CSV.

    Returns:
        Dict[str, Any]: Verification report.
    """
    required_columns = ['id', 'question', 'answer', 'entity_node_id', 'confidence', 'chain_length', 'chain_bin', 'correctness']
    issues = []
    row_count = 0

    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames

        if not headers:
            issues.append("No headers found in file.")
            return {"valid": False, "issues": issues}

        missing = set(required_columns) - set(headers)
        if missing:
            issues.append(f"Missing columns: {missing}")

        for row in reader:
            row_count += 1
            # Basic type checks could go here
            if row.get('chain_length') == '':
                issues.append(f"Row {row_count}: Empty chain_length")

    return {
        "valid": len(issues) == 0,
        "row_count": row_count,
        "issues": issues
    }

def main():
    """
    Main entry point for the verify_annotation_output script.
    """
    logger.info("Verifying annotation output...")
    file_path = Path("data/processed/annotated_videokr.csv")
    result = verify_annotation_output(file_path)

    if result["valid"]:
        logger.info(f"Verification passed. Rows: {result['row_count']}")
    else:
        logger.error(f"Verification failed. Issues: {result['issues']}")
        sys.exit(1)

if __name__ == "__main__":
    main()
