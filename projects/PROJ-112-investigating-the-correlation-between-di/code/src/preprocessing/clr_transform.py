"""
Centered Log-Ratio (CLR) Transformation for Microbiome Data.

This module implements the CLR transformation for compositional data (taxon abundances).
It adds a pseudocount to handle zero-inflation, applies the transformation, and validates
the output for NaN/Inf values.
"""

import argparse
import logging
import sys
import os
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any

import pandas as pd
import numpy as np

# Import logger from the project's utility module
from src.utils.logger import get_logger

# Constants
DEFAULT_PSEUDOCOUNT = 1e-6
DEFAULT_INPUT_FILE = "data/processed/merged_harmonized.tsv"
DEFAULT_OUTPUT_FILE = "data/processed/clr_transformed.tsv"
DEFAULT_VALIDATION_LOG = "data/processed/results/clr_validation_log.txt"
TAXON_COLUMNS_PREFIX = "taxon_"  # Assumption: taxon columns start with this or are identified by schema
# Based on T014 schema: sample_id, cohort_id, fiber_g_day, read_count, taxon_abundances...
# We will identify taxon columns as all numeric columns excluding known metadata columns.

METADATA_COLUMNS = ["sample_id", "cohort_id", "fiber_g_day", "read_count"]


def get_project_root() -> Path:
    """Determine the project root directory."""
    # Assume the script is run from the project root or code/ directory
    # We look for a .git folder or specific structure
    current = Path(__file__).resolve()
    # Traverse up until we find a directory with 'data' or '.git'
    for parent in current.parents:
        if (parent / "data").exists() or (parent / ".git").exists():
            return parent
    # Fallback to parent of src/preprocessing
    return current.parent.parent.parent


def add_pseudocount(
    df: pd.DataFrame,
    taxon_cols: List[str],
    pseudocount: float = DEFAULT_PSEUDOCOUNT
) -> pd.DataFrame:
    """
    Add a pseudocount to zero-inflated taxon abundance columns.

    Args:
        df: Input DataFrame.
        taxon_cols: List of column names representing taxon abundances.
        pseudocount: Value to add to zeros (default 1e-6).

    Returns:
        DataFrame with pseudocount added to specified columns.
    """
    df_copy = df.copy()
    for col in taxon_cols:
        # Ensure we don't double count if already non-zero, but the operation is safe: x + c
        # Specifically, we want to ensure no zeros exist before log.
        # The standard approach is simply adding the count to all values or just zeros.
        # Adding to all is mathematically equivalent to shifting the log domain.
        df_copy[col] = df_copy[col] + pseudocount
    return df_copy


def apply_clr(
    df: pd.DataFrame,
    taxon_cols: List[str]
) -> pd.DataFrame:
    """
    Apply Centered Log-Ratio (CLR) transformation.

    CLR(x) = log(x / geometric_mean(x)) = log(x) - mean(log(x))

    Args:
        df: DataFrame with pseudocount added.
        taxon_cols: List of taxon column names.

    Returns:
        DataFrame with CLR-transformed values in the taxon columns.
    """
    df_copy = df.copy()

    # Calculate log of taxon columns
    log_vals = np.log(df_copy[taxon_cols])

    # Calculate geometric mean per sample (row-wise mean of logs)
    # geometric_mean = exp(mean(log(x)))
    # CLR = log(x) - mean(log(x))
    row_means = log_vals.mean(axis=1)

    for col in taxon_cols:
        df_copy[col] = log_vals[col] - row_means

    return df_copy


def validate_output(
    df: pd.DataFrame,
    taxon_cols: List[str],
    logger: logging.Logger
) -> Tuple[bool, str]:
    """
    Validate that the output contains no NaN or Inf values.

    Args:
        df: Transformed DataFrame.
        taxon_cols: List of taxon column names to check.
        logger: Logger instance.

    Returns:
        Tuple of (is_valid, message).
    """
    issues = []
    for col in taxon_cols:
        if df[col].isna().any():
            count = df[col].isna().sum()
            issues.append(f"Column '{col}' contains {count} NaN values.")
        if np.isinf(df[col]).any():
            count = np.isinf(df[col]).sum()
            issues.append(f"Column '{col}' contains {count} Inf values.")

    if issues:
        message = "Validation FAILED:\n" + "\n".join(issues)
        logger.error(message)
        return False, message
    else:
        message = "Validation PASSED: No NaN or Inf values detected in transformed taxon columns."
        logger.info(message)
        return True, message


