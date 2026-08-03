"""
Data integrity validators for HEA alloy analysis pipeline.

This module provides validation functions to ensure data quality:
- Composition sums equal 1.0 (within tolerance)
- Sample count thresholds for statistical validity
- General data integrity checks
"""

import logging
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional, Union
import pandas as pd
import numpy as np
from utils.seeds import get_seed

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Custom exception for data validation errors."""
    pass


def validate_composition_sum(
    df: pd.DataFrame,
    composition_cols: List[str],
    tolerance: float = 1e-6
) -> Tuple[bool, List[int], Dict[str, Any]]:
    """
    Validate that composition columns sum to 1.0 within tolerance.

    Args:
        df: DataFrame containing composition data
        composition_cols: List of column names representing element fractions
        tolerance: Maximum allowed deviation from 1.0

    Returns:
        Tuple of (is_valid, list of invalid row indices, summary stats)

    Raises:
        ValidationError: If more than 0.1% of rows fail validation
    """
    if not composition_cols:
        raise ValidationError("No composition columns provided for validation")

    # Calculate sums
    sums = df[composition_cols].sum(axis=1)
    deviations = np.abs(sums - 1.0)
    invalid_mask = deviations > tolerance

    invalid_indices = df[invalid_mask].index.tolist()
    invalid_count = len(invalid_indices)
    total_count = len(df)

    summary = {
        "total_samples": total_count,
        "invalid_samples": invalid_count,
        "invalid_percentage": (invalid_count / total_count * 100) if total_count > 0 else 0,
        "max_deviation": float(deviations.max()) if len(deviations) > 0 else 0,
        "mean_deviation": float(deviations.mean()) if len(deviations) > 0 else 0,
        "tolerance": tolerance
    }

    # Fail if more than 0.1% of rows are invalid
    failure_threshold = 0.001  # 0.1%
    if total_count > 0 and (invalid_count / total_count) > failure_threshold:
        raise ValidationError(
            f"Composition sum validation failed: {invalid_count}/{total_count} "
            f"rows ({summary['invalid_percentage']:.2f}%) exceed tolerance {tolerance}. "
            f"Max deviation: {summary['max_deviation']:.6f}"
        )

    is_valid = invalid_count == 0
    logger.info(
        f"Composition sum validation: {invalid_count}/{total_count} rows failed "
        f"(tolerance={tolerance}, max_deviation={summary['max_deviation']:.6f})"
    )

    return is_valid, invalid_indices, summary


def normalize_compositions(
    df: pd.DataFrame,
    composition_cols: List[str],
    inplace: bool = False
) -> pd.DataFrame:
    """
    Normalize composition columns to sum exactly to 1.0.

    This function adjusts composition fractions to ensure they sum to 1.0,
    which is required for downstream processing.

    Args:
        df: DataFrame with composition columns
        composition_cols: List of column names to normalize
        inplace: If True, modify df in place; otherwise return a copy

    Returns:
        Normalized DataFrame (or None if inplace=True)

    Raises:
        ValidationError: If any composition sum is zero or negative
    """
    if not inplace:
        df = df.copy()

    if not composition_cols:
        return df

    # Calculate current sums
    sums = df[composition_cols].sum(axis=1)

    # Check for zero or negative sums
    zero_mask = sums <= 0
    if zero_mask.any():
        zero_count = zero_mask.sum()
        raise ValidationError(
            f"Cannot normalize compositions: {zero_count} rows have zero or "
            f"negative composition sums. These samples must be filtered out."
        )

    # Normalize
    df[composition_cols] = df[composition_cols].div(sums, axis=0)

    # Verify normalization
    new_sums = df[composition_cols].sum(axis=1)
    max_deviation = np.abs(new_sums - 1.0).max()

    if max_deviation > 1e-10:
        logger.warning(
            f"Normalization residual: max deviation from 1.0 is {max_deviation:.2e}"
        )

    logger.info(f"Normalized {len(composition_cols)} composition columns")
    return df


def validate_sample_count(
    df: pd.DataFrame,
    min_samples: int = 500,
    column: Optional[str] = None
) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate that the dataset meets minimum sample count requirements.

    Args:
        df: DataFrame to validate
        min_samples: Minimum required number of samples
        column: Optional column name to count non-null values.
               If None, uses total row count.

    Returns:
        Tuple of (meets_threshold, summary dict)
    """
    if column is not None:
        if column not in df.columns:
            raise ValidationError(f"Column '{column}' not found in DataFrame")
        sample_count = df[column].notna().sum()
    else:
        sample_count = len(df)

    meets_threshold = sample_count >= min_samples
    summary = {
        "sample_count": int(sample_count),
        "min_required": min_samples,
        "meets_threshold": meets_threshold,
        "deficit": max(0, min_samples - sample_count)
    }

    logger.info(
        f"Sample count validation: {sample_count} samples (min: {min_samples}, "
        f"{'PASS' if meets_threshold else 'FAIL'})"
    )

    return meets_threshold, summary


