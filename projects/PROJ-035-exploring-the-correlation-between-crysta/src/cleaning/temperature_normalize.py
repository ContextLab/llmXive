"""
Temperature normalization module for thermal conductivity data.

Implements the Slack (1979) formula to normalize thermal conductivity
measurements to a reference temperature (typically 300K).

Formula: k(T) = k_ref * (T_ref / T)^1.0

This module is callable as a utility function by T016 (clean_merge.py)
and accepts --seed argument for deterministic operations.
"""
import sys
import logging
import argparse
from pathlib import Path
from typing import Optional, List, Tuple
import pandas as pd
import numpy as np

# Import seed management utility
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.utils.seed_manager import init_seed, get_seed, add_seed_argument
from src.utils.validation import setup_logger, validate_dataframe_columns

# Constants
DEFAULT_REFERENCE_TEMP = 300.0  # Kelvin
SLACK_EXPONENT = 1.0

def setup_logger_module(name: str = __name__) -> logging.Logger:
    """
    Setup a logger for this module.

    Args:
        name: Logger name (default: __name__)

    Returns:
        Configured logger instance
    """
    return setup_logger(name, level=logging.INFO)

def slack_normalization_factor(
    current_temp: float,
    reference_temp: float = DEFAULT_REFERENCE_TEMP,
    exponent: float = SLACK_EXPONENT
) -> float:
    """
    Calculate the Slack (1979) normalization factor.

    Formula: factor = (T_ref / T)^exponent

    Args:
        current_temp: Current measurement temperature in Kelvin
        reference_temp: Reference temperature in Kelvin (default: 300K)
        exponent: Exponent for the power law (default: 1.0 per Slack 1979)

    Returns:
        Normalization factor to multiply k(T) by

    Raises:
        ValueError: If current_temp <= 0 or reference_temp <= 0
    """
    if current_temp <= 0:
        raise ValueError(f"Current temperature must be positive, got {current_temp}")
    if reference_temp <= 0:
        raise ValueError(f"Reference temperature must be positive, got {reference_temp}")

    return (reference_temp / current_temp) ** exponent

def is_within_reference_window(
    temperature: float,
    reference_temp: float = DEFAULT_REFERENCE_TEMP,
    tolerance: float = 10.0
) -> bool:
    """
    Check if a temperature is within the reference window.

    Args:
        temperature: Temperature to check in Kelvin
        reference_temp: Reference temperature in Kelvin
        tolerance: Tolerance in Kelvin (default: ±10K)

    Returns:
        True if temperature is within [reference_temp - tolerance, reference_temp + tolerance]
    """
    return abs(temperature - reference_temp) <= tolerance

def normalize_thermal_conductivity(
    k_value: float,
    current_temp: float,
    reference_temp: float = DEFAULT_REFERENCE_TEMP,
    exponent: float = SLACK_EXPONENT
) -> float:
    """
    Normalize a single thermal conductivity value to reference temperature.

    Formula: k(T_ref) = k(T) * (T_ref / T)^exponent

    Args:
        k_value: Thermal conductivity at current temperature (W/m·K)
        current_temp: Current measurement temperature in Kelvin
        reference_temp: Reference temperature in Kelvin
        exponent: Exponent for the power law (default: 1.0)

    Returns:
        Normalized thermal conductivity at reference temperature

    Raises:
        ValueError: If current_temp is missing, 'unknown', or <= 0
    """
    if pd.isna(current_temp) or current_temp == 'unknown' or current_temp == 'Unknown':
        raise ValueError("Cannot normalize: temperature is missing or 'unknown'")

    if not isinstance(current_temp, (int, float)) or current_temp <= 0:
        raise ValueError(f"Invalid temperature value: {current_temp}")

    factor = slack_normalization_factor(current_temp, reference_temp, exponent)
    return k_value * factor

