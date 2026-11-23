"""
Task T070: Validate Threshold Sweep Completeness.
Verifies that the threshold sweep covers the full range of relevant values
and that data/results/threshold_sweep.json contains valid entries for all specified thresholds.
"""
import os
import sys
import json
import logging
import argparse
from typing import List, Dict, Any, Set

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Expected thresholds defined in T025b
EXPECTED_THRESHOLDS: Set[float] = {0.90, 0.92, 0.94, 0.95, 0.96, 0.98}
SWEEP_FILE_PATH: str = "data/results/threshold_sweep.json"

class ThresholdSweepValidationError(Exception):
    """Raised when threshold sweep validation fails."""
    pass

def load_sweep_result(filepath: str) -> Dict[str, Any]:
    """Load and parse the threshold sweep JSON file."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Sweep result file not found: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return data

def validate_sweep_completeness(data: Dict[str, Any]) -> bool:
    """
    Validate that the sweep covers all expected thresholds.
    
    Args:
        data: The loaded sweep result dictionary.
        
    Returns:
        True if valid, raises ThresholdSweepValidationError otherwise.
    """
    results = data.get("results", [])
    if not results:
        raise ThresholdSweepValidationError("No results found in sweep file.")
    
    # Collect all unique thresholds present in the results
    present_thresholds: Set[float] = set()
    for entry in results:
        threshold = entry.get("threshold")
        if threshold is not None:
            present_thresholds.add(float(threshold))
    
    # Check for missing thresholds
    missing = EXPECTED_THRESHOLDS - present_thresholds
    extra = present_thresholds - EXPECTED_THRESHOLDS
    
    if missing:
        raise ThresholdSweepValidationError(
            f"Missing required thresholds: {sorted(missing)}. "
            f"Expected: {sorted(EXPECTED_THRESHOLDS)}, Found: {sorted(present_thresholds)}."
        )
    
    if extra:
        logger.warning(
            f"Extra thresholds found (not in T025b spec): {sorted(extra)}. "
            f"This is allowed but not required."
        )
    
    # Validate structure of each entry
    required_fields = {"seed", "variant", "ndcg_score", "wasted_call_ratio", "total_calls", 
                     "wasted_calls", "runtime_seconds", "peak_memory_mb", "threshold", "reduction_percentage"}
    
    for i, entry in enumerate(results):
        missing_fields = required_fields - set(entry.keys())
        if missing_fields:
            raise ThresholdSweepValidationError(
                f"Result entry {i} missing fields: {missing_fields}. Entry: {entry}"
            )
    
    logger.info(f"Validation passed. Found thresholds: {sorted(present_thresholds)}")
    logger.info(f"Required thresholds covered: {sorted(EXPECTED_THRESHOLDS)}")
    return True

def write_validation_report(filepath: str, is_valid: bool, details: Dict[str, Any]) -> None:
    """Write the validation report to a JSON file."""
    report = {
        "task_id": "T070",
        "validation_status": "passed" if is_valid else "failed",
        "expected_thresholds": sorted(list(EXPECTED_THRESHOLDS)),
        "details": details
    }
    
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Validation report written to {filepath}")

def main():
    parser = argparse.ArgumentParser(description="Validate threshold sweep completeness (T070)")
    parser.add_argument(
        "--input", 
        type=str, 
        default=SWEEP_FILE_PATH,
        help=f"Path to the threshold sweep JSON file (default: {SWEEP_FILE_PATH})"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/results/t070_validation_report.json",
        help="Path to write the validation report"
    )
    
    args = parser.parse_args()
    
    try:
        logger.info(f"Loading sweep results from {args.input}")
        data = load_sweep_result(args.input)
        
        logger.info("Validating sweep completeness...")
        is_valid = validate_sweep_completeness(data)
        
        details = {
            "message": "All required thresholds present and valid."
        }
        
        write_validation_report(args.output, is_valid, details)
        
        if is_valid:
            logger.info("SUCCESS: Threshold sweep validation passed.")
            sys.exit(0)
        else:
            logger.error("FAILURE: Threshold sweep validation failed.")
            sys.exit(1)
            
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        write_validation_report(args.output, False, {"error": str(e)})
        sys.exit(1)
    except ThresholdSweepValidationError as e:
        logger.error(f"Validation error: {e}")
        write_validation_report(args.output, False, {"error": str(e)})
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Unexpected error during validation: {e}")
        write_validation_report(args.output, False, {"error": str(e)})
        sys.exit(1)

if __name__ == "__main__":
    main()