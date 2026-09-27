"""Structural Baseline Verification Module.

Implements T062: Compare pre- and post-irradiation structural baselines (UV-Vis spectra)
and flag deviations exceeding the noise threshold to ensure kinetic data integrity.
Addresses Rosalind Franklin's review regarding structural baseline measurement.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

# Import from sibling modules based on provided API surface
# We assume ground_state.py produced the baseline data at the expected path
from config import get_processed_data_path, ensure_directories
from utils.logging import setup_logging, log_operation

# Constants
BASELINE_DATA_PATH = "data/processed/ground_state_spectra.csv"
OUTPUT_PATH = "data/processed/baseline_verification_report.json"
DEFAULT_NOISE_THRESHOLD = 0.005  # Absorbance units (AU) - matches T055 baseline noise


def load_baseline_data() -> pd.DataFrame:
    """Load the ground state spectra data produced by T055.

    Returns:
        DataFrame with columns: wavelength, absorbance_pre, absorbance_post, solvent

    Raises:
        FileNotFoundError: If the baseline data file does not exist.
    """
    processed_path = get_processed_data_path()
    file_path = Path(processed_path) / "ground_state_spectra.csv"

    if not file_path.exists():
        raise FileNotFoundError(
            f"Baseline data file not found at {file_path}. "
            "Please ensure T055 (Ground-State Characterization) has been executed successfully."
        )

    return pd.read_csv(file_path)


def calculate_baseline_deviation(
    pre_spectrum: np.ndarray, post_spectrum: np.ndarray
) -> np.ndarray:
    """Calculate the absolute deviation between pre- and post-irradiation spectra.

    Args:
        pre_spectrum: Array of pre-irradiation absorbance values.
        post_spectrum: Array of post-irradiation absorbance values.

    Returns:
        Array of absolute deviations.
    """
    return np.abs(pre_spectrum - post_spectrum)


def flag_deviations(
    deviations: np.ndarray, threshold: float
) -> Tuple[List[bool], int]:
    """Flag points where deviation exceeds the noise threshold.

    Args:
        deviations: Array of absolute deviations.
        threshold: Maximum allowable deviation (noise threshold).

    Returns:
        Tuple of (list of boolean flags, count of exceeded points).
    """
    flags = deviations > threshold
    exceeded_count = int(np.sum(flags))
    return flags.tolist(), exceeded_count


def verify_baseline_integrity(
    df: pd.DataFrame, noise_threshold: float = DEFAULT_NOISE_THRESHOLD
) -> Dict[str, Any]:
    """Perform the full baseline verification analysis.

    Args:
        df: DataFrame containing baseline spectra data.
        noise_threshold: Threshold in AU for flagging deviations.

    Returns:
        Dictionary containing the verification report data.
    """
    results = []
    total_spectra = 0
    total_exceeded = 0
    passed_count = 0
    failed_count = 0

    # Group by solvent and replicate if available
    group_cols = [col for col in df.columns if col in ['solvent', 'replicate_id']]
    if not group_cols:
        # Fallback if grouping columns don't exist
        group_cols = []

    for name, group in df.groupby(group_cols) if group_cols else [(None, df)]:
        total_spectra += 1

        # Extract pre and post arrays
        # Assuming the CSV has 'absorbance_pre' and 'absorbance_post' columns
        # or 'absorbance' is repeated for pre/post in a wide format.
        # Based on T055 description, we expect wide format or specific columns.
        if 'absorbance_pre' in df.columns and 'absorbance_post' in df.columns:
            pre_vals = group['absorbance_pre'].values
            post_vals = group['absorbance_post'].values
        else:
            # Fallback: assume single column and structure is different,
            # but for this implementation we rely on T055 output format.
            raise ValueError(
                "Expected 'absorbance_pre' and 'absorbance_post' columns in baseline data. "
                "Please verify T055 output format."
            )

        # Ensure equal length
        min_len = min(len(pre_vals), len(post_vals))
        pre_vals = pre_vals[:min_len]
        post_vals = post_vals[:min_len]

        deviations = calculate_baseline_deviation(pre_vals, post_vals)
        flags, exceeded_count = flag_deviations(deviations, noise_threshold)

        total_exceeded += exceeded_count

        # Determine pass/fail for this run
        # A run fails if ANY point exceeds the threshold significantly,
        # or if the mean deviation is above threshold (depending on strictness).
        # We'll use a strict rule: fail if any point exceeds threshold.
        run_passed = exceeded_count == 0

        if run_passed:
            passed_count += 1
        else:
            failed_count += 1

        # Construct result entry
        result_entry = {
            "solvent": name[0] if group_cols and isinstance(name, tuple) else (name if not group_cols else "unknown"),
            "replicate_id": name[1] if group_cols and isinstance(name, tuple) else None,
            "n_points": min_len,
            "exceeded_points": exceeded_count,
            "max_deviation": float(np.max(deviations)),
            "mean_deviation": float(np.mean(deviations)),
            "status": "PASS" if run_passed else "FAIL",
            "flags": flags, # List of booleans per wavelength point
            "threshold_applied": noise_threshold
        }
        results.append(result_entry)

    # Calculate overall statistics
    overall_status = "PASS" if failed_count == 0 else "FAIL"

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "noise_threshold_au": noise_threshold,
        "total_runs_analyzed": total_spectra,
        "runs_passed": passed_count,
        "runs_failed": failed_count,
        "overall_status": overall_status,
        "total_points_exceeded": total_exceeded,
        "details": results
    }

    return report


def write_verification_report(report: Dict[str, Any], output_path: str) -> None:
    """Write the verification report to a JSON file.

    Args:
        report: The report dictionary.
        output_path: Path to the output JSON file.
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    logging.info(f"Verification report written to {output_file}")


def run_baseline_verification(
    noise_threshold: float = DEFAULT_NOISE_THRESHOLD
) -> Dict[str, Any]:
    """Main entry point for the baseline verification pipeline.

    Args:
        noise_threshold: The noise threshold in AU.

    Returns:
        The generated report dictionary.
    """
    logging.info("Starting Structural Baseline Verification (T062)")

    # 1. Load Data
    logging.info(f"Loading baseline data from {BASELINE_DATA_PATH}")
    try:
        df = load_baseline_data()
    except FileNotFoundError as e:
        logging.error(str(e))
        raise

    logging.info(f"Loaded {len(df)} rows of baseline data")

    # 2. Verify
    report = verify_baseline_integrity(df, noise_threshold)

    # 3. Write Output
    output_path = Path(get_processed_data_path()) / OUTPUT_PATH
    write_verification_report(report, str(output_path))

    logging.info(f"Baseline verification complete. Overall Status: {report['overall_status']}")

    return report


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="T062: Structural Baseline Verification"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=DEFAULT_NOISE_THRESHOLD,
        help=f"Noise threshold in AU (default: {DEFAULT_NOISE_THRESHOLD})"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level"
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(level=args.log_level)

    try:
        run_baseline_verification(noise_threshold=args.threshold)
    except Exception as e:
        logging.exception(f"Baseline verification failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
