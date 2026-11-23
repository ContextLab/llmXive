"""
Validation script for LLM-generated explanations (Task T016).

Verifies:
1. No null values in critical fields (snippet_id, code, explanation, complexity, complexity_score)
2. All complexity labels are valid ('low', 'medium', 'high')
3. All token counts are < 200
4. Total number of records N >= 20

Input: data/intermediate/explanations.json
Output: data/processed/explanation_validation_report.json and console summary
"""
import json
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple, Set

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/intermediate/explanation_validation.log')
    ]
)
logger = logging.getLogger(__name__)

# Constants
INPUT_PATH = Path("data/intermediate/explanations.json")
OUTPUT_REPORT_PATH = Path("data/processed/explanation_validation_report.json")
MIN_RECORDS = 20
MAX_TOKENS = 200
VALID_LABELS: Set[str] = {'low', 'medium', 'high'}
REQUIRED_FIELDS: Set[str] = {'snippet_id', 'code', 'explanation', 'complexity', 'complexity_score'}

def load_data(input_path: Path) -> List[Dict[str, Any]]:
    """Load and parse the explanations JSON file."""
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if not isinstance(data, list):
        raise ValueError(f"Expected JSON list at {input_path}, got {type(data)}")
    
    logger.info(f"Loaded {len(data)} records from {input_path}")
    return data

def validate_record(record: Dict[str, Any], index: int) -> List[str]:
    """
    Validate a single record against all criteria.
    Returns a list of error messages (empty if valid).
    """
    errors = []
    
    # Check for null/missing required fields
    for field in REQUIRED_FIELDS:
        if field not in record or record[field] is None:
            errors.append(f"Record {index}: Missing or null field '{field}'")
        elif field == 'complexity' and record[field] not in VALID_LABELS:
            errors.append(f"Record {index}: Invalid complexity label '{record[field]}'. Expected one of {VALID_LABELS}")
    
    # Check token count constraint
    token_count = record.get('token_count')
    if token_count is None:
        errors.append(f"Record {index}: Missing 'token_count' field")
    elif not isinstance(token_count, (int, float)):
        errors.append(f"Record {index}: 'token_count' is not a number: {token_count}")
    elif token_count >= MAX_TOKENS:
        errors.append(f"Record {index}: Token count {token_count} exceeds limit of {MAX_TOKENS}")
    
    # Check explanation is not empty if present
    if 'explanation' in record and record['explanation'] is not None:
        if not isinstance(record['explanation'], str) or len(record['explanation'].strip()) == 0:
            errors.append(f"Record {index}: Explanation is empty or not a string")
    
    return errors

def run_validation(data: List[Dict[str, Any]]) -> Tuple[bool, Dict[str, Any]]:
    """
    Run all validation checks on the dataset.
    Returns (is_valid, summary_report).
    """
    all_errors = []
    record_results = []
    
    for i, record in enumerate(data):
        errors = validate_record(record, i)
        if errors:
            all_errors.extend(errors)
            record_results.append({
                "index": i,
                "valid": False,
                "errors": errors
            })
        else:
            record_results.append({
                "index": i,
                "valid": True,
                "errors": []
            })
    
    total_records = len(data)
    valid_count = sum(1 for r in record_results if r["valid"])
    invalid_count = total_records - valid_count
    
    summary = {
        "total_records": total_records,
        "valid_records": valid_count,
        "invalid_records": invalid_count,
        "min_records_met": total_records >= MIN_RECORDS,
        "all_labels_valid": all(
            r.get('complexity') in VALID_LABELS 
            for r in data 
            if r.get('complexity') is not None
        ),
        "all_tokens_under_limit": all(
            r.get('token_count', MAX_TOKENS) < MAX_TOKENS 
            for r in data
        ),
        "no_nulls": all(
            all(r.get(field) is not None for field in REQUIRED_FIELDS)
            for r in data
        ),
        "overall_valid": (
            total_records >= MIN_RECORDS and
            invalid_count == 0
        ),
        "error_count": len(all_errors),
        "errors": all_errors
    }
    
    return summary["overall_valid"], summary

def save_report(summary: Dict[str, Any], output_path: Path) -> None:
    """Save the validation report to JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, default=str)
    logger.info(f"Validation report saved to {output_path}")

def main() -> int:
    """Main entry point."""
    logger.info("Starting explanation validation (T016)...")
    
    try:
        # Load data
        data = load_data(INPUT_PATH)
        
        # Run validation
        is_valid, summary = run_validation(data)
        
        # Save report
        save_report(summary, OUTPUT_REPORT_PATH)
        
        # Log summary
        logger.info(f"Validation Summary:")
        logger.info(f"  Total Records: {summary['total_records']}")
        logger.info(f"  Valid Records: {summary['valid_records']}")
        logger.info(f"  Invalid Records: {summary['invalid_records']}")
        logger.info(f"  Min Records (N >= {MIN_RECORDS}): {'PASS' if summary['min_records_met'] else 'FAIL'}")
        logger.info(f"  All Labels Valid: {'PASS' if summary['all_labels_valid'] else 'FAIL'}")
        logger.info(f"  All Tokens < {MAX_TOKENS}: {'PASS' if summary['all_tokens_under_limit'] else 'FAIL'}")
        logger.info(f"  No Nulls: {'PASS' if summary['no_nulls'] else 'FAIL'}")
        logger.info(f"  Overall Status: {'PASS' if is_valid else 'FAIL'}")
        
        if summary['errors']:
            logger.warning(f"Found {len(summary['errors'])} validation errors:")
            for err in summary['errors'][:10]:  # Log first 10
                logger.warning(f"  - {err}")
            if len(summary['errors']) > 10:
                logger.warning(f"  ... and {len(summary['errors']) - 10} more")
        
        return 0 if is_valid else 1
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in input file: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during validation: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
