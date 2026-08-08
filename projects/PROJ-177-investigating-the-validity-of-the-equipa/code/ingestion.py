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
from scipy.signal import hilbert
from datetime import datetime
import itertools

from config import load_config, get_material_properties, get_mass
from checksum_raw_data import calculate_sha256

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class IngestionError(Exception):
    """Custom exception for ingestion errors."""
    pass

class DataExclusionWarning(UserWarning):
    """Warning for data exclusion events."""
    pass

def find_csv_files(directory: Path) -> List[Path]:
    """Find all CSV files in a directory recursively."""
    return list(directory.rglob("*.csv"))

def load_tracking_data(file_paths: List[Path]) -> pd.DataFrame:
    """
    Load particle tracking data from CSV files.
    Expected columns: particle_id, timestamp, x, y, z (optional), theta (optional).
    """
    dfs = []
    for fp in file_paths:
        try:
            df = pd.read_csv(fp)
            # Ensure required columns exist
            required = ['particle_id', 'timestamp', 'x', 'y']
            missing = [c for c in required if c not in df.columns]
            if missing:
                logger.warning(f"File {fp} missing columns {missing}, skipping.")
                continue
            dfs.append(df)
        except Exception as e:
            logger.error(f"Failed to load {fp}: {e}")
            continue

    if not dfs:
        raise IngestionError("No valid tracking data files found.")

    combined = pd.concat(dfs, ignore_index=True)
    combined = combined.sort_values(['particle_id', 'timestamp']).reset_index(drop=True)
    return combined

def load_driving_data(file_path: Path) -> pd.DataFrame:
    """
    Load driving signal logs.
    Expected columns: timestamp, frequency, amplitude.
    """
    if not file_path.exists():
        raise IngestionError(f"Driving signal file not found: {file_path}")
    
    try:
        df = pd.read_csv(file_path)
        required = ['timestamp', 'frequency']
        missing = [c for c in required if c not in df.columns]
        if missing:
            raise IngestionError(f"Driving signal file missing columns: {missing}")
        return df
    except Exception as e:
        raise IngestionError(f"Failed to load driving data: {e}")

def sync_timestamps(tracking_df: pd.DataFrame, driving_df: pd.DataFrame) -> pd.DataFrame:
    """
    Sync particle tracking data with driving signal logs by timestamp.
    Merges on closest timestamp within a tolerance.
    """
    # Ensure timestamps are numeric/float for interpolation if needed
    if tracking_df['timestamp'].dtype != float:
        tracking_df['timestamp'] = pd.to_numeric(tracking_df['timestamp'], errors='coerce')
    
    # Merge: for each tracking row, find the closest driving timestamp
    # We'll use a simple asof merge or nearest join logic
    # For simplicity, we assume driving data is dense enough or we interpolate
    driving_df = driving_df.sort_values('timestamp')
    tracking_df = tracking_df.sort_values('timestamp')
    
    # Perform an asof merge to attach driving frequency to each particle frame
    merged = pd.merge_asof(
        tracking_df,
        driving_df,
        on='timestamp',
        direction='nearest',
        tolerance=pd.Timedelta('1ms') # Adjust tolerance as needed
    )
    
    # Drop rows where driving data couldn't be matched
    if merged['frequency'].isnull().any():
        logger.warning("Some tracking rows have no matching driving signal. Dropping them.")
        merged = merged.dropna(subset=['frequency'])
        
    return merged

def handle_missing_frames(df: pd.DataFrame, max_gap: float = 0.01) -> pd.DataFrame:
    """
    Handle missing frames via linear interpolation or flagging.
    If gap > max_gap, log warning and set gap_flag.
    """
    df = df.sort_values(['particle_id', 'timestamp'])
    df['gap_flag'] = False
    
    for pid, group in df.groupby('particle_id'):
        timestamps = group['timestamp'].values
        gaps = np.diff(timestamps)
        large_gaps = gaps > max_gap
        
        if np.any(large_gaps):
            logger.warning(f"Particle {pid} has {np.sum(large_gaps)} large gaps (> {max_gap}s). Flagging.")
            # Flag the row AFTER the large gap
            indices = group.index[1:][large_gaps]
            df.loc[indices, 'gap_flag'] = True
        
        # Interpolate missing numeric columns
        numeric_cols = ['x', 'y', 'z', 'theta', 'frequency', 'amplitude']
        cols_to_interp = [c for c in numeric_cols if c in df.columns]
        if cols_to_interp:
            df.loc[group.index, cols_to_interp] = group[cols_to_interp].interpolate(method='linear')
            
    return df

def check_z_axis_completeness(df: pd.DataFrame) -> pd.DataFrame:
    """
    Handle missing z-axis data by adding a 'pot_incomplete' boolean column.
    """
    if 'z' not in df.columns:
        logger.warning("Z-axis data missing. Marking all rows as pot_incomplete=True.")
        df['pot_incomplete'] = True
        return df
    
    df['pot_incomplete'] = df['z'].isnull()
    if df['pot_incomplete'].any():
        logger.warning(f"{df['pot_incomplete'].sum()} rows have missing z-axis data.")
    return df

