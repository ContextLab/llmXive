"""
Validation script for T022: Ensure teacher_logits_raw.jsonl is complete and matches expected prompt count.

Logic:
1. Load data/context_splits.json to calculate expected total unselected rationales.
2. Count lines in data/teacher_logits_raw.jsonl.
3. Assert line count == expected count.
4. Validate schema of each line (prompt_id, rationale_id, logits, tokens).

Output: results/validation_report.json with status, expected_count, actual_count.
Exits with code 0 on pass, 1 on fail.
"""
import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CONTEXT_SPLITS_PATH = PROJECT_ROOT / "data" / "context_splits.json"
TEACHER_LOGITS_PATH = PROJECT_ROOT / "data" / "teacher_logits_raw.jsonl"
RESULTS_DIR = PROJECT_ROOT / "results"
VALIDATION_REPORT_PATH = RESULTS_DIR / "validation_report.json"

def load_context_splits() -> List[Dict[str, Any]]:
    """Load the context splits file."""
    if not CONTEXT_SPLITS_PATH.exists():
        raise FileNotFoundError(f"Context splits file not found: {CONTEXT_SPLITS_PATH}")
    
    with open(CONTEXT_SPLITS_PATH, 'r', encoding='utf-8') as f:
        return [json.loads(line) for line in f if line.strip()]

def count_expected_unselected(splits: List[Dict[str, Any]]) -> int:
    """Calculate the total expected number of unselected rationales."""
    total = 0
    for split in splits:
        # Each split should have a list of unselected rationale IDs
        unselected = split.get("unselected_rationale_ids", [])
        total += len(unselected)
    return total

def validate_line_schema(line: Dict[str, Any], line_num: int) -> Tuple[bool, str]:
    """Validate the schema of a single line in the logits file."""
    required_keys = ["prompt_id", "rationale_id", "logits", "tokens"]
    
    for key in required_keys:
        if key not in line:
            return False, f"Line {line_num}: Missing required key '{key}'"
    
    if not isinstance(line["prompt_id"], str):
        return False, f"Line {line_num}: 'prompt_id' must be a string"
    
    if not isinstance(line["rationale_id"], str):
        return False, f"Line {line_num}: 'rationale_id' must be a string"
    
    if not isinstance(line["logits"], list):
        return False, f"Line {line_num}: 'logits' must be a list of floats"
    
    if not all(isinstance(x, (int, float)) for x in line["logits"]):
        return False, f"Line {line_num}: 'logits' must contain only numbers"
    
    if not isinstance(line["tokens"], list):
        return False, f"Line {line_num}: 'tokens' must be a list of strings"
    
    if not all(isinstance(x, str) for x in line["tokens"]):
        return False, f"Line {line_num}: 'tokens' must contain only strings"
    
    return True, ""

def count_and_validate_logits() -> Tuple[int, List[str]]:
    """Count lines and validate schema of the logits file."""
    if not TEACHER_LOGITS_PATH.exists():
        raise FileNotFoundError(f"Teacher logits file not found: {TEACHER_LOGITS_PATH}")
    
    errors = []
    count = 0
    
    with open(TEACHER_LOGITS_PATH, 'r', encoding='utf-8') as f:
        for line_num, line_str in enumerate(f, start=1):
            if not line_str.strip():
                continue
            
            try:
                line_data = json.loads(line_str)
            except json.JSONDecodeError as e:
                errors.append(f"Line {line_num}: Invalid JSON - {str(e)}")
                continue
            
            valid, error_msg = validate_line_schema(line_data, line_num)
            if not valid:
                errors.append(error_msg)
                continue
            
            count += 1
    
    return count, errors

def main():
    """Main validation entry point."""
    # Ensure results directory exists
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    
    report = {
        "status": "fail",
        "expected_count": 0,
        "actual_count": 0,
        "errors": []
    }
    
    try:
        # 1. Load context splits
        splits = load_context_splits()
        expected_count = count_expected_unselected(splits)
        report["expected_count"] = expected_count
        
        if expected_count == 0:
            report["errors"].append("Expected count is 0. Check context_splits.json.")
            with open(VALIDATION_REPORT_PATH, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2)
            print("Validation failed: Expected count is 0.")
            sys.exit(1)
        
        # 2. Count and validate logits
        actual_count, schema_errors = count_and_validate_logits()
        report["actual_count"] = actual_count
        report["errors"].extend(schema_errors)
        
        # 3. Compare counts
        if actual_count != expected_count:
            report["errors"].append(
                f"Count mismatch: Expected {expected_count}, got {actual_count}"
            )
        
        # 4. Determine status
        if len(report["errors"]) == 0 and actual_count == expected_count:
            report["status"] = "pass"
            print("Validation PASSED.")
            print(f"  Expected: {expected_count}")
            print(f"  Actual:   {actual_count}")
            sys.exit(0)
        else:
            print("Validation FAILED.")
            print(f"  Errors: {len(report['errors'])}")
            for err in report["errors"][:5]: # Show first 5 errors
                print(f"    - {err}")
            if len(report["errors"]) > 5:
                print(f"    ... and {len(report['errors']) - 5} more errors")
            sys.exit(1)
            
    except FileNotFoundError as e:
        report["errors"].append(str(e))
        print(f"Validation FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        report["errors"].append(f"Unexpected error: {str(e)}")
        print(f"Validation FAILED with unexpected error: {e}")
        sys.exit(1)
    finally:
        # Always write the report
        with open(VALIDATION_REPORT_PATH, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)

if __name__ == "__main__":
    main()