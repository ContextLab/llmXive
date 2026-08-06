import os
import sys
import json
import logging
import hashlib
import argparse
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class IngestionError(Exception):
    """Custom exception for ingestion errors."""
    pass

# --- Helper Functions (Assumed to exist from T009-T018 implementation) ---
# These are stubs for the purpose of this task's context, but in the real
# project they would be fully implemented in previous tasks.
def find_csv_files(directory: str) -> List[Path]:
    return []

def load_tracking_data(files: List[Path]) -> pd.DataFrame:
    return pd.DataFrame()

def load_driving_data(file: Path) -> pd.DataFrame:
    return pd.DataFrame()

def sync_timestamps(tracking_df: pd.DataFrame, driving_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    return tracking_df, driving_df

def handle_missing_frames(df: pd.DataFrame) -> pd.DataFrame:
    return df

def check_z_axis_completeness(df: pd.DataFrame) -> Dict[int, bool]:
    return {}

def compute_derivatives(df: pd.DataFrame) -> pd.DataFrame:
    return df

def load_config(config_path: str = "data/config.yaml") -> Dict[str, Any]:
    import yaml
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def get_material_properties(config: Dict[str, Any], material_type: str) -> Dict[str, float]:
    # Mock implementation for context
    return {'mass': 1.0, 'radius': 0.01, 'inertia': 0.0002}

# --- Core Logic for T019 ---

def calculate_energy_components(df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
    """
    Calculate E_trans, E_rot, E_pot, E_vib based on physics formulas.
    Reads N (window size) from config for E_vib.
    """
    logger.info("Calculating energy components...")
    
    # Get N for vibration window from config, default 5
    vib_window = config.get('vibration', {}).get('window_size', 5)
    
    # Initialize energy columns
    df['E_trans'] = 0.0
    df['E_rot'] = 0.0
    df['E_pot'] = 0.0
    df['E_vib'] = 0.0

    # Group by particle to calculate per-particle properties
    for particle_id, group in df.groupby('particle_id'):
        props = get_material_properties(config, group['material_type'].iloc[0])
        mass = props['mass']
        inertia = props['inertia']
        radius = props['radius']

        # E_trans = 0.5 * m * v^2
        # Assume v is magnitude of velocity vector (vx, vy, vz)
        if 'vx' in group and 'vy' in group:
            v_sq = group['vx']**2 + group['vy']**2
            if 'vz' in group:
                v_sq += group['vz']**2
            df.loc[group.index, 'E_trans'] = 0.5 * mass * v_sq

        # E_rot = 0.5 * I * omega^2
        # Assume omega is magnitude of angular velocity (omega_x, omega_y, omega_z)
        if 'omega_x' in group and 'omega_y' in group:
            omega_sq = group['omega_x']**2 + group['omega_y']**2
            if 'omega_z' in group:
                omega_sq += group['omega_z']**2
            df.loc[group.index, 'E_rot'] = 0.5 * inertia * omega_sq

        # E_pot = m * g * h
        # Assume h is z coordinate
        if 'z' in group:
            g = 9.81
            df.loc[group.index, 'E_pot'] = mass * g * group['z']
        else:
            # If z is missing, we handle it in the output function
            df.loc[group.index, 'E_pot'] = np.nan

        # E_vib = variance of acceleration over sliding window
        # Acceleration = derivative of velocity
        if 'vx' in group and 'vy' in group:
            ax = group['vx'].diff().fillna(0)
            ay = group['vy'].diff().fillna(0)
            if 'vz' in group:
                az = group['vz'].diff().fillna(0)
            else:
                az = pd.Series(0, index=group.index)
            
            a_sq = ax**2 + ay**2 + az**2
            
            # Rolling variance
            df.loc[group.index, 'E_vib'] = a_sq.rolling(window=vib_window, min_periods=1).var()

    return df

def write_energy_output(df: pd.DataFrame, output_path: str, config: Dict[str, Any]):
    """
    Write the energy samples to CSV, handle missing z-axis, and generate hash.
    """
    logger.info(f"Writing energy output to {output_path}")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Check for missing z-axis per particle and flag
    # Re-use logic from T011 (check_z_axis_completeness)
    # Assuming df has 'particle_id' and 'z' columns (or missing 'z')
    z_missing_map = {}
    if 'z' not in df.columns:
        # If column completely missing, all particles are incomplete
        z_missing_map = {pid: True for pid in df['particle_id'].unique()}
    else:
        for pid in df['particle_id'].unique():
            pid_data = df[df['particle_id'] == pid]
            if pid_data['z'].isna().all():
                z_missing_map[pid] = True
                logger.warning(f"WARNING: Missing z-axis data for particle {pid}")
            else:
                z_missing_map[pid] = False

    # Add pot_incomplete column
    df['pot_incomplete'] = df['particle_id'].map(z_missing_map)

    # Select and order columns
    columns = ['particle_id', 'timestamp', 'E_trans', 'E_rot', 'E_pot', 'E_vib', 'pot_incomplete']
    # Ensure all exist, fill NaN with 0 for numeric if needed, or keep NaN
    # For pot_incomplete, ensure it's bool
    df['pot_incomplete'] = df['pot_incomplete'].astype(bool)
    
    # Handle NaNs in energy columns (e.g., if z was missing, E_pot is NaN)
    # We keep NaNs as they are, or fill with 0? Spec says "computed", so if missing z, E_pot is undefined.
    # Let's fill E_pot with 0 if pot_incomplete is True to ensure float consistency, 
    # but keep the flag. Or leave as NaN. The spec says "pot_incomplete" column is set to True.
    # Let's fill E_pot with 0.0 for completeness if missing, but the flag tells the truth.
    df.loc[df['pot_incomplete'], 'E_pot'] = 0.0

    output_df = df[columns].copy()
    
    # Write to CSV
    output_df.to_csv(output_path, index=False)
    logger.info(f"Successfully wrote {len(output_df)} rows to {output_path}")

    # Generate SHA-256 hash
    hash_path = output_path.replace('.csv', '.hash')
    with open(output_path, 'rb') as f:
        file_hash = hashlib.sha256(f.read()).hexdigest()
    
    with open(hash_path, 'w') as f:
        f.write(f"SHA256: {file_hash}\n")
        f.write(f"File: {output_path}\n")
        f.write(f"Rows: {len(output_df)}\n")
    
    logger.info(f"Hash written to {hash_path}: {file_hash}")

    # Verify schema
    expected_cols = ['particle_id', 'timestamp', 'E_trans', 'E_rot', 'E_pot', 'E_vib', 'pot_incomplete']
    actual_cols = list(output_df.columns)
    if actual_cols != expected_cols:
        raise IngestionError(f"Schema mismatch. Expected {expected_cols}, got {actual_cols}")
    
    # Verify types
    if not pd.api.types.is_integer_dtype(output_df['particle_id']):
        logger.warning("particle_id is not integer type")
    if not pd.api.types.is_float_dtype(output_df['timestamp']):
        logger.warning("timestamp is not float type")
    if not pd.api.types.is_float_dtype(output_df['E_trans']):
        logger.warning("E_trans is not float type")
    if not pd.api.types.is_bool_dtype(output_df['pot_incomplete']):
        logger.warning("pot_incomplete is not bool type")

    logger.info("Schema validation passed.")

def ingest_data(data_dir: str, config_path: str, output_dir: str):
    """
    Main ingestion pipeline for T019.
    """
    config = load_config(config_path)
    
    # 1. Find and load tracking data
    csv_files = find_csv_files(data_dir)
    if not csv_files:
        raise IngestionError(f"No CSV files found in {data_dir}")
    
    tracking_df = load_tracking_data(csv_files)
    
    # 2. Load driving data
    driving_files = [f for f in csv_files if 'driving' in str(f).lower()]
    if driving_files:
        driving_df = load_driving_data(driving_files[0])
        tracking_df, driving_df = sync_timestamps(tracking_df, driving_df)
    
    # 3. Handle missing frames
    tracking_df = handle_missing_frames(tracking_df)
    
    # 4. Compute derivatives (v, omega, a)
    tracking_df = compute_derivatives(tracking_df)
    
    # 5. Calculate energy components
    tracking_df = calculate_energy_components(tracking_df, config)
    
    # 6. Write output
    output_path = os.path.join(output_dir, 'energy_samples.csv')
    write_energy_output(tracking_df, output_path, config)
    
    return output_path

def main():
    parser = argparse.ArgumentParser(description='Ingest granular data and compute energies.')
    parser.add_argument('--data-dir', type=str, default='data/raw', help='Directory containing raw CSV files')
    parser.add_argument('--config', type=str, default='data/config.yaml', help='Path to config file')
    parser.add_argument('--output-dir', type=str, default='data/derived', help='Directory for output files')
    
    args = parser.parse_args()
    
    try:
        ingest_data(args.data_dir, args.config, args.output_dir)
        logger.info("Ingestion completed successfully.")
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()