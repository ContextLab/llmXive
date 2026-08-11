"""
Temperature normalization module for perovskite thermal conductivity data.

Implements the Slack (1979) formula to normalize thermal conductivity values
to a standard reference temperature of 300K ± 10K window.

Reference: Slack, G. A. (1979). Thermal Conductivity of Nonmetallic Crystals.
In D. T. Morelli (Ed.), Nonmetallic Crystals (pp. 1-34). Springer.
"""
import sys
import logging
from pathlib import Path
from typing import Optional, List, Tuple
import pandas as pd
import numpy as np

# Import shared utilities from existing API surface
from utils.validation import setup_logger, handle_error

# Constants
REFERENCE_TEMPERATURE_K = 300.0
TEMP_WINDOW_TOLERANCE_K = 10.0
MIN_SAMPLES_REQUIRED = 1
SLACK_EXPONENT = 1.0  # Slack (1979) typically uses T^(-1) for phonon scattering


def setup_logger_module(name: str = __name__) -> logging.Logger:
    """Configure module logger."""
    return setup_logger(name, level=logging.INFO)


def slack_normalization_factor(
    measured_temp: float,
    ref_temp: float = REFERENCE_TEMPERATURE_K,
    exponent: float = SLACK_EXPONENT
) -> float:
    """
    Calculate the normalization factor using Slack (1979) formula.

    The formula assumes thermal conductivity κ scales with temperature as:
    κ(T) ∝ T^(-exponent)

    Therefore, the normalization factor to convert κ(T_meas) to κ(T_ref) is:
    factor = (T_meas / T_ref)^(exponent)

    Args:
        measured_temp: The temperature at which thermal conductivity was measured (K).
        ref_temp: The reference temperature to normalize to (K). Default: 300K.
        exponent: The temperature exponent from Slack's model. Default: 1.0.

    Returns:
        float: The multiplicative factor to apply to the measured conductivity.
    """
    if measured_temp <= 0:
        raise ValueError(f"Measured temperature must be positive, got {measured_temp}")
    if ref_temp <= 0:
        raise ValueError(f"Reference temperature must be positive, got {ref_temp}")

    return (measured_temp / ref_temp) ** exponent


def normalize_thermal_conductivity(
    measured_k: float,
    measured_temp: float,
    ref_temp: float = REFERENCE_TEMPERATURE_K,
    exponent: float = SLACK_EXPONENT
) -> float:
    """
    Normalize a thermal conductivity value to a reference temperature.

    κ_norm = κ_meas * (T_meas / T_ref)^exponent

    Args:
        measured_k: Measured thermal conductivity (W/m·K).
        measured_temp: Temperature at which measurement was taken (K).
        ref_temp: Reference temperature for normalization (K).
        exponent: Slack exponent (default 1.0).

    Returns:
        float: Normalized thermal conductivity at ref_temp.
    """
    factor = slack_normalization_factor(measured_temp, ref_temp, exponent)
    return measured_k * factor


def is_within_reference_window(
    temp: float,
    ref_temp: float = REFERENCE_TEMPERATURE_K,
    tolerance: float = TEMP_WINDOW_TOLERANCE_K
) -> bool:
    """
    Check if a temperature is within the acceptable reference window.

    Args:
        temp: Temperature to check (K).
        ref_temp: Reference temperature (K).
        tolerance: Acceptable deviation from reference (K).

    Returns:
        bool: True if temp is within [ref_temp - tolerance, ref_temp + tolerance].
    """
    return abs(temp - ref_temp) <= tolerance


def normalize_dataframe(
    df: pd.DataFrame,
    k_col: str = 'thermal_conductivity',
    temp_col: str = 'measurement_temperature',
    ref_temp: float = REFERENCE_TEMPERATURE_K,
    tolerance: float = TEMP_WINDOW_TOLERANCE_K,
    new_col_suffix: str = '_normalized_300K'
) -> Tuple[pd.DataFrame, List[str], List[str]]:
    """
    Normalize thermal conductivity values in a DataFrame to 300K using Slack formula.

    This function:
    1. Identifies rows where temperature is known and within the reference window.
    2. Normalizes values for rows outside the window using the Slack formula.
    3. Marks rows with unknown temperature for exclusion or flagging.

    Args:
        df: Input DataFrame with thermal conductivity and temperature columns.
        k_col: Name of the thermal conductivity column.
        temp_col: Name of the temperature column.
        ref_temp: Reference temperature for normalization (default 300K).
        tolerance: Acceptable temperature window (default ±10K).
        new_col_suffix: Suffix for the normalized column name.

    Returns:
        Tuple containing:
            - Modified DataFrame with normalized column added.
            - List of indices normalized (were outside window but had temp).
            - List of indices flagged as unknown temperature.
    """
    if k_col not in df.columns:
        raise ValueError(f"Column '{k_col}' not found in DataFrame")
    if temp_col not in df.columns:
        raise ValueError(f"Column '{temp_col}' not found in DataFrame")

    logger = setup_logger_module()
    normalized_indices = []
    unknown_temp_indices = []

    # Create new column name
    new_col_name = f"{k_col}{new_col_suffix}"

    # Initialize new column with NaN
    df[new_col_name] = np.nan

    for idx, row in df.iterrows():
        k_val = row[k_col]
        temp_val = row[temp_col]

        # Handle missing data
        if pd.isna(k_val):
            logger.warning(f"Row {idx}: Missing thermal conductivity value")
            continue

        if pd.isna(temp_val):
            logger.warning(f"Row {idx}: Unknown temperature for thermal conductivity {k_val}")
            unknown_temp_indices.append(idx)
            continue

        if temp_val <= 0:
            logger.error(f"Row {idx}: Invalid temperature {temp_val} (must be > 0)")
            continue

        # Check if within window
        if is_within_reference_window(temp_val, ref_temp, tolerance):
            logger.debug(f"Row {idx}: Temperature {temp_val}K within window, keeping original")
            df.at[idx, new_col_name] = k_val
        else:
            # Apply Slack normalization
            try:
                k_norm = normalize_thermal_conductivity(k_val, temp_val, ref_temp)
                df.at[idx, new_col_name] = k_norm
                normalized_indices.append(idx)
                logger.info(f"Row {idx}: Normalized {k_val} @ {temp_val}K -> {k_norm:.4f} @ {ref_temp}K")
            except ValueError as e:
                handle_error(f"Normalization failed for row {idx}: {e}", level="ERROR")
                continue

    return df, normalized_indices, unknown_temp_indices


