"""
Uncertainty Calculator Module for Perovskite Stability Analysis.

This module computes the total uncertainty for thermal decomposition temperature (T_d)
by combining instrument precision and reported experimental error using the root-sum-square method.
"""

import logging
import math
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import pandas as pd

# Import from existing API surface
from .instrument_registry import get_precision
from .uncertainty_parser import parse_temperature_precision

# Configure logging
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Default values as per specification
DEFAULT_PRECISION = 10.0  # ±10°C default for missing instrument precision
DEFAULT_EXPERIMENTAL_ERROR = 0.0  # 0 for missing experimental error

def calculate_total_uncertainty(
    instrument_precision: float,
    experimental_error: float
) -> float:
    """
    Calculate the total uncertainty using the root-sum-square method.

    Formula: sigma = sqrt(precision^2 + experimental_error^2)

    Args:
        instrument_precision: The precision of the TGA instrument (±°C).
        experimental_error: Any reported experimental error (±°C).

    Returns:
        The combined standard uncertainty (sigma).
    """
    if instrument_precision < 0 or experimental_error < 0:
        raise ValueError("Uncertainty components cannot be negative.")

    total_uncertainty = math.sqrt(
        instrument_precision ** 2 + experimental_error ** 2
    )
    return total_uncertainty


def compute_uncertainties_for_dataframe(
    df: pd.DataFrame,
    precision_column: str = 'precision_celsius',
    experimental_error_column: str = 'experimental_error',
    output_column: str = 'total_uncertainty'
) -> pd.DataFrame:
    """
    Compute total uncertainty for each row in a DataFrame.

    This function iterates through the DataFrame, extracting instrument precision
    and experimental error, handling missing values with documented defaults,
    and calculating the combined uncertainty.

    Args:
        df: Input DataFrame containing perovskite data with instrumentation metadata.
        precision_column: Name of the column containing instrument precision values.
        experimental_error_column: Name of the column containing experimental error values.
        output_column: Name of the column to write the total uncertainty to.

    Returns:
        The DataFrame with a new 'total_uncertainty' column added.
    """
    logger.info(f"Computing uncertainties for {len(df)} records...")

    uncertainties = []
    precision_used = []
    error_used = []

    for idx, row in df.iterrows():
        formula = row.get('formula', 'Unknown')
        source = row.get('source', 'Unknown')

        # Extract instrument precision
        if precision_column in row and pd.notna(row[precision_column]):
            precision = float(row[precision_column])
        else:
            precision = DEFAULT_PRECISION
            logger.warning(
                f"WARNING: Missing precision for {formula} (source: {source}), "
                f"defaulting to {DEFAULT_PRECISION}°C"
            )

        # Extract experimental error
        if experimental_error_column in row and pd.notna(row[experimental_error_column]):
            error = float(row[experimental_error_column])
        else:
            error = DEFAULT_EXPERIMENTAL_ERROR
            logger.debug(
                f"INFO: Missing experimental error for {formula} (source: {source}), "
                f"using default {DEFAULT_EXPERIMENTAL_ERROR}"
            )

        # Calculate total uncertainty
        try:
            total_unc = calculate_total_uncertainty(precision, error)
        except ValueError as e:
            logger.error(f"Error calculating uncertainty for {formula}: {e}")
            total_unc = float('nan')

        uncertainties.append(total_unc)
        precision_used.append(precision)
        error_used.append(error)

    df = df.copy()
    df[output_column] = uncertainties
    df['_precision_used'] = precision_used
    df['_experimental_error_used'] = error_used

    logger.info(f"Uncertainty calculation complete. "
                f"Min: {min([u for u in uncertainties if not math.isnan(u)]):.4f}, "
                f"Max: {max([u for u in uncertainties if not math.isnan(u)]):.4f}, "
                f"Mean: {sum([u for u in uncertainties if not math.isnan(u)])/len([u for u in uncertainties if not math.isnan(u)]):.4f}")

    return df


def main():
    """
    Main entry point for the uncertainty calculator.

    Reads the merged perovskite dataset, computes total uncertainty,
    and writes the result to the processed directory.
    """
    # Define paths relative to project root
    project_root = Path(__file__).parent.parent.parent
    input_path = project_root / 'data' / 'raw' / 'perovskites_merged.csv'
    output_path = project_root / 'data' / 'processed' / 'descriptors_uncertainty.csv'

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Check if input file exists
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        logger.error("Please ensure T012e (merge_datasets) has been completed successfully.")
        sys.exit(1)

    logger.info(f"Loading data from {input_path}...")
    try:
        df = pd.read_csv(input_path)
    except Exception as e:
        logger.error(f"Failed to read input CSV: {e}")
        sys.exit(1)

    # Verify required columns
    required_cols = ['formula', 'T_d']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        logger.error(f"Missing required columns in input: {missing_cols}")
        sys.exit(1)

    # Determine precision column name (could be 'precision_celsius' or similar)
    # Check for common variations
    precision_col = None
    possible_precision_cols = ['precision_celsius', 'temperature_precision', 'instrument_precision', 'precision']
    for col in possible_precision_cols:
        if col in df.columns:
            precision_col = col
            break

    if precision_col is None:
        logger.warning("No precision column found in input data. Using default ±10°C for all entries.")
        precision_col = 'precision_celsius' # Will be created with defaults if needed
        df[precision_col] = None

    # Determine experimental error column name
    error_col = None
    possible_error_cols = ['experimental_error', 'error', 'uncertainty', 'T_d_error']
    for col in possible_error_cols:
        if col in df.columns:
            error_col = col
            break

    if error_col is None:
        logger.warning("No experimental error column found in input data. Using default 0.0 for all entries.")
        error_col = 'experimental_error' # Will be created with defaults if needed
        df[error_col] = None

    # Compute uncertainties
    df_processed = compute_uncertainties_for_dataframe(
        df,
        precision_column=precision_col,
        experimental_error_column=error_col,
        output_column='total_uncertainty'
    )

    # Clean up temporary columns before saving if desired, but keeping them for audit
    # The task requires writing the new column to the output file.
    # We will keep the audit columns for now as they are useful for validation.

    logger.info(f"Writing output to {output_path}...")
    try:
        df_processed.to_csv(output_path, index=False)
    except Exception as e:
        logger.error(f"Failed to write output CSV: {e}")
        sys.exit(1)

    logger.info(f"Successfully wrote {len(df_processed)} records to {output_path}")
    logger.info(f"Output columns: {list(df_processed.columns)}")


if __name__ == '__main__':
    main()