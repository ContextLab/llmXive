"""
Ingestion module for granular system particle tracking data.
Handles loading, syncing, interpolating, and computing energy components.
"""
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import numpy as np

from config import get_material_properties, get_mass, get_inertia, load_config

class IngestionError(Exception):
    """Custom exception for ingestion failures."""
    pass

def find_csv_files(directory: str) -> List[Path]:
    """Find all CSV files in a directory."""
    path = Path(directory)
    if not path.exists():
        return []
    return list(path.glob("*.csv"))

def load_tracking_data(csv_path: Path) -> pd.DataFrame:
    """Load particle tracking data from a CSV file."""
    if not csv_path.exists():
        raise IngestionError(f"File not found: {csv_path}")
    df = pd.read_csv(csv_path)
    # Ensure required columns exist
    required = ['particle_id', 'timestamp', 'x', 'y']
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise IngestionError(f"Missing columns in {csv_path}: {missing}")
    return df

def load_driving_data(csv_path: Path) -> pd.DataFrame:
    """Load driving signal logs from a CSV file."""
    if not csv_path.exists():
        raise IngestionError(f"File not found: {csv_path}")
    df = pd.read_csv(csv_path)
    required = ['timestamp', 'frequency', 'amplitude']
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise IngestionError(f"Missing columns in {csv_path}: {missing}")
    return df

