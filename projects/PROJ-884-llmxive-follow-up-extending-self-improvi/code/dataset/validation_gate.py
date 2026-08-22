"""
Task T036: Validate dataset distribution and produce validation gate.

This script reads the distribution validation report (from T014e-exec) and verifies:
1. The distribution of puzzle types matches the intended ratio.
2. The complexity scaling is continuous across the N range.

It outputs `data/processed/validation_gate.json` with status PASS or FAIL.
"""

import json
import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional

# Ensure we can import from the code package
sys.path.insert(0, str(Path(__file__).parent.parent))

def load_json(path: Path) -> Optional[Dict[str, Any]]:
    """Load a JSON file, returning None if it doesn't exist or is invalid."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"ERROR: Required file not found: {path}")
        return None
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in {path}: {e}")
        return None

def save_json(path: Path, data: Dict[str, Any]) -> bool:
    """Save data to a JSON file."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"ERROR: Failed to write {path}: {e}")
        return False

def validate_distribution(validation_data: Dict[str, Any]) -> tuple[bool, str, Dict[str, Any]]:
    """
    Validate the distribution report.

    Returns:
        (is_valid, reason, stats)
    """
    if not validation_data:
        return False, "Validation data is missing or empty", {}

    is_valid = validation_data.get("is_valid", False)
    notes = validation_data.get("notes", "")
    power_estimate = validation_data.get("power_estimate", 0.0)

    # Check if the validation passed
    if not is_valid:
        reason = f"Distribution validation failed: {notes}"
        return False, reason, {"is_valid": is_valid, "notes": notes, "power_estimate": power_estimate}

    # Check power estimate (statistical robustness)
    if power_estimate < 0.8:
        reason = f"Statistical power is too low: {power_estimate:.2f} < 0.8. The sample size may be insufficient."
        return False, reason, {"is_valid": is_valid, "power_estimate": power_estimate}

    # Check that distribution stats exist
    distribution_stats = validation_data.get("distribution_stats", {})
    if not distribution_stats:
        reason = "Distribution stats are missing from the validation report."
        return False, reason, {"is_valid": is_valid, "notes": notes}

    # Check for continuous complexity scaling if available
    complexity_scaling = distribution_stats.get("complexity_scaling", {})
    if not complexity_scaling.get("is_continuous", False):
        reason = "Complexity scaling is not continuous."
        return False, reason, {"is_valid": is_valid, "distribution_stats": distribution_stats}

    # If we get here, validation passed
    return True, "Distribution validation passed: type ratio matches and complexity scaling is continuous.", {
        "is_valid": is_valid,
        "power_estimate": power_estimate,
        "distribution_stats": distribution_stats
    }

def main():
    """Main entry point for T036."""
    # Define paths relative to project root
    project_root = Path(__file__).parent.parent.parent
    input_path = project_root / "data" / "processed" / "distribution_validation.json"
    output_path = project_root / "data" / "processed" / "validation_gate.json"

    print(f"Reading distribution validation from: {input_path}")
    validation_data = load_json(input_path)

    if validation_data is None:
        # Fail loudly if input is missing
        error_gate = {
            "status": "FAIL",
            "reason": "Input file distribution_validation.json not found or invalid. Cannot proceed.",
            "distribution_stats": {}
        }
        save_json(output_path, error_gate)
        print(f"Written failure gate to: {output_path}")
        sys.exit(1)

    is_valid, reason, stats = validate_distribution(validation_data)

    gate_output = {
        "status": "PASS" if is_valid else "FAIL",
        "reason": reason,
        "distribution_stats": stats
    }

    if not save_json(output_path, gate_output):
        print("ERROR: Could not write validation gate output.")
        sys.exit(1)

    print(f"Validation Gate Result: {gate_output['status']}")
    print(f"Reason: {gate_output['reason']}")
    print(f"Written to: {output_path}")

    if not is_valid:
        sys.exit(1)

    sys.exit(0)

if __name__ == "__main__":
    main()
