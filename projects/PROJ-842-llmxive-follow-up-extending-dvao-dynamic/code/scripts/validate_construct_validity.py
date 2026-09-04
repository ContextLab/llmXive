"""
Script to validate Construct Validity and Validation Independence.

This script loads results from `data/processed/construct_validity_results.json` 
and `data/processed/empirical_results.json`, compares deviations against a 
predefined threshold (10%) for all distributions (Linear, Sparse, Non-Convex, 
Heavy-Tailed), and outputs a clear PASS/FAIL summary.

Verification: Run `python scripts/validate_construct_validity.py` and verify 
it outputs "PASS: All distributions within 10% deviation" or a detailed failure 
report.
"""
import json
import os
import sys
from typing import Dict, Any, List, Tuple

# Constants
DEVIATION_THRESHOLD = 0.10  # 10% deviation threshold
REQUIRED_FILES = [
    "data/processed/construct_validity_results.json",
    "data/processed/empirical_results.json"
]
VALID_DISTRIBUTIONS = ["linear", "sparse", "non-convex", "heavy-tailed"]

def load_json_file(file_path: str) -> Dict[str, Any]:
    """Load a JSON file and return its contents."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Required file not found: {file_path}")
    
    with open(file_path, 'r') as f:
        return json.load(f)

def validate_distribution_deviations(
    results: Dict[str, Any], 
    threshold: float = DEVIATION_THRESHOLD
) -> List[Tuple[str, float, bool]]:
    """
    Validate deviations for each distribution against the threshold.
    
    Args:
        results: Dictionary containing deviation metrics per distribution.
        threshold: Maximum allowed deviation (default 0.10).
    
    Returns:
        List of tuples: (distribution_name, deviation, passed)
    """
    validation_results = []
    
    # Handle both flat and nested structures
    distributions_data = results.get("distributions", results)
    
    for dist_name in VALID_DISTRIBUTIONS:
        # Normalize case for lookup
        lookup_name = dist_name.lower()
        
        # Find matching key (case-insensitive)
        actual_key = None
        for key in distributions_data.keys():
            if key.lower() == lookup_name:
                actual_key = key
                break
        
        if actual_key is None:
            # Distribution not found in results
            validation_results.append((dist_name, None, False))
            continue
        
        dist_data = distributions_data[actual_key]
        
        # Extract deviation value
        if isinstance(dist_data, dict):
            deviation = dist_data.get("deviation", dist_data.get("deviation_pct", None))
            if deviation is None:
                # Try to calculate from raw values if available
                theoretical = dist_data.get("theoretical_bound")
                empirical = dist_data.get("empirical_result")
                if theoretical and empirical and theoretical != 0:
                    deviation = abs(empirical - theoretical) / abs(theoretical)
                else:
                    deviation = None
        elif isinstance(dist_data, (int, float)):
            deviation = float(dist_data)
        else:
            deviation = None
        
        passed = deviation is not None and deviation <= threshold
        validation_results.append((dist_name, deviation, passed))
    
    return validation_results

def validate_construct_validity(
    construct_results_path: str,
    empirical_results_path: str,
    threshold: float = DEVIATION_THRESHOLD
) -> Tuple[bool, str]:
    """
    Main validation function for construct validity.
    
    Args:
        construct_results_path: Path to construct_validity_results.json
        empirical_results_path: Path to empirical_results.json
        threshold: Maximum allowed deviation (default 0.10)
    
    Returns:
        Tuple of (overall_pass, summary_message)
    """
    try:
        # Load required files
        construct_results = load_json_file(construct_results_path)
        empirical_results = load_json_file(empirical_results_path)
        
        # Validate construct validity results
        construct_validations = validate_distribution_deviations(
            construct_results, threshold
        )
        
        # Validate empirical results (if they contain distribution data)
        empirical_validations = []
        if "distributions" in empirical_results or any(
            k.lower() in VALID_DISTRIBUTIONS for k in empirical_results.keys()
        ):
            empirical_validations = validate_distribution_deviations(
                empirical_results, threshold
            )
        
        # Combine results
        all_validations = construct_validations + empirical_validations
        
        # Generate report
        failed_items = []
        passed_count = 0
        total_count = 0
        
        summary_lines = []
        summary_lines.append("=== Construct Validity Validation Report ===")
        summary_lines.append(f"Threshold: {threshold * 100}% deviation")
        summary_lines.append("")
        
        for dist_name, deviation, passed in all_validations:
            total_count += 1
            if deviation is None:
                summary_lines.append(f"[MISSING] {dist_name}: No deviation data found")
            elif passed:
                passed_count += 1
                summary_lines.append(f"[PASS] {dist_name}: {deviation:.4f} <= {threshold}")
            else:
                failed_items.append((dist_name, deviation))
                summary_lines.append(f"[FAIL] {dist_name}: {deviation:.4f} > {threshold}")
        
        summary_lines.append("")
        if total_count == 0:
            summary_lines.append("ERROR: No distributions found in results.")
            return False, "\n".join(summary_lines)
        
        overall_pass = len(failed_items) == 0 and passed_count == total_count
        
        if overall_pass:
            summary_lines.append(f"PASS: All {total_count} distributions within {threshold * 100}% deviation")
        else:
            summary_lines.append(f"FAIL: {len(failed_items)} distribution(s) exceeded {threshold * 100}% deviation")
            summary_lines.append("Failed distributions:")
            for dist, dev in failed_items:
                summary_lines.append(f"  - {dist}: {dev:.4f}")
        
        return overall_pass, "\n".join(summary_lines)
        
    except FileNotFoundError as e:
        return False, f"ERROR: Missing required file - {str(e)}"
    except json.JSONDecodeError as e:
        return False, f"ERROR: Invalid JSON format - {str(e)}"
    except Exception as e:
        return False, f"ERROR: Unexpected error - {str(e)}"

def main():
    """Main entry point for the validation script."""
    print("Starting Construct Validity Validation...")
    print("-" * 50)
    
    # Define paths relative to project root
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    construct_results_path = os.path.join(
        project_root, REQUIRED_FILES[0]
    )
    empirical_results_path = os.path.join(
        project_root, REQUIRED_FILES[1]
    )
    
    # Run validation
    passed, report = validate_construct_validity(
        construct_results_path,
        empirical_results_path,
        threshold=DEVIATION_THRESHOLD
    )
    
    # Output report
    print(report)
    print("-" * 50)
    
    # Exit with appropriate code
    sys.exit(0 if passed else 1)

if __name__ == "__main__":
    main()
