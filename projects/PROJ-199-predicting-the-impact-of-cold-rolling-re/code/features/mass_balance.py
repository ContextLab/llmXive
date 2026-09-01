import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import numpy as np
import pandas as pd

from utils.logging import get_logger

logger = get_logger(__name__)

# Constants for mass balance validation
TOLERANCE = 0.01
COMPONENTS = ['brass', 'copper', 's', 'goss', 'random']


def calculate_random_fraction(
    brass: float,
    copper: float,
    s: float,
    goss: float,
    tolerance: float = TOLERANCE
) -> float:
    """
    Calculate the implied random fraction based on the sum of known components.
    If the sum of known components exceeds 1.0 + tolerance, this indicates an
    invalid state, but we return the residual (which will be negative).

    Args:
        brass: Brass volume fraction
        copper: Copper volume fraction
        s: S component volume fraction
        goss: Goss volume fraction
        tolerance: Tolerance for floating point errors

    Returns:
        The calculated random fraction (1.0 - sum(others)).
    """
    known_sum = brass + copper + s + goss
    return 1.0 - known_sum


def check_mass_balance(
    sample_id: str,
    brass: float,
    copper: float,
    s: float,
    goss: float,
    random_frac: float,
    tolerance: float = TOLERANCE
) -> Tuple[bool, str]:
    """
    Check if the sum of all components equals 1.0 within tolerance.

    Args:
        sample_id: Identifier for the sample
        brass: Brass volume fraction
        copper: Copper volume fraction
        s: S component volume fraction
        goss: Goss volume fraction
        random_frac: Random fraction
        tolerance: Acceptable deviation from 1.0

    Returns:
        Tuple of (is_valid, reason_string)
    """
    total = brass + copper + s + goss + random_frac
    deviation = abs(total - 1.0)

    if deviation > tolerance:
        return False, f"Mass balance violation: Sum={total:.4f}, Deviation={deviation:.4f} (Tolerance={tolerance})"
    return True, "Valid"


def validate_descriptor_mass_balance(
    descriptors: pd.DataFrame,
    tolerance: float = TOLERANCE
) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """
    Validate mass balance for every row in the descriptors dataframe.
    Flags invalid samples and returns a report of excluded samples.

    Args:
        descriptors: DataFrame containing texture descriptors (must include
                     'brass', 'copper', 's', 'goss', 'random' columns).
        tolerance: Acceptable deviation from 1.0.

    Returns:
        Tuple of (valid_descriptors_df, excluded_samples_report_list)
    """
    if not all(col in descriptors.columns for col in COMPONENTS):
        missing = [c for c in COMPONENTS if c not in descriptors.columns]
        raise ValueError(f"Missing required columns for mass balance check: {missing}")

    # Calculate total sum
    total_sum = (
        descriptors['brass'] +
        descriptors['copper'] +
        descriptors['s'] +
        descriptors['goss'] +
        descriptors['random']
    )

    # Identify invalid rows
    invalid_mask = (total_sum - 1.0).abs() > tolerance

    # Prepare exclusion report
    excluded_samples = []
    if invalid_mask.any():
        invalid_rows = descriptors[invalid_mask]
        for idx, row in invalid_rows.iterrows():
            sample_id = row.get('sample_id', f'index_{idx}')
            total_val = total_sum.loc[idx]
            deviation = abs(total_val - 1.0)
            excluded_samples.append({
                'sample_id': sample_id,
                'reason': f"Mass balance violation: Sum={total_val:.6f}, Deviation={deviation:.6f}",
                'brass': row['brass'],
                'copper': row['copper'],
                's': row['s'],
                'goss': row['goss'],
                'random': row['random'],
                'total': total_val
            })
            logger.warning(f"Excluding sample {sample_id} due to mass balance violation: {deviation:.6f}")

    # Filter valid data
    valid_descriptors = descriptors[~invalid_mask].reset_index(drop=True)

    return valid_descriptors, excluded_samples


def validate_dataset_mass_balance(
    descriptors_path: str,
    output_report_path: str,
    tolerance: float = TOLERANCE
) -> bool:
    """
    Main entry point to run mass balance validation on the processed descriptors.
    Generates a JSON report of excluded samples and saves valid data to a new CSV.

    Args:
        descriptors_path: Path to the input descriptors CSV (data/processed/descriptors.csv).
        output_report_path: Path to save the mass balance report JSON.
        tolerance: Acceptable deviation from 1.0.

    Returns:
        True if validation passed (at least some valid data exists), False if all data excluded.
    """
    logger.info(f"Loading descriptors from {descriptors_path}")
    try:
        df = pd.read_csv(descriptors_path)
    except FileNotFoundError:
        raise FileNotFoundError(f"Input file not found: {descriptors_path}")

    logger.info(f"Loaded {len(df)} samples. Validating mass balance (tolerance={tolerance})...")

    valid_df, excluded_report = validate_descriptor_mass_balance(df, tolerance)

    # Save the exclusion report
    report_data = {
        'validation_status': 'completed',
        'tolerance': tolerance,
        'total_samples': len(df),
        'valid_samples': len(valid_df),
        'excluded_samples_count': len(excluded_report),
        'excluded_samples': excluded_report
    }

    report_path = Path(output_report_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, 'w') as f:
        json.dump(report_data, f, indent=2)
    logger.info(f"Mass balance report saved to {output_report_path}")

    # If valid data exists, save the cleaned CSV for downstream tasks (T020a)
    if len(valid_df) > 0:
        cleaned_output_path = report_path.parent / 'descriptors_cleaned.csv'
        valid_df.to_csv(cleaned_output_path, index=False)
        logger.info(f"Cleaned descriptors saved to {cleaned_output_path}")
    else:
        logger.error("No valid samples remaining after mass balance check. Pipeline cannot proceed.")
        return False

    return True


def main():
    """
    CLI entry point for T019: Mass Balance Check.
    Reads data/processed/descriptors.csv, validates mass balance,
    and outputs data/processed/mass_balance_report.json.
    """
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parent.parent.parent
    input_path = project_root / "data" / "processed" / "descriptors.csv"
    output_report_path = project_root / "data" / "processed" / "mass_balance_report.json"

    # Check if input exists
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        logger.error("Ensure T018 (Descriptor Extraction) has completed successfully.")
        sys.exit(1)

    success = validate_dataset_mass_balance(
        descriptors_path=str(input_path),
        output_report_path=str(output_report_path)
    )

    if not success:
        logger.error("Mass balance validation failed: No valid data remaining.")
        sys.exit(1)

    logger.info("T019 Mass Balance Check completed successfully.")


if __name__ == "__main__":
    main()
