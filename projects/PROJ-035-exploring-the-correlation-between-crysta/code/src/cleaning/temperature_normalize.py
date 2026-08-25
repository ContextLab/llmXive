"""
Temperature normalization for thermal conductivity data.

Implements the Slack (1979) formula to normalize thermal conductivity values
to a reference temperature of 300K ± 10K window.

References:
    Slack, G. A. (1979). Thermal Conductivity of Nonmetallic Crystals.
    In H. J. Goldsmid (Ed.), Thermal Conductivity (pp. 1-23). Plenum Press.
"""
import sys
import logging
from pathlib import Path
from typing import Optional, List, Tuple

import pandas as pd
import numpy as np

# Project root setup for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.validation import setup_logger, handle_error

# Constants
REFERENCE_TEMPERATURE = 300.0  # Kelvin
TEMPERATURE_WINDOW = 10.0  # Kelvin
MIN_TEMP = 50.0  # Kelvin (physical lower bound for validity)
MAX_TEMP = 1500.0  # Kelvin (physical upper bound for validity)

def setup_logger_module(name: str = "temperature_normalize") -> logging.Logger:
    """Configure and return a logger for this module."""
    return setup_logger(name, level=logging.INFO)

logger = setup_logger_module()

def slack_normalization_factor(
    measured_temp: float,
    reference_temp: float = REFERENCE_TEMPERATURE
) -> float:
    """
    Calculate the Slack (1979) normalization factor.

    The Slack model approximates the temperature dependence of lattice thermal
    conductivity (κ) in non-metallic crystals as κ ∝ 1/T for temperatures
    above the Debye temperature.

    Formula:
        κ_ref = κ_meas * (T_meas / T_ref)

    Where:
        κ_ref: Normalized thermal conductivity at reference temperature
        κ_meas: Measured thermal conductivity
        T_meas: Measurement temperature
        T_ref: Reference temperature (300K)

    Args:
        measured_temp: Temperature at which measurement was taken (K).
        reference_temp: Target reference temperature (K).

    Returns:
        Factor to multiply measured thermal conductivity by.

    Raises:
        ValueError: If measured_temp is outside valid physical bounds.
    """
    if measured_temp < MIN_TEMP:
        raise ValueError(
            f"Measurement temperature {measured_temp}K is below valid range "
            f"(min {MIN_TEMP}K)."
        )
    if measured_temp > MAX_TEMP:
        raise ValueError(
            f"Measurement temperature {measured_temp}K is above valid range "
            f"(max {MAX_TEMP}K)."
        )

    if reference_temp <= 0:
        raise ValueError("Reference temperature must be positive.")

    # Slack normalization: κ_ref = κ_meas * (T_meas / T_ref)
    factor = measured_temp / reference_temp
    logger.debug(
        f"Calculated Slack factor: {measured_temp}K / {reference_temp}K = {factor:.4f}"
    )
    return factor

def is_within_reference_window(
    temperature: float,
    reference: float = REFERENCE_TEMPERATURE,
    window: float = TEMPERATURE_WINDOW
) -> bool:
    """
    Check if a temperature is within the reference window.

    Args:
        temperature: Temperature to check (K).
        reference: Reference temperature (K).
        window: Acceptable deviation from reference (K).

    Returns:
        True if |temperature - reference| <= window.
    """
    return abs(temperature - reference) <= window

def normalize_thermal_conductivity(
    thermal_conductivity: float,
    measured_temp: float,
    reference_temp: float = REFERENCE_TEMPERATURE
) -> float:
    """
    Normalize a single thermal conductivity value to the reference temperature.

    Args:
        thermal_conductivity: Measured thermal conductivity (W/m·K).
        measured_temp: Temperature at which measurement was taken (K).
        reference_temp: Target reference temperature (K).

    Returns:
        Normalized thermal conductivity at reference temperature.

    Raises:
        ValueError: If measured_temp is None, NaN, or out of bounds.
    """
    if pd.isna(measured_temp) or measured_temp is None:
        raise ValueError("Measurement temperature is missing or invalid.")

    factor = slack_normalization_factor(measured_temp, reference_temp)
    return thermal_conductivity * factor

