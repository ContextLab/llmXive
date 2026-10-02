"""
Uncertainty Calculator Module

Computes total uncertainty for T_d values by combining instrument precision
and experimental error using the root-sum-square method.
"""

import logging
import math
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Default values as per specification
DEFAULT_PRECISION = 10.0  # ±10°C for missing instrument precision
DEFAULT_EXPERIMENTAL_ERROR = 0.0  # 0 for missing experimental error


def calculate_total_uncertainty(
    instrument_precision: Optional[float],
    experimental_error: Optional[float]
) -> float:
    """
    Calculate total uncertainty using the root-sum-square method.

    Formula: sigma = sqrt(precision^2 + experimental_error^2)

    Args:
        instrument_precision: Instrument precision in °C. If None, uses DEFAULT_PRECISION.
        experimental_error: Experimental error in °C. If None, uses DEFAULT_EXPERIMENTAL_ERROR.

    Returns:
        Total uncertainty (sigma) in °C.

    Raises:
        ValueError: If calculated uncertainty is negative (should not happen with sqrt).
    """
    # Apply defaults if values are missing
    precision = instrument_precision if instrument_precision is not None else DEFAULT_PRECISION
    error = experimental_error if experimental_error is not None else DEFAULT_EXPERIMENTAL_ERROR

    # Log warnings for missing components
    if instrument_precision is None:
        logger.warning(f"Missing instrument precision, using default: {DEFAULT_PRECISION}°C")
    if experimental_error is None:
        logger.warning(f"Missing experimental error, using default: {DEFAULT_EXPERIMENTAL_ERROR}°C")

    # Calculate combined uncertainty using root-sum-square
    try:
        sigma = math.sqrt(precision**2 + error**2)
    except (ValueError, TypeError) as e:
        logger.error(f"Error calculating uncertainty: precision={precision}, error={error}")
        raise e

    if sigma < 0:
        raise ValueError(f"Calculated uncertainty cannot be negative: {sigma}")

    return sigma


def compute_uncertainties_for_dataframe(
    df: pd.DataFrame,
    precision_column: str = 'precision_celsius',
    error_column: str = 'experimental_error',
    output_column: str = 'total_uncertainty'
) -> pd.DataFrame:
    """
    Compute total uncertainty for each row in a DataFrame.

    Args:
        df: Input DataFrame containing T_d measurements and uncertainty components.
        precision_column: Name of the column containing instrument precision.
        error_column: Name of the column containing experimental error.
        output_column: Name of the column to write the total uncertainty to.

    Returns:
        DataFrame with the new total_uncertainty column added.
    """
    logger.info(f"Computing uncertainties for {len(df)} rows")

    # Apply the calculation row-wise
    def calculate_row_uncertainty(row):
        precision = row.get(precision_column)
        error = row.get(error_column)
        return calculate_total_uncertainty(precision, error)

    # Compute and assign
    df[output_column] = df.apply(calculate_row_uncertainty, axis=1)

    # Verify non-negative values
    if (df[output_column] < 0).any():
        raise ValueError("Detected negative uncertainty values after calculation")

    logger.info(f"Successfully computed {output_column} column")
    logger.info(f"Uncertainty statistics: min={df[output_column].min():.2f}, max={df[output_column].max():.2f}, median={df[output_column].median():.2f}")

    return df


def main():
    """
    Main entry point for the uncertainty calculator script.

    Reads data from data/raw/perovskites_merged.csv, computes total uncertainty,
    and writes the result to data/processed/descriptors_uncertainty.csv.
    """
    # Define paths
    project_root = Path(__file__).resolve().parent.parent.parent
    input_path = project_root / "data" / "raw" / "perovskites_merged.csv"
    output_path = project_root / "data" / "processed" / "descriptors_uncertainty.csv"

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Reading input data from: {input_path}")

    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        logger.error("Please ensure T012e (merge logic) has completed successfully.")
        sys.exit(1)

    try:
        # Load the merged dataset
        df = pd.read_csv(input_path)
        logger.info(f"Loaded {len(df)} rows from {input_path}")

        # Check for required columns
        required_cols = ['formula', 'T_d']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            logger.error(f"Missing required columns in input: {missing_cols}")
            sys.exit(1)

        # Identify uncertainty columns (they might be named differently or missing)
        # We look for 'precision_celsius' (from T042/T047c) and 'experimental_error'
        # If 'precision_celsius' is missing, the function will use the default
        # If 'experimental_error' is missing, the function will use the default

        # Check if columns exist, if not, create them with NaN to trigger defaults
        if 'precision_celsius' not in df.columns:
            logger.warning(f"Column 'precision_celsius' not found. Using default precision for all rows.")
            df['precision_celsius'] = None

        if 'experimental_error' not in df.columns:
            logger.warning(f"Column 'experimental_error' not found. Using default error (0) for all rows.")
            df['experimental_error'] = None

        # Compute uncertainties
        df = compute_uncertainties_for_dataframe(
            df,
            precision_column='precision_celsius',
            error_column='experimental_error',
            output_column='total_uncertainty'
        )

        # Ensure output path exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write the result
        df.to_csv(output_path, index=False)
        logger.info(f"Successfully wrote {len(df)} rows to {output_path}")
        logger.info(f"Output columns: {list(df.columns)}")

    except Exception as e:
        logger.error(f"Error processing data: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
