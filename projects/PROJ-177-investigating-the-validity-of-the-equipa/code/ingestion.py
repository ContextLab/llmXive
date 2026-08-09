"""
Ingestion module for granular system data processing.
Handles loading, syncing, and energy calculation for particle tracking data.
"""
import os
import sys
import json
import logging
import hashlib
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional, Union
import pandas as pd
import numpy as np
from scipy import signal

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class IngestionError(Exception):
    """Custom exception for ingestion errors."""
    pass

class DataExclusionWarning(UserWarning):
    """Warning for data exclusion events."""
    pass

def load_driving_data(data_path: str) -> pd.DataFrame:
    """Load driving signal logs."""
    path = Path(data_path)
    if not path.exists():
        raise FileNotFoundError(f"Driving data file not found: {data_path}")
    
    # Try to infer format
    if path.suffix == '.csv':
        df = pd.read_csv(path)
    elif path.suffix == '.json':
        with open(path, 'r') as f:
            data = json.load(f)
            df = pd.DataFrame(data)
    else:
        raise IngestionError(f"Unsupported file format: {path.suffix}")
    
    logger.info(f"Loaded driving data with {len(df)} rows from {data_path}")
    return df

def write_driving_signals(df: pd.DataFrame, output_path: str) -> None:
    """Write driving signals to CSV."""
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output, index=False)
    logger.info(f"Wrote driving signals to {output_path}")

def load_particle_tracking_data(data_path: str) -> pd.DataFrame:
    """Load particle tracking CSVs."""
    path = Path(data_path)
    if not path.exists():
        raise FileNotFoundError(f"Particle tracking data file not found: {data_path}")
    
    df = pd.read_csv(path)
    logger.info(f"Loaded particle tracking data with {len(df)} rows from {data_path}")
    return df

def sync_particle_and_driving_data(
    particle_df: pd.DataFrame, 
    driving_df: pd.DataFrame, 
    time_col: str = 'timestamp'
) -> pd.DataFrame:
    """Synchronize particle tracking with driving signals by timestamp."""
    # Merge on timestamp
    merged = pd.merge(
        particle_df, 
        driving_df, 
        on=time_col, 
        how='left', 
        suffixes=('', '_driving')
    )
    logger.info(f"Synchronized data: {len(merged)} rows")
    return merged

def handle_missing_frames_linear_interpolation(
    df: pd.DataFrame, 
    time_col: str = 'timestamp',
    threshold: int = 10
) -> pd.DataFrame:
    """Handle missing frames via linear interpolation."""
    df = df.sort_values(time_col)
    df['gap_flag'] = False
    
    # Calculate time deltas
    time_diffs = df[time_col].diff().dt.total_seconds()
    mean_dt = time_diffs.mean()
    
    # Identify gaps
    gap_mask = time_diffs > (threshold * mean_dt)
    df.loc[gap_mask, 'gap_flag'] = True
    
    if gap_mask.any():
        logger.warning(f"Detected {gap_mask.sum()} frames with gaps exceeding threshold")
    
    # Interpolate numeric columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    df[numeric_cols] = df[numeric_cols].interpolate(method='linear')
    
    return df

def calculate_tracking_failure_rate(
    df: pd.DataFrame, 
    time_col: str = 'timestamp',
    window_size: int = 100
) -> pd.DataFrame:
    """Calculate percentage of missing frames per time window."""
    df = df.sort_values(time_col)
    
    # Calculate expected vs actual frames in windows
    df['window_id'] = (df[time_col].cumsum() / window_size).astype(int)
    
    failure_rates = df.groupby('window_id').apply(
        lambda x: x['gap_flag'].sum() / len(x) if len(x) > 0 else 0
    )
    
    df['failure_rate'] = df['window_id'].map(failure_rates)
    df['exclude_window'] = df['failure_rate'] > 0.20
    
    logger.info(f"Calculated tracking failure rates for {df['window_id'].nunique()} windows")
    return df