def compute_derivatives(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute velocity (v) and angular velocity (omega) via finite differences.
    v = sqrt(vx^2 + vy^2 + vz^2)
    omega = d(theta)/dt
    """
    df = df.sort_values(['particle_id', 'timestamp'])
    
    # Velocity components
    for col in ['x', 'y', 'z']:
        if col in df.columns:
            df[f'd{col}'] = df.groupby('particle_id')[col].diff() / df.groupby('particle_id')['timestamp'].diff()
        else:
            df[f'd{col}'] = 0.0
            
    # Handle division by zero (first row of each group)
    df['vx'] = df['dx'].fillna(0)
    df['vy'] = df['dy'].fillna(0)
    df['vz'] = df['dz'].fillna(0)
    
    df['v'] = np.sqrt(df['vx']**2 + df['vy']**2 + df['vz']**2)
    
    # Angular velocity
    if 'theta' in df.columns:
        df['dtheta'] = df.groupby('particle_id')['theta'].diff() / df.groupby('particle_id')['timestamp'].diff()
        df['omega'] = df['dtheta'].fillna(0)
    else:
        df['omega'] = 0.0
        
    return df

def calculate_energy_components(df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
    """
    Calculate E_trans, E_rot, E_pot, E_vib.
    E_vib = m * var(a) over a sliding window (N=5).
    All energies in Joules.
    """
    # Get mass from config
    material = df.get('material_type', 'steel').iloc[0] if 'material_type' in df.columns else 'steel'
    mass = get_mass(material, config)
    inertia = 0.4 * mass * (0.005**2) # Simplified sphere inertia proxy: 0.4 * m * r^2, r=5mm
    
    # Acceleration for E_vib
    df = df.sort_values(['particle_id', 'timestamp'])
    df['ax'] = df.groupby('particle_id')['vx'].diff() / df.groupby('particle_id')['timestamp'].diff()
    df['ay'] = df.groupby('particle_id')['vy'].diff() / df.groupby('particle_id')['timestamp'].diff()
    df['az'] = df.groupby('particle_id')['vz'].diff() / df.groupby('particle_id')['timestamp'].diff()
    df['a'] = np.sqrt(df['ax']**2 + df['ay']**2 + df['az']**2)
    
    # Fill NaNs in acceleration
    df['ax'] = df['ax'].fillna(0)
    df['ay'] = df['ay'].fillna(0)
    df['az'] = df['az'].fillna(0)
    df['a'] = df['a'].fillna(0)
    
    # E_trans = 0.5 * m * v^2
    df['E_trans'] = 0.5 * mass * df['v']**2
    
    # E_rot = 0.5 * I * omega^2
    df['E_rot'] = 0.5 * inertia * df['omega']**2
    
    # E_pot = m * g * z
    g = 9.81
    if 'z' in df.columns:
        df['E_pot'] = mass * g * df['z']
    else:
        df['E_pot'] = 0.0
        
    # E_vib = m * var(a) over sliding window N=5
    N = config.get('vib_window_size', 5)
    df['E_vib'] = 0.0 # Initialize
    
    for pid, group in df.groupby('particle_id'):
        group = group.sort_values('timestamp')
        a_series = group['a'].values
        if len(a_series) < N:
            continue
        
        # Rolling variance
        var_a = pd.Series(a_series).rolling(window=N, min_periods=1).var().values
        df.loc[group.index, 'E_vib'] = mass * var_a
        
    return df

def detect_non_stationary_segments(df: pd.DataFrame, threshold: float = 0.05) -> pd.DataFrame:
    """
    Detect non-stationary (chirped) segments using Hilbert transform on frequency.
    Flag segments where frequency variance > 5% of mean.
    """
    if 'frequency' not in df.columns:
        return df
        
    df = df.sort_values('timestamp')
    freq = df['frequency'].values
    
    if len(freq) < 10:
        return df
        
    # Analytic signal
    analytic_signal = hilbert(freq)
    instantaneous_phase = np.unwrap(np.angle(analytic_signal))
    # This is a simplified check; real instantaneous frequency derivative might be needed
    # But for variance check on the signal itself:
    window_size = 50
    if len(freq) > window_size:
        rolling_mean = pd.Series(freq).rolling(window=window_size, center=True).mean()
        rolling_std = pd.Series(freq).rolling(window=window_size, center=True).std()
        df['freq_var_ratio'] = rolling_std / rolling_mean
        df['chirp_flag'] = (df['freq_var_ratio'] > threshold).fillna(False)
    else:
        df['chirp_flag'] = False
        
    return df

def verify_chirp_segments(df: pd.DataFrame, output_path: Path) -> None:
    """
    Count excluded frames and log percentage.
    """
    if 'chirp_flag' not in df.columns:
        return
        
    total = len(df)
    excluded = df['chirp_flag'].sum()
    pct = (excluded / total * 100) if total > 0 else 0
    
    logger.info(f"Chirp exclusion: {excluded} frames ({pct:.2f}%)")
    
    if pct > 20.0:
        logger.warning(f"More than 20% of data excluded due to chirping in some window.")
        
    # Save exclusion report
    report = {
        "total_frames": int(total),
        "excluded_frames": int(excluded),
        "exclusion_percentage": float(pct),
        "timestamp": datetime.now().isoformat()
    }
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

def write_energy_output(df: pd.DataFrame, output_path: Path, sampling_metadata: Dict) -> None:
    """
    Write final energy_samples.csv and related artifacts.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Select and order columns
    cols = ['particle_id', 'timestamp', 'E_trans', 'E_rot', 'E_pot', 'E_vib', 'pot_incomplete']
    # Add optional columns if present
    optional = ['gap_flag', 'chirp_flag', 'material_type', 'frequency']
    for c in optional:
        if c in df.columns:
            cols.append(c)
            
    final_df = df[cols]
    final_df.to_csv(output_path, index=False)
    
    # Calculate hash
    hash_val = calculate_sha256(output_path)
    hash_path = output_path.parent / f"{output_path.name}.hash"
    with open(hash_path, 'w') as f:
        f.write(hash_val)
        
    # Update sampling metadata
    metadata_path = Path("artifacts/sampling_metadata.json")
    if metadata_path.exists():
        with open(metadata_path, 'r') as f:
            meta = json.load(f)
        meta['energy_samples_hash'] = hash_val
        meta['energy_samples_rows'] = len(final_df)
        with open(metadata_path, 'w') as f:
            json.dump(meta, f, indent=2)
    else:
        logger.warning("Sampling metadata not found, skipping update.")

def ingest_data(config_path: str, data_source: Optional[str] = None, sample_ratio: Optional[float] = None, local_only: bool = False) -> None:
    """
    Main ingestion pipeline: load, sync, compute, save.
    """
    config = load_config(config_path)
    
    # Validate data source
    source_id = os.environ.get('DATA_SOURCE_ID')
    if not source_id and data_source:
        source_id = data_source
    if not source_id:
        source_id = config.get('data_source', {}).get('source_id')
    
    if not source_id:
        raise IngestionError("No data source ID provided or found in config.")
        
    # Determine data path (simplified for local or assumed download)
    # In a real scenario, this would fetch from Zenodo/UCI based on source_id
    # For this implementation, we assume data is in data/raw/ or data/derived/
    data_dir = Path("data/raw")
    if not data_dir.exists():
        # Fallback to data/derived if raw doesn't exist (for test scenarios)
        data_dir = Path("data/derived")
        
    if not data_dir.exists():
        data_dir.mkdir(parents=True, exist_ok=True)
        
    # Find files
    tracking_files = find_csv_files(data_dir)
    driving_file = data_dir / "driving_signals.csv"
    
    if not tracking_files:
        raise IngestionError("No particle tracking CSV files found.")
    if not driving_file.exists():
        raise IngestionError("Driving signal file not found.")
        
    # Load data
    tracking_df = load_tracking_data(tracking_files)
    driving_df = load_driving_data(driving_file)
    
    # Sample if needed
    if sample_ratio and sample_ratio < 1.0:
        tracking_df = tracking_df.sample(frac=sample_ratio, random_state=42)
        logger.info(f"Sampled data to {sample_ratio*100}%")
        
    # Sync
    merged_df = sync_timestamps(tracking_df, driving_df)
    
    # Handle missing frames
    merged_df = handle_missing_frames(merged_df)
    
    # Check z-axis
    merged_df = check_z_axis_completeness(merged_df)
    
    # Compute derivatives
    merged_df = compute_derivatives(merged_df)
    
    # Calculate energies
    merged_df = calculate_energy_components(merged_df, config)
    
    # Detect chirps
    merged_df = detect_non_stationary_segments(merged_df)
    
    # Verify chirp segments
    chirp_report_path = Path("artifacts/exclusion_report.json")
    verify_chirp_segments(merged_df, chirp_report_path)
    
    # Write output
    output_path = Path("data/derived/energy_samples.csv")
    sampling_metadata = {
        "sample_ratio": sample_ratio,
        "seed": 42,
        "timestamp": datetime.now().isoformat()
    }
    write_energy_output(merged_df, output_path, sampling_metadata)
    
    logger.info(f"Energy calculation complete. Output: {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Ingest granular data and calculate energies.")
    parser.add_argument("--config", type=str, default="data/config.yaml", help="Path to config file.")
    parser.add_argument("--data-source", type=str, default=None, help="Data source ID.")
    parser.add_argument("--sample-ratio", type=float, default=None, help="Fraction of data to sample.")
    parser.add_argument("--local-only", action="store_true", help="Enforce local-only mode.")
    
    args = parser.parse_args()
    
    try:
        ingest_data(
            config_path=args.config,
            data_source=args.data_source,
            sample_ratio=args.sample_ratio,
            local_only=args.local_only
        )
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