def sync_timestamps(tracking_df: pd.DataFrame, driving_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Sync tracking and driving data to a common time base."""
    # Simple approach: filter tracking to driving time range
    t_min = driving_df['timestamp'].min()
    t_max = driving_df['timestamp'].max()
    tracking_df = tracking_df[(tracking_df['timestamp'] >= t_min) & (tracking_df['timestamp'] <= t_max)]
    return tracking_df, driving_df

def merge_datasets(tracking_df: pd.DataFrame, driving_df: pd.DataFrame) -> pd.DataFrame:
    """Merge tracking data with driving signal data."""
    # Sort by timestamp
    tracking_df = tracking_df.sort_values('timestamp')
    driving_df = driving_df.sort_values('timestamp')
    
    # Merge on timestamp (nearest neighbor or exact match)
    merged = pd.merge_asof(
        tracking_df,
        driving_df,
        on='timestamp',
        direction='nearest'
    )
    return merged

def handle_missing_frames(df: pd.DataFrame, max_gap: int = 5) -> pd.DataFrame:
    """Handle missing frames via linear interpolation or flagging."""
    # Group by particle_id
    result_dfs = []
    for pid, group in df.groupby('particle_id'):
        group = group.sort_values('timestamp')
        # Check for gaps in index or timestamp
        # Simple interpolation for missing values in numeric columns
        numeric_cols = group.select_dtypes(include=[np.number]).columns
        group[numeric_cols] = group[numeric_cols].interpolate(method='linear', limit=max_gap)
        # Flag rows that were interpolated (NaN became non-NaN) - simplified logic
        result_dfs.append(group)
    return pd.concat(result_dfs, ignore_index=True)

def compute_derivatives(df: pd.DataFrame) -> pd.DataFrame:
    """Compute velocity and angular velocity via finite differences."""
    df = df.sort_values(['particle_id', 'timestamp'])
    
    # Compute velocity components
    df['vx'] = df.groupby('particle_id')['x'].diff() / df.groupby('particle_id')['timestamp'].diff()
    df['vy'] = df.groupby('particle_id')['y'].diff() / df.groupby('particle_id')['timestamp'].diff()
    
    # Handle z if present
    if 'z' in df.columns:
        df['vz'] = df.groupby('particle_id')['z'].diff() / df.groupby('particle_id')['timestamp'].diff()
    else:
        df['vz'] = np.nan
    
    # Compute angular velocity (omega) from orientation or theta if available
    # Assuming 'theta' column exists for rotation angle
    if 'theta' in df.columns:
        df['omega'] = df.groupby('particle_id')['theta'].diff() / df.groupby('particle_id')['timestamp'].diff()
    else:
        df['omega'] = 0.0  # Default if no orientation data
    
    # Fill NaN from first/last diff
    df = df.fillna(0)
    return df

def check_z_axis_completeness(df: pd.DataFrame) -> pd.DataFrame:
    """Check if z-axis data is present and add a flag column."""
    has_z = 'z' in df.columns and not df['z'].isna().all()
    df['pot_incomplete'] = not has_z
    
    if not has_z:
        # Log warning
        sys.stderr.write("Warning: Z-axis data missing or incomplete. Potential energy calculation may be inaccurate.\n")
    
    return df

def calculate_energy_components(df: pd.DataFrame, config_path: Optional[str] = None) -> pd.DataFrame:
    """
    Calculate E_trans, E_rot, E_pot, and E_vib using independent physics formulas.
    
    Formulas:
    - E_trans = 0.5 * m * (vx^2 + vy^2 + vz^2)
    - E_rot = 0.5 * I * omega^2
    - E_pot = m * g * z (if z available, else 0)
    - E_vib = derived from high-frequency acceleration variance (NOT residual)
    
    Args:
        df: DataFrame with columns: particle_id, timestamp, x, y, z, theta, vx, vy, vz, omega
        config_path: Path to config.yaml. If None, uses default path.
    
    Returns:
        DataFrame with added energy columns.
    """
    if config_path is None:
        # Default path relative to project root
        config_path = "data/config.yaml"
    
    # Load config to get material properties
    try:
        config = load_config(config_path)
    except Exception as e:
        raise IngestionError(f"Failed to load config: {e}")
    
    # Constants
    g = 9.81  # m/s^2
    
    # Initialize energy columns
    df['E_trans'] = 0.0
    df['E_rot'] = 0.0
    df['E_pot'] = 0.0
    df['E_vib'] = 0.0
    
    # Group by particle_id to apply material-specific properties
    results = []
    for pid, group in df.groupby('particle_id'):
        # Get material properties for this particle
        # Assuming 'material' column exists or infer from particle_id pattern
        material = group.iloc[0].get('material', 'steel')  # Default to steel if not specified
        
        m = get_mass(config, material)
        I = get_inertia(config, material)
        
        # Calculate E_trans
        v_sq = group['vx']**2 + group['vy']**2 + group['vz']**2
        group['E_trans'] = 0.5 * m * v_sq
        
        # Calculate E_rot
        group['E_rot'] = 0.5 * I * group['omega']**2
        
        # Calculate E_pot
        if 'z' in group.columns and not group['z'].isna().all():
            group['E_pot'] = m * g * group['z']
        else:
            group['E_pot'] = 0.0
        
        # Calculate E_vib: derived from high-frequency acceleration variance
        # Step 1: Compute acceleration (second derivative of velocity)
        # We use finite differences on velocity
        acc_x = group['vx'].diff().diff() / (group['timestamp'].diff().diff() + 1e-9)
        acc_y = group['vy'].diff().diff() / (group['timestamp'].diff().diff() + 1e-9)
        acc_z = group['vz'].diff().diff() / (group['timestamp'].diff().diff() + 1e-9)
        
        # Step 2: Isolate high-frequency component (variance of acceleration)
        # Use a rolling window to estimate local variance as a proxy for high-frequency content
        window_size = max(5, len(group) // 10)  # Adaptive window
        if window_size < 3:
            window_size = 3
        
        # Variance of acceleration magnitude
        acc_mag = np.sqrt(acc_x**2 + acc_y**2 + acc_z**2)
        acc_var = acc_mag.rolling(window=window_size, min_periods=1).var()
        
        # E_vib is proportional to the variance of high-frequency acceleration
        # Scaling factor could be derived from config or set as a constant
        # Using a simple scaling: E_vib = 0.5 * m * (sigma_acc)^2 * dt^2
        # But to keep it independent and simple: E_vib = k * variance
        # Here we use a normalized variance scaled by mass
        k_vib = 1.0  # Can be tuned or loaded from config
        group['E_vib'] = k_vib * m * acc_var
        
        results.append(group)
    
    return pd.concat(results, ignore_index=True)

def ingest_data(
    tracking_dir: str,
    driving_dir: str,
    output_path: str,
    config_path: Optional[str] = None
) -> pd.DataFrame:
    """
    Full ingestion pipeline: load, sync, interpolate, compute derivatives, calculate energy.
    
    Args:
        tracking_dir: Directory containing particle tracking CSVs
        driving_dir: Directory containing driving signal CSVs
        output_path: Path to save the final energy_samples.csv
        config_path: Path to config.yaml
    
    Returns:
        DataFrame with all energy components calculated.
    """
    # Find files
    tracking_files = find_csv_files(tracking_dir)
    driving_files = find_csv_files(driving_dir)
    
    if not tracking_files:
        raise IngestionError(f"No tracking files found in {tracking_dir}")
    if not driving_files:
        raise IngestionError(f"No driving files found in {driving_dir}")
    
    # Load first tracking and driving file (assuming single dataset for now)
    # In a full implementation, we would merge multiple files
    tracking_df = load_tracking_data(tracking_files[0])
    driving_df = load_driving_data(driving_files[0])
    
    # Sync
    tracking_df, driving_df = sync_timestamps(tracking_df, driving_df)
    
    # Merge
    merged_df = merge_datasets(tracking_df, driving_df)
    
    # Handle missing frames
    merged_df = handle_missing_frames(merged_df)
    
    # Compute derivatives (v, omega)
    merged_df = compute_derivatives(merged_df)
    
    # Check z-axis completeness
    merged_df = check_z_axis_completeness(merged_df)
    
    # Calculate energy components
    merged_df = calculate_energy_components(merged_df, config_path)
    
    # Select output columns
    output_cols = [
        'particle_id', 'timestamp', 
        'E_trans', 'E_rot', 'E_pot', 'E_vib', 
        'pot_incomplete'
    ]
    
    # Ensure all columns exist
    for col in output_cols:
        if col not in merged_df.columns:
            merged_df[col] = 0.0 if col != 'pot_incomplete' else True
    
    output_df = merged_df[output_cols]
    
    # Save to CSV
    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)
    output_df.to_csv(output_path_obj, index=False)
    
    return output_df

def main():
    """CLI entry point for ingestion."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Ingest granular data and compute energy components.")
    parser.add_argument("--tracking-dir", default="data/raw/tracking", help="Directory with tracking CSVs")
    parser.add_argument("--driving-dir", default="data/raw/driving", help="Directory with driving CSVs")
    parser.add_argument("--output", default="data/derived/energy_samples.csv", help="Output CSV path")
    parser.add_argument("--config", default="data/config.yaml", help="Path to config.yaml")
    
    args = parser.parse_args()
    
    try:
        df = ingest_data(args.tracking_dir, args.driving_dir, args.output, args.config)
        print(f"Successfully ingested data. Output written to {args.output}")
        print(f"Shape: {df.shape}")
        print(f"Columns: {list(df.columns)}")
    except IngestionError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()