"""
Module to add a 'constraint_count' metadata column to the filtered dataset.

This task implements T014: Add `constraint_count` metadata column to filtered output
in `data/processed/filtered_tasks.csv`.

The count is derived by parsing the 'progressive_constraints' field (expected to be a
list of constraints or a JSON string representation of a list) and counting the number
of items.
"""
import os
import sys
from pathlib import Path
from typing import List, Dict, Any
import pandas as pd
import json
import ast

from config import Paths


def compute_constraint_count(constraints_field: Any) -> int:
    """
    Compute the number of constraints from the 'progressive_constraints' field.

    Args:
        constraints_field: The value from the 'progressive_constraints' column.
                           Expected to be a list, a JSON string, or a stringified
                           Python list representation.

    Returns:
        The integer count of constraints. Returns 0 if the field is empty or None.
    """
    if constraints_field is None:
        return 0

    # Case 1: Already a list
    if isinstance(constraints_field, list):
        return len(constraints_field)

    # Case 2: String representation (JSON or Python literal)
    if isinstance(constraints_field, str):
        stripped = constraints_field.strip()
        if not stripped:
            return 0

        # Try JSON first
        try:
            parsed = json.loads(stripped)
            if isinstance(parsed, list):
                return len(parsed)
        except (json.JSONDecodeError, TypeError):
            pass

        # Try Python literal (ast.literal_eval) for safety
        try:
            parsed = ast.literal_eval(stripped)
            if isinstance(parsed, list):
                return len(parsed)
        except (ValueError, SyntaxError, TypeError):
            pass

        # If it's a non-empty string that isn't a list, count it as 1 if it looks like a constraint,
        # or 0 if it's just a description. For this benchmark, we assume if it's not a list,
        # it might be a single constraint string or a malformed entry.
        # However, the spec implies a list structure. If it's a single string, we count as 1.
        if len(stripped) > 0:
            return 1

    # Fallback: try to treat as a string and split if it looks like a delimited list,
    # though the primary format should be list/JSON.
    return 0


def add_constraint_count_column(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add a 'constraint_count' column to the dataframe based on 'progressive_constraints'.

    Args:
        df: The dataframe containing the filtered tasks. Must have a 'progressive_constraints' column.

    Returns:
        The dataframe with the new 'constraint_count' column added.
    """
    if 'progressive_constraints' not in df.columns:
        raise ValueError("Input dataframe must contain 'progressive_constraints' column.")

    # Apply the counting function
    df['constraint_count'] = df['progressive_constraints'].apply(compute_constraint_count)

    return df


def main() -> None:
    """
    Main entry point to load the filtered dataset, add the constraint_count column,
    and save the result to `data/processed/filtered_tasks.csv`.
    """
    print("Starting T014: Adding constraint_count metadata column...")

    input_path = Paths.PROCESSED / "filtered_tasks.csv"
    output_path = Paths.PROCESSED / "filtered_tasks.csv"

    if not input_path.exists():
        raise FileNotFoundError(
            f"Input file not found: {input_path}. "
            "Please ensure T012 and T013 have run successfully to generate the filtered dataset."
        )

    print(f"Loading dataset from {input_path}...")
    try:
        df = pd.read_csv(input_path)
    except Exception as e:
        raise RuntimeError(f"Failed to load dataset from {input_path}: {e}") from e

    print(f"Loaded {len(df)} rows.")

    print("Computing constraint counts...")
    df = add_constraint_count_column(df)

    # Verify the column was added
    if 'constraint_count' not in df.columns:
        raise RuntimeError("Failed to add 'constraint_count' column to dataframe.")

    # Ensure the count is non-negative and matches the filter logic (>=5)
    # The filter in T013 should have ensured >= 5, but we verify the column is populated.
    min_count = df['constraint_count'].min()
    print(f"Constraint count range in filtered data: [{min_count}, {df['constraint_count'].max()}]")

    if min_count < 5:
        print(f"Warning: Minimum constraint count is {min_count}, which is less than the expected 5. "
              "The filter logic in T013 might not have been applied correctly, or the count logic differs.")

    print(f"Saving updated dataset to {output_path}...")
    try:
        df.to_csv(output_path, index=False)
    except Exception as e:
        raise RuntimeError(f"Failed to save dataset to {output_path}: {e}") from e

    print(f"Successfully added 'constraint_count' column to {output_path}.")
    print(f"Total rows: {len(df)}")


if __name__ == "__main__":
    main()