def compute_velocities_angular_velocities(
    df: pd.DataFrame,
    time_col: str = 'timestamp',
    pos_cols: List[str] = None,
    angle_cols: List[str] = None
) -> pd.DataFrame:
    """Compute velocities and angular velocities via finite differences."""
    if pos_cols is None:
        pos_cols = ['x', 'y', 'z']
    if angle_cols is None:
        angle_cols = ['theta']
    
    df = df.sort_values(time_col).reset_index(drop=True)
    
    # Compute time deltas
    dt = df[time_col].diff().dt.total_seconds().fillna(0.0).values
    dt = np.where(dt == 0, 1e-6, dt)  # Avoid division by zero
    
    # Compute linear velocities
    for col in pos_cols:
        if col in df.columns:
            df[f'v_{col}'] = df[col].diff().values / dt
        else:
            logger.warning(f"Position column {col} not found, skipping velocity calculation")
    
    # Compute angular velocities
    for col in angle_cols:
        if col in df.columns:
            df[f'omega_{col}'] = df[col].diff().values / dt
        else:
            logger.warning(f"Angle column {col} not found, skipping angular velocity calculation")
    
    return df

def compute_energy(
    df: pd.DataFrame,
    mass: float,
    inertia: float,
    g: float = 9.81,
    window_size: int = 100
) -> pd.DataFrame:
    """
    Compute energy components: E_trans, E_rot, E_pot, E_vib.
    
    Formulas:
    - E_trans = 0.5 * m * v^2 (where v^2 = vx^2 + vy^2 + vz^2)
    - E_rot = 0.5 * I * omega^2
    - E_pot = m * g * z
    - E_vib = m * var(a) * (dt)^2 (Provisional formula from T018b)
    
    Units: All energies in Joules.
    """
    df = df.copy()
    
    # Ensure numeric types
    for col in df.columns:
        if df[col].dtype == 'object':
            try:
                df[col] = pd.to_numeric(df[col])
            except ValueError:
                pass
    
    # Calculate translational energy
    v_sq = 0.0
    v_cols = [c for c in df.columns if c.startswith('v_')]
    if v_cols:
        for v_col in v_cols:
            v_sq += df[v_col]**2
        df['E_trans'] = 0.5 * mass * v_sq
    else:
        df['E_trans'] = np.nan
        logger.warning("No velocity columns found for E_trans calculation")
    
    # Calculate rotational energy
    omega_sq = 0.0
    omega_cols = [c for c in df.columns if c.startswith('omega_')]
    if omega_cols:
        for omega_col in omega_cols:
            omega_sq += df[omega_col]**2
        df['E_rot'] = 0.5 * inertia * omega_sq
    else:
        df['E_rot'] = np.nan
        logger.warning("No angular velocity columns found for E_rot calculation")
    
    # Calculate potential energy
    if 'z' in df.columns:
        df['E_pot'] = mass * g * df['z']
    else:
        df['E_pot'] = np.nan
        df['pot_incomplete'] = True
        logger.warning("No z-axis data found, E_pot set to NaN and pot_incomplete=True")
    
    # Calculate vibrational energy using provisional formula: E_vib = m * var(a) * (dt)^2
    # First, compute acceleration (a = dv/dt)
    dt = df['timestamp'].diff().dt.total_seconds().fillna(0.0).values
    dt = np.where(dt == 0, 1e-6, dt)  # Avoid division by zero
    
    a_sq = 0.0
    v_cols = [c for c in df.columns if c.startswith('v_')]
    if v_cols:
        # Compute acceleration for each velocity component
        a_cols = []
        for v_col in v_cols:
            a_col = f'a_{v_col[2:]}'  # e.g., v_x -> a_x
            df[a_col] = df[v_col].diff().values / dt
            a_cols.append(a_col)
        
        # Sum of squared accelerations
        for a_col in a_cols:
            if a_col in df.columns:
                a_sq += df[a_col]**2
        
        # Compute variance of acceleration over a window
        # Use rolling variance for local acceleration variance
        df['a_sq'] = a_sq
        
        # Apply rolling variance with window_size
        # Handle edge cases where window_size > data length
        actual_window = min(window_size, len(df))
        if actual_window > 1:
            var_a = df['a_sq'].rolling(window=actual_window, min_periods=1).var()
            # E_vib = m * var(a) * (dt)^2
            # dt here is the time step for the variance calculation
            # Using mean dt for the (dt)^2 factor as per the formula interpretation
            mean_dt = np.mean(dt)
            df['E_vib'] = mass * var_a * (mean_dt ** 2)
        else:
            df['E_vib'] = np.nan
            logger.warning(f"Window size {window_size} too large for data length {len(df)}, E_vib set to NaN")
    else:
        df['E_vib'] = np.nan
        logger.warning("No velocity columns found for E_vib calculation")
    
    # Verify E_vib units and values
    if 'E_vib' in df.columns:
        non_zero_vib = df['E_vib'].dropna()
        if len(non_zero_vib) > 0:
            if (non_zero_vib <= 0).any():
                logger.warning(f"Found {((non_zero_vib <= 0).sum())} non-positive E_vib values")
            else:
                logger.info(f"E_vib calculated successfully: mean={non_zero_vib.mean():.6e}, min={non_zero_vib.min():.6e}, max={non_zero_vib.max():.6e} J")
        else:
            logger.warning("All E_vib values are NaN or zero")
    
    # Handle incomplete potential energy flag
    if 'pot_incomplete' not in df.columns:
        df['pot_incomplete'] = False
    
    return df

