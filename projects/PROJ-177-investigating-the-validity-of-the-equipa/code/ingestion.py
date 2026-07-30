import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import numpy as np
import logging
import warnings

# Ensure logging is configured
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/ingestion.log')
    ]
)
logger = logging.getLogger(__name__)

class IngestionError(Exception):
    """Custom exception for ingestion errors."""
    pass

def find_csv_files(base_dir: str) -> List[Path]:
    """Find all CSV files in the given directory and subdirectories."""
    base = Path(base_dir)
    if not base.exists():
        raise IngestionError(f"Directory {base_dir} does not exist")
    return list(base.rglob("*.csv"))

def load_tracking_data(file_paths: List[Path]) -> pd.DataFrame:
    """Load and concatenate particle tracking data from multiple CSV files."""
    if not file_paths:
        raise IngestionError("No CSV files found for tracking data")
    
    dfs = []
    for fp in file_paths:
        try:
            df = pd.read_csv(fp)
            # Ensure required columns exist
            required_cols = ['particle_id', 'timestamp', 'x', 'y']
            missing = [c for c in required_cols if c not in df.columns]
            if missing:
                logger.warning(f"File {fp} missing columns: {missing}. Attempting to continue with available data.")
            dfs.append(df)
        except Exception as e:
            logger.error(f"Failed to load {fp}: {e}")
            raise IngestionError(f"Failed to load {fp}: {e}")
    
    return pd.concat(dfs, ignore_index=True)

def load_driving_data(file_paths: List[Path]) -> pd.DataFrame:
    """Load driving signal logs."""
    if not file_paths:
        raise IngestionError("No CSV files found for driving data")
    
    dfs = []
    for fp in file_paths:
        try:
            df = pd.read_csv(fp)
            dfs.append(df)
        except Exception as e:
            logger.error(f"Failed to load driving data {fp}: {e}")
            raise IngestionError(f"Failed to load {fp}: {e}")
    
    return pd.concat(dfs, ignore_index=True)

