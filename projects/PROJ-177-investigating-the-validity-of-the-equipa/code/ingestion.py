"""
Data ingestion module for granular system analysis.
Handles loading, parsing, and computing energy components from particle tracking data.
"""
import os
import sys
import json
import logging
import hashlib
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
import pandas as pd
import numpy as np
from itertools import islice

from config import load_config, get_material_properties, get_mass

logger = logging.getLogger(__name__)

class IngestionError(Exception):
    """Custom exception for ingestion errors."""
    pass

def find_csv_files(directory: str) -> List[str]:
    """Find all CSV files in a directory."""
    path = Path(directory)
    return [str(f) for f in path.glob('*.csv')]

def load_tracking_data(file_path: str, sample_ratio: Optional[float] = None, seed: int = 42) -> pd.DataFrame:
    """
    Load particle tracking data from a CSV file.

    Args:
        file_path: Path to the CSV file
        sample_ratio: Optional sampling ratio for large datasets
        seed: Random seed for reproducibility

    Returns:
        DataFrame with tracking data
    """
    logger.info(f"Loading tracking data from {file_path}")

    if not os.path.exists(file_path):
        raise IngestionError(f"Tracking data file not found: {file_path}")

    # Count total rows first
    total_rows = sum(1 for _ in open(file_path)) - 1  # Subtract header
    logger.info(f"Total rows in {file_path}: {total_rows}")

    if sample_ratio and sample_ratio < 1.0:
        # Use fixed seed for reproducibility
        rng = np.random.default_rng(seed)
        # For large files, we sample by skipping lines
        # This is a simplified approach; for very large files, streaming is better
        if total_rows > 1000000:
            logger.warning(f"File has {total_rows} rows, using streaming sample")
            # Stream and sample
            df = pd.read_csv(file_path, skiprows=lambda x: x > 0 and rng.random() > sample_ratio)
        else:
            df = pd.read_csv(file_path)
            if len(df) > 1:
                df = df.sample(frac=sample_ratio, random_state=seed)
    else:
        df = pd.read_csv(file_path)

    logger.info(f"Loaded {len(df)} rows from {file_path}")
    return df

def load_driving_data(file_path: str) -> pd.DataFrame:
    """
    Load driving signal data from a CSV file.

    Args:
        file_path: Path to the CSV file

    Returns:
        DataFrame with driving signal data
    """
    logger.info(f"Loading driving data from {file_path}")

    if not os.path.exists(file_path):
        raise IngestionError(f"Driving data file not found: {file_path}")

    df = pd.read_csv(file_path)
    logger.info(f"Loaded {len(df)} rows from {file_path}")
    return df

