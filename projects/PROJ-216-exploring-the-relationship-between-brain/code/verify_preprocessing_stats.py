import os
import sys
import json
from pathlib import Path
from typing import Any, Dict

def verify_schema() -> bool:
    """
    Verifies the existence and schema of data/processed/preprocessing_stats.json.
    
    The file must contain:
    - 'success_rate': float >= 0.0
    - 'total_subjects': int
    - 'successful_subjects': int
    - 'excluded_subjects': list (optional but recommended)
    
    Returns True if valid, raises AssertionError otherwise.
    """
    stats_path = Path("data/processed/preprocessing_stats.json")
    
    if not stats_path.exists():
        raise FileNotFoundError(
            f"Preprocessing stats artifact not found at {stats_path}. "
            "Run the preprocessing pipeline (T017d) to generate this file."
        )
    
    try:
        with open(stats_path, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in preprocessing stats file: {e}")
    
    # Verify required fields
    required_fields = ['success_rate', 'total_subjects', 'successful_subjects']
    for field in required_fields:
        if field not in data:
            raise KeyError(f"Missing required field '{field}' in preprocessing stats")
    
    # Verify types and constraints
    if not isinstance(data['success_rate'], (int, float)):
        raise TypeError(f"'success_rate' must be a number, got {type(data['success_rate'])}")
    
    if data['success_rate'] < 0.0:
        raise ValueError(f"'success_rate' must be >= 0.0, got {data['success_rate']}")
    
    if data['success_rate'] > 1.0:
        # Allow > 1.0 if it's a raw count, but warn. Standardizing to 0-1 range.
        # If the pipeline outputs a percentage (0-100), we might need to adjust.
        # Based on T017d requirements, it expects a rate (0.0 to 1.0).
        pass 
    
    if not isinstance(data['total_subjects'], int):
        raise TypeError(f"'total_subjects' must be an integer, got {type(data['total_subjects'])}")
    
    if not isinstance(data['successful_subjects'], int):
        raise TypeError(f"'successful_subjects' must be an integer, got {type(data['successful_subjects'])}")
    
    # Verify consistency
    if data['successful_subjects'] > data['total_subjects']:
        raise ValueError(
            f"'successful_subjects' ({data['successful_subjects']}) cannot exceed "
            f"'total_subjects' ({data['total_subjects']})"
        )
    
    # Verify success rate calculation matches counts (allow small float tolerance)
    expected_rate = data['successful_subjects'] / data['total_subjects'] if data['total_subjects'] > 0 else 0.0
    if abs(data['success_rate'] - expected_rate) > 0.001:
        # Log warning but don't fail if it's close, as it might be a rounding difference
        # However, for strict verification, we fail if the discrepancy is large.
        # Re-calculating to ensure integrity.
        raise ValueError(
            f"Success rate mismatch: reported {data['success_rate']:.4f}, "
            f"calculated {expected_rate:.4f} from counts."
        )
    
    print(f"Verification PASSED: {stats_path}")
    print(f"  - Total subjects: {data['total_subjects']}")
    print(f"  - Successful subjects: {data['successful_subjects']}")
    print(f"  - Success rate: {data['success_rate']:.2%}")
    return True

def main() -> int:
    """Main entry point for the verification script."""
    try:
        verify_schema()
        return 0
    except (FileNotFoundError, ValueError, TypeError, KeyError) as e:
        print(f"Verification FAILED: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())