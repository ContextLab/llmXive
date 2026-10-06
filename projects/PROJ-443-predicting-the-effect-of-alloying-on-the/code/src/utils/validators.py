"""
Data integrity validation utilities for HEA project.

Provides functions to validate composition sums, sample counts,
and general data integrity checks.
"""
import logging
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional, Union
import pandas as pd
import numpy as np

from utils.seeds import get_seed

# Configure logging for this module
logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Custom exception for data validation errors."""
    pass


def validate_composition_sum(
    df: pd.DataFrame,
    composition_columns: List[str],
    tolerance: float = 1e-6
) -> Tuple[bool, List[str]]:
    """
    Validate that the sum of composition fractions equals 1.0 within tolerance.

    Args:
        df: DataFrame containing composition data.
        composition_columns: List of column names representing elemental fractions.
        tolerance: Maximum allowed deviation from 1.0.

    Returns:
        Tuple of (is_valid, list_of_error_messages).

    Raises:
        ValidationError: If any row fails validation.
    """
    if not composition_columns:
        raise ValidationError("No composition columns provided for validation.")

    missing_cols = [col for col in composition_columns if col not in df.columns]
    if missing_cols:
        raise ValidationError(f"Missing composition columns: {missing_cols}")

    sums = df[composition_columns].sum(axis=1)
    invalid_mask = np.abs(sums - 1.0) > tolerance
    invalid_indices = df.index[invalid_mask].tolist()

    errors = []
    if invalid_indices:
        errors.append(
            f"Found {len(invalid_indices)} rows where composition sum != 1.0 "
            f"(tolerance={tolerance}). First few indices: {invalid_indices[:5]}"
        )
        # Log details for debugging
        for idx in invalid_indices[:3]:
            row_sum = sums.loc[idx]
            errors.append(f"  Row {idx}: sum = {row_sum:.6f}")

    is_valid = len(invalid_indices) == 0
    return is_valid, errors


def normalize_compositions(
    df: pd.DataFrame,
    composition_columns: List[str],
    inplace: bool = False
) -> pd.DataFrame:
    """
    Normalize composition columns so they sum to exactly 1.0.

    Args:
        df: DataFrame containing composition data.
        composition_columns: List of column names representing elemental fractions.
        inplace: If True, modify the input DataFrame; otherwise return a copy.

    Returns:
        DataFrame with normalized compositions.

    Raises:
        ValidationError: If normalization would result in division by zero
                         or if non-positive sums are encountered.
    """
    if not composition_columns:
        raise ValidationError("No composition columns provided for normalization.")

    missing_cols = [col for col in composition_columns if col not in df.columns]
    if missing_cols:
        raise ValidationError(f"Missing composition columns: {missing_cols}")

    target_df = df if inplace else df.copy()
    sums = target_df[composition_columns].sum(axis=1)

    # Check for zero or negative sums
    zero_or_neg_mask = sums <= 0
    if zero_or_neg_mask.any():
        invalid_indices = target_df.index[zero_or_neg_mask].tolist()
        raise ValidationError(
            f"Found {len(invalid_indices)} rows with zero or negative composition sum. "
            f"Cannot normalize. First few indices: {invalid_indices[:5]}"
        )

    # Normalize
    target_df[composition_columns] = target_df[composition_columns].div(sums, axis=0)

    # Verify normalization
    new_sums = target_df[composition_columns].sum(axis=1)
    if not np.allclose(new_sums, 1.0, rtol=1e-10):
        raise ValidationError(
            f"Normalization failed: some rows still do not sum to 1.0. "
            f"Max deviation: {np.abs(new_sums - 1.0).max()}"
        )

    return target_df


def validate_sample_count(
    df: pd.DataFrame,
    min_samples: int = 500,
    group_column: Optional[str] = None
) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate that the dataset meets minimum sample count requirements.

    Args:
        df: DataFrame to validate.
        min_samples: Minimum required number of samples.
        group_column: Optional column name to check samples per group.

    Returns:
        Tuple of (is_valid, info_dict).
        info_dict contains:
          - 'total_samples': int
          - 'meets_threshold': bool
          - 'groups_info': dict (if group_column provided)

    Raises:
        ValidationError: If sample count is below threshold and no fallback is defined.
    """
    total_samples = len(df)
    info = {
        'total_samples': total_samples,
        'meets_threshold': total_samples >= min_samples,
        'min_required': min_samples
    }

    if group_column:
        if group_column not in df.columns:
            raise ValidationError(f"Group column '{group_column}' not found in DataFrame.")
        group_counts = df.groupby(group_column).size()
        info['groups_info'] = {
            'num_groups': len(group_counts),
            'min_group_size': int(group_counts.min()),
            'max_group_size': int(group_counts.max()),
            'mean_group_size': float(group_counts.mean())
        }

    if total_samples < min_samples:
        logger.warning(
            f"Sample count ({total_samples}) is below threshold ({min_samples}). "
            "Proceeding with Reduced Power Analysis as per spec."
        )
        # Per spec: DO NOT halt, just log and return info
        # The caller (e.g., power_report.py) will handle the underpowered logic

    return info['meets_threshold'], info


