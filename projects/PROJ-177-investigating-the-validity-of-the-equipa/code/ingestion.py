"""
Data Ingestion Module.

Handles loading, syncing, and processing of particle tracking and driving signal data.
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import numpy as np

from config import load_config, get_material_properties, get_mass, get_inertia


class IngestionError(Exception):
    """Custom exception for ingestion errors."""
    pass


def find_csv_files(directory: Path) -> List[Path]:
    """Find all CSV files in a directory recursively."""
    if not directory.exists():
        return []
    files = []
    for root, _, filenames in os.walk(directory):
        for filename in filenames:
            if filename.endswith(".csv"):
                files.append(Path(root) / filename)
    return sorted(files)


def load_tracking_data(file_path: Path) -> pd.DataFrame:
    """
    Load particle tracking data from a CSV file.
    
    Expected columns: particle_id, timestamp, x, y, z, theta
    """
    try:
        df = pd.read_csv(file_path)
        # Ensure timestamp is numeric
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_numeric(df['timestamp'], errors='coerce')
        return df
    except Exception as e:
        raise IngestionError(f"Failed to load tracking data from {file_path}: {e}")


def load_driving_data(file_path: Path) -> pd.DataFrame:
    """
    Load driving signal data from a CSV file.
    
    Expected columns: timestamp, frequency, amplitude
    """
    try:
        df = pd.read_csv(file_path)
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_numeric(df['timestamp'], errors='coerce')
        return df
    except Exception as e:
        raise IngestionError(f"Failed to load driving data from {file_path}: {e}")


def sync_timestamps(tracking_df: pd.DataFrame, driving_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Sync tracking and driving data by interpolating driving data to tracking timestamps.
    """
    # Sort by timestamp
    tracking_df = tracking_df.sort_values('timestamp').reset_index(drop=True)
    driving_df = driving_df.sort_values('timestamp').reset_index(drop=True)
    
    # Interpolate driving data to tracking timestamps
    tracking_timestamps = tracking_df['timestamp'].values
    
    # Create a mapping of driving data
    driving_interp = np.interp(
        tracking_timestamps,
        driving_df['timestamp'].values,
        driving_df['frequency'].values,
        left=driving_df['frequency'].iloc[0],
        right=driving_df['frequency'].iloc[-1]
    )
    
    tracking_df['driving_frequency'] = driving_interp
    
    return tracking_df, driving_df


def merge_datasets(tracking_df: pd.DataFrame, driving_df: pd.DataFrame) -> pd.DataFrame:
    """Merge tracking and driving data into a single dataframe."""
    # Assuming sync_timestamps has already been called
    if 'driving_frequency' not in tracking_df.columns:
        tracking_df, driving_df = sync_timestamps(tracking_df, driving_df)
    
    return tracking_df


def handle_missing_frames(df: pd.DataFrame, time_col: str = 'timestamp', tol: float = 0.1) -> pd.DataFrame:
    """
    Handle missing frames via linear interpolation.
    
    Args:
        df: DataFrame with time series data.
        time_col: Name of the timestamp column.
        tol: Tolerance for missing frame detection (seconds).
        
    Returns:
        DataFrame with interpolated values for missing frames.
    """
    if df.empty:
        return df
    
    df = df.sort_values(time_col).reset_index(drop=True)
    
    # Calculate time differences
    dt = df[time_col].diff()
    
    # Identify large gaps
    mask = dt > tol
    
    if mask.any():
        # Interpolate numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        df[numeric_cols] = df[numeric_cols].interpolate(method='linear')
        
    return df


def compute_derivatives(df: pd.DataFrame, pos_cols: List[str], time_col: str = 'timestamp') -> pd.DataFrame:
    """
    Compute velocity and acceleration via finite differences.
    
    Args:
        df: DataFrame with position and time data.
        pos_cols: List of position column names (e.g., ['x', 'y', 'z']).
        time_col: Name of the timestamp column.
        
    Returns:
        DataFrame with added velocity columns (v_x, v_y, v_z).
    """
    df = df.sort_values(time_col).reset_index(drop=True)
    
    for col in pos_cols:
        if col in df.columns:
            # Finite difference for velocity
            df[f'v_{col}'] = df[col].diff() / df[time_col].diff()
            # Fill NaN (first row) with 0 or forward fill
            df[f'v_{col}'] = df[f'v_{col}'].fillna(0)
    
    return df


def check_z_axis_completeness(df: pd.DataFrame) -> bool:
    """Check if z-axis data is present and complete."""
    if 'z' not in df.columns:
        return False
    return df['z'].notna().all()


