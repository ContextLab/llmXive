import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

from utils.config import get_path, get_hyperparameter
from utils.exceptions import LlmXiveError

def load_filtered_outcomes(path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """
    Load the filtered outcomes (latency failures excluded) from the evaluation results.
    """
    if path is None:
        path = get_path("processed_evaluation_outcomes")
    
    if not os.path.exists(path):
        raise FileNotFoundError(f"Filtered outcomes file not found at {path}")
    
    with open(path, 'r') as f:
        data = json.load(f)
    
    return data.get("outcomes", [])

def load_all_outcomes(path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """
    Load the full list of task outcomes (before filtering) from the categorized outcomes.
    We assume the 'categorized_outcomes' file contains the full set.
    """
    if path is None:
        path = get_path("categorized_outcomes")
    
    if not os.path.exists(path):
        raise FileNotFoundError(f"Categorized outcomes file not found at {path}")
    
    with open(path, 'r') as f:
        data = json.load(f)
    
    return data.get("outcomes", [])

def count_latency_failures(outcomes: List[Dict[str, Any]]) -> int:
    """
    Count the number of outcomes that are flagged as latency-induced failures.
    """
    count = 0
    for outcome in outcomes:
        # Check if the failure_category is 'latency' or if a specific flag exists
        failure_category = outcome.get("failure_category", "")
        is_latency = outcome.get("is_latency_failure", False)
        
        if failure_category == "latency" or is_latency:
            count += 1
    
    return count

def verify_exclusion_logic(
    total_tasks: int,
    latency_failures: int,
    filtered_count: int,
    tolerance: int = 0
) -> Dict[str, Any]:
    """
    Verify that the denominator used for the success rate calculation
    equals (total_tasks - latency_failures).
    
    Returns a verification result dictionary.
    """
    expected_denominator = total_tasks - latency_failures
    actual_denominator = filtered_count
    
    is_valid = (actual_denominator == expected_denominator)
    
    return {
        "total_tasks": total_tasks,
        "latency_failures_count": latency_failures,
        "expected_denominator": expected_denominator,
        "actual_denominator": actual_denominator,
        "is_valid": is_valid,
        "message": (
            "Verification PASSED: Denominator matches (total_tasks - latency_failures)."
            if is_valid else
            f"Verification FAILED: Expected {expected_denominator}, got {actual_denominator}."
        )
    }

def write_verification_result(result: Dict[str, Any], output_path: Optional[Path] = None) -> None:
    """
    Write the verification result to the artifacts directory.
    """
    if output_path is None:
        output_path = get_path("latency_exclusion_verified")
    
    # Ensure the directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"Verification result written to {output_path}")

def main() -> None:
    """
    Main entry point for the latency exclusion verification task.
    """
    try:
        # Load the filtered outcomes (T035 output)
        filtered_outcomes = load_filtered_outcomes()
        filtered_count = len(filtered_outcomes)
        
        # Load all outcomes to determine total tasks and count latency failures
        all_outcomes = load_all_outcomes()
        total_tasks = len(all_outcomes)
        latency_failures = count_latency_failures(all_outcomes)
        
        # Perform verification
        result = verify_exclusion_logic(total_tasks, latency_failures, filtered_count)
        
        # Write the result
        write_verification_result(result)
        
        # Exit with appropriate code
        if not result["is_valid"]:
            print(f"ERROR: {result['message']}")
            sys.exit(1)
        else:
            print(f"SUCCESS: {result['message']}")
            sys.exit(0)
            
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error during verification: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
