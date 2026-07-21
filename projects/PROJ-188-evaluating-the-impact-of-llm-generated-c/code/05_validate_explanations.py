"""
Validation script for LLM-generated explanations (Task T016).

Verifies:
1. No null values in critical fields.
2. All complexity labels are valid ('low', 'medium', 'high').
3. All token counts are strictly less than 200.
4. Total record count N >= 20.

Input: data/intermediate/explanations.json
Output: data/processed/validation_report.json (summary)
        Exit code 0 on success, 1 on failure.
"""

import json
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
INPUT_PATH = Path("data/intermediate/explanations.json")
OUTPUT_PATH = Path("data/processed/validation_report.json")
MIN_RECORDS = 20
MAX_TOKENS = 200
VALID_LABELS = {'low', 'medium', 'high'}
REQUIRED_FIELDS = {'snippet_id', 'code', 'complexity', 'complexity_score', 'explanation', 'token_count', 'model_used', 'status'}

def load_data(path: Path) -> List[Dict[str, Any]]:
    """Load the explanations JSON file."""
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if not isinstance(data, list):
        raise ValueError(f"Expected JSON list at {path}, got {type(data)}")
    
    return data

def validate_record(record: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate a single explanation record.
    Returns (is_valid, list_of_errors).
    """
    errors = []
    
    # Check for nulls in critical fields
    for field in REQUIRED_FIELDS:
        if field not in record or record[field] is None:
            errors.append(f"Missing or null field: {field}")
    
    # If critical fields are missing, skip further checks for this record
    if errors:
        return False, errors

    # Validate complexity label
    label = record.get('complexity')
    if label not in VALID_LABELS:
        errors.append(f"Invalid complexity label: '{label}'. Must be one of {VALID_LABELS}")

    # Validate token count
    token_count = record.get('token_count')
    if not isinstance(token_count, (int, float)):
        errors.append(f"Invalid token_count type: {type(token_count)}")
    elif token_count >= MAX_TOKENS:
        errors.append(f"Token count {token_count} exceeds limit of {MAX_TOKENS}")

    # Validate explanation is not empty if status is success
    if record.get('status') == 'success':
        explanation = record.get('explanation')
        if not explanation or len(str(explanation).strip()) == 0:
            errors.append("Explanation is empty for a successful generation")

    return len(errors) == 0, errors

def run_validation(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Run validation on all records.
    Returns a summary report.
    """
    total = len(data)
    valid_count = 0
    invalid_indices = []
    error_details = []

    logger.info(f"Validating {total} records...")

    for i, record in enumerate(data):
        is_valid, errors = validate_record(record)
        if is_valid:
            valid_count += 1
        else:
            invalid_indices.append(i)
            error_details.append({
                "index": i,
                "snippet_id": record.get('snippet_id', 'UNKNOWN'),
                "errors": errors
            })
            logger.warning(f"Record {i} ({record.get('snippet_id')}) failed validation: {errors}")

    # Check N >= 20
    n_check_passed = total >= MIN_RECORDS

    report = {
        "total_records": total,
        "valid_records": valid_count,
        "invalid_records": total - valid_count,
        "n_check_passed": n_check_passed,
        "n_threshold": MIN_RECORDS,
        "token_limit": MAX_TOKENS,
        "valid_labels": list(VALID_LABELS),
        "validation_passed": n_check_passed and (total - valid_count) == 0,
        "error_count": len(invalid_indices),
        "sample_errors": error_details[:5]  # Limit sample size for report
    }

    if error_details:
        logger.warning(f"Found {len(invalid_indices)} invalid records.")
    else:
        logger.info("All records passed validation.")

    if not n_check_passed:
        logger.error(f"Record count {total} is below minimum {MIN_RECORDS}.")

    return report

def save_report(report: Dict[str, Any], path: Path) -> None:
    """Save the validation report to JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Validation report saved to {path}")

def main() -> int:
    """Main entry point."""
    try:
        if not INPUT_PATH.exists():
            logger.error(f"Input file missing: {INPUT_PATH}")
            logger.error("Ensure code/01_data_curation.py has been run successfully first.")
            return 1

        data = load_data(INPUT_PATH)
        report = run_validation(data)
        save_report(report, OUTPUT_PATH)

        if report["validation_passed"]:
            logger.info("Validation PASSED.")
            return 0
        else:
            logger.error("Validation FAILED.")
            return 1

    except Exception as e:
        logger.exception(f"Validation failed with exception: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())