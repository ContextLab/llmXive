"""
Preprocessing module for converting MDSplus time-series data into structured DataFrames.

This module handles the conversion of raw MDSplus signals (EFIT, islands, tau_e, h98y2)
into a unified pandas DataFrame format suitable for analysis. It includes logic to
align time-series data, handle missing values, and derive confinement modes.
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

from utils.logger import get_logger
from utils.limits import timeout_guard, TimeoutError

# Configure logger
logger = get_logger(__name__)

# Constants for time alignment (seconds)
TIME_TOLERANCE = 0.01  # 10ms tolerance for time alignment
DEFAULT_TIME_WINDOW = (-0.1, 0.2)  # Relative to shot time (t=0)

def align_time_series(
    signals: Dict[str, Tuple[np.ndarray, np.ndarray]],
    reference_signal: str = 'time',
    time_tolerance: float = TIME_TOLERANCE
) -> pd.DataFrame:
    """
    Align multiple time-series signals to a common time base.

    Args:
        signals: Dictionary mapping signal names to (time, value) tuples.
        reference_signal: Name of the signal to use as time reference.
        time_tolerance: Tolerance in seconds for time alignment.

    Returns:
        Aligned DataFrame with columns for each signal.

    Raises:
        ValueError: If reference signal is missing or time arrays are incompatible.
    """
    if reference_signal not in signals:
        raise ValueError(f"Reference signal '{reference_signal}' not found in signals")

    ref_time, ref_values = signals[reference_signal]

    # Create base DataFrame with reference time
    df = pd.DataFrame({reference_signal: ref_time})

    # Sort by time
    df = df.sort_values(reference_signal).reset_index(drop=True)

    # Align other signals
    for name, (time_arr, values) in signals.items():
        if name == reference_signal:
            continue

        # Interpolate values to reference time base
        try:
            interpolated = np.interp(df[reference_signal].values, time_arr, values)
            df[name] = interpolated
            logger.debug(f"Aligned signal '{name}' with {len(values)} points to {len(ref_time)} reference points")
        except Exception as e:
            logger.warning(f"Failed to align signal '{name}': {e}. Dropping from DataFrame.")
            # Skip this signal but continue with others

    return df

def extract_snapshot(
    df: pd.DataFrame,
    time_window: Tuple[float, float] = DEFAULT_TIME_WINDOW,
    target_time: Optional[float] = None
) -> pd.DataFrame:
    """
    Extract a snapshot of data within a specified time window or at a target time.

    Args:
        df: Input DataFrame with time column.
        time_window: (start, end) tuple relative to shot time.
        target_time: Specific time point to extract (overrides window).

    Returns:
        DataFrame containing the snapshot data.
    """
    if target_time is not None:
        # Find closest time point
        mask = np.abs(df['time'] - target_time) < TIME_TOLERANCE
        if not mask.any():
            # Fallback to nearest neighbor
            idx = (df['time'] - target_time).abs().idxmin()
            return df.loc[[idx]].reset_index(drop=True)
        return df.loc[mask].reset_index(drop=True)
    else:
        # Use time window
        start, end = time_window
        mask = (df['time'] >= start) & (df['time'] <= end)
        if not mask.any():
            logger.warning(f"No data found in time window [{start}, {end}]")
            return pd.DataFrame()
        return df.loc[mask].reset_index(drop=True)

def calculate_island_width(
    df: pd.DataFrame,
    local_shear: float,
    q_value: float,
    magnetic_field: float,
    r_minor: float
) -> float:
    """
    Calculate island width using Rutherford equation approximation.

    Args:
        df: DataFrame containing plasma parameters (used for context).
        local_shear: Local magnetic shear (s).
        q_value: Safety factor at rational surface (q).
        magnetic_field: Toroidal magnetic field (T).
        r_minor: Minor radius (m).

    Returns:
        Calculated island width in meters.

    Note:
        This is a simplified approximation: w ~ sqrt(epsilon * B_r / (s * B_t))
        where epsilon is the island perturbation amplitude.
    """
    # Simplified Rutherford approximation
    # w = 4 * sqrt( (m * B_r) / (s * q * B_t) ) * r_minor
    # Assuming m=2, n=1 for dominant mode, B_r/B_t ~ 1e-4 (typical perturbation)
    B_r_ratio = 1e-4  # Typical resonant field perturbation ratio
    m = 2
    n = 1

    if local_shear <= 0:
        logger.warning("Non-positive local shear detected, returning 0 for island width")
        return 0.0

    # Simplified formula
    w = 4 * np.sqrt(
        (m * B_r_ratio) / (local_shear * q_value)
    ) * r_minor

    return float(w)

def determine_confinement_mode(
    h98y2: float,
    threshold: float = 0.85
) -> str:
    """
    Determine confinement mode based on H98y2 factor.

    Args:
        h98y2: H-factor relative to ITER98y2 scaling.
        threshold: Threshold for H-mode classification.

    Returns:
        'H-mode' if h98y2 >= threshold, 'L-mode' otherwise.
    """
    return 'H-mode' if h98y2 >= threshold else 'L-mode'

def parse_discharge_data(
    discharge_data: Dict[str, Any],
    discharge_id: int,
    time_window: Tuple[float, float] = DEFAULT_TIME_WINDOW
) -> pd.DataFrame:
    """
    Parse MDSplus discharge data into a structured DataFrame.

    Args:
        discharge_data: Dictionary containing raw MDSplus signals for a discharge.
        discharge_id: Discharge identifier.
        time_window: Time window for snapshot extraction.

    Returns:
        DataFrame with parsed and aligned data for the discharge.

    Raises:
        ValueError: If required data fields are missing.
    """
    required_fields = ['time', 'tau_e', 'h98y2', 'island_width', 'efit']

    missing = [f for f in required_fields if f not in discharge_data]
    if missing:
        raise ValueError(f"Missing required fields: {missing}")

    # Extract signals
    time_arr = discharge_data['time']
    tau_e_arr = discharge_data['tau_e']
    h98y2_arr = discharge_data['h98y2']
    island_width_raw = discharge_data['island_width']
    efit_data = discharge_data['efit']

    # Prepare signals for alignment
    signals = {
        'time': (time_arr, np.ones_like(time_arr)),  # Dummy values for time reference
        'tau_e': (time_arr, tau_e_arr),
        'h98y2': (time_arr, h98y2_arr),
    }

    # Add island_width if it's time-series
    if isinstance(island_width_raw, (list, np.ndarray)) and len(island_width_raw) == len(time_arr):
        signals['island_width'] = (time_arr, island_width_raw)
    else:
        # Single value, broadcast
        signals['island_width'] = (time_arr, np.full_like(time_arr, island_width_raw, dtype=float))

    # Add EFIT-derived signals if available
    if 'q_profile' in efit_data:
        q_time = efit_data.get('q_time', time_arr)
        q_vals = efit_data['q_profile']
        signals['q'] = (q_time, q_vals)

    if 'local_shear' in efit_data:
        shear_time = efit_data.get('shear_time', time_arr)
        shear_vals = efit_data['local_shear']
        signals['local_shear'] = (shear_time, shear_vals)

    if 'btor' in efit_data:
        btor_time = efit_data.get('btor_time', time_arr)
        btor_vals = efit_data['btor']
        signals['btor'] = (btor_time, btor_vals)

    if 'r_minor' in efit_data:
        r_minor_time = efit_data.get('r_minor_time', time_arr)
        r_minor_vals = efit_data['r_minor']
        signals['r_minor'] = (r_minor_time, r_minor_vals)

    # Align signals
    try:
        aligned_df = align_time_series(signals)
    except Exception as e:
        logger.error(f"Failed to align time series for discharge {discharge_id}: {e}")
        raise

    # Extract snapshot
    snapshot_df = extract_snapshot(aligned_df, time_window=time_window)

    if snapshot_df.empty:
        logger.warning(f"No data in time window for discharge {discharge_id}")
        return pd.DataFrame()

    # Derive confinement mode
    h98y2_val = snapshot_df['h98y2'].mean()
    confinement_mode = determine_confinement_mode(h98y2_val)

    # Add derived fields
    snapshot_df['discharge_id'] = discharge_id
    snapshot_df['confinement_mode'] = confinement_mode

    # If island_width was not directly available, derive it from EFIT
    if 'island_width' not in efit_data or (isinstance(island_width_raw, (float, int)) and np.isnan(island_width_raw)):
        logger.info(f"Deriving island width for discharge {discharge_id} from EFIT data")
        local_shear = snapshot_df['local_shear'].mean() if 'local_shear' in snapshot_df else 0.5
        q_val = snapshot_df['q'].mean() if 'q' in snapshot_df else 3.0
        btor_val = snapshot_df['btor'].mean() if 'btor' in snapshot_df else 2.0
        r_minor_val = snapshot_df['r_minor'].mean() if 'r_minor' in snapshot_df else 0.6

        derived_width = calculate_island_width(
            snapshot_df,
            local_shear=local_shear,
            q_value=q_val,
            magnetic_field=btor_val,
            r_minor=r_minor_val
        )
        snapshot_df['island_width'] = derived_width

    # Ensure numeric columns
    numeric_cols = ['tau_e', 'h98y2', 'island_width', 'local_shear', 'q', 'btor', 'r_minor']
    for col in numeric_cols:
        if col in snapshot_df.columns:
            snapshot_df[col] = pd.to_numeric(snapshot_df[col], errors='coerce')

    # Drop rows with critical NaNs
    critical_cols = ['discharge_id', 'tau_e', 'island_width', 'confinement_mode']
    snapshot_df = snapshot_df.dropna(subset=critical_cols)

    # Select final columns
    final_columns = [
        'discharge_id', 'tau_e', 'island_width', 'confinement_mode', 'h98y2',
        'local_shear', 'q', 'btor', 'r_minor', 'time'
    ]
    available_cols = [c for c in final_columns if c in snapshot_df.columns]
    result_df = snapshot_df[available_cols].reset_index(drop=True)

    logger.info(f"Successfully parsed discharge {discharge_id}: {len(result_df)} rows")
    return result_df

def process_multiple_discharges(
    discharge_list: List[Dict[str, Any]],
    time_window: Tuple[float, float] = DEFAULT_TIME_WINDOW
) -> pd.DataFrame:
    """
    Process multiple discharges and combine into a single DataFrame.

    Args:
        discharge_list: List of dictionaries, each containing discharge data.
        time_window: Time window for snapshot extraction.

    Returns:
        Combined DataFrame with all processed discharges.
    """
    all_dataframes = []

    for discharge_info in discharge_list:
        discharge_id = discharge_info.get('discharge_id')
        data = discharge_info.get('data')

        if data is None:
            logger.warning(f"Skipping discharge {discharge_id}: no data provided")
            continue

        try:
            df = parse_discharge_data(data, discharge_id, time_window)
            if not df.empty:
                all_dataframes.append(df)
                logger.info(f"Processed discharge {discharge_id}: {len(df)} rows")
            else:
                logger.warning(f"No valid data for discharge {discharge_id}")
        except Exception as e:
            logger.error(f"Failed to process discharge {discharge_id}: {e}")
            continue

    if not all_dataframes:
        logger.error("No discharges were successfully processed")
        return pd.DataFrame()

    combined_df = pd.concat(all_dataframes, ignore_index=True)
    logger.info(f"Combined {len(combined_df)} rows from {len(all_dataframes)} discharges")

    return combined_df

def validate_parsed_data(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    Validate the parsed DataFrame against expected schema.

    Args:
        df: Input DataFrame to validate.

    Returns:
        Tuple of (is_valid, list of error messages).
    """
    errors = []
    required_columns = ['discharge_id', 'tau_e', 'island_width', 'confinement_mode']

    # Check required columns
    missing_cols = [c for c in required_columns if c not in df.columns]
    if missing_cols:
        errors.append(f"Missing required columns: {missing_cols}")

    # Check for NaN in critical columns
    critical_cols = ['discharge_id', 'tau_e', 'island_width']
    for col in critical_cols:
        if col in df.columns:
            nan_count = df[col].isna().sum()
            if nan_count > 0:
                errors.append(f"Column '{col}' contains {nan_count} NaN values")

    # Check confinement_mode values
    if 'confinement_mode' in df.columns:
        valid_modes = ['L-mode', 'H-mode']
        invalid_modes = df[~df['confinement_mode'].isin(valid_modes)]['confinement_mode'].unique()
        if len(invalid_modes) > 0:
            errors.append(f"Invalid confinement modes found: {invalid_modes}")

    # Check positive values
    if 'tau_e' in df.columns:
        if (df['tau_e'] <= 0).any():
            errors.append("tau_e contains non-positive values")

    if 'island_width' in df.columns:
        if (df['island_width'] < 0).any():
            errors.append("island_width contains negative values")

    return len(errors) == 0, errors

# Main execution for testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.info("Preprocessing module loaded successfully")
    logger.info("Use process_multiple_discharges() to parse MDSplus data into DataFrames")
