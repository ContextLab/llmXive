"""
Temperature normalization module for thermal conductivity data.

Implements the Slack (1979) formula to normalize thermal conductivity values
to a reference temperature of 300K ± 10K window.

Reference: Slack, G. A. (1979). Thermal Conductivity of Nonmetallic Crystals.
In R. W. G. Wyckoff (Ed.), Crystal Structures (Vol. 1, pp. 31-32).
"""

import sys
import logging
from pathlib import Path
from typing import Optional, List, Tuple

import pandas as pd
import numpy as np

# Project-relative imports based on API surface
# Note: Using absolute imports relative to project root 'code/'
from utils.validation import setup_logger, handle_error

# Constants
REFERENCE_TEMPERATURE_K = 300.0
TEMPERATURE_TOLERANCE_K = 10.0
MIN_VALID_TEMP_K = 50.0
MAX_VALID_TEMP_K = 1500.0

# Slack (1979) empirical parameters for phonon-phonon scattering
# κ ∝ T^(-1) for high-temperature limit (T > Θ_D/2)
# Normalization: κ_ref = κ_meas * (T_meas / T_ref)^n
# Where n ≈ 1 for high-temperature regime
SLACK_EXPONENT = 1.0

def setup_logger_module(name: str = "temperature_normalize", level: int = logging.INFO) -> logging.Logger:
    """
    Setup a module-specific logger.

    Args:
        name: Logger name
        level: Logging level

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger

logger = setup_logger_module()

def slack_normalization_factor(
    measured_temp: float,
    reference_temp: float = REFERENCE_TEMPERATURE_K,
    exponent: float = SLACK_EXPONENT
) -> float:
    """
    Calculate the Slack (1979) normalization factor for thermal conductivity.

    The formula normalizes thermal conductivity from measured temperature to
    reference temperature using the power-law relationship:

        κ_ref = κ_meas * (T_meas / T_ref)^n

    Where n is the Slack exponent (typically ~1.0 for high-temperature regime).

    Args:
        measured_temp: Temperature at which thermal conductivity was measured (K)
        reference_temp: Target reference temperature (K), default 300K
        exponent: Slack exponent n, default 1.0

    Returns:
        Normalization factor to apply to κ_meas

    Raises:
        ValueError: If measured_temp is outside valid physical range
    """
    if measured_temp < MIN_VALID_TEMP_K or measured_temp > MAX_VALID_TEMP_K:
        raise ValueError(
            f"Measured temperature {measured_temp}K is outside valid range "
            f"[{MIN_VALID_TEMP_K}K, {MAX_VALID_TEMP_K}K]"
        )

    if measured_temp <= 0:
        raise ValueError(f"Measured temperature must be positive: {measured_temp}K")

    if reference_temp <= 0:
        raise ValueError(f"Reference temperature must be positive: {reference_temp}K")

    factor = (measured_temp / reference_temp) ** exponent
    return factor

def normalize_thermal_conductivity(
    kappa_meas: float,
    measured_temp: float,
    reference_temp: float = REFERENCE_TEMPERATURE_K,
    exponent: float = SLACK_EXPONENT
) -> float:
    """
    Normalize thermal conductivity to reference temperature using Slack formula.

    Args:
        kappa_meas: Measured thermal conductivity (W/m·K)
        measured_temp: Temperature at measurement (K)
        reference_temp: Target reference temperature (K)
        exponent: Slack exponent n

    Returns:
        Normalized thermal conductivity at reference temperature (W/m·K)
    """
    factor = slack_normalization_factor(measured_temp, reference_temp, exponent)
    return kappa_meas * factor

def is_within_reference_window(
    temperature: float,
    reference_temp: float = REFERENCE_TEMPERATURE_K,
    tolerance: float = TEMPERATURE_TOLERANCE_K
) -> bool:
    """
    Check if a temperature is within the reference window (300K ± 10K).

    Args:
        temperature: Temperature to check (K)
        reference_temp: Reference temperature (K)
        tolerance: Tolerance window (K)

    Returns:
        True if temperature is within [reference_temp - tolerance, reference_temp + tolerance]
    """
    lower_bound = reference_temp - tolerance
    upper_bound = reference_temp + tolerance
    return lower_bound <= temperature <= upper_bound

def normalize_dataframe(
    df: pd.DataFrame,
    kappa_col: str = "thermal_conductivity",
    temp_col: str = "temperature",
    reference_temp: float = REFERENCE_TEMPERATURE_K,
    tolerance: float = TEMPERATURE_TOLERANCE_K,
    output_col: str = "thermal_conductivity_normalized"
) -> Tuple[pd.DataFrame, List[str]]:
    """
    Normalize thermal conductivity values in a DataFrame to reference temperature.

    Applies Slack (1979) normalization to all rows. Rows with temperature
    outside the valid range or missing temperature data are flagged.

    Args:
        df: Input DataFrame with thermal conductivity and temperature columns
        kappa_col: Name of thermal conductivity column
        temp_col: Name of temperature column
        reference_temp: Target reference temperature (K)
        tolerance: Tolerance for "within window" flag
        output_col: Name for the normalized output column

    Returns:
        Tuple of (normalized DataFrame, list of warning messages)
    """
    warnings = []

    if kappa_col not in df.columns:
        raise ValueError(f"Column '{kappa_col}' not found in DataFrame")
    if temp_col not in df.columns:
        raise ValueError(f"Column '{temp_col}' not found in DataFrame")

    # Create a copy to avoid modifying original
    result_df = df.copy()
    result_df[output_col] = np.nan

    # Track rows needing special handling
    unknown_temp_indices = []
    out_of_range_indices = []
    normalized_count = 0

    for idx, row in result_df.iterrows():
        kappa_val = row[kappa_col]
        temp_val = row[temp_col]

        # Handle missing temperature
        if pd.isna(temp_val):
            unknown_temp_indices.append(idx)
            warnings.append(
                f"Row {idx}: Missing temperature value, cannot normalize "
                f"thermal conductivity (κ={kappa_val} W/m·K)"
            )
            continue

        # Check if within valid physical range
        if temp_val < MIN_VALID_TEMP_K or temp_val > MAX_VALID_TEMP_K:
            out_of_range_indices.append(idx)
            warnings.append(
                f"Row {idx}: Temperature {temp_val}K outside valid range "
                f"[{MIN_VALID_TEMP_K}K, {MAX_VALID_TEMP_K}K], skipping normalization"
            )
            continue

        try:
            normalized_kappa = normalize_thermal_conductivity(
                kappa_val, temp_val, reference_temp, SLACK_EXPONENT
            )
            result_df.at[idx, output_col] = normalized_kappa
            normalized_count += 1
        except ValueError as e:
            warnings.append(f"Row {idx}: Normalization failed - {str(e)}")
            continue

    # Add metadata columns
    result_df['temperature_window_flag'] = result_df[temp_col].apply(
        lambda t: is_within_reference_window(t, reference_temp, tolerance)
        if pd.notna(t) else False
    )

    logger.info(
        f"Normalized {normalized_count} rows. "
        f"Unknown temperature: {len(unknown_temp_indices)}, "
        f"Out of range: {len(out_of_range_indices)}"
    )

    return result_df, warnings

def apply_temperature_normalization(
    input_path: str,
    output_path: str,
    kappa_col: str = "thermal_conductivity",
    temp_col: str = "temperature",
    reference_temp: float = REFERENCE_TEMPERATURE_K,
    tolerance: float = TEMPERATURE_TOLERANCE_K
) -> str:
    """
    Main entry point to normalize thermal conductivity in a CSV file.

    Reads input CSV, applies Slack (1979) normalization, and writes output.

    Args:
        input_path: Path to input CSV file
        output_path: Path to output CSV file
        kappa_col: Name of thermal conductivity column
        temp_col: Name of temperature column
        reference_temp: Target reference temperature (K)
        tolerance: Tolerance for "within window" flag

    Returns:
        Path to output file

    Raises:
        FileNotFoundError: If input file does not exist
        ValueError: If required columns are missing
    """
    input_file = Path(input_path)
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(input_file)

    logger.info(f"Input dataset shape: {df.shape}")
    logger.info(f"Columns: {list(df.columns)}")

    # Validate required columns
    if kappa_col not in df.columns:
        raise ValueError(
            f"Required column '{kappa_col}' not found. "
            f"Available columns: {list(df.columns)}"
        )
    if temp_col not in df.columns:
        raise ValueError(
            f"Required column '{temp_col}' not found. "
            f"Available columns: {list(df.columns)}"
        )

    # Apply normalization
    normalized_df, warnings = normalize_dataframe(
        df,
        kappa_col=kappa_col,
        temp_col=temp_col,
        reference_temp=reference_temp,
        tolerance=tolerance
    )

    # Log warnings
    for warning in warnings:
        logger.warning(warning)

    # Ensure output directory exists
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Write output
    normalized_df.to_csv(output_path, index=False)
    logger.info(f"Normalized data written to {output_path}")

    # Summary statistics
    if not normalized_df.empty:
        stats = {
            'total_rows': len(normalized_df),
            'normalized_count': normalized_df['thermal_conductivity_normalized'].notna().sum(),
            'missing_temp_count': normalized_df[temp_col].isna().sum(),
            'within_window_count': normalized_df['temperature_window_flag'].sum(),
            'kappa_mean': normalized_df['thermal_conductivity_normalized'].mean(),
            'kappa_std': normalized_df['thermal_conductivity_normalized'].std()
        }
        logger.info(f"Normalization summary: {stats}")

    return output_path

def main():
    """
    Command-line entry point for temperature normalization.

    Usage:
        python -m src.cleaning.temperature_normalize \
            --input data/cleaned/merged_perovskite.csv \
            --output data/results/normalized_perovskite.csv
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Normalize thermal conductivity to 300K using Slack (1979) formula"
    )
    parser.add_argument(
        "--input", "-i",
        type=str,
        required=True,
        help="Path to input CSV file with thermal conductivity and temperature"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        required=True,
        help="Path to output CSV file"
    )
    parser.add_argument(
        "--kappa-col",
        type=str,
        default="thermal_conductivity",
        help="Name of thermal conductivity column (default: thermal_conductivity)"
    )
    parser.add_argument(
        "--temp-col",
        type=str,
        default="temperature",
        help="Name of temperature column (default: temperature)"
    )
    parser.add_argument(
        "--ref-temp",
        type=float,
        default=REFERENCE_TEMPERATURE_K,
        help=f"Reference temperature in Kelvin (default: {REFERENCE_TEMPERATURE_K})"
    )
    parser.add_argument(
        "--tolerance",
        type=float,
        default=TEMPERATURE_TOLERANCE_K,
        help=f"Temperature tolerance window in Kelvin (default: {TEMPERATURE_TOLERANCE_K})"
    )

    args = parser.parse_args()

    try:
        output_path = apply_temperature_normalization(
            input_path=args.input,
            output_path=args.output,
            kappa_col=args.kappa_col,
            temp_col=args.temp_col,
            reference_temp=args.ref_temp,
            tolerance=args.tolerance
        )
        logger.info(f"Success: Output written to {output_path}")
    except FileNotFoundError as e:
        handle_error(str(e), "ERROR")
        sys.exit(1)
    except ValueError as e:
        handle_error(str(e), "ERROR")
        sys.exit(1)
    except Exception as e:
        handle_error(f"Unexpected error: {str(e)}", "ERROR")
        sys.exit(1)

if __name__ == "__main__":
    main()
