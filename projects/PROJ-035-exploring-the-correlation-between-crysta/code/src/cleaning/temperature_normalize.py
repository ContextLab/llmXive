"""
Temperature normalization module for thermal conductivity data.

Implements the Slack (1979) formula to normalize thermal conductivity
measurements to a reference temperature of 300K ± 10K.

Formula: k(T) = k_ref * (T_ref / T)^1.0

This module explicitly identifies and discards entries with 'unknown'
temperature before normalization, as required by FR-013.
"""

import sys
import logging
from pathlib import Path
from typing import Optional, List, Tuple
import pandas as pd
import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.seed_manager import setup_logger_module, init_seed
from src.utils.validation import setup_logger, handle_error

# Reference temperature for normalization (K)
REFERENCE_TEMP = 300.0
TEMP_TOLERANCE = 10.0  # ±10K window

def slack_normalization_factor(temp_measured: float, temp_ref: float = REFERENCE_TEMP) -> float:
    """
    Calculate the Slack (1979) normalization factor.

    k(T) = k_ref * (T_ref / T)^1.0
    Therefore: k_ref = k(T) * (T / T_ref)^1.0

    Args:
        temp_measured: The temperature at which the measurement was taken (K).
        temp_ref: The reference temperature (default 300K).

    Returns:
        The factor to multiply k(T) by to get k_ref.
    """
    if temp_measured <= 0:
        raise ValueError(f"Temperature must be positive, got {temp_measured}")
    return (temp_measured / temp_ref) ** 1.0

def is_within_reference_window(temp: float, tolerance: float = TEMP_TOLERANCE) -> bool:
    """
    Check if a temperature is within the acceptable reference window.

    Args:
        temp: Temperature to check (K).
        tolerance: Acceptable deviation from reference (default 10K).

    Returns:
        True if temp is within [REFERENCE_TEMP - tolerance, REFERENCE_TEMP + tolerance].
    """
    return (REFERENCE_TEMP - tolerance) <= temp <= (REFERENCE_TEMP + tolerance)

def normalize_thermal_conductivity(
    k_measured: float,
    temp_measured: float,
    temp_ref: float = REFERENCE_TEMP
) -> float:
    """
    Normalize a single thermal conductivity measurement to reference temperature.

    Args:
        k_measured: Measured thermal conductivity (W/m·K).
        temp_measured: Temperature at which k was measured (K).
        temp_ref: Reference temperature (default 300K).

    Returns:
        Normalized thermal conductivity at temp_ref (W/m·K).
    """
    factor = slack_normalization_factor(temp_measured, temp_ref)
    return k_measured * factor

def normalize_dataframe(
    df: pd.DataFrame,
    k_col: str = 'thermal_conductivity',
    temp_col: str = 'temperature'
) -> Tuple[pd.DataFrame, int, List[str]]:
    """
    Normalize thermal conductivity values in a DataFrame to 300K.

    This function:
    1. Identifies and discards rows with 'unknown' or missing temperature.
    2. Normalizes valid rows using the Slack formula.
    3. Returns the normalized DataFrame, count of discarded rows, and list of discarded IDs.

    Args:
        df: Input DataFrame with thermal conductivity and temperature columns.
        k_col: Name of the thermal conductivity column.
        temp_col: Name of the temperature column.

    Returns:
        Tuple of (normalized_df, discarded_count, discarded_ids).
    """
    if temp_col not in df.columns:
        raise ValueError(f"Temperature column '{temp_col}' not found in DataFrame")
    if k_col not in df.columns:
        raise ValueError(f"Thermal conductivity column '{k_col}' not found in DataFrame")

    # Create a copy to avoid modifying the original
    df_norm = df.copy()

    # Identify rows with 'unknown' or missing temperature
    # Handle both string 'unknown' and NaN/None values
    unknown_mask = df_norm[temp_col].isna() | (df_norm[temp_col].astype(str).str.lower() == 'unknown')

    discarded_count = unknown_mask.sum()
    discarded_ids = df_norm.loc[unknown_mask, 'structure_id'].tolist() if 'structure_id' in df_norm.columns else []

    # Filter out unknown temperatures
    df_valid = df_norm[~unknown_mask].copy()

    if len(df_valid) == 0:
        logging.warning("No valid temperature entries found after filtering unknown values.")
        return pd.DataFrame(), discarded_count, discarded_ids

    # Ensure temperature is numeric
    df_valid[temp_col] = pd.to_numeric(df_valid[temp_col], errors='coerce')

    # Drop rows where conversion failed (now NaN)
    valid_temp_mask = df_valid[temp_col].notna()
    if not valid_temp_mask.all():
        additional_discarded = df_valid[~valid_temp_mask]['structure_id'].tolist() if 'structure_id' in df_valid.columns else []
        discarded_ids.extend(additional_discarded)
        discarded_count += (~valid_temp_mask).sum()
        df_valid = df_valid[valid_temp_mask]

    if len(df_valid) == 0:
        logging.warning("No valid temperature entries after numeric conversion.")
        return pd.DataFrame(), discarded_count, discarded_ids

    # Apply normalization
    df_valid['thermal_conductivity_normalized'] = df_valid.apply(
        lambda row: normalize_thermal_conductivity(
            row[k_col],
            row[temp_col]
        ),
        axis=1
    )

    # Update the original thermal conductivity column with normalized values
    df_norm = df_norm.copy()
    df_norm.loc[df_valid.index, 'thermal_conductivity'] = df_valid['thermal_conductivity_normalized']

    # Add metadata about normalization
    df_norm['normalization_reference_temp'] = REFERENCE_TEMP
    df_norm['normalization_formula'] = 'Slack (1979): k(T) = k_ref * (T_ref / T)^1.0'

    return df_norm, discarded_count, discarded_ids

