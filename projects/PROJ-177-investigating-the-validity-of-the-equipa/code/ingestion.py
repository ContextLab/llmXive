"""
Data ingestion module for granular system particle tracking and driving signals.
Handles loading, syncing, interpolation, and energy calculation.
"""
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import numpy as np
import logging
from config import load_config, get_material_properties

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IngestionError(Exception):
    """Custom exception for ingestion errors."""
    pass

def find_csv_files(directory: str) -> List[Path]:
    """Find all CSV files in a directory."""
    path = Path(directory)
    if not path.exists():
        raise IngestionError(f"Directory not found: {directory}")
    return list(path.glob("*.csv"))

def load_tracking_data(file_paths: List[Path]) -> pd.DataFrame:
    """Load and concatenate particle tracking CSVs."""
    dfs = []
    for fp in file_paths:
        try:
            df = pd.read_csv(fp)
            dfs.append(df)
        except Exception as e:
            logger.warning(f"Failed to load {fp}: {e}")
    if not dfs:
        raise IngestionError("No valid tracking data files found.")
    return pd.concat(dfs, ignore_index=True)

def load_driving_data(file_paths: List[Path]) -> pd.DataFrame:
    """Load driving signal logs."""
    dfs = []
    for fp in file_paths:
        try:
            df = pd.read_csv(fp)
            dfs.append(df)
        except Exception as e:
            logger.warning(f"Failed to load driving data {fp}: {e}")
    if not dfs:
        raise IngestionError("No valid driving data files found.")
    return pd.concat(dfs, ignore_index=True)

def sync_timestamps(tracking_df: pd.DataFrame, driving_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Sync tracking and driving data to common timestamps."""
    # Assume 'timestamp' column exists in both
    if 'timestamp' not in tracking_df.columns or 'timestamp' not in driving_df.columns:
        raise IngestionError("Missing 'timestamp' column in data.")

    # Merge on timestamp
    # We'll do a left join from tracking to driving to keep all tracking points
    merged = tracking_df.merge(driving_df, on='timestamp', how='left')
    return merged, driving_df

def handle_missing_frames(df: pd.DataFrame, time_col: str = 'timestamp') -> pd.DataFrame:
    """Handle missing frames via linear interpolation."""
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        if col != time_col:
            df[col] = df[col].interpolate(method='linear', limit_direction='both')
    return df

def compute_derivatives(df: pd.DataFrame, time_col: str = 'timestamp') -> pd.DataFrame:
    """Compute velocity and angular velocity via finite differences."""
    if 'x' not in df.columns or 'y' not in df.columns or 'z' not in df.columns:
        raise IngestionError("Missing position columns (x, y, z).")

    dt = df[time_col].diff().mean()
    if dt == 0:
        raise IngestionError("Time step is zero or undefined.")

    # Velocity
    df['vx'] = df['x'].diff() / dt
    df['vy'] = df['y'].diff() / dt
    df['vz'] = df['z'].diff() / dt
    df['v'] = np.sqrt(df['vx']**2 + df['vy']**2 + df['vz']**2)

    # Angular velocity (assuming theta is present)
    if 'theta' in df.columns:
        df['omega'] = df['theta'].diff() / dt
    else:
        df['omega'] = 0.0

    return df

def check_z_axis_completeness(df: pd.DataFrame) -> pd.DataFrame:
    """Check for missing z-axis data and flag."""
    df['pot_incomplete'] = df['z'].isna()
    # Log warnings for particles with missing z
    missing_z_ids = df[df['pot_incomplete']]['particle_id'].unique()
    for pid in missing_z_ids:
        logger.warning(f"WARNING: Missing z-axis data for particle {pid}")
    return df

def calculate_energy_components(df: pd.DataFrame, config_path: str) -> pd.DataFrame:
    """Calculate E_trans, E_rot, E_pot, E_vib."""
    config = load_config(config_path)
    mass = get_material_properties(config, df['material_type'].iloc[0])['mass']
    inertia = get_material_properties(config, df['material_type'].iloc[0])['inertia']

    # E_trans = 0.5 * m * v^2
    df['E_trans'] = 0.5 * mass * df['v']**2

    # E_rot = 0.5 * I * omega^2
    df['E_rot'] = 0.5 * inertia * df['omega']**2

    # E_pot = m * g * z (assuming g=9.81)
    g = 9.81
    df['E_pot'] = mass * g * df['z'].fillna(0)

    # E_vib = variance of acceleration over sliding window of N=5
    # Acceleration = derivative of velocity
    # We need to compute acceleration first
    df['ax'] = df['vx'].diff()
    df['ay'] = df['vy'].diff()
    df['az'] = df['vz'].diff()
    df['a'] = np.sqrt(df['ax']**2 + df['ay']**2 + df['az']**2)

    # Sliding window variance
    window_size = 5
    df['E_vib'] = df['a'].rolling(window=window_size, min_periods=1).var()

    return df

def ingest_data(
    tracking_dir: str,
    driving_dir: str,
    config_path: str,
    output_path: str,
    sample_ratio: float = 1.0
) -> None:
    """Main ingestion pipeline."""
    logger.info(f"Ingesting data from {tracking_dir} and {driving_dir}")

    # Find files
    tracking_files = find_csv_files(tracking_dir)
    driving_files = find_csv_files(driving_dir)

    # Load data
    tracking_df = load_tracking_data(tracking_files)
    driving_df = load_driving_data(driving_files)

    # Sample if needed
    if sample_ratio < 1.0:
        n_samples = int(len(tracking_df) * sample_ratio)
        tracking_df = tracking_df.sample(n=n_samples, random_state=42)
        logger.info(f"Sampled data to {n_samples} rows ({sample_ratio*100}%)")

    # Sync
    merged_df, _ = sync_timestamps(tracking_df, driving_df)

    # Handle missing frames
    merged_df = handle_missing_frames(merged_df)

    # Compute derivatives
    merged_df = compute_derivatives(merged_df)

    # Check z-axis
    merged_df = check_z_axis_completeness(merged_df)

    # Calculate energies
    merged_df = calculate_energy_components(merged_df, config_path)

    # Select output columns
    output_cols = ['particle_id', 'timestamp', 'E_trans', 'E_rot', 'E_pot', 'E_vib', 'pot_incomplete', 'material_type', 'frequency']
    # Ensure columns exist
    available_cols = [c for c in output_cols if c in merged_df.columns]
    output_df = merged_df[available_cols]

    # Write output
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    output_df.to_csv(output_path, index=False)
    logger.info(f"Wrote energy samples to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Ingest granular particle tracking data.")
    parser.add_argument("--input", type=str, default="data/raw", help="Directory containing tracking CSVs.")
    parser.add_argument("--driving-input", type=str, default="data/raw", help="Directory containing driving logs.")
    parser.add_argument("--config", type=str, default="data/config.yaml", help="Path to config file.")
    parser.add_argument("--output", type=str, default="data/derived/energy_samples.csv", help="Output CSV path.")
    parser.add_argument("--sample-ratio", type=float, default=1.0, help="Sampling ratio.")
    args = parser.parse_args()

    ingest_data(args.input, args.driving_input, args.config, args.output, args.sample_ratio)

if __name__ == "__main__":
    main()
