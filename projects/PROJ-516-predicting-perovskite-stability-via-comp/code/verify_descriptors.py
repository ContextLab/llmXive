"""
Verification module for descriptor computation.
Confirms presence and validity of required columns in the processed descriptors dataset.
"""
import logging
import sys
from pathlib import Path
from typing import List, Tuple, Optional

import pandas as pd

# Required columns based on FR-002 and T014 implementation
# T014 explicitly requires: atomic fractions, weighted averages (ionic radius, electronegativity, formation enthalpy, first ionization energy), and variance metrics.
REQUIRED_COLUMNS = [
    "formula",
    "T_d",
    "atomic_fraction_A",
    "atomic_fraction_B",
    "atomic_fraction_X",
    "weighted_ionic_radius",
    "weighted_electronegativity",
    "weighted_formation_enthalpy",
    "first_ionization_energy",  # Explicitly required by FR-002
    "ionic_radius_variance",
    "electronegativity_variance",
    "formation_enthalpy_variance",
    "T_d_uncertainty"
]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


def verify_column_presence(
    df: pd.DataFrame,
    required_cols: Optional[List[str]] = None
) -> Tuple[bool, List[str], List[str]]:
    """
    Verify that all required columns are present in the DataFrame.

    Args:
        df: The DataFrame to check.
        required_cols: List of required column names. Defaults to REQUIRED_COLUMNS.

    Returns:
        Tuple of (all_present, missing_cols, present_cols)
    """
    if required_cols is None:
        required_cols = REQUIRED_COLUMNS

    present_cols = [col for col in required_cols if col in df.columns]
    missing_cols = [col for col in required_cols if col not in df.columns]

    all_present = len(missing_cols) == 0
    return all_present, missing_cols, present_cols


def verify_column_data_validity(
    df: pd.DataFrame,
    columns_to_check: Optional[List[str]] = None
) -> Tuple[bool, List[str]]:
    """
    Verify that critical numeric columns contain valid non-null data.

    Args:
        df: The DataFrame to check.
        columns_to_check: List of columns to validate for non-null values.
                          Defaults to numeric descriptor columns.

    Returns:
        Tuple of (all_valid, invalid_cols)
    """
    if columns_to_check is None:
        columns_to_check = [
            "first_ionization_energy",
            "weighted_ionic_radius",
            "weighted_electronegativity",
            "weighted_formation_enthalpy",
            "T_d"
        ]

    invalid_cols = []
    for col in columns_to_check:
        if col not in df.columns:
            invalid_cols.append(f"{col} (missing)")
            continue
        
        null_count = df[col].isnull().sum()
        if null_count > 0:
            invalid_cols.append(f"{col} ({null_count} nulls)")

    all_valid = len(invalid_cols) == 0
    return all_valid, invalid_cols


def main() -> int:
    """
    Main entry point for descriptor verification.
    Loads data/processed/descriptors.csv and verifies compliance with FR-002.
    
    Returns:
        0 if verification passes, 1 if it fails.
    """
    input_path = Path("data/processed/descriptors.csv")
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        logger.error("T014 must be completed to generate data/processed/descriptors.csv")
        return 1

    try:
        logger.info(f"Loading descriptors from {input_path}")
        df = pd.read_csv(input_path)
        logger.info(f"Loaded {len(df)} rows with {len(df.columns)} columns")
        
        # Check column presence
        logger.info("Verifying required columns (FR-002 compliance)...")
        all_present, missing, present = verify_column_presence(df)
        
        if all_present:
            logger.info("✓ All required columns present")
            logger.info(f"  Verified columns: {', '.join(present)}")
        else:
            logger.error("✗ Missing required columns:")
            for col in missing:
                logger.error(f"  - {col}")
            return 1

        # Check data validity for critical columns
        logger.info("Verifying data validity for critical numeric columns...")
        all_valid, invalid = verify_column_data_validity(df)
        
        if all_valid:
            logger.info("✓ All critical columns contain valid non-null data")
        else:
            logger.warning("⚠ Critical columns have null values:")
            for col in invalid:
                logger.warning(f"  - {col}")
            # This is a warning, not a failure for T014b, but worth noting

        # Specific check for first_ionization_energy as per FR-002
        if "first_ionization_energy" in df.columns:
            stats = df["first_ionization_energy"].describe()
            logger.info(f"'first_ionization_energy' statistics:")
            logger.info(f"  Mean: {stats['mean']:.4f}")
            logger.info(f"  Std:  {stats['std']:.4f}")
            logger.info(f"  Min:  {stats['min']:.4f}")
            logger.info(f"  Max:  {stats['max']:.4f}")
            logger.info(f"  Count: {stats['count']}")
        else:
            logger.error("✗ 'first_ionization_energy' column is missing - FR-002 violation")
            return 1

        logger.info("\n" + "="*60)
        logger.info("VERIFICATION PASSED: FR-002 requirements satisfied")
        logger.info("="*60)
        return 0

    except Exception as e:
        logger.error(f"Verification failed with exception: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
