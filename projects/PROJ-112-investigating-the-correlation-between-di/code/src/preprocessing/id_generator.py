"""
ID Generator Module for llmXive Project.

Generates deterministic, anonymized SHA256 sample IDs based on
the cohort name and the original sample ID.

This module ensures that:
1. IDs are unique per (cohort, original_id) pair.
2. IDs are deterministic (same input always yields same output).
3. No PII is retained in the output ID.
"""

import hashlib
import pandas as pd
from typing import List, Optional, Tuple


def generate_sample_id(cohort: str, original_id: str, separator: str = "_") -> str:
    """
    Generate a SHA256 hash ID for a sample based on cohort and original_id.

    Args:
        cohort (str): The cohort name (e.g., 'AGP', 'UKBB').
        original_id (str): The original sample identifier from the source dataset.
        separator (str): The string used to join cohort and original_id before hashing.

    Returns:
        str: The hexadecimal SHA256 hash string (first 32 characters).
    """
    if not isinstance(cohort, str) or not isinstance(original_id, str):
        raise TypeError("Both cohort and original_id must be strings.")

    if not cohort or not original_id:
        raise ValueError("Cohort and original_id cannot be empty.")

    # Normalize inputs to ensure consistency (lowercase, strip whitespace)
    normalized_cohort = cohort.strip().lower()
    normalized_original_id = original_id.strip()

    # Construct the unique string to hash
    raw_string = f"{normalized_cohort}{separator}{normalized_original_id}"

    # Generate SHA256 hash
    hash_object = hashlib.sha256(raw_string.encode('utf-8'))
    full_hash = hash_object.hexdigest()

    # Return a truncated version for readability (first 32 chars)
    # Full hash is 64 chars, 32 chars is still collision-resistant for this scale
    return full_hash[:32]


def generate_sample_ids_dataframe(
    df: pd.DataFrame,
    cohort_col: str,
    id_col: str,
    new_col_name: str = "sample_id",
    separator: str = "_"
) -> pd.DataFrame:
    """
    Add a new column of generated SHA256 sample IDs to a DataFrame.

    Args:
        df (pd.DataFrame): The input DataFrame containing sample data.
        cohort_col (str): The name of the column containing the cohort string.
        id_col (str): The name of the column containing the original ID.
        new_col_name (str): The name for the new generated ID column.
        separator (str): Separator used between cohort and original_id.

    Returns:
        pd.DataFrame: A copy of the input DataFrame with the new 'sample_id' column.
    """
    if cohort_col not in df.columns:
        raise ValueError(f"Column '{cohort_col}' not found in DataFrame.")
    if id_col not in df.columns:
        raise ValueError(f"Column '{id_col}' not found in DataFrame.")

    # Create the new column by applying the generation function
    # Using list comprehension for efficiency over apply for simple string ops
    new_ids = [
        generate_sample_id(cohort, original_id, separator)
        for cohort, original_id in zip(df[cohort_col], df[id_col])
    ]

    result_df = df.copy()
    result_df[new_col_name] = new_ids

    return result_df


def main():
    """
    Main entry point for running the ID generator as a standalone script.
    Demonstrates functionality with a small synthetic example and writes
    output to data/processed/sample_ids.tsv.
    """
    import os
    from pathlib import Path

    # Define paths relative to project root
    # Assuming this script is run from the project root
    output_dir = Path("data/processed")
    output_file = output_dir / "sample_ids.tsv"

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create a sample dataset for demonstration
    # In real usage, this would be loaded from data/processed/merged_harmonized.tsv
    data = {
        "cohort": ["AGP", "AGP", "UKBB", "UKBB", "AGP"],
        "original_id": ["sample_001", "sample_002", "UK_1001", "UK_1002", "sample_001"],
        "fiber_g_day": [25.5, 12.0, 30.0, 5.5, 25.5],
        "read_count": [10000, 4000, 15000, 8000, 10000]
    }

    df = pd.DataFrame(data)

    print(f"Processing {len(df)} samples...")
    print(f"Input columns: {list(df.columns)}")

    # Generate IDs
    df_with_ids = generate_sample_ids_dataframe(
        df,
        cohort_col="cohort",
        id_col="original_id",
        new_col_name="sample_id"
    )

    print(f"Generated IDs: {list(df_with_ids['sample_id'])}")

    # Save to TSV
    df_with_ids.to_csv(output_file, sep='\t', index=False)
    print(f"Successfully wrote sample IDs to {output_file}")

    # Verify determinism by re-generating
    df_check = generate_sample_ids_dataframe(
        df,
        cohort_col="cohort",
        id_col="original_id",
        new_col_name="sample_id_check"
    )
    assert (df_with_ids['sample_id'] == df_check['sample_id_check']).all(), "ID generation is not deterministic!"
    print("Determinism check passed.")


if __name__ == "__main__":
    main()