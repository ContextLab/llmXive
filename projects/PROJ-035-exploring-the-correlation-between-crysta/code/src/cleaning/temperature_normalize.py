"""
Temperature normalization module for thermal conductivity data.

Implements the Slack (1979) formula to normalize thermal conductivity
measurements to a reference temperature of 300K.

Formula: k(T) = k_ref * (T_ref / T)^n
where:
    k(T) = thermal conductivity at temperature T
    k_ref = thermal conductivity at reference temperature T_ref
    T_ref = reference temperature (300K)
    T = measurement temperature
    n = dimensionless temperature scaling exponent (default 1.5 for perovskites)
"""

import sys
import logging
from pathlib import Path
from typing import Optional, List, Tuple
import pandas as pd
import numpy as np

# Set up logger
logger = logging.getLogger(__name__)

# Reference temperature for normalization
REFERENCE_TEMPERATURE = 300.0  # Kelvin
TEMPERATURE_TOLERANCE = 10.0   # ±10K tolerance window

# Default exponent for perovskites (Slack, 1979)
DEFAULT_EXPONENT = 1.5


def setup_logger_module(name: str = __name__, level: int = logging.INFO) -> logging.Logger:
    """
    Configure and return a module logger.
    
    Args:
        name: Logger name (default: module name)
        level: Logging level (default: INFO)
        
    Returns:
        Configured logger instance
    """
    log = logging.getLogger(name)
    log.setLevel(level)
    if not log.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        log.addHandler(handler)
    return log


def slack_normalization_factor(
    T: float, 
    T_ref: float = REFERENCE_TEMPERATURE, 
    n: float = DEFAULT_EXPONENT
) -> float:
    """
    Calculate the Slack (1979) normalization factor.
    
    Args:
        T: Measurement temperature in Kelvin
        T_ref: Reference temperature in Kelvin (default: 300K)
        n: Dimensionless temperature scaling exponent (default: 1.5)
        
    Returns:
        Normalization factor (T_ref / T)^n
        
    Raises:
        ValueError: If T <= 0 or T_ref <= 0
    """
    if T <= 0:
        raise ValueError(f"Temperature must be positive, got {T}")
    if T_ref <= 0:
        raise ValueError(f"Reference temperature must be positive, got {T_ref}")
    
    return (T_ref / T) ** n


def is_within_reference_window(
    T: float, 
    T_ref: float = REFERENCE_TEMPERATURE, 
    tolerance: float = TEMPERATURE_TOLERANCE
) -> bool:
    """
    Check if a temperature is within the reference window.
    
    Args:
        T: Temperature to check in Kelvin
        T_ref: Reference temperature in Kelvin
        tolerance: Tolerance in Kelvin (default: ±10K)
        
    Returns:
        True if |T - T_ref| <= tolerance
    """
    return abs(T - T_ref) <= tolerance


def is_unknown_temperature(value) -> bool:
    """
    Check if a temperature value is unknown/invalid.
    
    Args:
        value: Temperature value to check
        
    Returns:
        True if value is null, NaN, 'N/A', -1, 'unknown', 'None', or empty string
    """
    if pd.isna(value):
        return True
    if isinstance(value, str):
        lower_val = value.strip().lower()
        if lower_val in ['n/a', 'unknown', 'none', '']:
            return True
    if isinstance(value, (int, float)):
        if value == -1:
            return True
    return False


def normalize_thermal_conductivity(
    k: float, 
    T: float, 
    T_ref: float = REFERENCE_TEMPERATURE, 
    n: float = DEFAULT_EXPONENT
) -> float:
    """
    Normalize thermal conductivity to reference temperature using Slack formula.
    
    Args:
        k: Thermal conductivity at temperature T
        T: Measurement temperature in Kelvin
        T_ref: Reference temperature in Kelvin
        n: Dimensionless temperature scaling exponent
        
    Returns:
        Normalized thermal conductivity at T_ref
    """
    factor = slack_normalization_factor(T, T_ref, n)
    return k * factor


