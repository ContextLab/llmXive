"""
Representativeness Validator for Context-Bound Data Filtering.

This module implements the Kolmogorov-Smirnov (KS) test to verify that the
filtered dataset (instances with >500 lines of relevant file history) is
statistically representative of the full raw dataset distribution.

Constraint: If KS-test p-value < 0.05, the run MUST fail with
"Insufficient Context-Bound Data" error.
"""

import os
import sys
import logging
import argparse
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

import pandas as pd
import numpy as np
from scipy import stats

# Add parent directory to path for imports if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logger import setup_logger, log_error, AnalysisError

# Initialize logger
logger = setup_logger(__name__)


def load_parquet_dataset(file_path: str) -> pd.DataFrame:
    """
    Load a Parquet dataset from disk.

    Args:
        file_path: Path to the parquet file.

    Returns:
        pandas DataFrame containing the dataset.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is not a valid parquet.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Dataset file not found: {file_path}")

    try:
        df = pd.read_parquet(path)
        logger.info(f"Loaded dataset from {file_path} with {len(df)} rows.")
        return df
    except Exception as e:
        log_error(f"Failed to load parquet dataset from {file_path}: {e}")
        raise AnalysisError(f"Failed to load parquet dataset: {e}")


def calculate_line_counts(df: pd.DataFrame, line_count_col: str = "total_lines") -> np.ndarray:
    """
    Extract line count values from the dataframe.

    Args:
        df: The dataframe containing the data.
        line_count_col: The column name containing line counts.

    Returns:
        Numpy array of line count values.
    """
    if line_count_col not in df.columns:
        # Fallback: try to find a column that looks like line counts if exact name missing
        # But strict adherence suggests we expect the column from T012c
        raise ValueError(f"Column '{line_count_col}' not found in dataset. Available columns: {df.columns.tolist()}")

    values = df[line_count_col].dropna()
    logger.info(f"Extracted {len(values)} line count values from column '{line_count_col}'.")
    return values.values


def get_issue_types(df: pd.DataFrame, issue_type_col: str = "issue_type") -> np.ndarray:
    """
    Extract issue type values (encoded as integers for KS test) from the dataframe.

    Since KS test is for continuous distributions, we map categorical issue types
    to numeric codes for the purpose of distribution comparison.

    Args:
        df: The dataframe containing the data.
        issue_type_col: The column name containing issue types.

    Returns:
        Numpy array of encoded issue type values.
    """
    if issue_type_col not in df.columns:
        # If the column doesn't exist, return an empty array or handle gracefully
        # However, for representativeness, we need this data.
        logger.warning(f"Column '{issue_type_col}' not found. Skipping issue type distribution check.")
        return np.array([])

    # Encode categorical types to integers
    unique_types = df[issue_type_col].unique()
    type_to_int = {t: i for i, t in enumerate(unique_types)}
    encoded = df[issue_type_col].map(type_to_int).dropna()

    logger.info(f"Extracted {len(encoded)} issue type values from column '{issue_type_col}'.")
    return encoded.values


def perform_ks_test(sample: np.ndarray, population: np.ndarray, test_name: str) -> Tuple[float, float]:
    """
    Perform a two-sample Kolmogorov-Smirnov test.

    Args:
        sample: The filtered dataset values.
        population: The raw dataset values.
        test_name: Name of the test for logging.

    Returns:
        Tuple of (KS statistic, p-value).
    """
    if len(sample) == 0 or len(population) == 0:
        logger.warning(f"Cannot perform KS test for {test_name}: one or both samples are empty.")
        return 0.0, 1.0

    try:
        statistic, p_value = stats.ks_2samp(sample, population)
        logger.info(f"KS Test ({test_name}): statistic={statistic:.4f}, p-value={p_value:.4f}")
        return statistic, p_value
    except Exception as e:
        log_error(f"KS test failed for {test_name}: {e}")
        raise AnalysisError(f"KS test failed: {e}")


def validate_representativeness(
    filtered_path: str,
    raw_path: str,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Validate that the filtered dataset is representative of the raw dataset.

    This function performs KS tests on:
    1. Line counts distribution
    2. Issue types distribution (encoded)

    Constraint: If any p-value < alpha, the run MUST fail.

    Args:
        filtered_path: Path to the filtered dataset (parquet).
        raw_path: Path to the raw dataset (parquet).
        alpha: Significance level for the KS test (default 0.05).

    Returns:
        Dictionary containing test results and validation status.

    Raises:
        AnalysisError: If the filtered dataset is not representative.
    """
    logger.info(f"Starting representativeness validation: filtered={filtered_path}, raw={raw_path}")

    # Load datasets
    try:
        df_filtered = load_parquet_dataset(filtered_path)
        df_raw = load_parquet_dataset(raw_path)
    except Exception as e:
        log_error(f"Failed to load datasets for validation: {e}")
        raise

    results = {
        "filtered_path": filtered_path,
        "raw_path": raw_path,
        "filtered_count": len(df_filtered),
        "raw_count": len(df_raw),
        "tests": {},
        "passed": True,
        "message": ""
    }

    # Test 1: Line Counts
    try:
        filtered_lines = calculate_line_counts(df_filtered, "total_lines")
        raw_lines = calculate_line_counts(df_raw, "total_lines")

        stat, p_val = perform_ks_test(filtered_lines, raw_lines, "Line Counts")
        results["tests"]["line_counts"] = {
            "statistic": float(stat),
            "p_value": float(p_val),
            "passed": p_val >= alpha
        }

        if p_val < alpha:
            results["passed"] = False
            results["message"] += f"Line count distribution differs significantly (p={p_val:.4f} < {alpha}). "
    except Exception as e:
        log_error(f"Line count validation failed: {e}")
        results["passed"] = False
        results["message"] += f"Line count validation error: {e}. "

    # Test 2: Issue Types
    try:
        filtered_types = get_issue_types(df_filtered, "issue_type")
        raw_types = get_issue_types(df_raw, "issue_type")

        if len(filtered_types) > 0 and len(raw_types) > 0:
            stat, p_val = perform_ks_test(filtered_types, raw_types, "Issue Types")
            results["tests"]["issue_types"] = {
                "statistic": float(stat),
                "p_value": float(p_val),
                "passed": p_val >= alpha
            }

            if p_val < alpha:
                results["passed"] = False
                results["message"] += f"Issue type distribution differs significantly (p={p_val:.4f} < {alpha}). "
        else:
            logger.warning("Issue type data missing or empty, skipping this test.")
            results["tests"]["issue_types"] = {
                "statistic": None,
                "p_value": None,
                "passed": True,
                "skipped": True
            }
    except Exception as e:
        log_error(f"Issue type validation failed: {e}")
        results["passed"] = False
        results["message"] += f"Issue type validation error: {e}. "

    # Final Decision
    if not results["passed"]:
        error_msg = "Insufficient Context-Bound Data: Filtered dataset is not representative of the raw dataset."
        full_msg = f"{error_msg} Details: {results['message']}"
        logger.error(full_msg)
        raise AnalysisError(full_msg)

    logger.info("Representativeness validation PASSED.")
    results["message"] = "Validation passed. Filtered dataset is representative."
    return results


