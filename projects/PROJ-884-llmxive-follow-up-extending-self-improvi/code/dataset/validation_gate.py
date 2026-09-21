"""
Validation Gate: Validates dataset distribution and generates validation_gate.json.

This script reads the distribution validation results from
data/processed/distribution_validation.json and generates a final
validation gate status file at data/processed/validation_gate.json.

It ensures that the dataset meets the statistical requirements before
proceeding to the BES loop.
"""
import json
import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional

# Ensure we can import from the project root
PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

def load_json(file_path: Path) -> Dict[str, Any]:
    """Load a JSON file and return its contents."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Required input file not found: {file_path}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {file_path}: {e}")

def save_json(data: Dict[str, Any], file_path: Path) -> None:
    """Save data to a JSON file."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def validate_distribution(
    validation_result: Dict[str, Any],
    min_power_estimate: float = 0.8,
    min_sample_size: int = 10
) -> Dict[str, Any]:
    """
    Validate the distribution results and determine gate status.
    
    Args:
        validation_result: The contents of distribution_validation.json
        min_power_estimate: Minimum acceptable power estimate (default 0.8)
        min_sample_size: Minimum acceptable sample size (default 10)
        
    Returns:
        A dictionary with status, reason, and distribution_stats
    """
    is_valid = validation_result.get('is_valid', False)
    power_estimate = validation_result.get('power_estimate', 0.0)
    sample_size = validation_result.get('sample_size', 0)
    notes = validation_result.get('notes', [])
    distribution_stats = validation_result.get('distribution_stats', {})
    
    reasons = []
    
    # Check if the validation passed at the source
    if not is_valid:
        reasons.append("Distribution validation failed at source")
    
    # Check power estimate
    if power_estimate < min_power_estimate:
        reasons.append(f"Power estimate ({power_estimate:.2f}) is below threshold ({min_power_estimate})")
    
    # Check sample size
    if sample_size < min_sample_size:
        reasons.append(f"Sample size ({sample_size}) is below minimum ({min_sample_size})")
    
    # Determine final status
    if len(reasons) == 0:
        status = "PASS"
        reason = "All validation checks passed. Dataset is suitable for BES loop."
    else:
        status = "FAIL"
        reason = "; ".join(reasons)
    
    return {
        "status": status,
        "reason": reason,
        "distribution_stats": distribution_stats,
        "power_estimate": power_estimate,
        "sample_size": sample_size,
        "validation_notes": notes
    }

def main():
    """Main entry point for the validation gate."""
    # Define paths
    input_path = PROJECT_ROOT / "data" / "processed" / "distribution_validation.json"
    output_path = PROJECT_ROOT / "data" / "processed" / "validation_gate.json"
    
    print(f"Validation Gate: Reading from {input_path}")
    
    # Load the distribution validation result
    try:
        validation_result = load_json(input_path)
    except (FileNotFoundError, ValueError) as e:
        # If the input file is missing or invalid, we must FAIL the gate
        # and report the reason. We still generate the output file.
        error_output = {
            "status": "FAIL",
            "reason": f"Input validation file missing or invalid: {e}",
            "distribution_stats": {}
        }
        save_json(error_output, output_path)
        print(f"Validation Gate: FAILED - {e}")
        print(f"Validation Gate: Output written to {output_path}")
        sys.exit(1)
    
    # Perform validation
    gate_result = validate_distribution(validation_result)
    
    # Write the gate result
    save_json(gate_result, output_path)
    
    print(f"Validation Gate: Status = {gate_result['status']}")
    print(f"Validation Gate: Reason = {gate_result['reason']}")
    print(f"Validation Gate: Output written to {output_path}")
    
    # Exit with appropriate code
    if gate_result['status'] == "FAIL":
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
