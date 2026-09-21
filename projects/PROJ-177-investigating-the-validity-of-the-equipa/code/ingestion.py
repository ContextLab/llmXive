"""
Data ingestion and energy calculation module for granular system analysis.
Handles loading, preprocessing, and energy component calculation.
"""

import os
import sys
import json
import logging
import hashlib
import argparse
import math
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional, Union
import pandas as pd
import numpy as np
from scipy.signal import hilbert, welch
from scipy.interpolate import interp1d
import yaml

# Configure logging to file (ensure directory exists first)
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / "pipeline.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class DataIngestionError(Exception):
    """Custom exception for data ingestion errors."""
    pass


class ConfigurationError(Exception):
    """Custom exception for configuration errors."""
    pass


class DataExclusionWarning(Warning):
    """Warning for data exclusion events."""
    pass


def calculate_sha256(file_path: str) -> str:
    """Calculate SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def load_research_md() -> Optional[str]:
    """Load Zenodo ID from research.md if present."""
    research_path = Path("research.md")
    if research_path.exists():
        content = research_path.read_text()
        # Simple heuristic: look for zenodo-id in the content
        for line in content.splitlines():
            if "zenodo-id" in line.lower() or "zenodo" in line.lower():
                # Extract ID if possible
                parts = line.split()
                for part in parts:
                    if part.replace('.', '').replace('-', '').isdigit() or 'zenodo' in part.lower():
                        return part
    return None


def load_config(config_path: str = "data/config.yaml") -> Dict[str, Any]:
    """Load configuration from YAML file."""
    if not os.path.exists(config_path):
        raise ConfigurationError(f"Config file not found: {config_path}")
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def fetch_zenodo_granular(zenodo_id: str, output_dir: str = "data/raw") -> str:
    """
    Fetch granular dataset from Zenodo.
    Uses streaming if dataset is large.
    """
    from datasets import load_dataset
    from huggingface_hub import hf_hub_download

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    try:
        # Try to load as HuggingFace dataset (Zenodo datasets often mirrored there)
        logger.info(f"Attempting to fetch dataset from Zenodo ID: {zenodo_id}")
        dataset = load_dataset(zenodo_id, streaming=True)
        # For simplicity, assume the first split is the data
        split_name = list(dataset.keys())[0]
        # Save to parquet or csv if needed, or return iterator
        # For this implementation, we'll assume we need to download the file
        # Since we can't easily stream to a file with the datasets library without knowing the file type,
        # we'll try to download the file directly if we can infer the filename.
        # In a real scenario, we'd inspect the dataset config.
        # Fallback: try to download a likely file name
        # This is a simplified approach; real implementation would need more robust file discovery.
        file_name = f"granular_data_{zenodo_id}.csv"
        # Attempt to download from hub if it's a HF mirror
        try:
            local_file = hf_hub_download(repo_id=zenodo_id, filename=file_name, repo_type="dataset")
            return local_file
        except Exception as e:
            logger.warning(f"Direct file download failed: {e}. Trying full dataset load.")
            # Fallback: load full dataset into memory (not ideal for large data)
            df = dataset[split_name].to_pandas()
            output_file = output_path / file_name
            df.to_csv(output_file, index=False)
            return str(output_file)
    except Exception as e:
        raise RuntimeError(f"Real data fetch failed: {str(e)}")


def stream_dataset(file_path: str, chunk_size: int = 10000) -> pd.DataFrame:
    """
    Stream a large dataset in chunks.
    Returns a DataFrame with the sampled data.
    """
    chunks = []
    for chunk in pd.read_csv(file_path, chunksize=chunk_size):
        chunks.append(chunk)
    return pd.concat(chunks, ignore_index=True)


def load_and_sample(
    data_source: str,
    sample_ratio: float = 1.0,
    seed: Optional[int] = None,
    streaming: bool = False
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Load data from source and sample if necessary.
    """
    logger.info(f"Loading data from: {data_source}")
    if seed is not None:
        np.random.seed(seed)

    if streaming or os.path.getsize(data_source) > 14 * 1024 * 1024 * 1024:  # 14 GB
        df = stream_dataset(data_source)
    else:
        df = pd.read_csv(data_source)

    total_rows = len(df)
    if sample_ratio < 1.0:
        if seed is not None:
            df = df.sample(frac=sample_ratio, random_state=seed)
        else:
            df = df.sample(frac=sample_ratio)

    sampling_metadata = {
        "total_rows_streamed": total_rows,
        "rows_sampled": len(df),
        "sampling_seed": seed,
        "sampling_fraction": sample_ratio,
        "data_source": data_source
    }

    return df, sampling_metadata


