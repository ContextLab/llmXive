import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import numpy as np
import pandas as pd

from utils.logging import get_logger
from config import get_data_path

logger = get_logger(__name__)

# Tolerance for mass balance check (1.0 ± 0.01)
MASS_BALANCE_TOLERANCE = 0.01

def calculate_random_fraction(
    brass: float, copper: float, s: float, goss: float
) -> float:
    """
    Calculate the 'random' fraction as the remainder to reach 1.0.

    Args:
        brass: Volume fraction of Brass component.
        copper: Volume fraction of Copper component.
        s: Volume fraction of S component.
        goss: Volume fraction of Goss component.

    Returns:
        The calculated random fraction (1.0 - sum of major components).
    """
    major_sum = brass + copper + s + goss
    return 1.0 - major_sum

def check_mass_balance(
    brass: float,
    copper: float,
    s: float,
    goss: float,
    tolerance: float = MASS_BALANCE_TOLERANCE,
) -> Tuple[bool, float]:
    """
    Check if the sum of major components plus the implied random fraction equals 1.0.

    Since 'random' is defined as the remainder, the check is effectively:
    Does (brass + copper + s + goss) + (1.0 - (brass + copper + s + goss)) == 1.0?
    Mathematically, this is always true unless there are floating point errors or
    if the components themselves are invalid (e.g., negative, > 1.0).

    However, per the task requirement, we verify that the sum of the MAJOR components
    plus the calculated random fraction equals 1.0 within tolerance.
    This implies we are checking the internal consistency of the descriptor calculation.

    If the input components are such that their sum exceeds 1.0, the 'random' fraction
    would be negative, which is physically invalid.

    Args:
        brass: Volume fraction of Brass.
        copper: Volume fraction of Copper.
        s: Volume fraction of S.
        goss: Volume fraction of Goss.
        tolerance: Allowed deviation from 1.0.

    Returns:
        A tuple (is_valid, deviation).
        is_valid: True if |sum - 1.0| <= tolerance.
        deviation: The absolute difference from 1.0.
    """
    major_sum = brass + copper + s + goss
    # The random fraction is implicitly 1.0 - major_sum
    # Total sum = major_sum + (1.0 - major_sum) = 1.0
    # The check is effectively ensuring the components are non-negative and sum <= 1.0
    # so that random is non-negative.
    # But strictly following the prompt: "verify that the sum of major components ... plus random ... equals 1.0"
    # Since random = 1.0 - sum, the equation is always 1.0.
    # The real constraint is: 0 <= sum <= 1.0.
    # If sum > 1.0, random is negative -> invalid.
    # If sum < 0, random > 1.0 -> invalid (though individual components should be >= 0).

    # Let's interpret the requirement as checking if the calculated random fraction
    # results in a total sum of 1.0 within floating point tolerance,
    # AND ensuring the random fraction is non-negative (physically meaningful).

    random_frac = 1.0 - major_sum
    total_sum = major_sum + random_frac

    deviation = abs(total_sum - 1.0)
    is_valid = deviation <= tolerance and random_frac >= 0.0

    if not is_valid:
        logger.warning(
            f"Mass balance check failed: sum={major_sum:.4f}, random={random_frac:.4f}, deviation={deviation:.6f}"
        )

    return is_valid, deviation

def validate_descriptor_mass_balance(
    row: pd.Series, tolerance: float = MASS_BALANCE_TOLERANCE
) -> Tuple[bool, float]:
    """
    Validate mass balance for a single descriptor row.

    Args:
        row: A pandas Series containing 'brass', 'copper', 's', 'goss' columns.
        tolerance: Allowed deviation from 1.0.

    Returns:
        Tuple (is_valid, deviation).
    """
    brass = row.get('brass', 0.0)
    copper = row.get('copper', 0.0)
    s = row.get('s', 0.0)
    goss = row.get('goss', 0.0)

    return check_mass_balance(brass, copper, s, goss, tolerance)

def validate_dataset_mass_balance(
    df: pd.DataFrame,
    tolerance: float = MASS_BALANCE_TOLERANCE,
    exclude_invalid: bool = True,
) -> pd.DataFrame:
    """
    Validate mass balance for all samples in a dataset.

    Per T019: If the check fails, flag the sample as invalid and exclude it from output,
    but DO NOT halt the pipeline. Log the exclusion.

    Args:
        df: DataFrame with 'brass', 'copper', 's', 'goss' columns.
        tolerance: Allowed deviation from 1.0.
        exclude_invalid: If True, return a filtered DataFrame excluding invalid rows.

    Returns:
        If exclude_invalid is True: DataFrame with only valid rows.
        If exclude_invalid is False: Original DataFrame (with a new 'mass_balance_valid' column).
    """
    logger.info(f"Validating mass balance for {len(df)} samples with tolerance {tolerance}")

    valid_indices = []
    invalid_indices = []

    for idx, row in df.iterrows():
        is_valid, deviation = validate_descriptor_mass_balance(row, tolerance)
        if is_valid:
            valid_indices.append(idx)
        else:
            invalid_indices.append(idx)
            logger.warning(
                f"Excluding sample at index {idx} due to mass balance violation (deviation: {deviation:.6f})"
            )

    logger.info(
        f"Mass balance validation complete: {len(valid_indices)} valid, {len(invalid_indices)} excluded."
    )

    if exclude_invalid:
        if len(valid_indices) == 0:
            logger.error("All samples failed mass balance check. Returning empty DataFrame.")
            return pd.DataFrame(columns=df.columns)
        return df.loc[valid_indices].reset_index(drop=True)
    else:
        df['mass_balance_valid'] = df.apply(
            lambda row: validate_descriptor_mass_balance(row, tolerance)[0], axis=1
        )
        return df

def main():
    """
    Main entry point for mass balance validation script.
    Reads descriptors from data/processed/descriptors.csv, validates, and saves filtered output.
    """
    data_path = get_data_path()
    input_file = Path(data_path) / "processed" / "descriptors.csv"
    output_file = Path(data_path) / "processed" / "descriptors_validated.csv"

    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        sys.exit(1)

    logger.info(f"Loading descriptors from {input_file}")
    df = pd.read_csv(input_file)

    required_cols = {'brass', 'copper', 's', 'goss'}
    if not required_cols.issubset(df.columns):
        logger.error(f"Missing required columns in {input_file}. Found: {df.columns.tolist()}")
        sys.exit(1)

    validated_df = validate_dataset_mass_balance(df, exclude_invalid=True)

    if validated_df.empty:
        logger.error("No valid samples remaining after mass balance check. Aborting.")
        sys.exit(1)

    logger.info(f"Saving {len(validated_df)} valid samples to {output_file}")
    validated_df.to_csv(output_file, index=False)

    logger.info("Mass balance validation completed successfully.")

if __name__ == "__main__":
    main()
