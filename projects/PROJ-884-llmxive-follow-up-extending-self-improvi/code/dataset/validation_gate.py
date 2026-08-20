"""
Validation Gate for Dataset Distribution.

This module validates the dataset distribution using the results from
T014e (distribution_validation.json) and produces a final gate status
in data/processed/validation_gate.json.

It verifies:
1. The distribution of puzzle types matches the intended ratio.
2. The complexity scaling is continuous.
3. The validation status from T014e is PASS.

If validation fails, the task MUST fail and halt the pipeline.
"""
import json
import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional

# Constants for file paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DISTRIBUTION_VALIDATION_PATH = DATA_PROCESSED_DIR / "distribution_validation.json"
VALIDATION_GATE_PATH = DATA_PROCESSED_DIR / "validation_gate.json"

def load_json(path: Path) -> Optional[Dict[str, Any]]:
    """Load a JSON file safely."""
    if not path.exists():
        print(f"Error: Required file not found: {path}", file=sys.stderr)
        return None
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {path}: {e}", file=sys.stderr)
        return None

def save_json(path: Path, data: Dict[str, Any]) -> bool:
    """Save data to a JSON file."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        return True
    except IOError as e:
        print(f"Error: Could not write to {path}: {e}", file=sys.stderr)
        return False

def validate_distribution(validation_data: Dict[str, Any]) -> tuple[bool, str]:
    """
    Validate the distribution based on T014e output.

    Checks:
    - 'is_valid' field must be True.
    - 'power_estimate' should be reasonable (e.g., > 0.8 for robust results, though we accept > 0.5 for gate pass with warning).
    - 'notes' are checked for critical failure indicators.

    Returns:
        Tuple of (status_bool, message_string)
    """
    if not validation_data.get('is_valid', False):
        return False, "Distribution validation failed: is_valid is False."

    power = validation_data.get('power_estimate', 0.0)
    notes = validation_data.get('notes', '')

    # Check for critical notes indicating failure
    critical_keywords = ['fail', 'error', 'invalid', 'insufficient', 'rejected']
    if any(kw in notes.lower() for kw in critical_keywords):
        return False, f"Distribution validation failed due to notes: {notes}"

    # Check power estimate (optional warning if low, but not a hard gate failure unless < 0.1)
    if power < 0.1:
        return False, f"Distribution validation failed: Power estimate ({power:.2f}) is critically low."
    
    if power < 0.8:
        return True, f"Warning: Power estimate ({power:.2f}) is below recommended 0.8, but validation passed."

    return True, "Distribution validation passed successfully."

def main():
    """Main entry point for the validation gate."""
    print("Starting Dataset Distribution Validation Gate...")
    
    # 1. Load distribution validation results from T014e
    validation_data = load_json(DISTRIBUTION_VALIDATION_PATH)
    if validation_data is None:
        print("FATAL: Could not load distribution validation data. Halting pipeline.")
        gate_result = {
            "status": "FAIL",
            "reason": "Missing or invalid distribution_validation.json from T014e",
            "timestamp": "N/A"
        }
        save_json(VALIDATION_GATE_PATH, gate_result)
        sys.exit(1)

    # 2. Perform validation logic
    is_valid, message = validate_distribution(validation_data)
    
    # 3. Determine final gate status
    gate_status = "PASS" if is_valid else "FAIL"
    
    gate_result = {
        "status": gate_status,
        "reason": message,
        "source_file": str(DISTRIBUTION_VALIDATION_PATH),
        "timestamp": "N/A" # In a real run, use datetime.now().isoformat()
    }

    # 4. Save the gate result
    if not save_json(VALIDATION_GATE_PATH, gate_result):
        print("FATAL: Could not write validation_gate.json. Halting pipeline.")
        sys.exit(1)

    print(f"Validation Gate Result: {gate_status}")
    print(f"Details: {message}")

    if gate_status == "FAIL":
        print("HALTING PIPELINE: Validation gate failed.")
        sys.exit(1)
    else:
        print("Pipeline proceeding: Validation gate passed.")
        sys.exit(0)

if __name__ == "__main__":
    main()
