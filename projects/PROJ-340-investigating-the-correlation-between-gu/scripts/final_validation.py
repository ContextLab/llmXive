"""
Final Validation Script
Validates statistical methods and causal language compliance.
"""
import os
import sys
import json
from pathlib import Path

def load_json_file(path):
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: File not found: {path}")
        return None
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in file: {path}")
        return None

def validate_method_selection(method_log_path):
    """
    Validates that method_selection_log.json exists and contains valid entries.
    """
    data = load_json_file(method_log_path)
    if not data:
        return False, "method_selection_log.json missing or invalid"

    # Check for required keys
    required_keys = ['method', 'reason', 'data_distribution']
    for key in required_keys:
        if key not in data:
            return False, f"Missing key '{key}' in method_selection_log.json"

    return True, "Method selection log is valid"

def validate_causal_scan(causal_scan_path):
    """
    Validates that causal_scan_report.json exists and confirms no violations.
    """
    data = load_json_file(causal_scan_path)
    if not data:
        return False, "causal_scan_report.json missing or invalid"

    # Check for violation flag
    violations = data.get('violations', [])
    if violations:
        return False, f"Causal language violations detected: {violations}"

    return True, "No causal language violations detected"

def main():
    base_dir = Path(__file__).parent.parent
    method_log_path = base_dir / 'data' / 'metadata' / 'method_selection_log.json'
    causal_scan_path = base_dir / 'data' / 'results' / 'causal_scan_report.json'
    output_path = base_dir / 'data' / 'results' / 'final_validation_report.json'

    results = {
        'method_selection_valid': False,
        'method_selection_message': '',
        'causal_scan_valid': False,
        'causal_scan_message': '',
        'overall_valid': False,
        'timestamp': str(Path().cwd()) # Placeholder for real timestamp logic
    }

    # Validate Method Selection
    valid, msg = validate_method_selection(method_log_path)
    results['method_selection_valid'] = valid
    results['method_selection_message'] = msg

    # Validate Causal Scan
    valid, msg = validate_causal_scan(causal_scan_path)
    results['causal_scan_valid'] = valid
    results['causal_scan_message'] = msg

    # Overall Status
    results['overall_valid'] = results['method_selection_valid'] and results['causal_scan_valid']

    # Write Output
    os.makedirs(output_path.parent, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"Final validation complete. Report saved to {output_path}")
    if not results['overall_valid']:
        print("VALIDATION FAILED. Check report for details.")
        sys.exit(1)
    else:
        print("VALIDATION PASSED.")
        sys.exit(0)

if __name__ == '__main__':
    main()
