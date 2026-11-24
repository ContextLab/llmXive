"""
Verification script for deterministic user matching.

This script runs the matching pipeline twice on the same input
datasets and asserts that the resulting matched DataFrames are
identical. It ensures that:
  1. The hashing step (`hash_username`) is fully deterministic.
  2. No random sampling or nondeterministic operations occur during
     matching.

The script is intended to be used by the verification step
`src/validation/verify_deterministic_match.py` referenced in the
task description. It can be executed manually:

    python -m src.validation.verify_deterministic_match

If the assertion fails, an `AssertionError` is raised and the
pipeline should be considered nondeterministic.
"""

import sys
from pathlib import Path

import pandas as pd
from pandas.testing import assert_frame_equal

# Project utilities
from llmxive_toolkit import paths, get_logger

# Import matching utilities
from src.match.user_match import (
    load_and_validate_loneliness_data,
    load_pushshift_data,
    perform_matching,
)

logger = get_logger(__name__)

def _load_datasets() -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load the required loneliness and Pushshift datasets.

    Returns
    -------
    tuple of (loneliness_df, pushshift_df)
    """
    # Define absolute paths using the toolkit helper (creates folders if needed)
    loneliness_path = paths.data("raw", "loneliness_dataset.parquet")
    pushshift_path = paths.data("raw", "pushshift_logs.parquet")

    logger.info(f"Loading loneliness data from {loneliness_path}")
    loneliness_df = load_and_validate_loneliness_data(loneliness_path)

    logger.info(f"Loading Pushshift data from {pushshift_path}")
    pushshift_df = load_pushshift_data(pushshift_path)

    return loneliness_df, pushshift_df

def _run_matching_twice(
    loneliness_df: pd.DataFrame, pushshift_df: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Execute the matching pipeline twice and return both results.

    The two runs are performed sequentially on the same in‑memory
    DataFrames to guarantee that any nondeterminism would be due
    to the matching logic itself (e.g., random sampling).

    Returns
    -------
    (first_match, second_match)
    """
    first_match = perform_matching(loneliness_df, pushshift_df)
    second_match = perform_matching(loneliness_df, pushshift_df)
    return first_match, second_match

def _normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Sort rows and columns to provide a canonical representation for
    comparison. This removes any ordering differences that are not
    semantically relevant.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame to normalize.

    Returns
    -------
    pd.DataFrame
        Normalized DataFrame.
    """
    # Ensure deterministic column order
    df = df.reindex(sorted(df.columns), axis=1)

    # Sort rows by all columns (lexicographic order)
    if not df.empty:
        df = df.sort_values(by=list(df.columns)).reset_index(drop=True)
    return df

def verify_deterministic_match() -> None:
    """
    Main verification routine.

    Loads the datasets, runs matching twice, normalizes the results,
    and asserts that they are identical. If the assertion fails,
    an AssertionError is raised with a detailed message.
    """
    logger.info("Starting deterministic matching verification")
    loneliness_df, pushshift_df = _load_datasets()

    first_match, second_match = _run_matching_twice(loneliness_df, pushshift_df)

    # Normalise both DataFrames before comparison
    first_norm = _normalize_dataframe(first_match)
    second_norm = _normalize_dataframe(second_match)

    try:
        assert_frame_equal(first_norm, second_norm, check_dtype=False)
        logger.info("Deterministic matching verification PASSED")
    except AssertionError as exc:
        logger.error("Deterministic matching verification FAILED")
        raise AssertionError(
            "Matching output differed between runs. "
            "Hashing or matching logic is nondeterministic."
        ) from exc

def main() -> int:
    """
    CLI entry point.

    Returns
    -------
    int
        Exit code: 0 on success, 1 on failure.
    """
    try:
        verify_deterministic_match()
        return 0
    except Exception as exc:
        logger.error(f"Verification failed: {exc}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