def main():
    """Main entry point for ingestion pipeline."""
    parser = argparse.ArgumentParser(description='Granular System Data Ingestion')
    parser.add_argument('--config', type=str, default='data/config.yaml', help='Path to config file')
    parser.add_argument('--data-source', type=str, help='Path to data source')
    parser.add_argument('--output-dir', type=str, default='data/derived', help='Output directory')
    parser.add_argument('--sample-ratio', type=float, default=1.0, help='Sampling ratio for large datasets')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    logger.info("Starting ingestion pipeline")
    
    # Load configuration
    config_path = Path(args.config)
    if not config_path.exists():
        logger.warning(f"Config file not found: {config_path}. Using defaults.")
        config = {'mass': 0.01, 'inertia': 0.0001, 'window_size': 100}
    else:
        import yaml
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
    
    mass = config.get('mass', 0.01)
    inertia = config.get('inertia', 0.0001)
    window_size = config.get('window_size', 100)
    
    # Process data
    if args.data_source:
        try:
            # Load driving data
            driving_df = load_driving_data(args.data_source)
            write_driving_signals(driving_df, os.path.join(args.output_dir, 'driving_signals.csv'))
            
            # Load and process particle tracking (assuming same source for simplicity)
            particle_df = load_particle_tracking_data(args.data_source)
            
            # Sync data
            synced_df = sync_particle_and_driving_data(particle_df, driving_df)
            
            # Handle missing frames
            synced_df = handle_missing_frames_linear_interpolation(synced_df)
            
            # Calculate failure rates
            synced_df = calculate_tracking_failure_rate(synced_df)
            
            # Compute velocities
            synced_df = compute_velocities_angular_velocities(synced_df)
            
            # Compute energies
            energy_df = compute_energy(synced_df, mass, inertia, window_size=window_size)
            
            # Write output
            output_path = os.path.join(args.output_dir, 'energy_samples.csv')
            Path(args.output_dir).mkdir(parents=True, exist_ok=True)
            energy_df.to_csv(output_path, index=False)
            logger.info(f"Energy calculations saved to {output_path}")
            
        except Exception as e:
            logger.error(f"Error during ingestion: {e}")
            raise
    else:
        logger.warning("No data source provided. Use --data-source to specify input.")

if __name__ == '__main__':
    main()
