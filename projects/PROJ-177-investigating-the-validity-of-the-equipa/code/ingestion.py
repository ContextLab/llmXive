import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import numpy as np
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class IngestionError(Exception):
    """Custom exception for ingestion errors."""
    pass

def find_csv_files(directory: Path) -> List[Path]:
    """Find all CSV files in the given directory."""
    if not directory.exists():
        raise IngestionError(f"Directory not found: {directory}")
    return list(directory.glob("*.csv"))

def load_tracking_data(file_paths: List[Path]) -> pd.DataFrame:
    """Load and concatenate particle tracking CSVs."""
    dfs = []
    for path in file_paths:
        try:
            df = pd.read_csv(path)
            dfs.append(df)
            logger.info(f"Loaded tracking data from {path}")
        except Exception as e:
            raise IngestionError(f"Failed to load {path}: {e}")
    if not dfs:
        raise IngestionError("No tracking data files found.")
    return pd.concat(dfs, ignore_index=True)

def load_driving_data(file_paths: List[Path]) -> pd.DataFrame:
    """Load driving signal logs."""
    dfs = []
    for path in file_paths:
        try:
            df = pd.read_csv(path)
            dfs.append(df)
            logger.info(f"Loaded driving data from {path}")
        except Exception as e:
            raise IngestionError(f"Failed to load {path}: {e}")
    if not dfs:
        raise IngestionError("No driving data files found.")
    return pd.concat(dfs, ignore_index=True)