def apply_temperature_normalization(
    input_path: str,
    output_path: str,
    k_col: str = 'thermal_conductivity',
    temp_col: str = 'measurement_temperature',
    ref_temp: float = REFERENCE_TEMPERATURE_K,
    tolerance: float = TEMP_WINDOW_TOLERANCE_K,
    strict_mode: bool = True
) -> None:
    """
    Main entry point to normalize thermal conductivity data from a CSV file.

    Args:
        input_path: Path to input CSV file.
        output_path: Path to write output CSV file.
        k_col: Name of thermal conductivity column.
        temp_col: Name of temperature column.
        ref_temp: Reference temperature (default 300K).
        tolerance: Temperature window tolerance (default ±10K).
        strict_mode: If True, fail if no rows are within window and none can be normalized.

    Raises:
        FileNotFoundError: If input file does not exist.
        ValueError: If required columns are missing or no valid data found.
    """
    logger = setup_logger_module()
    logger.info(f"Starting temperature normalization: {input_path} -> {output_path}")

    input_file = Path(input_path)
    output_file = Path(output_path)

    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    # Load data
    df = pd.read_csv(input_file)
    logger.info(f"Loaded {len(df)} rows from {input_path}")

    # Perform normalization
    df_normalized, normalized_idx, unknown_idx = normalize_dataframe(
        df, k_col, temp_col, ref_temp, tolerance
    )

    logger.info(f"Normalized {len(normalized_idx)} rows, {len(unknown_idx)} rows have unknown temperature")

    # Validate results
    if len(normalized_idx) == 0 and len(unknown_idx) == len(df):
        if strict_mode:
            raise ValueError(
                "No valid data to normalize: all rows have unknown temperature "
                f"or are outside the {ref_temp}K ± {tolerance}K window."
            )
        logger.warning("No data could be normalized, but continuing in non-strict mode")

    # Ensure minimum samples if we have any normalized data
    if len(normalized_idx) < MIN_SAMPLES_REQUIRED and len(normalized_idx) > 0:
        logger.warning(f"Only {len(normalized_idx)} rows normalized, below recommended minimum")

    # Save output
    output_file.parent.mkdir(parents=True, exist_ok=True)
    df_normalized.to_csv(output_file, index=False)
    logger.info(f"Saved normalized data to {output_path}")

    # Log summary
    logger.info(f"Normalization complete: {len(df)} -> {len(df_normalized)} rows (excluding NaN)")
    logger.info(f"  - Original values kept (within window): {len(df) - len(normalized_idx) - len(unknown_idx)}")
    logger.info(f"  - Normalized values: {len(normalized_idx)}")
    logger.info(f"  - Unknown temperature (flagged): {len(unknown_idx)}")


def main() -> None:
    """
    Command-line entry point for temperature normalization.

    Usage:
        python -m cleaning.temperature_normalize \
            --input data/cleaned/merged_perovskites.csv \
            --output data/cleaned/merged_perovskites_normalized.csv
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Normalize thermal conductivity to 300K using Slack (1979) formula."
    )
    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Path to input CSV file with thermal conductivity data."
    )
    parser.add_argument(
        "--output", "-o",
        required=True,
        help="Path to output CSV file for normalized data."
    )
    parser.add_argument(
        "--k-col",
        default="thermal_conductivity",
        help="Name of thermal conductivity column (default: thermal_conductivity)"
    )
    parser.add_argument(
        "--temp-col",
        default="measurement_temperature",
        help="Name of temperature column (default: measurement_temperature)"
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
        default=TEMP_WINDOW_TOLERANCE_K,
        help=f"Temperature window tolerance in Kelvin (default: {TEMP_WINDOW_TOLERANCE_K})"
    )
    parser.add_argument(
        "--no-strict",
        action="store_true",
        help="Do not fail if no data can be normalized"
    )

    args = parser.parse_args()

    try:
        apply_temperature_normalization(
            input_path=args.input,
            output_path=args.output,
            k_col=args.k_col,
            temp_col=args.temp_col,
            ref_temp=args.ref_temp,
            tolerance=args.tolerance,
            strict_mode=not args.no_strict
        )
        print(f"SUCCESS: Normalized data written to {args.output}")
    except FileNotFoundError as e:
        handle_error(str(e), level="FATAL")
        sys.exit(1)
    except ValueError as e:
        handle_error(str(e), level="FATAL")
        sys.exit(1)
    except Exception as e:
        handle_error(f"Unexpected error: {e}", level="FATAL")
        sys.exit(1)


if __name__ == "__main__":
    main()
