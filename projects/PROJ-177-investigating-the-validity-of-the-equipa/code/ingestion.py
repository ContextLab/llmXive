import os
import sys
import json
import logging
import hashlib
import argparse
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
from config import load_config, get_material_properties, get_frequency_bins
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class IngestionError(Exception):
    """Custom exception for ingestion errors."""
    pass

class DataExclusionWarning(Warning):
    """Custom warning for data exclusion."""
    pass

def load_driving_data(data_path: str) -> pd.DataFrame:
    """Load driving signal logs."""
    if not os.path.exists(data_path):
        raise IngestionError(f"Driving data file not found: {data_path}")
    df = pd.read_csv(data_path)
    logger.info(f"Loaded driving data with {len(df)} rows")
    return df

def write_driving_signals(df: pd.DataFrame, output_path: str):
    """Write driving signals to CSV."""
    df.to_csv(output_path, index=False)
    logger.info(f"Wrote driving signals to {output_path}")

def load_particle_tracking_data(data_path: str) -> pd.DataFrame:
    """Load particle tracking CSV."""
    if not os.path.exists(data_path):
        raise IngestionError(f"Particle tracking data file not found: {data_path}")
    df = pd.read_csv(data_path)
    logger.info(f"Loaded particle tracking data with {len(df)} rows")
    return df

def sync_particle_and_driving_data(particle_df: pd.DataFrame, driving_df: pd.DataFrame) -> pd.DataFrame:
    """Sync particle tracking with driving signals by timestamp."""
    # Assuming both have 'timestamp' column
    merged = pd.merge(particle_df, driving_df, on='timestamp', how='inner')
    logger.info(f"Synchronized data: {len(merged)} rows")
    return merged

def handle_missing_frames_linear_interpolation(df: pd.DataFrame, time_col: str = 'timestamp') -> pd.DataFrame:
    """Handle missing frames via linear interpolation."""
    df_sorted = df.sort_values(by=time_col)
    df_interp = df_sorted.interpolate(method='linear')
    return df_interp

def calculate_tracking_failure_rate(df: pd.DataFrame, window_size: int = 100) -> float:
    """Calculate percentage of missing frames per time window."""
    total_rows = len(df)
    if total_rows == 0:
        return 0.0
    # Placeholder logic: count gaps in timestamp sequence
    # In real implementation, compare against expected frame rate
    return 0.0

def compute_velocities_angular_velocities(df: pd.DataFrame) -> pd.DataFrame:
    """Compute v and omega via finite differences."""
    df = df.copy()
    # Compute translational velocity (v)
    if 'x' in df.columns and 'y' in df.columns:
        df['dx'] = df['x'].diff()
        df['dy'] = df['y'].diff()
        df['v'] = np.sqrt(df['dx']**2 + df['dy']**2) / df['timestamp'].diff()
    # Compute angular velocity (omega) from orientation if available
    if 'theta' in df.columns:
        df['omega'] = df['theta'].diff() / df['timestamp'].diff()
    else:
        df['omega'] = 0.0
    return df