def sync_timestamps(tracking_df: pd.DataFrame, driving_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Sync timestamps between tracking and driving data."""
    # Assume both have a 'timestamp' column
    common_ts = np.intersect1d(tracking_df['timestamp'].values, driving_df['timestamp'].values)
    tracking_df = tracking_df[tracking_df['timestamp'].isin(common_ts)].reset_index(drop=True)
    driving_df = driving_df[driving_df['timestamp'].isin(common_ts)].reset_index(drop=True)
    logger.info(f"Synced timestamps: {len(common_ts)} common points")
    return tracking_df, driving_df

def merge_datasets(tracking_df: pd.DataFrame, driving_df: pd.DataFrame) -> pd.DataFrame:
    """Merge tracking and driving data on timestamp."""
    merged = pd.merge(tracking_df, driving_df, on='timestamp', how='inner')
    logger.info(f"Merged dataset shape: {merged.shape}")
    return merged

def handle_missing_frames(df: pd.DataFrame, max_gap: int = 5) -> pd.DataFrame:
    """Handle missing frames via linear interpolation."""
    df = df.sort_values('timestamp')
    for col in df.select_dtypes(include=[np.number]).columns:
        if col == 'timestamp':
            continue
        # Interpolate missing values
        df[col] = df[col].interpolate(method='linear', limit=max_gap)
    # Forward/backward fill remaining NaNs
    df = df.ffill().bfill()
    logger.info("Handled missing frames via interpolation")
    return df

def compute_derivatives(df: pd.DataFrame) -> pd.DataFrame:
    """Compute velocity (v) and angular velocity (omega) via finite differences."""
    # Assume columns: x, y, z, theta (orientation)
    # dt is assumed constant or derived from timestamp
    dt = df['timestamp'].diff().fillna(df['timestamp'].iloc[1] - df['timestamp'].iloc[0]).values
    dt = np.where(dt == 0, 1e-9, dt)  # Avoid division by zero

    # Velocity components
    df['vx'] = np.gradient(df['x'].values, dt)
    df['vy'] = np.gradient(df['y'].values, dt)
    df['vz'] = np.gradient(df['z'].values, dt) if 'z' in df.columns else 0.0

    # Angular velocity
    df['omega'] = np.gradient(df['theta'].values, dt) if 'theta' in df.columns else 0.0

    logger.info("Computed derivatives (v, omega)")
    return df

def check_z_axis_completeness(df: pd.DataFrame) -> Tuple[bool, pd.Series]:
    """Check if z-axis data is complete."""
    if 'z' not in df.columns:
        logger.warning("z-axis data is missing in the dataset.")
        pot_incomplete = pd.Series([True] * len(df), index=df.index)
        return False, pot_incomplete
    
    # Check for NaNs in z
    has_nans = df['z'].isna().any()
    if has_nans:
        logger.warning("z-axis data contains NaNs.")
    
    pot_incomplete = df['z'].isna()
    return not has_nans, pot_incomplete

def calculate_energy_components(df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
    """Calculate E_trans, E_rot, E_pot, E_vib using config constants."""
    # Extract config parameters
    mass = config.get('mass', 1.0)
    inertia = config.get('inertia', 1.0)
    g = config.get('gravity', 9.81)
    k_spring = config.get('k_spring', 100.0)  # Vibrational spring constant
    z_ref = config.get('z_ref', 0.0)  # Reference height for potential energy

    # Translational kinetic energy: E_trans = 0.5 * m * v^2
    v_squared = df['vx']**2 + df['vy']**2 + (df['vz'] if 'vz' in df.columns else 0.0)**2
    df['E_trans'] = 0.5 * mass * v_squared

    # Rotational kinetic energy: E_rot = 0.5 * I * omega^2
    df['E_rot'] = 0.5 * inertia * df['omega']**2

    # Potential energy: E_pot = m * g * z
    if 'z' in df.columns:
        df['E_pot'] = mass * g * (df['z'] - z_ref)
    else:
        df['E_pot'] = 0.0
        logger.warning("z-axis missing; E_pot set to 0.")

    # Vibrational energy: E_vib = 0.5 * k * (z - z_ref)^2 (simplified model)
    if 'z' in df.columns:
        df['E_vib'] = 0.5 * k_spring * (df['z'] - z_ref)**2
    else:
        df['E_vib'] = 0.0
        logger.warning("z-axis missing; E_vib set to 0.")

    logger.info("Calculated energy components")
    return df

def ingest_data(input_dir: Path, output_dir: Path, config: Dict[str, Any]) -> None:
    """Main ingestion pipeline: load, sync, merge, interpolate, compute energies, save."""
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "energy_samples.csv"

    # Find and load data
    tracking_files = find_csv_files(input_dir / "tracking")
    driving_files = find_csv_files(input_dir / "driving")

    tracking_df = load_tracking_data(tracking_files)
    driving_df = load_driving_data(driving_files)

    # Sync and merge
    tracking_df, driving_df = sync_timestamps(tracking_df, driving_df)
    merged_df = merge_datasets(tracking_df, driving_df)

    # Handle missing frames
    merged_df = handle_missing_frames(merged_df)

    # Compute derivatives
    merged_df = compute_derivatives(merged_df)

    # Check z-axis completeness
    z_complete, pot_incomplete = check_z_axis_completeness(merged_df)
    merged_df['pot_incomplete'] = pot_incomplete

    # Calculate energy components
    merged_df = calculate_energy_components(merged_df, config)

    # Select output columns
    output_cols = ['particle_id', 'timestamp', 'E_trans', 'E_rot', 'E_pot', 'E_vib', 'pot_incomplete']
    # Ensure particle_id exists; if not, create a dummy one
    if 'particle_id' not in merged_df.columns:
        merged_df['particle_id'] = 0
    
    output_df = merged_df[output_cols]

    # Save to CSV
    output_df.to_csv(output_file, index=False)
    logger.info(f"Saved energy samples to {output_file}")

def main():
    """CLI entry point for ingestion."""
    import argparse
    parser = argparse.ArgumentParser(description="Ingest granular data and compute energies.")
    parser.add_argument("--input", type=str, required=True, help="Input directory containing 'tracking' and 'driving' subdirs")
    parser.add_argument("--output", type=str, required=True, help="Output directory for energy_samples.csv")
    parser.add_argument("--config", type=str, required=True, help="Path to config.yaml")
    
    args = parser.parse_args()
    
    # Load config
    import yaml
    with open(args.config, 'r') as f:
        config = yaml.safe_load(f)
    
    input_dir = Path(args.input)
    output_dir = Path(args.output)
    
    ingest_data(input_dir, output_dir, config)

if __name__ == "__main__":
    main()