def validate_metadata(df: pd.DataFrame, config: Dict[str, Any], allow_incomplete: bool = False) -> pd.DataFrame:
    """
    Validate required metadata fields in the dataset.
    """
    required_fields = ['mass', 'radius', 'material_type']
    missing_fields = [f for f in required_fields if f not in df.columns]

    if missing_fields:
        if not allow_incomplete:
            raise DataIngestionError(f"Missing required fields: {missing_fields}")
        else:
            logger.warning(f"Missing fields: {missing_fields}. Proceeding with incomplete data.")
            for field in missing_fields:
                df[field] = np.nan

    # Validate against config if material_type is present
    if 'material_type' in df.columns and 'materials' in config:
        valid_materials = list(config['materials'].keys())
        invalid_materials = df[~df['material_type'].isin(valid_materials)]['material_type'].unique()
        if len(invalid_materials) > 0:
            logger.warning(f"Found invalid material types: {invalid_materials}")

    return df


def handle_kinetic_only_fallback(df: pd.DataFrame) -> pd.DataFrame:
    """
    Handle datasets with incomplete data by calculating only available energy components.
    """
    logger.warning("Handling kinetic-only fallback. Setting potential/vibrational energy to NaN.")
    if 'E_pot' not in df.columns:
        df['E_pot'] = np.nan
    if 'E_vib' not in df.columns:
        df['E_vib'] = np.nan
    return df


def handle_missing_z_axis(df: pd.DataFrame) -> pd.DataFrame:
    """
    Handle missing z-axis data by adding a pot_incomplete flag.
    """
    if 'z' not in df.columns:
        df['pot_incomplete'] = True
        df['E_pot'] = np.nan
        logger.warning("Missing z-axis data. Set pot_incomplete=True and E_pot=NaN.")
    else:
        df['pot_incomplete'] = False
    return df


def ingest_driving_logs(log_dir: str = "data/raw") -> pd.DataFrame:
    """
    Ingest and parse raw driving signal logs.
    Output: data/derived/driving_signals.csv
    """
    log_path = Path(log_dir)
    if not log_path.exists():
        raise DataIngestionError(f"Log directory not found: {log_dir}")

    # Assume CSV or JSON logs in the directory
    driving_data = []
    for file in log_path.glob("*"):
        if file.suffix in ['.csv', '.json']:
            try:
                if file.suffix == '.csv':
                    df = pd.read_csv(file)
                else:
                    df = pd.read_json(file)
                driving_data.append(df)
            except Exception as e:
                logger.warning(f"Failed to load {file}: {e}")

    if not driving_data:
        raise DataIngestionError("No valid driving log files found.")

    combined_df = pd.concat(driving_data, ignore_index=True)

    # Ensure timestamp column exists and is sorted
    if 'timestamp' not in combined_df.columns:
        # Assume first column is timestamp
        combined_df = combined_df.rename(columns={combined_df.columns[0]: 'timestamp'})

    combined_df = combined_df.sort_values('timestamp')

    # Write to derived
    derived_dir = Path("data/derived")
    derived_dir.mkdir(exist_ok=True)
    output_path = derived_dir / "driving_signals.csv"
    combined_df.to_csv(output_path, index=False)
    logger.info(f"Driving signals written to: {output_path}")

    return combined_df


def handle_missing_frames(df: pd.DataFrame, max_gap: int = 10) -> pd.DataFrame:
    """
    Handle missing frames via linear interpolation or flagging.
    """
    if 'timestamp' not in df.columns:
        return df

    df = df.sort_values('timestamp')
    df['gap_flag'] = False

    # Detect gaps in timestamp
    time_diff = df['timestamp'].diff()
    median_time_diff = time_diff.median()
    if pd.isna(median_time_diff):
        return df

    gap_threshold = median_time_diff * max_gap
    gap_indices = time_diff[time_diff > gap_threshold].index
    df.loc[gap_indices, 'gap_flag'] = True

    # Interpolate numeric columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    df[numeric_cols] = df[numeric_cols].interpolate(method='linear')

    return df