def normalize_dataframe(
    df: pd.DataFrame,
    k_column: str = 'thermal_conductivity',
    temp_column: str = 'temperature',
    reference_temp: float = DEFAULT_REFERENCE_TEMP,
    exclude_unknown: bool = True,
    logger: Optional[logging.Logger] = None
) -> Tuple[pd.DataFrame, int]:
    """
    Normalize thermal conductivity values in a DataFrame to reference temperature.

    This function applies the Slack (1979) formula to all rows with valid
    temperature data. Rows with missing or 'unknown' temperature are either
    excluded or marked, depending on the exclude_unknown parameter.

    Args:
        df: Input DataFrame with thermal conductivity and temperature columns
        k_column: Name of the thermal conductivity column (default: 'thermal_conductivity')
        temp_column: Name of the temperature column (default: 'temperature')
        reference_temp: Reference temperature in Kelvin (default: 300K)
        exclude_unknown: If True, remove rows with missing/unknown temperature
        logger: Optional logger instance for progress messages

    Returns:
        Tuple of (normalized DataFrame, count of excluded rows)

    Raises:
        ValueError: If required columns are missing
        TypeError: If input is not a DataFrame
    """
    if logger is None:
        logger = setup_logger_module()

    # Validate input
    if not isinstance(df, pd.DataFrame):
        raise TypeError(f"Expected DataFrame, got {type(df)}")

    required_cols = [k_column, temp_column]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    # Create a copy to avoid modifying the original
    result_df = df.copy()

    # Identify rows with unknown/missing temperature
    unknown_mask = (
        result_df[temp_column].isna() |
        (result_df[temp_column].astype(str).str.lower() == 'unknown') |
        (result_df[temp_column] <= 0)
    )
    excluded_count = unknown_mask.sum()

    if exclude_unknown and excluded_count > 0:
        logger.warning(f"Excluding {excluded_count} rows with missing/unknown temperature")
        result_df = result_df[~unknown_mask]

    # Normalize thermal conductivity for remaining rows
    def normalize_row(row):
        try:
            return normalize_thermal_conductivity(
                row[k_column],
                row[temp_column],
                reference_temp,
                SLACK_EXPONENT
            )
        except ValueError as e:
            logger.error(f"Normalization error for row: {e}")
            return np.nan

    result_df[f'{k_column}_normalized'] = result_df.apply(normalize_row, axis=1)

    # Log summary
    if excluded_count == 0:
        logger.info(f"Normalized {len(result_df)} rows to {reference_temp}K")
    else:
        logger.info(f"Normalized {len(result_df)} rows (excluded {excluded_count} unknown temps)")

    return result_df, excluded_count

def apply_temperature_normalization(
    input_path: str,
    output_path: str,
    reference_temp: float = DEFAULT_REFERENCE_TEMP,
    exclude_unknown: bool = True,
    seed: Optional[int] = None,
    logger: Optional[logging.Logger] = None
) -> dict:
    """
    Load data from file, normalize thermal conductivity, and save results.

    Args:
        input_path: Path to input CSV file
        output_path: Path to output CSV file
        reference_temp: Reference temperature in Kelvin (default: 300K)
        exclude_unknown: If True, remove rows with missing/unknown temperature
        seed: Optional random seed for reproducibility
        logger: Optional logger instance

    Returns:
        Dictionary with operation statistics

    Raises:
        FileNotFoundError: If input file does not exist
        ValueError: If input file is empty or has invalid structure
    """
    if logger is None:
        logger = setup_logger_module()

    # Initialize seed if provided
    if seed is not None:
        init_seed(seed)
        logger.info(f"Initialized random seed: {seed}")

    input_file = Path(input_path)
    output_file = Path(output_path)

    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    # Load data
    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(input_file)

    if df.empty:
        raise ValueError(f"Input file is empty: {input_path}")

    # Normalize
    normalized_df, excluded_count = normalize_dataframe(
        df,
        reference_temp=reference_temp,
        exclude_unknown=exclude_unknown,
        logger=logger
    )

    # Save results
    output_file.parent.mkdir(parents=True, exist_ok=True)
    normalized_df.to_csv(output_file, index=False)
    logger.info(f"Saved normalized data to {output_path}")

    return {
        'input_rows': len(df),
        'output_rows': len(normalized_df),
        'excluded_rows': excluded_count,
        'reference_temp': reference_temp,
        'output_path': str(output_file)
    }

def main():
    """
    Main entry point for command-line execution.

    Usage:
        python src/cleaning/temperature_normalize.py \
            --input data/raw/thermal_raw.csv \
            --output data/cleaned/normalized_thermal.csv \
            --seed 42
    """
    parser = argparse.ArgumentParser(
        description='Normalize thermal conductivity to reference temperature using Slack (1979) formula'
    )
    parser.add_argument(
        '--input',
        type=str,
        required=True,
        help='Path to input CSV file with thermal conductivity data'
    )
    parser.add_argument(
        '--output',
        type=str,
        required=True,
        help='Path to output CSV file for normalized data'
    )
    parser.add_argument(
        '--reference-temp',
        type=float,
        default=DEFAULT_REFERENCE_TEMP,
        help=f'Reference temperature in Kelvin (default: {DEFAULT_REFERENCE_TEMP})'
    )
    parser.add_argument(
        '--exclude-unknown',
        action='store_true',
        default=True,
        help='Exclude rows with missing/unknown temperature (default: True)'
    )
    parser.add_argument(
        '--k-column',
        type=str,
        default='thermal_conductivity',
        help='Name of thermal conductivity column (default: thermal_conductivity)'
    )
    parser.add_argument(
        '--temp-column',
        type=str,
        default='temperature',
        help='Name of temperature column (default: temperature)'
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=None,
        help='Random seed for reproducibility'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    # Setup logger
    level = logging.DEBUG if args.verbose else logging.INFO
    logger = setup_logger(__name__, level=level)

    try:
        stats = apply_temperature_normalization(
            input_path=args.input,
            output_path=args.output,
            reference_temp=args.reference_temp,
            exclude_unknown=args.exclude_unknown,
            seed=args.seed,
            logger=logger
        )

        logger.info("Normalization completed successfully")
        logger.info(f"Statistics: {stats}")
        sys.exit(0)

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