def validate_data_integrity(
    df: pd.DataFrame,
    composition_columns: List[str],
    target_column: Optional[str] = None,
    tolerance: float = 1e-6
) -> Tuple[bool, List[str]]:
    """
    Perform comprehensive data integrity checks.

    Checks:
      1. Composition sum = 1.0
      2. No NaN values in composition columns
      3. No negative values in composition columns
      4. Target column (if provided) has no NaN and is positive

    Args:
        df: DataFrame to validate.
        composition_columns: List of composition column names.
        target_column: Optional target variable column name.
        tolerance: Tolerance for composition sum validation.

    Returns:
        Tuple of (is_valid, list_of_error_messages).
    """
    errors = []

    # Check 1: Composition sum
    is_valid_sum, sum_errors = validate_composition_sum(
        df, composition_columns, tolerance
    )
    errors.extend(sum_errors)

    # Check 2: NaN in composition
    nan_counts = df[composition_columns].isna().sum()
    if nan_counts.any():
        cols_with_nan = nan_counts[nan_counts > 0].index.tolist()
        errors.append(
            f"Found NaN values in composition columns: {cols_with_nan}. "
            f"Counts: {nan_counts[nan_counts > 0].to_dict()}"
        )

    # Check 3: Negative values in composition
    neg_mask = df[composition_columns] < 0
    if neg_mask.any().any():
        neg_counts = neg_mask.sum(axis=1)
        rows_with_neg = neg_counts[neg_counts > 0].index.tolist()
        errors.append(
            f"Found {len(rows_with_neg)} rows with negative composition values."
        )

    # Check 4: Target column (if provided)
    if target_column:
        if target_column not in df.columns:
            errors.append(f"Target column '{target_column}' not found in DataFrame.")
        else:
            target_nan = df[target_column].isna().sum()
            if target_nan > 0:
                errors.append(
                    f"Found {target_nan} NaN values in target column '{target_column}'."
                )
            if (df[target_column] <= 0).any():
                non_positive = (df[target_column] <= 0).sum()
                errors.append(
                    f"Found {non_positive} non-positive values in target column "
                    f"'{target_column}'."
                )

    is_valid = len(errors) == 0
    return is_valid, errors


