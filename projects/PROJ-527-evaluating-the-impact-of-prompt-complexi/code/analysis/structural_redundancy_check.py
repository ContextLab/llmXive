"""
Structural Redundancy Verification Module.

This module implements T039: Verify that 'degenerate' prompts have higher
structural element counts than 'very complex' prompts. If this condition fails
for any problem, flag the sample for manual review as per spec.md US-1/US-3.
"""

import os
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd

from config import Paths
from utils.logger import get_logger

logger = get_logger(__name__)


def load_prompt_variants() -> pd.DataFrame:
    """
    Load the prompt variants dataset from the processed data directory.

    Returns:
        pd.DataFrame: DataFrame containing prompt variant data with columns:
            - problem_id
            - complexity_label
            - structural_element_count
    """
    input_path = Paths.PROCESSED_DATA_DIR / "prompt_variants.parquet"

    if not input_path.exists():
        raise FileNotFoundError(
            f"Required data file not found: {input_path}. "
            "Ensure T018 (storage) has been executed to generate prompt_variants.parquet."
        )

    logger.info(f"Loading prompt variants from {input_path}")
    df = pd.read_parquet(input_path)

    required_cols = {"problem_id", "complexity_label", "structural_element_count"}
    if not required_cols.issubset(df.columns):
        missing = required_cols - set(df.columns)
        raise ValueError(
            f"DataFrame missing required columns: {missing}. "
            f"Found columns: {list(df.columns)}"
        )

    return df


def verify_redundancy(df: pd.DataFrame) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Verify structural redundancy: 'degenerate' prompts must have higher
    structural element counts than 'very complex' prompts for the same problem.

    Args:
        df: DataFrame with problem_id, complexity_label, structural_element_count.

    Returns:
        Tuple of (passed_samples, failed_samples):
            - passed_samples: List of dicts for problems where degenerate > very_complex
            - failed_samples: List of dicts for problems where degenerate <= very_complex
    """
    passed_samples = []
    failed_samples = []

    # Group by problem_id to compare variants within the same problem
    grouped = df.groupby("problem_id")

    for problem_id, group in grouped:
        # Filter for the two specific complexity levels
        degenerate_row = group[group["complexity_label"] == "degenerate"]
        very_complex_row = group[group["complexity_label"] == "very_complex"]

        if degenerate_row.empty or very_complex_row.empty:
            # If either is missing, we cannot verify. Flag for manual review.
            logger.warning(
                f"Problem {problem_id} missing 'degenerate' or 'very_complex' variant. "
                "Flagging for manual review."
            )
            failed_samples.append({
                "problem_id": problem_id,
                "reason": "Missing required complexity variants (degenerate or very_complex)",
                "degenerate_count": None,
                "very_complex_count": None
            })
            continue

        degenerate_count = degenerate_row["structural_element_count"].iloc[0]
        very_complex_count = very_complex_row["structural_element_count"].iloc[0]

        # Verification logic: degenerate MUST be strictly greater than very_complex
        if degenerate_count > very_complex_count:
            passed_samples.append({
                "problem_id": problem_id,
                "degenerate_count": degenerate_count,
                "very_complex_count": very_complex_count,
                "delta": degenerate_count - very_complex_count
            })
        else:
            logger.warning(
                f"Structural redundancy violation for problem {problem_id}: "
                f"degenerate ({degenerate_count}) <= very_complex ({very_complex_count}). "
                "Flagging for manual review."
            )
            failed_samples.append({
                "problem_id": problem_id,
                "reason": "Degenerate prompt does not have higher structural count than very complex",
                "degenerate_count": degenerate_count,
                "very_complex_count": very_complex_count,
                "delta": degenerate_count - very_complex_count
            })

    return passed_samples, failed_samples


def write_manual_review_flags(failed_samples: List[Dict[str, Any]]) -> Path:
    """
    Write flagged samples to the manual review queue CSV.

    Args:
        failed_samples: List of dicts containing failed verification records.

    Returns:
        Path to the written CSV file.
    """
    output_path = Paths.RESULTS_DIR / "manual_review_queue.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not failed_samples:
        # Create empty file with headers if no failures
        with open(output_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["problem_id", "reason", "degenerate_count", "very_complex_count", "delta"])
            writer.writeheader()
        logger.info(f"No structural redundancy failures found. Created empty queue at {output_path}")
        return output_path

    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["problem_id", "reason", "degenerate_count", "very_complex_count", "delta"])
        writer.writeheader()
        writer.writerows(failed_samples)

    logger.info(f"Wrote {len(failed_samples)} structural redundancy failures to {output_path}")
    return output_path


def run_structural_redundancy_check() -> Tuple[int, int]:
    """
    Main entry point for the structural redundancy verification task (T039).

    Returns:
        Tuple of (passed_count, failed_count)
    """
    logger.info("Starting structural redundancy verification (T039)...")

    try:
        df = load_prompt_variants()
    except FileNotFoundError as e:
        logger.error(str(e))
        raise

    passed_samples, failed_samples = verify_redundancy(df)

    write_manual_review_flags(failed_samples)

    logger.info(
        f"Structural redundancy check complete: "
        f"{len(passed_samples)} passed, {len(failed_samples)} flagged for manual review."
    )

    return len(passed_samples), len(failed_samples)


def main():
    """CLI entry point."""
    try:
        passed, failed = run_structural_redundancy_check()
        if failed > 0:
            print(f"WARNING: {failed} samples failed structural redundancy verification and were flagged for manual review.")
        else:
            print("SUCCESS: All samples passed structural redundancy verification.")
    except Exception as e:
        logger.exception("Fatal error during structural redundancy check")
        raise


if __name__ == "__main__":
    main()