def calculate_tracking_failure_rate(df: pd.DataFrame, window_size: int = 100) -> Tuple[float, pd.DataFrame]:
    """
    Calculate the percentage of missing frames per time window.
    """
    if 'gap_flag' not in df.columns:
        return 0.0, df

    df['gap_flag'] = df['gap_flag'].astype(int)
    df['rolling_gap_rate'] = df['gap_flag'].rolling(window=window_size, center=True).mean()
    failure_rate = df['gap_flag'].mean()

    # Flag windows with > 20% missing frames
    df['exclude_window'] = df['rolling_gap_rate'] > 0.20

    return failure_rate, df


def compute_velocity_angular_velocity(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute velocity (v) and angular velocity (omega) via finite differences.
    """
    df = df.sort_values('timestamp')

    # Velocity from position derivatives
    if all(col in df.columns for col in ['x', 'y', 'z']):
        dt = df['timestamp'].diff()
        dx = df['x'].diff()
        dy = df['y'].diff()
        dz = df['z'].diff()

        # Avoid division by zero
        dt = dt.replace(0, np.nan).fillna(dt.median())

        vx = dx / dt
        vy = dy / dt
        vz = dz / dt

        df['v'] = np.sqrt(vx**2 + vy**2 + vz**2)
    elif 'v' not in df.columns:
        logger.warning("Position data missing, cannot compute velocity.")
        df['v'] = 0.0

    # Angular velocity from orientation derivatives (simplified)
    if all(col in df.columns for col in ['theta', 'phi', 'psi']):
        dtheta = df['theta'].diff()
        dphi = df['phi'].diff()
        dpsi = df['psi'].diff()

        df['omega'] = np.sqrt(dtheta**2 + dphi**2 + dpsi**2) / dt
    elif 'omega' not in df.columns:
        logger.warning("Orientation data missing, cannot compute angular velocity.")
        df['omega'] = 0.0

    return df


def detect_non_stationary_segments(df: pd.DataFrame, signal_col: str = 'amplitude', window_size: int = 100) -> pd.DataFrame:
    """
    Detect non-stationary (chirped) segments using Hilbert transform.
    """
    if signal_col not in df.columns:
        logger.warning(f"Signal column {signal_col} not found. Skipping non-stationary detection.")
        return df

    signal = df[signal_col].values
    if len(signal) < window_size:
        return df

    # Compute instantaneous frequency using Hilbert transform
    analytic_signal = hilbert(signal)
    instantaneous_phase = np.unwrap(np.angle(analytic_signal))
    instantaneous_freq = np.diff(instantaneous_phase) / (2.0 * np.pi)

    # Pad to match original length
    instantaneous_freq = np.concatenate(([instantaneous_freq[0]], instantaneous_freq))

    df['instantaneous_freq'] = instantaneous_freq

    # Detect chirps (rapid change in frequency)
    freq_diff = np.diff(df['instantaneous_freq'])
    df['is_chirp'] = np.abs(freq_diff) > np.std(freq_diff) * 2

    return df


def handle_non_stationary_segments(
    df: pd.DataFrame,
    strategy: str = 'exclude',
    chirp_result_path: str = "artifacts/chirp_handling_result.csv"
) -> pd.DataFrame:
    """
    Handle non-stationary segments by excluding or binning.
    """
    derived_dir = Path("data/derived")
    derived_dir.mkdir(exist_ok=True)
    artifacts_dir = Path("artifacts")
    artifacts_dir.mkdir(exist_ok=True)

    if 'is_chirp' not in df.columns:
        logger.warning("No chirp detection results found. Skipping non-stationary handling.")
        return df

    chirp_indices = df[df['is_chirp']].index
    result_data = []

    if strategy == 'exclude':
        df = df[~df['is_chirp']].copy()
        for idx in chirp_indices:
          result_data.append({'timestamp': df.loc[idx, 'timestamp'] if 'timestamp' in df.columns else idx, 'strategy': 'excluded', 'value': idx})
    elif strategy == 'bin':
        # Assign to frequency bin (simplified: use median frequency of the segment)
        if 'instantaneous_freq' in df.columns:
            df['frequency_bin'] = pd.qcut(df['instantaneous_freq'], q=10, labels=False, duplicates='drop')
        for idx in chirp_indices:
          result_data.append({'timestamp': df.loc[idx, 'timestamp'] if 'timestamp' in df.columns else idx, 'strategy': 'binned', 'value': df.loc[idx, 'frequency_bin'] if 'frequency_bin' in df.columns else 0})
    else:
        raise ValueError(f"Invalid strategy: {strategy}. Use 'exclude' or 'bin'.")

    # Write chirp handling result
    result_df = pd.DataFrame(result_data)
    result_df.to_csv(chirp_result_path, index=False)
    logger.info(f"Chirp handling result written to: {chirp_result_path}")

    return df


def verify_chirp_segments(df: pd.DataFrame, exclusion_report_path: str = "artifacts/exclusion_report.json") -> pd.DataFrame:
    """
    Verify chirp segments and count excluded frames.
    """
    artifacts_dir = Path("artifacts")
    artifacts_dir.mkdir(exist_ok=True)

    if 'is_chirp' not in df.columns:
        logger.warning("No chirp detection results found. Skipping verification.")
        return df

    total_frames = len(df)
    excluded_frames = df['is_chirp'].sum()
    exclusion_rate = excluded_frames / total_frames if total_frames > 0 else 0

    exclusion_report = {
        "total_frames": total_frames,
        "excluded_frames": int(excluded_frames),
        "exclusion_rate": exclusion_rate,
        "bins_insufficient_data": []
    }

    # Check per-bin data sufficiency
    if 'frequency_bin' in df.columns:
        bin_counts = df.groupby('frequency_bin').size()
        insufficient_bins = bin_counts[bin_counts < 50].index.tolist()
        exclusion_report["bins_insufficient_data"] = insufficient_bins

        # Exclude bins with insufficient data
        if len(insufficient_bins) > 0:
            df = df[~df['frequency_bin'].isin(insufficient_bins)]

    # Log warning if exclusion rate is high
    if exclusion_rate > 0.20:
        logger.warning(f"High exclusion rate: {exclusion_rate:.2%}. Data may be insufficient.")
        data_exclusion_warning = DataExclusionWarning(f"Exclusion rate exceeds 20%: {exclusion_rate:.2%}")
        warnings.warn(data_exclusion_warning, DataExclusionWarning)

    with open(exclusion_report_path, 'w') as f:
        json.dump(exclusion_report, f, indent=2)
    logger.info(f"Exclusion report written to: {exclusion_report_path}")

    return df


def calculate_energy_components(
    df: pd.DataFrame,
    config: Dict[str, Any],
    driving_signal_path: Optional[str] = None
) -> pd.DataFrame:
    """
    Calculate E_trans, E_rot, E_pot, and E_vib using independent physics formulas.

    Formulas:
    E_trans = 0.5 * m * v^2
    E_rot = 0.5 * I * omega^2
    E_pot = m * g * z
    E_vib = PSD Integration of driving signal cross-correlation
    """
    logger.info("Calculating energy components...")

    # Get config parameters
    g = 9.81  # m/s^2
    mass = config.get('mass', 0.01)  # default 10g if not specified
    radius = config.get('radius', 0.005)  # default 5mm
    material_type = config.get('material_type', 'steel')

    # Get material-specific properties if available
    if 'materials' in config and material_type in config['materials']:
        mat_props = config['materials'][material_type]
        mass = mat_props.get('mass', mass)
        radius = mat_props.get('radius', radius)

    # Moment of inertia for sphere: I = (2/5) * m * r^2
    inertia = (2.0 / 5.0) * mass * (radius ** 2)

    # Ensure required columns exist
    if 'v' not in df.columns:
        df['v'] = 0.0
    if 'omega' not in df.columns:
        df['omega'] = 0.0
    if 'z' not in df.columns:
        df['z'] = 0.0
        df['pot_incomplete'] = True
    else:
        df['pot_incomplete'] = False

    # Calculate translational energy
    df['E_trans'] = 0.5 * mass * (df['v'] ** 2)

    # Calculate rotational energy
    df['E_rot'] = 0.5 * inertia * (df['omega'] ** 2)

    # Calculate potential energy
    df['E_pot'] = mass * g * df['z']

    # Calculate vibrational energy via PSD integration of driving signal
    if driving_signal_path and os.path.exists(driving_signal_path):
        try:
            driving_df = pd.read_csv(driving_signal_path)
            if 'amplitude' in driving_df.columns:
                signal = driving_df['amplitude'].values
                # Use Welch's method to estimate PSD
                freqs, psd = welch(signal, fs=100.0, nperseg=256)  # Assume 100Hz sampling
                # Integrate PSD to get total power (vibrational energy proxy)
                total_power = np.trapz(psd, freqs)
                # Normalize by number of frames and scale factor
                df['E_vib'] = total_power / len(df)
            else:
                logger.warning("Amplitude column not found in driving signal. Setting E_vib to 0.")
                df['E_vib'] = 0.0
        except Exception as e:
            logger.warning(f"Failed to calculate E_vib from driving signal: {e}. Setting to 0.")
            df['E_vib'] = 0.0
    else:
        logger.warning("Driving signal path not provided or file not found. Setting E_vib to 0.")
        df['E_vib'] = 0.0

    # Ensure all energies are in Joules (kg*m^2/s^2)
    # Current units: mass (kg), v (m/s), omega (rad/s), z (m) -> Joules
    logger.info("Energy components calculated successfully.")

    return df


def main():
    """Main entry point for ingestion module."""
    parser = argparse.ArgumentParser(description="Data Ingestion and Energy Calculation")
    parser.add_argument('--config', type=str, default='data/config.yaml', help='Path to config file')
    parser.add_argument('--data-source', type=str, required=True, help='Path to data source')
    parser.add_argument('--driving-signal', type=str, default='data/derived/driving_signals.csv', help='Path to driving signal file')
    parser.add_argument('--sample-ratio', type=float, default=1.0, help='Sampling ratio')
    parser.add_argument('--seed', type=int, default=None, help='Random seed')
    parser.add_argument('--streaming', action='store_true', help='Use streaming for large datasets')
    parser.add_argument('--allow-incomplete', action='store_true', help='Allow incomplete metadata')
    parser.add_argument('--chirp-handling', type=str, default='exclude', choices=['exclude', 'bin'], help='Strategy for handling chirps')
    args = parser.parse_args()

    try:
        # Load config
        config = load_config(args.config)

        # Load and sample data
        df, sampling_metadata = load_and_sample(
            args.data_source,
            sample_ratio=args.sample_ratio,
            seed=args.seed,
            streaming=args.streaming
        )

        # Validate metadata
        df = validate_metadata(df, config, allow_incomplete=args.allow_incomplete)

        # Handle missing z-axis
        df = handle_missing_z_axis(df)

        # Ingest driving logs if not already done
        if not os.path.exists(args.driving_signal):
            logger.info("Ingesting driving logs...")
            ingest_driving_logs()

        # Handle missing frames
        df = handle_missing_frames(df)

        # Calculate tracking failure rate
        failure_rate, df = calculate_tracking_failure_rate(df)

        # Compute velocity and angular velocity
        df = compute_velocity_angular_velocity(df)

        # Detect non-stationary segments
        if 'amplitude' in df.columns or os.path.exists(args.driving_signal):
            df = detect_non_stationary_segments(df)

        # Handle non-stationary segments
        df = handle_non_stationary_segments(df, strategy=args.chirp_handling)

        # Verify chirp segments
        df = verify_chirp_segments(df)

        # Calculate energy components
        df = calculate_energy_components(df, config, driving_signal_path=args.driving_signal)

        # Output final energy data
        derived_dir = Path("data/derived")
        derived_dir.mkdir(exist_ok=True)
        output_path = derived_dir / "energy_samples.csv"
        df.to_csv(output_path, index=False)
        logger.info(f"Energy samples written to: {output_path}")

        # Save sampling metadata
        artifacts_dir = Path("artifacts")
        artifacts_dir.mkdir(exist_ok=True)
        with open(artifacts_dir / "sampling_metadata.json", 'w') as f:
            json.dump(sampling_metadata, f, indent=2)

        # Generate hash
        hash_value = calculate_sha256(output_path)
        with open(artifacts_dir / "energy_samples.hash", 'w') as f:
            f.write(hash_value)

        logger.info("Ingestion pipeline completed successfully.")

    except Exception as e:
        logger.error(f"Ingestion pipeline failed: {e}")
        raise


if __name__ == "__main__":
    main()