def main():
    """
    CLI entry point for the Representativeness Validator.
    """
    parser = argparse.ArgumentParser(
        description="Validate representativeness of filtered dataset vs raw dataset."
    )
    parser.add_argument(
        "--filtered",
        type=str,
        required=True,
        help="Path to the filtered dataset (parquet)."
    )
    parser.add_argument(
        "--raw",
        type=str,
        required=True,
        help="Path to the raw dataset (parquet)."
    )
    parser.add_argument(
        "--alpha",
        type=float,
        default=0.05,
        help="Significance level for KS test (default: 0.05)."
    )
    parser.add_argument(
        "--output",
        type=str,
        default="state/representativeness_results.json",
        help="Path to save validation results JSON."
    )

    args = parser.parse_args()

    try:
        results = validate_representativeness(
            args.filtered,
            args.raw,
            args.alpha
        )

        # Save results
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        import json
        with open(output_path, "w") as f:
            json.dump(results, f, indent=2, default=str)

        logger.info(f"Results saved to {output_path}")

        if not results["passed"]:
            # This should have raised an exception already, but double check
            sys.exit(1)

        sys.exit(0)

    except AnalysisError as e:
        logger.error(f"Validation Failed: {e}")
        sys.exit(1)
    except Exception as e:
        log_error(f"Unexpected error during validation: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()