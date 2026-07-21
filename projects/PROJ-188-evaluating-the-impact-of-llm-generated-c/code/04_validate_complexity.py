import json
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Define the mapping logic used in T013
# These ranges must match the logic in code/01_data_curation.py
COMPLEXITY_THRESHOLDS = {
    "low": (0.0, 10.0),
    "medium": (10.0, 25.0),
    "high": (25.0, float("inf"))
}

def load_data(input_path: str) -> List[Dict[str, Any]]:
    """Load the intermediate data file containing snippets and complexity scores."""
    path = Path(input_path)
    if not path.exists():
        logger.error(f"Input file not found: {input_path}")
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    logger.info(f"Loaded {len(data)} records from {input_path}")
    return data

def validate_record(record: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate a single record to ensure the 'complexity' label correctly 
    maps to the 'complexity_score' range.
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if "complexity_score" not in record:
        return False, "Missing 'complexity_score' field"
    
    if "complexity" not in record:
        return False, "Missing 'complexity' field"
    
    score = record["complexity_score"]
    label = record["complexity"]
    
    if not isinstance(score, (int, float)):
        return False, f"complexity_score must be numeric, got {type(score)}"
    
    if label not in COMPLEXITY_THRESHOLDS:
        return False, f"Invalid complexity label: {label}. Must be one of {list(COMPLEXITY_THRESHOLDS.keys())}"
    
    min_val, max_val = COMPLEXITY_THRESHOLDS[label]
    
    # Check boundary conditions
    # Low: 0 <= score < 10
    # Medium: 10 <= score < 25
    # High: score >= 25
    
    is_valid = False
    if label == "low":
        is_valid = (0.0 <= score < 10.0)
    elif label == "medium":
        is_valid = (10.0 <= score < 25.0)
    elif label == "high":
        is_valid = (score >= 25.0)
    
    if not is_valid:
        return False, f"Label '{label}' does not match score {score} (expected range: {min_val}-{max_val})"
    
    return True, ""

def run_validation(input_path: str) -> Dict[str, Any]:
    """
    Run validation on the entire dataset.
    
    Returns:
        Summary dictionary with counts and any errors found.
    """
    data = load_data(input_path)
    valid_count = 0
    invalid_records = []
    
    for i, record in enumerate(data):
        is_valid, error_msg = validate_record(record)
        if is_valid:
            valid_count += 1
        else:
            invalid_records.append({
                "index": i,
                "snippet_id": record.get("snippet_id", "unknown"),
                "error": error_msg
            })
    
    total = len(data)
    success_rate = (valid_count / total * 100) if total > 0 else 0.0
    
    summary = {
        "total_records": total,
        "valid_records": valid_count,
        "invalid_records": len(invalid_records),
        "success_rate": f"{success_rate:.2f}%",
        "errors": invalid_records
    }
    
    return summary

def main():
    input_file = "data/intermediate/explanations.json"
    logger.info(f"Starting complexity validation for {input_file}")
    
    try:
        summary = run_validation(input_file)
        
        logger.info(f"Validation Complete:")
        logger.info(f"  Total: {summary['total_records']}")
        logger.info(f"  Valid: {summary['valid_records']}")
        logger.info(f"  Invalid: {summary['invalid_records']}")
        logger.info(f"  Success Rate: {summary['success_rate']}")
        
        if summary['invalid_records'] > 0:
            logger.warning(f"Found {summary['invalid_records']} invalid records. Details below:")
            for err in summary['errors'][:10]:  # Show first 10 errors
                logger.warning(f"  - [{err['snippet_id']}] {err['error']}")
            if len(summary['errors']) > 10:
                logger.warning(f"  ... and {len(summary['errors']) - 10} more errors")
            sys.exit(1)
        else:
            logger.info("All records passed validation.")
            sys.exit(0)
            
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()