def sync_timestamps(tracking_df: pd.DataFrame, driving_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Synchronize timestamps between tracking and driving data."""
    # Simple synchronization: align on common time range
    min_time = max(tracking_df['timestamp'].min(), driving_df['timestamp'].min())
    max_time = min(tracking_df['timestamp'].max(), driving_df['timestamp'].max())
    
    tracking_sync = tracking_df[(tracking_df['timestamp'] >= min_time) & (tracking_df['timestamp'] <= max_time)].copy()
    driving_sync = driving_df[(driving_df['timestamp'] >= min_time) & (driving_df['timestamp'] <= max_time)].copy()
    
    return tracking_sync, driving_sync

def merge_datasets(tracking_df: pd.DataFrame, driving_df: pd.DataFrame) -> pd.DataFrame:
    """Merge tracking and driving data on timestamp."""
    # Assuming driving data has a single row per timestamp or needs to be broadcast
    # For simplicity, we merge on timestamp if driving data has it
    if 'timestamp' in driving_df.columns:
        merged = pd.merge(tracking_df, driving_df, on='timestamp', how='left')
    else:
        # If driving data doesn't have timestamp, assume it applies to all
        merged = tracking_df.copy()
        for col in driving_df.columns:
            merged[col] = driving_df[col].iloc[0] if len(driving_df) == 1 else driving_df[col].values[0]
    
    return merged

def handle_missing_frames(df: pd.DataFrame, time_col: str = 'timestamp', id_col: str = 'particle_id') -> pd.DataFrame:
    """Handle missing frames via linear interpolation or flagging."""
    df_sorted = df.sort_values([id_col, time_col])
    
    # Group by particle_id and interpolate
    def interpolate_group(group):
        group = group.set_index(time_col)
        # Interpolate numeric columns
        numeric_cols = group.select_dtypes(include=[np.number]).columns
        group[numeric_cols] = group[numeric_cols].interpolate(method='linear', limit_direction='both')
        return group.reset_index()
    
    df_interpolated = df_sorted.groupby(id_col, group_keys=False).apply(interpolate_group)
    return df_interpolated

def compute_derivatives(df: pd.DataFrame, time_col: str = 'timestamp') -> pd.DataFrame:
    """Compute velocity (v) and angular velocity (omega) via finite differences."""
    df = df.sort_values([time_col]).copy()
    
    # Velocity: dx/dt, dy/dt, dz/dt
    df['vx'] = df['x'].diff() / df[time_col].diff()
    df['vy'] = df['y'].diff() / df[time_col].diff()
    if 'z' in df.columns:
        df['vz'] = df['z'].diff() / df[time_col].diff()
    else:
        df['vz'] = np.nan
    
    # Fill NaN from diff with forward fill or 0
    df['vx'] = df['vx'].fillna(0)
    df['vy'] = df['vy'].fillna(0)
    df['vz'] = df['vz'].fillna(0)
    
    # Angular velocity (assuming theta is in radians)
    if 'theta' in df.columns:
        df['omega'] = df['theta'].diff() / df[time_col].diff()
        df['omega'] = df['omega'].fillna(0)
    else:
        df['omega'] = 0.0
    
    return df

def check_z_axis_completeness(df: pd.DataFrame) -> Tuple[pd.DataFrame, bool]:
    """Check if z-axis data is present and flag accordingly."""
    has_z = 'z' in df.columns and not df['z'].isna().all()
    
    if not has_z:
        df['pot_incomplete'] = True
        logger.warning("Z-axis data is missing or incomplete. 'pot_incomplete' flag set to True for all rows.")
    else:
        df['pot_incomplete'] = False
    
    return df, has_z

def calculate_energy_components(df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
    """
    Calculate E_trans, E_rot, E_pot, E_vib using config constants.
    
    Formulas:
    E_trans = 0.5 * m * (vx^2 + vy^2 + vz^2)
    E_rot = 0.5 * I * omega^2
    E_pot = m * g * z (if z available)
    E_vib = variance of acceleration (high-frequency component) or derived from acceleration variance
    """
    # Extract config
    mass = config.get('mass', 1.0)  # kg
    inertia = config.get('inertia', 1.0)  # kg*m^2
    g = config.get('gravity', 9.81)  # m/s^2
    radius = config.get('radius', 0.0025)  # m (2.5mm default)
    
    # If inertia not provided, derive using I = 2/5 * m * r^2
    if inertia == 1.0 and mass != 1.0:
        inertia = (2/5) * mass * (radius ** 2)
        logger.info(f"Inertia derived from mass and radius: I = {inertia:.6e} kg*m^2")
    
    df = df.copy()
    
    # Translational Energy
    v_squared = df['vx']**2 + df['vy']**2 + df['vz']**2
    df['E_trans'] = 0.5 * mass * v_squared
    
    # Rotational Energy
    df['E_rot'] = 0.5 * inertia * df['omega']**2
    
    # Potential Energy
    if 'z' in df.columns and not df['z'].isna().all():
        df['E_pot'] = mass * g * df['z']
    else:
        df['E_pot'] = 0.0
        logger.warning("Potential energy set to 0 due to missing z-axis data.")
    
    # Vibrational Energy: Derived from acceleration variance
    # Acceleration is the derivative of velocity
    if 'vx' in df.columns and 'vy' in df.columns and 'vz' in df.columns:
        ax = df['vx'].diff() / df['timestamp'].diff()
        ay = df['vy'].diff() / df['timestamp'].diff()
        az = df['z'].diff().diff() / (df['timestamp'].diff()**2) if 'z' in df.columns else 0
        
        # Replace NaN with 0
        ax = ax.fillna(0)
        ay = ay.fillna(0)
        az = az.fillna(0)
        
        # Acceleration magnitude squared
        a_squared = ax**2 + ay**2 + az**2
        
        # Vibrational energy as a scaled variance of acceleration (simplified model)
        # E_vib = 0.5 * m * variance(a)
        # We use a rolling window variance for local vibrational energy
        window_size = 5
        if len(df) > window_size:
            a_var = a_squared.rolling(window=window_size, min_periods=1).var()
            df['E_vib'] = 0.5 * mass * a_var
        else:
            df['E_vib'] = 0.0
    else:
        df['E_vib'] = 0.0
    
    return df

def ingest_data(
    tracking_files: List[str],
    driving_files: List[str],
    config: Dict[str, Any],
    output_path: str
) -> str:
    """
    Main ingestion pipeline:
    1. Load tracking and driving data
    2. Sync timestamps
    3. Merge datasets
    4. Handle missing frames
    5. Compute derivatives
    6. Check z-axis completeness
    7. Calculate energy components
    8. Output to CSV
    """
    logger.info("Starting data ingestion pipeline...")
    
    # 1. Load data
    tracking_df = load_tracking_data([Path(f) for f in tracking_files])
    driving_df = load_driving_data([Path(f) for f in driving_files])
    
    # 2. Sync timestamps
    tracking_df, driving_df = sync_timestamps(tracking_df, driving_df)
    
    # 3. Merge
    merged_df = merge_datasets(tracking_df, driving_df)
    
    # 4. Handle missing frames
    merged_df = handle_missing_frames(merged_df)
    
    # 5. Compute derivatives (v, omega)
    merged_df = compute_derivatives(merged_df)
    
    # 6. Check z-axis completeness
    merged_df, has_z = check_z_axis_completeness(merged_df)
    
    # 7. Calculate energy components
    merged_df = calculate_energy_components(merged_df, config)
    
    # 8. Select and order output columns
    output_columns = [
        'particle_id', 'timestamp', 
        'E_trans', 'E_rot', 'E_pot', 'E_vib', 
        'pot_incomplete'
    ]
    
    # Ensure all columns exist
    for col in output_columns:
        if col not in merged_df.columns:
            merged_df[col] = 0.0 if col != 'pot_incomplete' else False
    
    output_df = merged_df[output_columns]
    
    # Ensure output directory exists
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write to CSV
    output_df.to_csv(output_path, index=False)
    logger.info(f"Energy samples written to {output_path}")
    
    return str(output_path)

def main():
    """CLI entry point for ingestion."""
    import argparse
    import yaml
    
    parser = argparse.ArgumentParser(description="Ingest granular particle data and calculate energies.")
    parser.add_argument("--tracking", nargs="+", required=True, help="List of tracking CSV files")
    parser.add_argument("--driving", nargs="+", required=True, help="List of driving signal CSV files")
    parser.add_argument("--config", type=str, required=True, help="Path to config.yaml")
    parser.add_argument("--output", type=str, default="data/derived/energy_samples.csv", help="Output CSV path")
    
    args = parser.parse_args()
    
    # Load config
    try:
        with open(args.config, 'r') as f:
            config = yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        sys.exit(1)
    
    # Run ingestion
    try:
        ingest_data(args.tracking, args.driving, config, args.output)
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
