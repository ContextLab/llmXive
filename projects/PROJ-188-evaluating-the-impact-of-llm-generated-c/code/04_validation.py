"""
Validation script for User Story 1 (Dataset Curation).
Verifies the integrity of data/intermediate/explanations.json.
"""
import json
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Set

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Constants
VALID_COMPLEXITY_LABELS: Set[str] = {'low', 'medium', 'high'}
MAX_TOKEN_COUNT: int = 150
MIN_RECORD_COUNT: int = 20
REQUIRED_FIELDS: Set[str] = {'snippet_id', 'code', 'complexity', 'explanation', 'token_count', 'model_used', 'status'}


def load_data(file_path: Path) -> List[Dict[str, Any]]:
    """Load JSON data from file."""
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        raise FileNotFoundError(f"Data file not found: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if not isinstance(data, list):
        raise ValueError(f"Expected a list of records, got {type(data).__name__}")
    
    return data


def validate_record(record: Dict[str, Any], index: int) -> List[str]:
    """
    Validate a single record against all constraints.
    Returns a list of error messages (empty if valid).
    """
    errors = []
    
    # Check required fields
    missing_fields = REQUIRED_FIELDS - set(record.keys())
    if missing_fields:
        errors.append(f"Record {index}: Missing required fields: {missing_fields}")
    
    # Check for nulls in critical fields
    for field in REQUIRED_FIELDS:
        if field in record and record[field] is None:
            errors.append(f"Record {index}: Field '{field}' is null")
    
    # Validate complexity label
    if 'complexity' in record:
        if record['complexity'] not in VALID_COMPLEXITY_LABELS:
            errors.append(f"Record {index}: Invalid complexity label '{record['complexity']}'")
    
    # Validate token count
    if 'token_count' in record:
        try:
            count = int(record['token_count'])
            if count >= MAX_TOKEN_COUNT:
                errors.append(f"Record {index}: Token count {count} exceeds limit {MAX_TOKEN_COUNT}")
        except (ValueError, TypeError):
            errors.append(f"Record {index}: Invalid token_count value: {record['token_count']}")
    
    # Validate explanation is not empty if present
    if 'explanation' in record:
        if not record['explanation'] or not record['explanation'].strip():
            errors.append(f"Record {index}: Explanation is empty or whitespace")
    
    # Validate status
    if 'status' in record:
        if record['status'] not in ['success', 'skipped']:
            errors.append(f"Record {index}: Invalid status '{record['status']}'")
    
    return errors


def run_validation(input_path: Path) -> bool:
    """
    Run full validation suite on the dataset.
    Returns True if all validations pass, False otherwise.
    """
    logger.info(f"Starting validation of {input_path}")
    
    try:
        data = load_data(input_path)
    except (FileNotFoundError, ValueError) as e:
        logger.error(f"Failed to load data: {e}")
        return False
    
    total_records = len(data)
    logger.info(f"Loaded {total_records} records")
    
    # Check minimum count
    if total_records < MIN_RECORD_COUNT:
        logger.error(f"Record count {total_records} is below minimum {MIN_RECORD_COUNT}")
        return False
    
    all_errors: List[str] = []
    valid_count = 0
    skipped_count = 0
    success_count = 0
    
    for i, record in enumerate(data):
        errors = validate_record(record, i)
        if errors:
            all_errors.extend(errors)
        else:
            valid_count += 1
            if record.get('status') == 'skipped':
                skipped_count += 1
            elif record.get('status') == 'success':
                success_count += 1
    
    # Report results
    logger.info(f"Validation complete: {valid_count}/{total_records} valid records")
    logger.info(f"Successes: {success_count}, Skipped: {skipped_count}")
    
    if all_errors:
        logger.error(f"Found {len(all_errors)} validation errors:")
        for err in all_errors[:10]:  # Log first 10 errors
            logger.error(f"  - {err}")
        if len(all_errors) > 10:
            logger.error(f"  ... and {len(all_errors) - 10} more errors")
        return False
    
    logger.info("All validations passed!")
    return True


def main():
    """Main entry point."""
    input_file = Path("data/intermediate/explanations.json")
    
    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        print("Validation failed: Input file missing.")
        sys.exit(1)
    
    success = run_validation(input_file)
    
    if success:
        print("Validation PASSED")
        sys.exit(0)
    else:
        print("Validation FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()
