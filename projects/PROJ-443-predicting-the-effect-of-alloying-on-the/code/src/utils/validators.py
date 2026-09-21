"""
Data validation utilities for High-Entropy Alloy (HEA) datasets.

This module provides functions to validate data integrity, specifically:
- Composition normalization (sum = 1.0)
- Sample count thresholds for statistical power
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
    row: Dict[str, float],
    composition_cols: List[str],
    tolerance: float = 1e-6
) -> bool:
    """
    Validate that the sum of composition fractions equals 1.0 within tolerance.

    Args:
        row: A dictionary representing a single data row.
        composition_cols: List of column names representing elemental fractions.
        tolerance: Maximum allowed deviation from 1.0.

    Returns:
        True if valid, False otherwise.

    Raises:
        ValidationError: If the sum is outside the tolerance range.
    """
    if not composition_cols:
        raise ValidationError("No composition columns provided for validation.")

    total = sum(row.get(col, 0.0) for col in composition_cols)
    
    if abs(total - 1.0) > tolerance:
        raise ValidationError(
            f"Composition sum {total:.6f} deviates from 1.0 by {abs(total - 1.0):.6f} "
            f"(tolerance: {tolerance})."
        )
    return True

def normalize_compositions(
    df: pd.DataFrame,
    composition_cols: List[str],
    tolerance: float = 1e-6,
    inplace: bool = False
) -> pd.DataFrame:
    """
    Normalize composition columns so they sum to 1.0.

    Args:
        df: Input DataFrame.
        composition_cols: List of column names representing elemental fractions.
        tolerance: Threshold below which normalization is skipped (already normalized).
        inplace: If True, modify df in place; otherwise return a copy.

    Returns:
        Normalized DataFrame.

    Raises:
        ValidationError: If any composition value is negative or NaN before normalization.
    """
    if not inplace:
        df = df.copy()

    if composition_cols:
        # Check for invalid values before normalization
        if df[composition_cols].isnull().any().any():
            raise ValidationError("Composition columns contain NaN values.")
        if (df[composition_cols] < 0).any().any():
            raise ValidationError("Composition columns contain negative values.")

        # Calculate current sums
        sums = df[composition_cols].sum(axis=1)
        
        # Normalize only rows that are not already within tolerance
        needs_normalization = (abs(sums - 1.0) > tolerance).values
        
        if needs_normalization.any():
            logger.debug(
                f"Normalizing {needs_normalization.sum()} rows with composition sums "
                f"outside tolerance."
            )
            # Avoid division by zero
            safe_sums = sums.replace(0.0, 1.0)
            df.loc[needs_normalization, composition_cols] = (
                df.loc[needs_normalization, composition_cols].values 
                / safe_sums[needs_normalization].values[:, np.newaxis]
            )
    
    return df

def validate_sample_count(
    sample_count: int,
    min_threshold: int = 500,
    warning_threshold: int = 1000
) -> Dict[str, Any]:
    """
    Validate sample count against statistical power thresholds.

    Args:
        sample_count: Total number of samples.
        min_threshold: Absolute minimum samples required (study fails below this).
        warning_threshold: Samples below this trigger a reduced power warning.

    Returns:
        Dictionary with validation status and power analysis details.
    """
    result = {
        "count": sample_count,
        "is_valid": sample_count >= min_threshold,
        "is_reduced_power": sample_count < warning_threshold,
        "message": ""
    }

    if sample_count < min_threshold:
        result["message"] = (
            f"CRITICAL: Sample count ({sample_count}) is below minimum threshold ({min_threshold}). "
            "Study cannot proceed with standard statistical power."
        )
    elif sample_count < warning_threshold:
        deficit = warning_threshold - sample_count
        # Simple linear approximation of power deficit (placeholder for real power calc)
        # In a real scenario, this would use power analysis formulas based on effect size
        power_deficit = (deficit / warning_threshold) * 100
        result["message"] = (
            f"WARNING: Sample count ({sample_count}) is below recommended threshold ({warning_threshold}). "
            f"Estimated power deficit: {power_deficit:.1f}%. Proceeding with Reduced Power Analysis."
        )
    else:
        result["message"] = "Sample count sufficient for standard analysis."

    return result

def validate_data_integrity(
    df: pd.DataFrame,
    composition_cols: List[str],
    target_col: Optional[str] = None,
    min_samples: int = 500
) -> Tuple[bool, List[str]]:
    """
    Perform comprehensive data integrity checks.

    Args:
        df: Input DataFrame.
        composition_cols: List of elemental composition columns.
        target_col: Optional name of the target variable column.
        min_samples: Minimum required sample count.

    Returns:
        Tuple of (is_valid, list_of_errors).
    """
    errors = []

    # 1. Check sample count
    if len(df) < min_samples:
        errors.append(
            f"Sample count ({len(df)}) is below minimum threshold ({min_samples})."
        )

    # 2. Check for NaN in composition columns
    if composition_cols:
        nan_counts = df[composition_cols].isnull().sum()
        if nan_counts.any():
            cols_with_nan = nan_counts[nan_counts > 0].index.tolist()
            errors.append(
                f"Composition columns contain NaN values: {cols_with_nan}."
            )

    # 3. Check for negative composition values
    if composition_cols:
        neg_counts = (df[composition_cols] < 0).sum()
        if neg_counts.any():
            cols_with_neg = neg_counts[neg_counts > 0].index.tolist()
            errors.append(
                f"Composition columns contain negative values: {cols_with_neg}."
            )

    # 4. Check composition sum = 1.0
    if composition_cols:
        sums = df[composition_cols].sum(axis=1)
        invalid_sums = sums[(abs(sums - 1.0) > 1e-6)]
        if len(invalid_sums) > 0:
            errors.append(
                f"{len(invalid_sums)} rows have composition sums deviating from 1.0 "
                f"(max deviation: {invalid_sums.abs().max() - 1:.6f})."
            )

    # 5. Check target column if provided
    if target_col:
        if target_col not in df.columns:
            errors.append(f"Target column '{target_col}' not found in DataFrame.")
        else:
            if df[target_col].isnull().any():
                nan_count = df[target_col].isnull().sum()
                errors.append(
                    f"Target column '{target_col}' contains {nan_count} NaN values."
                )
            if (df[target_col] == 0).any() and target_col != "Bulk_Modulus_Residual":
                # Zero target might be valid for residuals but suspicious for absolute values
                logger.warning(
                    f"Target column '{target_col}' contains zero values. "
                    "Verify if this is expected."
                )

    is_valid = len(errors) == 0
    return is_valid, errors

def run_validations(
    df: pd.DataFrame,
    composition_cols: List[str],
    target_col: Optional[str] = None,
    min_samples: int = 500,
    raise_on_error: bool = True
) -> Dict[str, Any]:
    """
    Run all validation checks and return a comprehensive report.

    Args:
        df: Input DataFrame.
        composition_cols: List of elemental composition columns.
        target_col: Optional name of the target variable column.
        min_samples: Minimum required sample count.
        raise_on_error: If True, raise ValidationError on first critical error.

    Returns:
        Dictionary containing validation results and statistics.
    """
    report = {
        "total_samples": len(df),
        "is_valid": True,
        "errors": [],
        "warnings": [],
        "sample_count_status": {}
    }

    # Run sample count validation
    report["sample_count_status"] = validate_sample_count(
        len(df), min_threshold=min_samples, warning_threshold=min_samples * 2
    )

    if not report["sample_count_status"]["is_valid"]:
        report["is_valid"] = False
        report["errors"].append(
            report["sample_count_status"]["message"]
        )
        if raise_on_error:
            raise ValidationError(report["errors"][-1])

    # Run data integrity checks
    is_integrity_valid, integrity_errors = validate_data_integrity(
        df, composition_cols, target_col, min_samples
    )

    if not is_integrity_valid:
        report["is_valid"] = False
        report["errors"].extend(integrity_errors)
        if raise_on_error:
            raise ValidationError("; ".join(integrity_errors))

    # Log warnings if reduced power
    if report["sample_count_status"]["is_reduced_power"]:
        report["warnings"].append(
            report["sample_count_status"]["message"]
        )

    logger.info(
        f"Validation complete: {len(df)} samples. "
        f"Valid: {report['is_valid']}, Errors: {len(report['errors'])}"
    )

    return report

def main():
    """
    Command-line entry point for running validators on a CSV file.
    Usage: python -m src.utils.validators --input path/to/data.csv --output results/validation_report.json
    """
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Validate HEA dataset integrity.")
    parser.add_argument("--input", type=str, required=True, help="Input CSV file path.")
    parser.add_argument("--output", type=str, required=True, help="Output JSON report path.")
    parser.add_argument("--min-samples", type=int, default=500, help="Minimum sample count.")
    parser.add_argument("--composition-prefix", type=str, default="composition_", help="Prefix for composition columns.")

    args = parser.parse_args()

    # Load data
    if not Path(args.input).exists():
        print(f"Error: Input file '{args.input}' not found.")
        return 1

    df = pd.read_csv(args.input)
    
    # Identify composition columns
    composition_cols = [col for col in df.columns if col.startswith(args.composition_prefix)]
    
    if not composition_cols:
        print(f"Error: No composition columns found with prefix '{args.composition_prefix}'.")
        return 1

    # Run validations
    try:
        report = run_validations(
            df, 
            composition_cols, 
            target_col="Bulk_Modulus_Residual",
            min_samples=args.min_samples,
            raise_on_error=False
        )
        
        # Write report
        with open(args.output, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"Validation report written to {args.output}")
        return 0 if report["is_valid"] else 1

    except ValidationError as e:
        print(f"Validation Error: {e}")
        return 1
    except Exception as e:
        print(f"Unexpected Error: {e}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
