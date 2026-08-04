"""
T015a: Validate Slope Test Results

Reads global_regression.json, verifies p_value validity, and writes
slope_test_results.json.
"""
import json
import sys
from pathlib import Path

# Add project root to path for imports if running as script
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

INPUT_FILE = project_root / "data" / "processed" / "global_regression.json"
OUTPUT_FILE = project_root / "data" / "processed" / "slope_test_results.json"

def main():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input file not found: {INPUT_FILE}. "
            "Ensure T013e-Write (global regression) has been run successfully."
        )

    with open(INPUT_FILE, 'r') as f:
        regression_data = json.load(f)

    # Validate required fields
    required_keys = ['slope', 'p_value', 'confidence_interval', 'r_squared']
    for key in required_keys:
        if key not in regression_data:
            raise ValueError(f"Missing required key '{key}' in {INPUT_FILE}")

    p_value = regression_data['p_value']

    # Validate p_value is a valid number and within [0, 1]
    if not isinstance(p_value, (int, float)):
        raise TypeError(f"p_value must be numeric, got {type(p_value)}")

    if not (0.0 <= p_value <= 1.0):
        raise ValueError(f"p_value {p_value} is outside valid range [0, 1]")

    # Construct validation result
    validation_result = {
        "source_file": str(INPUT_FILE),
        "validation_status": "passed",
        "slope": regression_data['slope'],
        "p_value": p_value,
        "confidence_interval": regression_data['confidence_interval'],
        "r_squared": regression_data['r_squared'],
        "is_significant_at_0.05": p_value < 0.05,
        "is_significant_at_0.01": p_value < 0.01,
        "message": "Slope test results validated successfully."
    }

    # Write output
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(validation_result, f, indent=2)

    print(f"Validation successful. Results written to {OUTPUT_FILE}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