def normalize_dataframe(
    df: pd.DataFrame,
    thermal_col: str = "thermal_conductivity",
    temp_col: str = "measurement_temperature",
    output_col: str = "thermal_conductivity_300K",
    reference_temp: float = REFERENCE_TEMPERATURE
) -> pd.DataFrame:
    """
    Normalize thermal conductivity values in a DataFrame to 300K.

    This function applies the Slack normalization to all rows where:
    1. Thermal conductivity is present.
    2. Measurement temperature is present and valid.
    3. Measurement temperature is within the valid physical range.

    Rows with missing or invalid temperatures are left unchanged in the
    output column (NaN) and logged as warnings.

    Args:
        df: Input DataFrame with thermal data.
        thermal_col: Name of the thermal conductivity column.
        temp_col: Name of the measurement temperature column.
        output_col: Name for the normalized thermal conductivity column.
        reference_temp: Reference temperature for normalization.

    Returns:
        DataFrame with a new column containing normalized values.

    Raises:
        KeyError: If required columns are missing.
    """
    if thermal_col not in df.columns:
        raise KeyError(f"Column '{thermal_col}' not found in DataFrame.")
    if temp_col not in df.columns:
        raise KeyError(f"Column '{temp_col}' not found in DataFrame.")

    df = df.copy()
    normalized_values = []
    error_indices = []

    for idx, row in df.iterrows():
        k_val = row[thermal_col]
        t_val = row[temp_col]

        if pd.isna(k_val):
            normalized_values.append(np.nan)
            continue

        if pd.isna(t_val):
            logger.warning(
                f"Row {idx}: Missing measurement temperature. "
                f"Cannot normalize thermal conductivity."
            )
            normalized_values.append(np.nan)
            continue

        try:
            norm_k = normalize_thermal_conductivity(k_val, t_val, reference_temp)
            normalized_values.append(norm_k)
        except ValueError as e:
            logger.warning(f"Row {idx}: {e}")
            normalized_values.append(np.nan)
            error_indices.append(idx)

    df[output_col] = normalized_values

    if error_indices:
        logger.warning(
            f"Normalization failed for {len(error_indices)} rows due to "
            f"invalid temperature values."
        )

    return df

def apply_temperature_normalization(
    input_path: str,
    output_path: str,
    thermal_col: str = "thermal_conductivity",
    temp_col: str = "measurement_temperature",
    reference_temp: float = REFERENCE_TEMPERATURE
) -> Tuple[int, int]:
    """
    Main function to load, normalize, and save thermal conductivity data.

    Reads a CSV file, normalizes thermal conductivity to 300K using the
    Slack (1979) formula, and saves the result.

    Args:
        input_path: Path to input CSV file.
        output_path: Path to save output CSV file.
        thermal_col: Name of the thermal conductivity column.
        temp_col: Name of the measurement temperature column.
        reference_temp: Reference temperature for normalization.

    Returns:
        Tuple of (rows_processed, rows_normalized).
    """
    logger.info(f"Loading data from {input_path}")
    try:
        df = pd.read_csv(input_path)
    except FileNotFoundError:
        handle_error(f"Input file not found: {input_path}", level="CRITICAL")
        raise
    except Exception as e:
        handle_error(f"Error reading input file: {e}", level="ERROR")
        raise

    logger.info(f"Loaded {len(df)} rows. Normalizing thermal conductivity...")
    df_normalized = normalize_dataframe(
        df,
        thermal_col=thermal_col,
        temp_col=temp_col,
        reference_temp=reference_temp
    )

    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Saving normalized data to {output_path}")
    df_normalized.to_csv(output_path, index=False)

    rows_processed = len(df)
    rows_normalized = df_normalized[
        f"{thermal_col}_normalized" if "normalized" not in output_path else "thermal_conductivity_300K"
    ].notna().sum()

    logger.info(
        f"Normalization complete: {rows_normalized}/{rows_processed} rows normalized."
    )

    return rows_processed, int(rows_normalized)

def main():
    """Entry point for command-line execution."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Normalize thermal conductivity to 300K using Slack (1979) formula."
    )
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to input CSV file containing thermal data."
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Path to save output CSV with normalized values."
    )
    parser.add_argument(
        "--thermal-col",
        type=str,
        default="thermal_conductivity",
        help="Name of the thermal conductivity column."
    )
    parser.add_argument(
        "--temp-col",
        type=str,
        default="measurement_temperature",
        help="Name of the measurement temperature column."
    )
    parser.add_argument(
        "--ref-temp",
        type=float,
        default=300.0,
        help="Reference temperature (default: 300K)."
    )

    args = parser.parse_args()

    try:
        processed, normalized = apply_temperature_normalization(
            input_path=args.input,
            output_path=args.output,
            thermal_col=args.thermal_col,
            temp_col=args.temp_col,
            reference_temp=args.ref_temp
        )
        logger.info(
            f"Successfully processed {processed} rows, "
            f"normalized {normalized} rows."
        )
    except Exception as e:
        handle_error(f"Pipeline execution failed: {e}", level="CRITICAL")
        sys.exit(1)

if __name__ == "__main__":
    main()