def validate_data_integrity(
    df: pd.DataFrame,
    composition_cols: List[str],
    target_col: Optional[str] = None,
    min_samples: int = 500,
    composition_tolerance: float = 1e-6
) -> Dict[str, Any]:
    """
    Run comprehensive data integrity checks.

    Args:
        df: DataFrame to validate
        composition_cols: Columns representing element fractions
        target_col: Optional target variable column
        min_samples: Minimum sample count threshold
        composition_tolerance: Tolerance for composition sum validation

    Returns:
        Dictionary with validation results and summary statistics

    Raises:
        ValidationError: If any critical validation fails
    """
    results = {
        "valid": True,
        "checks": {},
        "warnings": [],
        "errors": []
    }

    # Check 1: Composition sum validation
    try:
        comp_valid, invalid_indices, comp_summary = validate_composition_sum(
            df, composition_cols, composition_tolerance
        )
        results["checks"]["composition_sum"] = {
            "passed": comp_valid,
            "summary": comp_summary
        }
        if not comp_valid:
            results["warnings"].append(
                f"{len(invalid_indices)} rows have composition sums outside tolerance"
            )
    except ValidationError as e:
        results["checks"]["composition_sum"] = {"passed": False, "error": str(e)}
        results["errors"].append(str(e))
        results["valid"] = False

    # Check 2: Sample count validation
    sample_valid, sample_summary = validate_sample_count(df, min_samples)
    results["checks"]["sample_count"] = sample_summary
    if not sample_valid:
        results["warnings"].append(
            f"Dataset has {sample_summary['sample_count']} samples, "
            f"below threshold of {min_samples}"
        )

    # Check 3: Target variable validation (if provided)
    if target_col:
        if target_col not in df.columns:
            results["errors"].append(f"Target column '{target_col}' not found")
            results["valid"] = False
        else:
            target_valid_count = df[target_col].notna().sum()
            target_null_count = df[target_col].isna().sum()
            results["checks"]["target_variable"] = {
                "valid_count": int(target_valid_count),
                "null_count": int(target_null_count),
                "null_percentage": float(target_null_count / len(df) * 100) if len(df) > 0 else 0
            }
            if target_null_count > 0:
                results["warnings"].append(
                    f"{target_null_count} rows have missing target values"
                )

    # Check 4: Negative values in composition (should not exist)
    if composition_cols:
        negative_mask = (df[composition_cols] < 0).any(axis=1)
        negative_count = negative_mask.sum()
        if negative_count > 0:
            results["errors"].append(
                f"Found {negative_count} rows with negative composition values"
            )
            results["valid"] = False
        else:
            results["checks"]["negative_compositions"] = {"passed": True}

    # Check 5: NaN values in composition columns
    if composition_cols:
        nan_count = df[composition_cols].isna().sum().sum()
        if nan_count > 0:
            results["errors"].append(
                f"Found {nan_count} NaN values in composition columns"
            )
            results["valid"] = False
        else:
            results["checks"]["composition_nans"] = {"passed": True}

    logger.info(
        f"Data integrity validation complete: "
        f"{'PASSED' if results['valid'] else 'FAILED'} "
        f"({len(results['warnings'])} warnings, {len(results['errors'])} errors)"
    )

    return results


def run_validations(
    df: pd.DataFrame,
    composition_cols: List[str],
    target_col: Optional[str] = None,
    min_samples: int = 500,
    raise_on_error: bool = True
) -> Dict[str, Any]:
    """
    Execute all validation checks and return comprehensive results.

    This is the main entry point for data validation in the pipeline.

    Args:
        df: DataFrame to validate
        composition_cols: Columns representing element fractions
        target_col: Optional target variable column
        min_samples: Minimum sample count threshold
        raise_on_error: If True, raise ValidationError on critical failures

    Returns:
        Dictionary with all validation results

    Raises:
        ValidationError: If raise_on_error=True and critical validation fails
    """
    results = validate_data_integrity(
        df, composition_cols, target_col, min_samples
    )

    if raise_on_error and not results["valid"]:
        error_msg = "\n".join(results["errors"])
        raise ValidationError(f"Data validation failed:\n{error_msg}")

    return results