def apply_temperature_normalization(
    input_path: str,
    output_path: str,
    seed: int = 42,
    k_col: str = 'thermal_conductivity',
    temp_col: str = 'temperature'
) -> None:
    """
    Main function to load, normalize, and save thermal conductivity data.

    Args:
        input_path: Path to input CSV file.
        output_path: Path to save normalized CSV file.
        seed: Random seed for reproducibility (used for logging consistency).
        k_col: Name of thermal conductivity column.
        temp_col: Name of temperature column.
    """
    # Initialize seed for reproducibility
    init_seed(seed)

    # Setup logger
    logger = setup_logger('temperature_normalize', logging.INFO)
    logger.info(f"Starting temperature normalization for {input_path}")
    logger.info(f"Reference temperature: {REFERENCE_TEMP}K ± {TEMP_TOLERANCE}K")

    # Load data
    try:
        df = pd.read_csv(input_path)
        logger.info(f"Loaded {len(df)} records from {input_path}")
    except FileNotFoundError:
        handle_error(f"Input file not found: {input_path}", logger, "FileNotFoundError")
        sys.exit(1)
    except Exception as e:
        handle_error(f"Error loading input file: {e}", logger, "IOError")
        sys.exit(1)

    # Normalize
    df_normalized, discarded_count, discarded_ids = normalize_dataframe(
        df, k_col=k_col, temp_col=temp_col
    )

    logger.info(f"Discarded {discarded_count} entries with unknown/invalid temperature")
    if discarded_ids:
        logger.debug(f"Discarded structure IDs: {discarded_ids[:10]}...")  # Log first 10

    if len(df_normalized) == 0:
        handle_error("No valid data remaining after normalization", logger, "ValueError")
        sys.exit(1)

    # Save output
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        df_normalized.to_csv(output_path, index=False)
        logger.info(f"Saved {len(df_normalized)} normalized records to {output_path}")
    except Exception as e:
        handle_error(f"Error saving output file: {e}", logger, "IOError")
        sys.exit(1)

def main():
    """CLI entry point for temperature normalization."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Normalize thermal conductivity data to 300K using Slack (1979) formula."
    )
    parser.add_argument(
        '--input', '-i',
        type=str,
        required=True,
        help='Path to input CSV file containing thermal conductivity data.'
    )
    parser.add_argument(
        '--output', '-o',
        type=str,
        required=True,
        help='Path to save normalized CSV file.'
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help='Random seed for reproducibility (default: 42).'
    )
    parser.add_argument(
        '--k-col',
        type=str,
        default='thermal_conductivity',
        help='Name of thermal conductivity column (default: thermal_conductivity).'
    )
    parser.add_argument(
        '--temp-col',
        type=str,
        default='temperature',
        help='Name of temperature column (default: temperature).'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging.'
    )

    args = parser.parse_args()

    log_level = logging.DEBUG if args.verbose else logging.INFO
    logger = setup_logger('temperature_normalize', log_level)

    apply_temperature_normalization(
        input_path=args.input,
        output_path=args.output,
        seed=args.seed,
        k_col=args.k_col,
        temp_col=args.temp_col
    )

    logger.info("Temperature normalization completed successfully.")

if __name__ == '__main__':
    main()