def compute_energy(df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
    """
    Compute E_trans, E_rot, E_pot, and E_vib.
    E_vib uses provisional formula: E_vib = m * var(a) * (dt)^2
    """
    df = df.copy()
    mass = config.get('mass', 1.0)
    inertia = config.get('inertia', 1.0)
    
    # Translational Energy: E_trans = 0.5 * m * v^2
    if 'v' in df.columns:
        df['E_trans'] = 0.5 * mass * df['v']**2
    else:
        df['E_trans'] = 0.0

    # Rotational Energy: E_rot = 0.5 * I * omega^2
    if 'omega' in df.columns:
        df['E_rot'] = 0.5 * inertia * df['omega']**2
    else:
        df['E_rot'] = 0.0

    # Potential Energy: E_pot = m * g * h (assuming g=9.81, h from z if available)
    g = 9.81
    if 'z' in df.columns:
        df['E_pot'] = mass * g * df['z']
        df['pot_incomplete'] = False
    else:
        df['E_pot'] = np.nan
        df['pot_incomplete'] = True
        logger.warning("Missing z-axis data; E_pot set to NaN and pot_incomplete=True")

    # Vibrational Energy: E_vib = m * var(a) * (dt)^2
    # Compute acceleration a from v (finite difference)
    if 'v' in df.columns:
        df['a'] = df['v'].diff() / df['timestamp'].diff()
        # Calculate variance of acceleration within a window (simplified: global variance for now)
        var_a = df['a'].var()
        if pd.isna(var_a):
            var_a = 0.0
        # dt is the time step (average)
        dt = df['timestamp'].diff().mean()
        if pd.isna(dt) or dt == 0:
            dt = 1.0
        df['E_vib'] = mass * var_a * (dt**2)
    else:
        df['E_vib'] = 0.0

    # Ensure E_vib units are Joules: kg * (m/s^2)^2 * s^2 = kg * m^2/s^2 = J
    # Verification: mass (kg) * var(a) ((m/s^2)^2) * dt^2 (s^2) = kg * m^2/s^2 = J
    
    return df

def main():
    parser = argparse.ArgumentParser(description='Ingest and process granular data for energy calculation.')
    parser.add_argument('--config', type=str, default='data/config.yaml', help='Path to config file')
    parser.add_argument('--data-source', type=str, required=True, help='Path to input particle tracking data')
    parser.add_argument('--output-dir', type=str, default='data/derived', help='Output directory')
    parser.add_argument('--sample-ratio', type=float, default=1.0, help='Sample ratio for downsampling')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Load config
    config = load_config(args.config)
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Load data
    logger.info(f"Loading data from {args.data_source}")
    particle_df = load_particle_tracking_data(args.data_source)
    
    # Apply sampling if needed
    if args.sample_ratio < 1.0:
        sample_size = int(len(particle_df) * args.sample_ratio)
        particle_df = particle_df.sample(n=sample_size, random_state=42)
        logger.info(f"Sampled data to {sample_size} rows")
    
    # Sync with driving data (assuming driving data path is in config or default)
    driving_path = config.get('driving_data_path', 'data/raw/driving_signals.csv')
    if os.path.exists(driving_path):
        driving_df = load_driving_data(driving_path)
        particle_df = sync_particle_and_driving_data(particle_df, driving_df)
    else:
        logger.warning(f"Driving data not found at {driving_path}; proceeding without sync")
    
    # Handle missing frames
    particle_df = handle_missing_frames_linear_interpolation(particle_df)
    
    # Compute velocities
    particle_df = compute_velocities_angular_velocities(particle_df)
    
    # Compute energy
    energy_df = compute_energy(particle_df, config)
    
    # Select output columns
    output_cols = ['particle_id', 'timestamp', 'E_trans', 'E_rot', 'E_pot', 'E_vib', 'pot_incomplete']
    # Ensure all columns exist
    for col in output_cols:
        if col not in energy_df.columns:
            energy_df[col] = np.nan if col == 'pot_incomplete' else 0.0
    
    final_df = energy_df[output_cols]
    
    # Write output
    output_path = os.path.join(args.output_dir, 'energy_samples.csv')
    final_df.to_csv(output_path, index=False)
    logger.info(f"Wrote energy samples to {output_path}")
    
    # Record sampling metadata
    metadata = {
        'random_seed': 42,
        'sampling_rule': f"sample_ratio={args.sample_ratio}",
        'row_count': len(final_df),
        'timestamp': datetime.now().isoformat()
    }
    metadata_path = 'artifacts/sampling_metadata.json'
    os.makedirs('artifacts', exist_ok=True)
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Wrote sampling metadata to {metadata_path}")
    
    # Compute SHA-256 hash of the CSV
    sha256_hash = hashlib.sha256()
    with open(output_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    hash_value = sha256_hash.hexdigest()
    
    hash_path = 'artifacts/energy_samples.hash'
    with open(hash_path, 'w') as f:
        f.write(hash_value)
    logger.info(f"Wrote SHA-256 hash to {hash_path}: {hash_value}")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
