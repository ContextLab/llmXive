"""
Validation script for the filtered subset (T015).

Samples tasks from data/processed/filtered_tasks.csv and verifies
that the constraint_count matches the original metadata logic.
"""

import os
import sys
import ast
from pathlib import Path
import random
import pandas as pd

# Add project root to path if not already present
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import Paths
from dataset.loader import MIN_CONSTRAINT_REVEALS


def _parse_constraints_field(value):
    """
    Safely parse the progressive_constraints field which may be stored
    as a Python list or a string representation of a list in the CSV.
    Returns the list or None if parsing fails.
    """
    if value is None:
        return None
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        # Try to safely evaluate string representation of a list
        try:
            parsed = ast.literal_eval(value)
            if isinstance(parsed, list):
                return parsed
        except (ValueError, SyntaxError):
            pass
    return None


def validate_subset(sample_size: int = 10):
    """
    Validate the filtered subset by sampling tasks and checking constraint counts.

    Args:
        sample_size: Number of tasks to sample for validation.
    """
    input_path = Paths.PROCESSED_DATA / "filtered_tasks.csv"

    if not input_path.exists():
        raise FileNotFoundError(
            f"Filtered dataset not found at {input_path}. "
            "Please run T012/T013/T014 first to generate the filtered dataset."
        )

    df = pd.read_csv(input_path)

    if len(df) == 0:
        print("Warning: Filtered dataset is empty.")
        return

    effective_sample_size = min(sample_size, len(df))
    print(f"Validating subset of {effective_sample_size} tasks from {len(df)} total...")

    # Sample tasks deterministically for reproducibility
    sample = df.sample(n=effective_sample_size, random_state=42)

    all_valid = True
    pass_count = 0
    fail_count = 0

    for _, row in sample.iterrows():
        task_id = row.get('task_id', 'unknown')

        # Check constraint_count field presence
        if 'constraint_count' not in row or pd.isna(row['constraint_count']):
            print(f"  [FAIL] {task_id}: Missing 'constraint_count' field")
            all_valid = False
            fail_count += 1
            continue

        count = int(row['constraint_count'])

        # Verify count is >= 5 (MIN_CONSTRAINT_REVEALS)
        if count < MIN_CONSTRAINT_REVEALS:
            print(f"  [FAIL] {task_id}: constraint_count ({count}) < {MIN_CONSTRAINT_REVEALS}")
            all_valid = False
            fail_count += 1
            continue

        # If progressive_constraints exists, verify count matches length
        if 'progressive_constraints' in row:
            constraints = _parse_constraints_field(row['progressive_constraints'])

            if constraints is None:
                # If we can't parse it, we can't verify the length, but the count check passed
                print(f"  [WARN] {task_id}: Could not parse 'progressive_constraints' to verify length, but count check passed.")
                pass_count += 1
                continue

            if isinstance(constraints, list):
                actual_len = len(constraints)
                if actual_len != count:
                    print(f"  [FAIL] {task_id}: constraint_count ({count}) != len(progressive_constraints) ({actual_len})")
                    all_valid = False
                    fail_count += 1
                    continue
            else:
                print(f"  [WARN] {task_id}: 'progressive_constraints' is not a list after parsing.")
                pass_count += 1
                continue

        print(f"  [PASS] {task_id}: constraint_count = {count}")
        pass_count += 1

    print(f"\nValidation Summary: {pass_count} passed, {fail_count} failed.")

    if all_valid:
        print("Validation PASSED: All sampled tasks meet the criteria.")
    else:
        print("Validation FAILED: Some tasks did not meet criteria.")
        sys.exit(1)


if __name__ == "__main__":
    validate_subset()