def identify_taxon_columns(df: pd.DataFrame) -> List[str]:
    """
    Identify taxon abundance columns.
    Heuristic: All numeric columns that are not in the METADATA_COLUMNS list.
    """
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    taxon_cols = [c for c in numeric_cols if c not in METADATA_COLUMNS]
    return taxon_cols


def run_clr_transform(
    input_path: str,
    output_path: str,
    validation_log_path: str,
    pseudocount: float = DEFAULT_PSEUDOCOUNT
) -> bool:
    """
    Main execution logic for CLR transformation.

    Args:
        input_path: Path to the harmonized input file.
        output_path: Path to write the CLR transformed file.
        validation_log_path: Path to write the validation log.
        pseudocount: Pseudocount value to add.

    Returns:
        True if successful and validation passes, False otherwise.
    """
    logger = get_logger("clr_transform")
    project_root = get_project_root()

    # Resolve paths relative to project root if they aren't absolute
    input_file = Path(input_path) if Path(input_path).is_absolute() else project_root / input_path
    output_file = Path(output_path) if Path(output_path).is_absolute() else project_root / output_path
    log_file = Path(validation_log_path) if Path(validation_log_path).is_absolute() else project_root / validation_log_path

    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        return False

    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)
    log_file.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Loading data from {input_file}")
    try:
        df = pd.read_csv(input_file, sep='\t')
    except Exception as e:
        logger.error(f"Failed to read input file: {e}")
        return False

    logger.info(f"Loaded {len(df)} samples with {len(df.columns)} columns")

    # Identify taxon columns
    taxon_cols = identify_taxon_columns(df)
    if not taxon_cols:
        logger.error("No taxon abundance columns found. Please check input schema.")
        return False

    logger.info(f"Identified {len(taxon_cols)} taxon columns for transformation")

    # Step 1: Add pseudocount
    logger.info(f"Adding pseudocount ({pseudocount}) to zero-inflated data")
    df_transformed = add_pseudocount(df, taxon_cols, pseudocount)

    # Step 2: Apply CLR
    logger.info("Applying CLR transformation")
    df_transformed = apply_clr(df_transformed, taxon_cols)

    # Step 3: Validate
    is_valid, message = validate_output(df_transformed, taxon_cols, logger)

    # Write validation log
    with open(log_file, 'w') as f:
        f.write(f"CLR Transformation Validation Report\n")
        f.write(f"Input: {input_file}\n")
        f.write(f"Output: {output_file}\n")
        f.write(f"Timestamp: {pd.Timestamp.now()}\n")
        f.write(f"Status: {'PASSED' if is_valid else 'FAILED'}\n")
        f.write(f"Details:\n{message}\n")

    if not is_valid:
        logger.error("Validation failed. Exiting.")
        return False

    # Write output
    logger.info(f"Writing CLR transformed data to {output_file}")
    try:
        df_transformed.to_csv(output_file, sep='\t', index=False)
    except Exception as e:
        logger.error(f"Failed to write output file: {e}")
        return False

    logger.info("CLR transformation completed successfully.")
    return True


def build_arg_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the CLI."""
    parser = argparse.ArgumentParser(
        description="Perform CLR transformation on harmonized microbiome data."
    )
    parser.add_argument(
        "--input",
        type=str,
        default=DEFAULT_INPUT_FILE,
        help=f"Path to the input harmonized TSV file (default: {DEFAULT_INPUT_FILE})"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=DEFAULT_OUTPUT_FILE,
        help=f"Path to the output CLR transformed TSV file (default: {DEFAULT_OUTPUT_FILE})"
    )
    parser.add_argument(
        "--validation-log",
        type=str,
        default=DEFAULT_VALIDATION_LOG,
        help=f"Path to the validation log file (default: {DEFAULT_VALIDATION_LOG})"
    )
    parser.add_argument(
        "--pseudocount",
        type=float,
        default=DEFAULT_PSEUDOCOUNT,
        help=f"Pseudocount value to add for zero handling (default: {DEFAULT_PSEUDOCOUNT})"
    )
    return parser


def main():
    """Entry point for the script."""
    parser = build_arg_parser()
    args = parser.parse_args()

    success = run_clr_transform(
        input_path=args.input,
        output_path=args.output,
        validation_log_path=args.validation_log,
        pseudocount=args.pseudocount
    )

    if not success:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