def normalize_dataframe(
    df: pd.DataFrame,
    temperature_col: str = 'temperature',
    thermal_col: str = 'thermal_conductivity',
    T_ref: float = REFERENCE_TEMPERATURE,
    tolerance: float = TEMPERATURE_TOLERANCE,
    n: float = DEFAULT_EXPONENT
) -> Tuple[pd.DataFrame, int, int]:
    """
    Normalize thermal conductivity values in a DataFrame to reference temperature.
    
    Logic:
        1. Identify 'unknown' temperatures and discard those entries
        2. For known temperatures outside T_ref ± tolerance: apply Slack correction
        3. For known temperatures within T_ref ± tolerance: keep as is
        
    Args:
        df: Input DataFrame with thermal conductivity and temperature columns
        temperature_col: Name of temperature column
        thermal_col: Name of thermal conductivity column
        T_ref: Reference temperature (default: 300K)
        tolerance: Tolerance window in Kelvin (default: ±10K)
        n: Slack exponent (default: 1.5)
        
    Returns:
        Tuple of (normalized DataFrame, count of discarded rows, count of corrected rows)
        
    Raises:
        ValueError: If required columns are missing
    """
    # Validate columns
    if temperature_col not in df.columns:
        raise ValueError(f"Temperature column '{temperature_col}' not found in DataFrame")
    if thermal_col not in df.columns:
        raise ValueError(f"Thermal conductivity column '{thermal_col}' not found in DataFrame")
    
    # Create a copy to avoid modifying original
    result_df = df.copy()
    
    # Track statistics
    discarded_count = 0
    corrected_count = 0
    
    # Identify unknown temperatures
    unknown_mask = result_df[temperature_col].apply(is_unknown_temperature)
    discarded_count = unknown_mask.sum()
    
    if discarded_count > 0:
        logger.warning(f"Discarding {discarded_count} rows with unknown temperatures")
    
    # Remove unknown temperature entries
    result_df = result_df[~unknown_mask]
    
    # Convert temperature column to numeric, coercing errors to NaN
    result_df[temperature_col] = pd.to_numeric(result_df[temperature_col], errors='coerce')
    
    # Re-check for any NaN that may have resulted from conversion
    nan_mask = result_df[temperature_col].isna()
    if nan_mask.sum() > 0:
        logger.warning(f"Discarding {nan_mask.sum()} additional rows with NaN temperatures after conversion")
        result_df = result_df[~nan_mask]
    
    # Identify temperatures outside the reference window
    outside_window = ~result_df[temperature_col].apply(
        lambda T: is_within_reference_window(T, T_ref, tolerance)
    )
    
    # Apply normalization only to those outside the window
    if outside_window.any():
        corrected_count = outside_window.sum()
        logger.info(f"Applying Slack normalization to {corrected_count} rows outside {T_ref}K ± {tolerance}K")
        
        # Apply normalization
        result_df.loc[outside_window, thermal_col] = result_df.loc[outside_window].apply(
            lambda row: normalize_thermal_conductivity(
                row[thermal_col],
                row[temperature_col],
                T_ref,
                n
            ),
            axis=1
        )
        
        # Update temperature to reference for normalized entries
        result_df.loc[outside_window, temperature_col] = T_ref
    else:
        logger.info("All temperatures already within reference window; no normalization needed")
    
    # Reset index
    result_df = result_df.reset_index(drop=True)
    
    return result_df, discarded_count, corrected_count


def apply_temperature_normalization(
    input_path: str,
    output_path: str,
    temperature_col: str = 'temperature',
    thermal_col: str = 'thermal_conductivity',
    T_ref: float = REFERENCE_TEMPERATURE,
    tolerance: float = TEMPERATURE_TOLERANCE,
    n: float = DEFAULT_EXPONENT,
    seed: Optional[int] = None
) -> dict:
    """
    Main function to load, normalize, and save thermal conductivity data.
    
    Args:
        input_path: Path to input CSV file
        output_path: Path to save normalized CSV file
        temperature_col: Name of temperature column
        thermal_col: Name of thermal conductivity column
        T_ref: Reference temperature (default: 300K)
        tolerance: Tolerance window in Kelvin (default: ±10K)
        n: Slack exponent (default: 1.5)
        seed: Random seed (for reproducibility, though not used in this deterministic operation)
        
    Returns:
        Dictionary with processing statistics
    """
    if seed is not None:
        np.random.seed(seed)
        logger.info(f"Seed set to {seed}")
    
    # Load input data
    logger.info(f"Loading data from {input_path}")
    input_file = Path(input_path)
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_file)
    logger.info(f"Loaded {len(df)} rows from {input_path}")
    
    # Normalize
    normalized_df, discarded, corrected = normalize_dataframe(
        df,
        temperature_col=temperature_col,
        thermal_col=thermal_col,
        T_ref=T_ref,
        tolerance=tolerance,
        n=n
    )
    
    # Ensure output directory exists
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Save normalized data
    normalized_df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(normalized_df)} rows to {output_path}")
    
    # Return statistics
    stats = {
        'input_rows': len(df),
        'output_rows': len(normalized_df),
        'discarded_unknown_temp': discarded,
        'normalized_outside_window': corrected,
        'reference_temperature': T_ref,
        'tolerance': tolerance,
        'slack_exponent': n,
        'output_path': str(output_path)
    }
    
    return stats


def main():
    """CLI entry point for temperature normalization."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Normalize thermal conductivity data to reference temperature using Slack (1979) formula'
    )
    parser.add_argument(
        '--input', '-i',
        required=True,
        help='Path to input CSV file with thermal conductivity data'
    )
    parser.add_argument(
        '--output', '-o',
        required=True,
        help='Path to save normalized CSV file'
    )
    parser.add_argument(
        '--temperature-col',
        default='temperature',
        help='Name of temperature column (default: temperature)'
    )
    parser.add_argument(
        '--thermal-col',
        default='thermal_conductivity',
        help='Name of thermal conductivity column (default: thermal_conductivity)'
    )
    parser.add_argument(
        '--ref-temp',
        type=float,
        default=REFERENCE_TEMPERATURE,
        help=f'Reference temperature in Kelvin (default: {REFERENCE_TEMPERATURE})'
    )
    parser.add_argument(
        '--tolerance',
        type=float,
        default=TEMPERATURE_TOLERANCE,
        help=f'Tolerance window in Kelvin (default: {TEMPERATURE_TOLERANCE})'
    )
    parser.add_argument(
        '--exponent', '-n',
        type=float,
        default=DEFAULT_EXPONENT,
        help=f'Slack exponent n (default: {DEFAULT_EXPONENT})'
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=None,
        help='Random seed for reproducibility'
    )
    parser.add_argument(
        '--log-level',
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Logging level (default: INFO)'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    level = getattr(logging, args.log_level.upper())
    setup_logger_module(level=level)
    
    try:
        stats = apply_temperature_normalization(
            input_path=args.input,
            output_path=args.output,
            temperature_col=args.temperature_col,
            thermal_col=args.thermal_col,
            T_ref=args.ref_temp,
            tolerance=args.tolerance,
            n=args.exponent,
            seed=args.seed
        )
        
        logger.info("Normalization completed successfully")
        logger.info(f"Statistics: {stats}")
        
    except Exception as e:
        logger.error(f"Normalization failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
