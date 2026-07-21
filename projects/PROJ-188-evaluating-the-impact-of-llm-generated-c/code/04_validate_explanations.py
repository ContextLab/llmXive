"""
Validation script for User Story 1: Explanations.

Verifies the output of T014 (generate_explanation) in data/intermediate/explanations.json:
1. No null values in critical fields.
2. All complexity labels are valid ('low', 'medium', 'high').
3. Token counts are strictly less than 200.
4. Total number of records (N) is at least 20.

Usage:
    python code/04_validate_explanations.py
"""
import json
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Constants
INPUT_FILE = Path("data/intermediate/explanations.json")
VALID_LABELS = {'low', 'medium', 'high'}
MAX_TOKENS = 200
MIN_RECORDS = 20
REQUIRED_FIELDS = ['snippet_id', 'code', 'complexity', 'complexity_score', 'explanation', 'token_count', 'model_used', 'status']

def load_data(file_path: Path) -> List[Dict[str, Any]]:
    """Load the explanations JSON file."""
    if not file_path.exists():
        raise FileNotFoundError(f"Input file not found: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if not isinstance(data, list):
        raise ValueError(f"Expected a list of records in {file_path}, got {type(data)}")
    
    return data

def validate_record(record: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate a single explanation record.
    Returns (is_valid, list_of_error_messages).
    """
    errors = []
    
    # Check for missing required fields
    for field in REQUIRED_FIELDS:
        if field not in record:
            errors.append(f"Missing required field: '{field}'")
        elif record[field] is None:
            errors.append(f"Null value in required field: '{field}'")
    
    if errors:
        return False, errors

    # Check complexity label validity
    complexity = record.get('complexity')
    if complexity not in VALID_LABELS:
        errors.append(f"Invalid complexity label: '{complexity}'. Expected one of {VALID_LABELS}")

    # Check token count
    token_count = record.get('token_count')
    if not isinstance(token_count, (int, float)):
        errors.append(f"token_count is not a number: {type(token_count)}")
    elif token_count >= MAX_TOKENS:
        errors.append(f"Token count {token_count} exceeds limit {MAX_TOKENS}")

    # Check snippet_id is not empty
    snippet_id = record.get('snippet_id')
    if not snippet_id:
        errors.append("snippet_id is empty or missing")

    # Check explanation is not empty
    explanation = record.get('explanation')
    if not explanation or len(str(explanation).strip()) == 0:
        errors.append("Explanation is empty")

    return len(errors) == 0, errors

def run_validation(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Run validation checks on the entire dataset.
    Returns a summary report.
    """
    total = len(data)
    valid_count = 0
    invalid_records = []
    null_count = 0
    label_errors = 0
    token_errors = 0

    logger.info(f"Starting validation on {total} records...")

    for i, record in enumerate(data):
        is_valid, errors = validate_record(record)
        
        if is_valid:
            valid_count += 1
        else:
            invalid_records.append({
                "index": i,
                "snippet_id": record.get('snippet_id', 'UNKNOWN'),
                "errors": errors
            })
            # Tally specific error types for summary
            for err in errors:
                if "Null" in err:
                    null_count += 1
                elif "Invalid complexity" in err:
                    label_errors += 1
                elif "Token count" in err:
                    token_errors += 1

    # Check N >= 20
    n_check_passed = valid_count >= MIN_RECORDS
    
    # Check no nulls (strictly speaking, we want 0 null errors)
    null_check_passed = null_count == 0
    
    # Check all labels valid
    label_check_passed = label_errors == 0
    
    # Check all tokens < 200
    token_check_passed = token_errors == 0

    report = {
        "total_records": total,
        "valid_records": valid_count,
        "invalid_records_count": len(invalid_records),
        "checks": {
            "n_ge_20": n_check_passed,
            "no_nulls": null_check_passed,
            "valid_labels": label_check_passed,
            "tokens_lt_200": token_check_passed
        },
        "error_counts": {
            "nulls": null_count,
            "invalid_labels": label_errors,
            "invalid_tokens": token_errors
        },
        "all_passed": all([n_check_passed, null_check_passed, label_check_passed, token_check_passed])
    }

    return report, invalid_records

def main():
    """Main entry point."""
    try:
        if not INPUT_FILE.exists():
            logger.error(f"Validation failed: Input file missing at {INPUT_FILE}")
            logger.error("Please ensure T014 (generate_explanation) has run successfully.")
            sys.exit(1)

        data = load_data(INPUT_FILE)
        
        if len(data) == 0:
            logger.error("Validation failed: Input file is empty.")
            sys.exit(1)

        report, invalid_records = run_validation(data)

        # Log Summary
        logger.info("-" * 40)
        logger.info("VALIDATION SUMMARY")
        logger.info("-" * 40)
        logger.info(f"Total Records: {report['total_records']}")
        logger.info(f"Valid Records: {report['valid_records']}")
        logger.info(f"Checks Passed: {report['checks']}")
        
        if report['all_passed']:
            logger.info("RESULT: SUCCESS - All validation checks passed.")
            logger.info(f"N = {report['valid_records']} (>= {MIN_RECORDS})")
            sys.exit(0)
        else:
            logger.error("RESULT: FAILURE - One or more validation checks failed.")
            for check, passed in report['checks'].items():
                if not passed:
                    logger.error(f"  - Failed: {check}")
            
            if invalid_records:
                logger.warning(f"First 5 invalid records details:")
                for item in invalid_records[:5]:
                    logger.warning(f"  Index {item['index']} ({item['snippet_id']}): {item['errors']}")
            
            sys.exit(1)

    except FileNotFoundError as e:
        logger.error(f"File Error: {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"JSON Parse Error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()