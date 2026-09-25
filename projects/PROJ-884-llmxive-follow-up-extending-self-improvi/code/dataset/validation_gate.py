import json
import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional

def load_json(file_path: Path) -> Optional[Dict[str, Any]]:
    """Load JSON from a file."""
    if not file_path.exists():
        return None
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading {file_path}: {e}", file=sys.stderr)
        return None

def save_json(file_path: Path, data: Dict[str, Any]) -> bool:
    """Save data to a JSON file."""
    try:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except IOError as e:
        print(f"Error saving {file_path}: {e}", file=sys.stderr)
        return False

def validate_distribution(distribution_stats: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate the distribution stats against expected criteria.
    
    This function checks:
    1. Presence of required fields
    2. Reasonable complexity scaling (N=10..500)
    3. Non-empty type distribution
    4. Sufficient sample size for statistical power (N >= 30 per bin)
    
    Returns a validation result with status, reason, and stats.
    """
    required_fields = ['type_distribution', 'complexity_scaling', 'total_count']
    
    # Check for required fields
    missing_fields = [f for f in required_fields if f not in distribution_stats]
    if missing_fields:
        return {
            "status": "FAIL",
            "reason": f"Missing required fields: {', '.join(missing_fields)}",
            "distribution_stats": distribution_stats
        }
    
    # Validate type distribution
    type_dist = distribution_stats.get('type_distribution', {})
    if not type_dist or len(type_dist) == 0:
        return {
            "status": "FAIL",
            "reason": "Type distribution is empty",
            "distribution_stats": distribution_stats
        }
    
    # Validate complexity scaling
    complexity_scaling = distribution_stats.get('complexity_scaling', {})
    if not complexity_scaling:
        return {
            "status": "FAIL",
            "reason": "Complexity scaling data is missing",
            "distribution_stats": distribution_stats
        }
    
    # Check for N values in expected range (10 to 500)
    n_values = list(complexity_scaling.keys())
    if not n_values:
        return {
            "status": "FAIL",
            "reason": "No complexity N values found",
            "distribution_stats": distribution_stats
        }
    
    # Convert to integers and check range
    try:
        n_ints = [int(n) for n in n_values]
        if not all(10 <= n <= 500 for n in n_ints):
            return {
                "status": "FAIL",
                "reason": f"N values must be in range 10-500. Found: {n_values}",
                "distribution_stats": distribution_stats
            }
    except ValueError:
        return {
            "status": "FAIL",
            "reason": f"Invalid N value format: {n_values}",
            "distribution_stats": distribution_stats
        }
    
    # Check total count (minimum 30 for basic statistical power)
    total_count = distribution_stats.get('total_count', 0)
    if total_count < 30:
        return {
            "status": "FAIL",
            "reason": f"Total count ({total_count}) is below minimum threshold of 30 for statistical power",
            "distribution_stats": distribution_stats
        }
    
    # All checks passed
    return {
        "status": "PASS",
        "reason": "Distribution validation passed all criteria",
        "distribution_stats": distribution_stats
    }

def main():
    """
    Main entry point for the validation gate.
    
    Reads data/processed/distribution_validation.json (or distribution_report.json if validation file missing),
    validates the dataset distribution, and writes data/processed/validation_gate.json.
    """
    project_root = Path(__file__).parent.parent.parent
    input_file = project_root / "data" / "processed" / "distribution_validation.json"
    fallback_input = project_root / "data" / "processed" / "distribution_report.json"
    output_file = project_root / "data" / "processed" / "validation_gate.json"
    
    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Try to load distribution validation stats
    distribution_stats = load_json(input_file)
    
    # Fallback to distribution report if validation file doesn't exist
    if distribution_stats is None:
        print(f"Warning: {input_file} not found, trying fallback: {fallback_input}", file=sys.stderr)
        distribution_stats = load_json(fallback_input)
    
    if distribution_stats is None:
        # If no input data, fail loudly
        result = {
            "status": "FAIL",
            "reason": "Input distribution data not found. Ensure distribution_report.json or distribution_validation.json exists.",
            "distribution_stats": {}
        }
        if not save_json(output_file, result):
            print(f"Failed to write output file: {output_file}", file=sys.stderr)
            sys.exit(1)
        print(f"Validation gate written to {output_file} with FAIL status.")
        return
    
    # Perform validation
    result = validate_distribution(distribution_stats)
    
    # Write result
    if not save_json(output_file, result):
        print(f"Failed to write output file: {output_file}", file=sys.stderr)
        sys.exit(1)
    
    print(f"Validation gate written to {output_file}")
    print(f"Status: {result['status']}")
    if result['status'] == "FAIL":
        print(f"Reason: {result['reason']}")
    
    # Exit with non-zero code on failure for CI/CD integration
    if result['status'] == "FAIL":
        sys.exit(1)

if __name__ == "__main__":
    main()