def calculate_energy_components(df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
    """
    Calculate energy components: E_trans, E_rot, E_pot, E_vib.
    
    E_trans = 0.5 * m * v^2
    E_rot = 0.5 * I * omega^2
    E_pot = m * g * z
    E_vib = derived from high-frequency acceleration variance
    
    Args:
        df: DataFrame with position, velocity, and time data.
        config: Configuration dictionary with material properties.
        
    Returns:
        DataFrame with added energy columns.
    """
    # Assume material is 'steel' for simplicity unless specified
    material = df.get('material', 'steel').iloc[0] if 'material' in df.columns else 'steel'
    
    mass = get_mass(config, material)
    inertia = get_inertia(config, material)
    g = config['constants']['g']
    
    # Translational Energy: 0.5 * m * (vx^2 + vy^2 + vz^2)
    v_cols = [c for c in df.columns if c.startswith('v_')]
    if len(v_cols) >= 2:
        v_sq = 0.0
        for col in v_cols:
            v_sq += df[col] ** 2
        df['E_trans'] = 0.5 * mass * v_sq
    else:
        df['E_trans'] = 0.0
    
    # Rotational Energy: 0.5 * I * omega^2
    # Assume omega is derived from theta changes if present
    if 'theta' in df.columns and 'timestamp' in df.columns:
        omega = df['theta'].diff() / df['timestamp'].diff()
        omega = omega.fillna(0)
        df['E_rot'] = 0.5 * inertia * (omega ** 2)
    else:
        df['E_rot'] = 0.0
    
    # Potential Energy: m * g * z
    if 'z' in df.columns:
        df['E_pot'] = mass * g * df['z']
    else:
        df['E_pot'] = 0.0
    
    # Vibrational Energy: Proxy using variance of acceleration in high freq
    # Simplified: Use variance of velocity as a proxy for vibrational energy
    if len(v_cols) > 0:
        # Calculate acceleration (derivative of velocity)
        acc_sq = 0.0
        for col in v_cols:
            acc = df[col].diff() / df['timestamp'].diff()
            acc = acc.fillna(0)
            acc_sq += acc ** 2
        # E_vib ~ variance of acceleration
        df['E_vib'] = acc_sq * 0.01 # Scaling factor for units
    else:
        df['E_vib'] = 0.0
    
    # Mark if z-axis is incomplete
    df['pot_incomplete'] = ~check_z_axis_completeness(df)
    
    return df


def ingest_data(raw_dir: Path, config_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Main ingestion pipeline: load, sync, process, and calculate energies.
    
    Args:
        raw_dir: Path to raw data directory.
        config_path: Path to config file.
        
    Returns:
        Processed DataFrame with energy components.
    """
    config = load_config(config_path)
    
    # Find CSV files
    tracking_files = [f for f in find_csv_files(raw_dir) if 'tracking' in f.name.lower()]
    driving_files = [f for f in find_csv_files(raw_dir) if 'driving' in f.name.lower()]
    
    if not tracking_files:
        raise IngestionError("No tracking data files found in raw directory.")
    
    # Load first tracking file for demo (in real use, merge all)
    tracking_df = load_tracking_data(tracking_files[0])
    
    if driving_files:
        driving_df = load_driving_data(driving_files[0])
        tracking_df = merge_datasets(tracking_df, driving_df)
    
    # Handle missing frames
    tracking_df = handle_missing_frames(tracking_df)
    
    # Compute derivatives (velocity)
    pos_cols = ['x', 'y', 'z']
    tracking_df = compute_derivatives(tracking_df, pos_cols)
    
    # Calculate energies
    tracking_df = calculate_energy_components(tracking_df, config)
    
    return tracking_df


def main():
    """Simple test runner for ingestion module."""
    try:
        # Create a small synthetic dataset for testing
        data = {
            'particle_id': [1, 1, 1, 2, 2, 2],
            'timestamp': [0.0, 0.1, 0.2, 0.0, 0.1, 0.2],
            'x': [0.0, 0.1, 0.2, 1.0, 1.1, 1.2],
            'y': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            'z': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            'theta': [0.0, 0.1, 0.2, 0.0, 0.1, 0.2]
        }
        df = pd.DataFrame(data)
        
        config = load_config()
        result = calculate_energy_components(df, config)
        
        print("Ingestion test passed.")
        print(result[['particle_id', 'timestamp', 'E_trans', 'E_rot', 'E_pot', 'E_vib']].head())
    except Exception as e:
        print(f"Ingestion Error: {e}")
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
