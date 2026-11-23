"""
System-level mass balance verification for texture descriptors.

This module implements the system-level mass balance check required by
spec.md US-2 Scenario 2 acceptance criteria. It verifies that the sum of
all texture components (Brass, Copper, S, Goss, and Random) equals 1.0 ± 0.01
for the aggregated dataset in data/processed/descriptors.csv.

This is distinct from T019 (sample-level check) and T009a (schema validation).
"""
import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

import pandas as pd
import numpy as np

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.logging import get_logger

logger = get_logger(__name__)

# Constants
DESCRIPTORS_PATH = project_root / "data" / "processed" / "descriptors.csv"
OUTPUT_REPORT_PATH = project_root / "data" / "processed" / "mass_balance_verification_report.json"
TOLERANCE = 0.01
COMPONENT_COLUMNS = ["brass_fraction", "copper_fraction", "s_fraction", "goss_fraction", "random_fraction"]


def load_descriptors() -> pd.DataFrame:
    """
    Load the descriptors CSV file.

    Returns:
        pd.DataFrame: The loaded descriptors dataframe.

    Raises:
        FileNotFoundError: If the descriptors file does not exist.
        ValueError: If required columns are missing.
    """
    if not DESCRIPTORS_PATH.exists():
        raise FileNotFoundError(
            f"Descriptors file not found at {DESCRIPTORS_PATH}. "
            "Ensure T020a has been completed successfully."
        )

    df = pd.read_csv(DESCRIPTORS_PATH)

    # Verify required columns exist
    missing_cols = [col for col in COMPONENT_COLUMNS if col not in df.columns]
    if missing_cols:
        raise ValueError(
            f"Missing required columns in descriptors file: {missing_cols}. "
            "Ensure T018/T020a has generated the correct output format."
        )

    logger.info(f"Loaded {len(df)} samples from {DESCRIPTORS_PATH}")
    return df


def calculate_total_fractions(df: pd.DataFrame) -> pd.Series:
    """
    Calculate the sum of all texture component fractions for each sample.

    Args:
        df: The descriptors dataframe.

    Returns:
        pd.Series: The sum of fractions for each row.
    """
    return df[COMPONENT_COLUMNS].sum(axis=1)


def validate_aggregated_mass_balance(df: pd.DataFrame) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate mass balance at the system level (aggregated dataset).

    This function checks if the sum of all components across the entire
    dataset averages to 1.0 within the specified tolerance.

    Args:
        df: The descriptors dataframe.

    Returns:
        Tuple[bool, Dict[str, Any]]: (is_valid, report_dict)
    """
    total_fractions = calculate_total_fractions(df)

    # Calculate statistics for the aggregated dataset
    mean_sum = total_fractions.mean()
    std_sum = total_fractions.std()
    min_sum = total_fractions.min()
    max_sum = total_fractions.max()

    # Check if the aggregated mean is within tolerance
    is_valid = abs(mean_sum - 1.0) <= TOLERANCE

    # Count samples that are individually out of tolerance
    out_of_tolerance_count = (abs(total_fractions - 1.0) > TOLERANCE).sum()
    total_samples = len(df)

    report = {
        "status": "PASS" if is_valid else "FAIL",
        "mean_sum": float(mean_sum),
        "std_sum": float(std_sum),
        "min_sum": float(min_sum),
        "max_sum": float(max_sum),
        "tolerance": TOLERANCE,
        "total_samples": total_samples,
        "out_of_tolerance_samples": int(out_of_tolerance_count),
        "out_of_tolerance_percentage": float(out_of_tolerance_count / total_samples * 100) if total_samples > 0 else 0.0,
        "message": (
            f"Aggregated mass balance check {'PASSED' if is_valid else 'FAILED'}. "
            f"Mean sum: {mean_sum:.6f} (target: 1.0, tolerance: ±{TOLERANCE}). "
            f"{out_of_tolerance_count}/{total_samples} samples are individually out of tolerance."
        )
    }

    return is_valid, report


def run_mass_balance_verification() -> Dict[str, Any]:
    """
    Main entry point for running the mass balance verification.

    Returns:
        Dict[str, Any]: The verification report.
    """
    logger.info("Starting system-level mass balance verification...")

    try:
        # Load data
        df = load_descriptors()

        # Validate mass balance
        is_valid, report = validate_aggregated_mass_balance(df)

        # Save report to file
        OUTPUT_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_REPORT_PATH, 'w') as f:
            json.dump(report, f, indent=2)

        logger.info(f"Verification report saved to {OUTPUT_REPORT_PATH}")
        logger.info(report["message"])

        if not is_valid:
            logger.error("System-level mass balance verification FAILED.")
            logger.error("This indicates a fundamental issue with the descriptor calculation pipeline.")
            logger.error("Check T018 (descriptor calculation) and T019 (sample-level validation).")
            raise ValueError("Mass balance verification failed at system level.")

        return report

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise
    except Exception as e:
        logger.exception(f"Unexpected error during mass balance verification: {e}")
        raise


def main():
    """CLI entry point."""
    try:
        report = run_mass_balance_verification()
        print(f"Verification Status: {report['status']}")
        print(f"Message: {report['message']}")
        sys.exit(0)
    except Exception as e:
        print(f"Verification FAILED: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
