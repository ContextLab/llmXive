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
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/intermediate/complexity_validation.log', mode='w')
    ]
)
logger = logging.getLogger(__name__)

# Constants for complexity thresholds
COMPLEXITY_THRESHOLDS = {
    'low': 5,
    'medium': 10,
    'high': float('inf')
}

def load_data(file_path: str) -> List[Dict[str, Any]]:
    """Load the processed snippets data from JSON."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {file_path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return data

def validate_record(record: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate that complexity_label correctly maps to complexity_score.
    
    Logic:
    - low if score < 5
    - medium if 5 <= score <= 10
    - high if score > 10
    """
    score = record.get('complexity_score')
    label = record.get('complexity_label')
    
    if score is None:
        return False, "Missing complexity_score"
    if label is None:
        return False, "Missing complexity_label"
    
    expected_label = None
    if score < COMPLEXITY_THRESHOLDS['low']:
        expected_label = 'low'
    elif score <= COMPLEXITY_THRESHOLDS['medium']:
        expected_label = 'medium'
    else:
        expected_label = 'high'
    
    if label != expected_label:
        return False, f"Mismatch: score={score}, label={label}, expected={expected_label}"
    
    return True, "OK"

def run_validation(data_path: str = 'data/intermediate/processed_snippets.json') -> bool:
    """
    Run validation on all records in the data file.
    Exits with code 0 if all assertions pass, 1 otherwise.
    """
    logger.info(f"Starting validation for {data_path}")
    
    try:
        data = load_data(data_path)
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        return False
    
    if not data:
        logger.warning("Data file is empty. Validation passed vacuously.")
        return True
    
    logger.info(f"Validating {len(data)} records...")
    
    failures = []
    for i, record in enumerate(data):
        is_valid, msg = validate_record(record)
        if not is_valid:
            failures.append((i, record.get('snippet_id', 'unknown'), msg))
            logger.error(f"Record {i} (ID: {record.get('snippet_id', 'unknown')}): {msg}")
        else:
            logger.debug(f"Record {i} passed.")
    
    if failures:
        logger.error(f"Validation FAILED: {len(failures)} records failed.")
        logger.error("First 5 failures:")
        for idx, snippet_id, msg in failures[:5]:
            logger.error(f"  - {snippet_id}: {msg}")
        return False
    
    logger.info("Validation PASSED: All records have correct complexity_label mapping.")
    return True

def main():
    """Entry point for the validation script."""
    # Default path matches the output of T012/T013b/T013 pipeline
    data_path = 'data/intermediate/processed_snippets.json'
    
    success = run_validation(data_path)
    
    if success:
        logger.info("Exiting with code 0 (Success)")
        sys.exit(0)
    else:
        logger.error("Exiting with code 1 (Failure)")
        sys.exit(1)

if __name__ == '__main__':
    main()