def sync_timestamps(tracking_df: pd.DataFrame, driving_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Synchronize tracking and driving data by timestamp.

    Args:
        tracking_df: Particle tracking data
        driving_df: Driving signal data

    Returns:
        Tuple of synchronized DataFrames
    """
    # Ensure timestamp columns exist
    if 'timestamp' not in tracking_df.columns:
        raise IngestionError("Tracking data missing 'timestamp' column")
    if 'timestamp' not in driving_df.columns:
        raise IngestionError("Driving data missing 'timestamp' column")

    # Find common timestamps
    common_ts = set(tracking_df['timestamp']).intersection(set(driving_df['timestamp']))
    logger.info(f"Found {len(common_ts)} common timestamps")

    if len(common_ts) == 0:
        raise IngestionError("No common timestamps between tracking and driving data")

    # Filter both DataFrames
    tracking_synced = tracking_df[tracking_df['timestamp'].isin(common_ts)].reset_index(drop=True)
    driving_synced = driving_df[driving_df['timestamp'].isin(common_ts)].reset_index(drop=True)

    # Sort by timestamp
    tracking_synced = tracking_synced.sort_values('timestamp').reset_index(drop=True)
    driving_synced = driving_synced.sort_values('timestamp').reset_index(drop=True)

    return tracking_synced, driving_synced

def handle_missing_frames(df: pd.DataFrame, max_gap: int = 5) -> pd.DataFrame:
    """
    Handle missing frames via linear interpolation or flagging.

    Args:
        df: DataFrame with time series data
        max_gap: Maximum allowed gap for interpolation

    Returns:
        DataFrame with interpolated values or flagged gaps
    """
    # Check for gaps in timestamp sequence
    df = df.sort_values('timestamp').reset_index(drop=True)
    time_diff = df['timestamp'].diff()
    expected_dt = time_diff.median()

    # Identify gaps
    gap_mask = time_diff > (expected_dt * 2)  # Gap is more than 2x expected
    gap_indices = df[gap_mask].index.tolist()

    if len(gap_indices) > 0:
        logger.warning(f"Detected {len(gap_indices)} missing frame gaps")

    # Interpolate numeric columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        if col != 'timestamp':
            df[col] = df[col].interpolate(method='linear', limit=max_gap)

    return df

def check_z_axis_completeness(df: pd.DataFrame) -> Dict[int, bool]:
    """
    Check if z-axis data is complete for each particle.

    Args:
        df: DataFrame with particle data

    Returns:
        Dictionary mapping particle_id to z-axis completeness (True if complete)
    """
    z_completeness = {}

    if 'z' not in df.columns:
        logger.warning("No 'z' column found in data")
        # If no z column, all particles have incomplete z-axis
        particle_ids = df['particle_id'].unique() if 'particle_id' in df.columns else []
        for pid in particle_ids:
            z_completeness[pid] = False
        return z_completeness

    for pid in df['particle_id'].unique():
        particle_data = df[df['particle_id'] == pid]
        # Check if z values are all NaN
        if particle_data['z'].isna().all():
            z_completeness[pid] = False
        else:
            z_completeness[pid] = True

    return z_completeness

def compute_derivatives(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute velocity and angular velocity via finite differences.

    Args:
        df: DataFrame with position and orientation data

    Returns:
        DataFrame with added velocity and angular velocity columns
    """
    df = df.sort_values(['particle_id', 'timestamp']).reset_index(drop=True)

    # Compute velocity (dx/dt, dy/dt, dz/dt)
    for pid in df['particle_id'].unique():
        mask = df['particle_id'] == pid
        pid_data = df.loc[mask].copy()

        # Time differences
        dt = pid_data['timestamp'].diff().fillna(0.001)  # Avoid division by zero

        # Position derivatives
        if 'x' in pid_data.columns:
            pid_data['vx'] = pid_data['x'].diff().fillna(0) / dt
        if 'y' in pid_data.columns:
            pid_data['vy'] = pid_data['y'].diff().fillna(0) / dt
        if 'z' in pid_data.columns:
            pid_data['vz'] = pid_data['z'].diff().fillna(0) / dt

        # Angular velocity (dtheta/dt)
        if 'theta' in pid_data.columns:
            pid_data['omega'] = pid_data['theta'].diff().fillna(0) / dt

        # Update main dataframe
        df.loc[mask] = pid_data

    # Compute acceleration for vibrational energy
    for pid in df['particle_id'].unique():
        mask = df['particle_id'] == pid
        pid_data = df.loc[mask].copy()

        dt = pid_data['timestamp'].diff().fillna(0.001)

        if 'vx' in pid_data.columns:
            pid_data['ax'] = pid_data['vx'].diff().fillna(0) / dt
        if 'vy' in pid_data.columns:
            pid_data['ay'] = pid_data['vy'].diff().fillna(0) / dt
        if 'vz' in pid_data.columns:
            pid_data['az'] = pid_data['vz'].diff().fillna(0) / dt

        df.loc[mask] = pid_data

    return df

def calculate_energy_components(df: pd.DataFrame, config_path: str) -> pd.DataFrame:
    """
    Calculate energy components: E_trans, E_rot, E_pot, E_vib.

    Args:
        df: DataFrame with kinematic data
        config_path: Path to configuration file

    Returns:
        DataFrame with energy components
    """
    config = load_config(config_path)

    # Initialize energy columns
    df['E_trans'] = 0.0
    df['E_rot'] = 0.0
    df['E_pot'] = 0.0
    df['E_vib'] = 0.0

    # Get material properties
    for pid in df['particle_id'].unique():
        mask = df['particle_id'] == pid
        pid_data = df.loc[mask].copy()

        # Get mass for this particle (from config or default)
        mass = get_mass(config, pid_data['material_type'].iloc[0] if 'material_type' in pid_data.columns else 'default')

        # Translational kinetic energy: E_trans = 0.5 * m * v^2
        if 'vx' in pid_data.columns and 'vy' in pid_data.columns:
            v_squared = pid_data['vx']**2 + pid_data['vy']**2
            if 'vz' in pid_data.columns:
                v_squared += pid_data['vz']**2
            pid_data['E_trans'] = 0.5 * mass * v_squared

        # Rotational kinetic energy: E_rot = 0.5 * I * omega^2
        # Assume moment of inertia I = 0.5 * m * r^2 (solid sphere)
        if 'omega' in pid_data.columns:
            # Default radius if not specified
            radius = 0.005  # 5mm default
            if 'radius' in config.get('materials', {}).get(pid_data['material_type'].iloc[0] if 'material_type' in pid_data.columns else 'default', {}):
                radius = config['materials'][pid_data['material_type'].iloc[0] if 'material_type' in pid_data.columns else 'default']['radius']
            I = 0.5 * mass * radius**2
            pid_data['E_rot'] = 0.5 * I * pid_data['omega']**2

        # Potential energy: E_pot = m * g * h
        # Assume g = 9.81 m/s^2, h = z position
        g = 9.81
        if 'z' in pid_data.columns:
            pid_data['E_pot'] = mass * g * pid_data['z'].fillna(0)

        # Vibrational energy: E_vib = variance of acceleration over sliding window (N=5)
        if 'ax' in pid_data.columns and 'ay' in pid_data.columns:
            window_size = 5
            a_squared = pid_data['ax']**2 + pid_data['ay']**2
            if 'az' in pid_data.columns:
                a_squared += pid_data['az']**2

            # Rolling variance
            pid_data['E_vib'] = a_squared.rolling(window=window_size, min_periods=1).var()

        df.loc[mask] = pid_data

    return df

def write_energy_output(df: pd.DataFrame, output_path: str, z_completeness: Dict[int, bool]):
    """
    Write energy output to CSV and generate hash.

    Args:
        df: DataFrame with energy components
        output_path: Output file path
        z_completeness: Dictionary of z-axis completeness per particle
    """
    # Ensure required columns exist
    required_cols = ['particle_id', 'timestamp', 'E_trans', 'E_rot', 'E_pot', 'E_vib']
    for col in required_cols:
        if col not in df.columns:
            logger.warning(f"Column {col} not found in output")
            df[col] = 0.0

    # Add pot_incomplete column
    df['pot_incomplete'] = df['particle_id'].map(lambda pid: not z_completeness.get(pid, True))

    # Log warnings for particles with incomplete z-axis
    for pid, incomplete in z_completeness.items():
        if not incomplete:
            logger.warning(f"WARNING: Missing z-axis data for particle {pid}")

    # Select and order columns
    output_cols = ['particle_id', 'timestamp', 'E_trans', 'E_rot', 'E_pot', 'E_vib', 'pot_incomplete']
    output_df = df[[col for col in output_cols if col in df.columns]]

    # Write to CSV
    output_df.to_csv(output_path, index=False)
    logger.info(f"Written energy output to {output_path}")

    # Generate SHA-256 hash
    with open(output_path, 'rb') as f:
        file_hash = hashlib.sha256(f.read()).hexdigest()

    # Write hash file
    hash_path = str(Path(output_path).parent / 'energy_samples.hash')
    with open(hash_path, 'w') as f:
        f.write(file_hash)
    logger.info(f"Written hash to {hash_path}")

    # Verify schema
    expected_schema = {
        'particle_id': 'int64',
        'timestamp': 'float64',
        'E_trans': 'float64',
        'E_rot': 'float64',
        'E_pot': 'float64',
        'E_vib': 'float64',
        'pot_incomplete': 'bool'
    }

    schema_valid = True
    for col, expected_type in expected_schema.items():
        if col in output_df.columns:
            if str(output_df[col].dtype) != expected_type:
                logger.warning(f"Column {col} has dtype {output_df[col].dtype}, expected {expected_type}")
                schema_valid = False
        else:
            logger.warning(f"Missing column in output: {col}")
            schema_valid = False

    if schema_valid:
        logger.info("Schema validation passed")
    else:
        logger.warning("Schema validation failed - check column types")

def ingest_data(data_source: str, config_path: str, sample_ratio: Optional[float] = None, local_only: bool = False):
    """
    Main ingestion function.

    Args:
        data_source: Data source path or identifier
        config_path: Path to configuration file
        sample_ratio: Optional sampling ratio
        local_only: If True, only use local data
    """
    logger.info(f"Starting ingestion from {data_source}")

    # Find data files
    tracking_files = find_csv_files(data_source)
    if not tracking_files:
        raise IngestionError(f"No tracking data found in {data_source}")

    # Load tracking data
    tracking_df = load_tracking_data(tracking_files[0], sample_ratio=sample_ratio)

    # Validate metadata (check for required fields)
    required_fields = ['particle_id', 'timestamp', 'x', 'y']
    missing_fields = [f for f in required_fields if f not in tracking_df.columns]
    if missing_fields:
        raise IngestionError(f"Missing required metadata fields: {missing_fields}")

    # Check z-axis completeness
    z_completeness = check_z_axis_completeness(tracking_df)

    # Handle missing frames
    tracking_df = handle_missing_frames(tracking_df)

    # Compute derivatives (velocity, acceleration)
    tracking_df = compute_derivatives(tracking_df)

    # Calculate energy components
    tracking_df = calculate_energy_components(tracking_df, config_path)

    # Write output
    output_path = 'data/derived/energy_samples.csv'
    write_energy_output(tracking_df, output_path, z_completeness)

    logger.info("Ingestion completed successfully")

def main():
    """Main entry point for ingestion script."""
    parser = argparse.ArgumentParser(description='Ingest granular system data')
    parser.add_argument('--config', type=str, default='data/config.yaml', help='Config file path')
    parser.add_argument('--data-source', type=str, default='data/raw', help='Data source path')
    parser.add_argument('--sample-ratio', type=float, default=None, help='Sampling ratio')
    parser.add_argument('--local-only', action='store_true', help='Local only mode')

    args = parser.parse_args()

    try:
        ingest_data(args.data_source, args.config, args.sample_ratio, args.local_only)
    except IngestionError as e:
        logger.error(f"Ingestion failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()