def run_validations(
    df: pd.DataFrame,
    composition_columns: List[str],
    target_column: Optional[str] = None,
    min_samples: int = 500,
    group_column: Optional[str] = None,
    tolerance: float = 1e-6
) -> Dict[str, Any]:
    """
    Run all validation checks and return a comprehensive report.

    Args:
        df: DataFrame to validate.
        composition_columns: List of composition column names.
        target_column: Optional target variable column name.
        min_samples: Minimum required sample count.
        group_column: Optional column for group-based checks.
        tolerance: Tolerance for composition sum validation.

    Returns:
        Dictionary containing:
          - 'valid': bool (True if all critical checks pass)
          - 'composition_sum_valid': bool
          - 'integrity_valid': bool
          - 'sample_count_valid': bool
          - 'errors': list of error messages
          - 'warnings': list of warning messages
          - 'sample_info': dict from validate_sample_count
    """
    result = {
        'valid': True,
        'composition_sum_valid': True,
        'integrity_valid': True,
        'sample_count_valid': True,
        'errors': [],
        'warnings': [],
        'sample_info': {}
    }

    # Composition sum validation
    try:
        is_valid, errors = validate_composition_sum(df, composition_columns, tolerance)
        result['composition_sum_valid'] = is_valid
        result['errors'].extend(errors)
    except ValidationError as e:
        result['composition_sum_valid'] = False
        result['errors'].append(f"Composition sum validation failed: {str(e)}")

    # Data integrity validation
    try:
        is_valid, errors = validate_data_integrity(
            df, composition_columns, target_column, tolerance
        )
        result['integrity_valid'] = is_valid
        result['errors'].extend(errors)
    except ValidationError as e:
        result['integrity_valid'] = False
        result['errors'].append(f"Data integrity validation failed: {str(e)}")

    # Sample count validation
    try:
        is_valid, info = validate_sample_count(df, min_samples, group_column)
        result['sample_count_valid'] = is_valid
        result['sample_info'] = info
        if not is_valid:
            result['warnings'].append(
                f"Sample count ({info['total_samples']}) below threshold ({min_samples}). "
                "Proceeding with Reduced Power Analysis."
            )
    except ValidationError as e:
        result['sample_count_valid'] = False
        result['errors'].append(f"Sample count validation failed: {str(e)}")

    # Overall validity
    result['valid'] = (
        result['composition_sum_valid'] and
        result['integrity_valid'] and
        result['sample_count_valid']
    )

    return result


def main():
    """
    Command-line entry point for running validation on a CSV file.

    Usage:
        python -m src.utils.validators --input data/processed/hea_features.csv
        --composition-columns Fe Cr Ni ... --target Bulk_Modulus
    """
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Validate HEA dataset integrity.")
    parser.add_argument("--input", required=True, help="Path to input CSV file.")
    parser.add_argument(
        "--composition-columns",
        nargs="+",
        required=True,
        help="List of composition column names."
    )
    parser.add_argument("--target", help="Target column name (optional).")
    parser.add_argument("--min-samples", type=int, default=500, help="Minimum samples.")
    parser.add_argument("--group-column", help="Group column name (optional).")
    parser.add_argument("--tolerance", type=float, default=1e-6, help="Sum tolerance.")

    args = parser.parse_args()

    # Set up logging
    logging.basicConfig(level=logging.INFO)

    # Load data
    logger.info(f"Loading data from {args.input}...")
    try:
        df = pd.read_csv(args.input)
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        sys.exit(1)

    logger.info(f"Loaded {len(df)} rows, {len(df.columns)} columns.")

    # Run validations
    result = run_validations(
        df,
        args.composition_columns,
        target_column=args.target,
        min_samples=args.min_samples,
        group_column=args.group_column,
        tolerance=args.tolerance
    )

    # Report results
    logger.info("=" * 60)
    logger.info("VALIDATION REPORT")
    logger.info("=" * 60)
    logger.info(f"Overall Valid: {result['valid']}")
    logger.info(f"Composition Sum Valid: {result['composition_sum_valid']}")
    logger.info(f"Data Integrity Valid: {result['integrity_valid']}")
    logger.info(f"Sample Count Valid: {result['sample_count_valid']}")
    logger.info(f"Total Samples: {result['sample_info'].get('total_samples', 'N/A')}")

    if result['errors']:
        logger.warning("ERRORS:")
        for err in result['errors']:
            logger.warning(f"  - {err}")

    if result['warnings']:
        logger.warning("WARNINGS:")
        for warn in result['warnings']:
            logger.warning(f"  - {warn}")

    if result['valid']:
        logger.info("All validations passed.")
        sys.exit(0)
    else:
        logger.error("Validation failed. See errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
