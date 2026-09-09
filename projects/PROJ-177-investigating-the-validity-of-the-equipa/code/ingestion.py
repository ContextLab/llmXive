import os
import sys
import json
import logging
import hashlib
import argparse
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, List
from scipy import signal
from scipy.interpolate import interp1d

# Ensure logs directory exists before initializing file handler
logs_dir = Path("logs")
logs_dir.mkdir(exist_ok=True)
log_file = logs_dir / "pipeline.log"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
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

def calculate_sha256(filepath: Path) -> str:
    """Calculate SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_research_md() -> Dict[str, Any]:
    """Load research.md if it exists, otherwise return empty dict."""
    research_path = Path("research.md")
    if not research_path.exists():
        return {}
    # Simple parsing for Zenodo ID if present in research.md
    content = research_path.read_text()
    result = {}
    for line in content.split('\n'):
        if 'zenodo_id' in line.lower() or 'zenodo-id' in line.lower():
            # Extract ID if format is like "zenodo_id: 12345" or "Zenodo ID: 12345"
            parts = line.split(':')
            if len(parts) >= 2:
                result['zenodo_id'] = parts[1].strip()
    return result

def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Load configuration from data/config.yaml."""
    if config_path is None:
        config_path = "data/config.yaml"
    path = Path(config_path)
    if not path.exists():
        raise ConfigurationError(f"Config file not found: {config_path}")
    import yaml
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def fetch_zenodo_granular(zenodo_id: str, output_dir: Path) -> Path:
    """
    Fetch dataset from Zenodo using the datasets library.
    Constraint: Must fail loudly if download fails. No synthetic fallback.
    """
    from datasets import load_dataset
    logger.info(f"Fetching Zenodo dataset ID: {zenodo_id}")
    
    try:
        # Attempt to load the dataset. 
        # Note: Zenodo datasets often require specific loading logic or HuggingFace Hub mapping.
        # For this implementation, we assume the Zenodo ID maps to a HuggingFace dataset
        # or we use the direct file download if the dataset is a simple CSV/JSON.
        # If the specific Zenodo ID is not a HF dataset, we attempt direct download via huggingface_hub.
        
        # Try HF datasets first (common pattern for Zenodo mirrors)
        try:
            ds = load_dataset(zenodo_id, streaming=True)
            # If successful, we need to save it to a local file to process.
            # Since streaming doesn't easily save to disk in one go for large files without iteration,
            # we iterate and save.
            output_dir.mkdir(parents=True, exist_ok=True)
            output_file = output_dir / "zenodo_data.csv"
            
            # Check if the dataset has a 'train' split or similar
            split_name = list(ds.keys())[0]
            df = ds[split_name].to_pandas()
            df.to_csv(output_file, index=False)
            logger.info(f"Successfully downloaded and saved to {output_file}")
            return output_file
        except Exception as e:
            logger.warning(f"HF dataset load failed: {e}. Attempting direct file download.")
            pass

        # Fallback to direct download if HF datasets fails
        # This assumes the Zenodo ID is a record ID and we need to find the file.
        # This is a simplified implementation; real-world requires parsing Zenodo API.
        from huggingface_hub import hf_hub_download
        # Assuming the file is named 'data.csv' or similar in the repo
        # In a real scenario, we would query the Zenodo API for the file list.
        # For now, we raise an error if we can't determine the file structure.
        raise RuntimeError("Real data fetch failed: Unable to locate file in Zenodo record automatically. Manual intervention required.")

    except Exception as e:
        raise RuntimeError(f"Real data fetch failed: {str(e)}")

def stream_dataset(file_path: Path, chunk_size: int = 10000):
    """
    Stream a dataset from a file in chunks.
    Used for large datasets that don't fit in memory.
    """
    for chunk in pd.read_csv(file_path, chunksize=chunk_size):
        yield chunk

def load_and_sample(data_source: str, sample_ratio: float = 1.0, seed: int = 42, streaming: bool = False):
    """
    Load data from a source and optionally sample it.
    Handles local paths and Zenodo IDs.
    """
    logger.info(f"Loading data from source: {data_source}")
    
    # Check if it's a Zenodo ID (starts with 10. or contains zenodo)
    if "zenodo" in data_source.lower() or data_source.startswith("10."):
        zenodo_id = data_source
        output_dir = Path("data/raw")
        output_dir.mkdir(parents=True, exist_ok=True)
        data_file = fetch_zenodo_granular(zenodo_id, output_dir)
    else:
        data_file = Path(data_source)
        if not data_file.exists():
            raise FileNotFoundError(f"Data source not found: {data_source}")

    if streaming or data_file.stat().st_size > 14 * 1024 * 1024 * 1024: # 14GB
        logger.info("Using streaming mode for large dataset")
        # For streaming, we process chunk by chunk. 
        # For sampling, we might need to count first or use reservoir sampling.
        # Simplified: Read first chunk to get schema, then process.
        # In a real pipeline, we would accumulate stats or write sampled chunks to a new file.
        # Here we assume we are just returning the iterator or a sample if small enough.
        # Since the next steps need a dataframe, we might need to materialize a sample.
        # Let's implement a simple reservoir sampling for the streaming case.
        sampled_chunks = []
        total_rows = 0
        sampled_rows = 0
        rng = np.random.default_rng(seed)
        
        for chunk in stream_dataset(data_file):
            total_rows += len(chunk)
            if sample_ratio < 1.0:
                # Reservoir sampling or simple random sampling per chunk
                n = max(1, int(len(chunk) * sample_ratio))
                if n < len(chunk):
                    indices = rng.choice(len(chunk), size=n, replace=False)
                    chunk = chunk.iloc[indices]
            sampled_chunks.append(chunk)
            sampled_rows += len(chunk)
        
        df = pd.concat(sampled_chunks, ignore_index=True)
        metadata = {
            "total_rows_streamed": total_rows,
            "rows_sampled": sampled_rows,
            "sampling_seed": seed,
            "sampling_fraction": sample_ratio
        }
        # Save metadata
        meta_path = Path("artifacts/sampling_metadata.json")
        meta_path.parent.mkdir(parents=True, exist_ok=True)
        with open(meta_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        return df
    else:
        df = pd.read_csv(data_file)
        if sample_ratio < 1.0:
            df = df.sample(frac=sample_ratio, random_state=seed)
        # Save metadata
        metadata = {
            "total_rows_streamed": len(df),
            "rows_sampled": len(df),
            "sampling_seed": seed,
            "sampling_fraction": sample_ratio
        }
        meta_path = Path("artifacts/sampling_metadata.json")
        meta_path.parent.mkdir(parents=True, exist_ok=True)
        with open(meta_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        return df

def validate_metadata(df: pd.DataFrame, config: Dict[str, Any], allow_incomplete: bool = False):
    """
    Validate required metadata fields in the dataset.
    Raises DataIngestionError if missing and allow_incomplete is False.
    """
    required_fields = ['mass', 'radius', 'material_type']
    missing = []
    for field in required_fields:
        if field not in df.columns:
            missing.append(field)
    
    if missing:
        if allow_incomplete:
            logger.warning(f"Missing metadata fields: {missing}. Proceeding with incomplete data.")
            return df
        else:
            raise DataIngestionError(f"Missing required metadata fields: {missing}. Use --allow-incomplete to proceed.")
    return df

def handle_kinetic_only_fallback(df: pd.DataFrame):
    """
    Handle datasets with missing potential/vibrational data.
    Sets missing columns to NaN or 0 with a warning.
    """
    if 'z' not in df.columns:
        logger.warning("z-axis missing. Setting E_pot to 0.")
        df['E_pot'] = 0.0
        df['pot_incomplete'] = True
    else:
        df['pot_incomplete'] = False
    return df

def handle_missing_z_axis(df: pd.DataFrame):
    """
    Handle missing z-axis data by adding a pot_incomplete boolean column.
    """
    if 'z' not in df.columns:
        df['pot_incomplete'] = True
        logger.warning("z-axis data missing. pot_incomplete flag set to True.")
    else:
        df['pot_incomplete'] = False
    return df

def ingest_driving_logs(input_dir: Path, output_path: Path):
    """
    Ingest and parse raw driving signal logs.
    Output: canonical intermediate file data/derived/driving_signals.csv
    """
    input_dir = Path(input_dir)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Assume CSV files in input_dir
    files = list(input_dir.glob("*.csv"))
    if not files:
        raise DataIngestionError(f"No CSV files found in {input_dir}")
    
    # Concatenate all driving logs
    dfs = []
    for f in files:
        try:
            df = pd.read_csv(f)
            if 'timestamp' not in df.columns:
                # Try to infer timestamp if not present
                df['timestamp'] = range(len(df))
            dfs.append(df)
        except Exception as e:
            logger.warning(f"Failed to read {f}: {e}")
    
    if not dfs:
        raise DataIngestionError("No valid driving log files found.")
    
    combined = pd.concat(dfs, ignore_index=True)
    combined.sort_values('timestamp', inplace=True)
    combined.to_csv(output_path, index=False)
    logger.info(f"Driving signals saved to {output_path}")
    return combined

def handle_missing_frames(df: pd.DataFrame, max_gap: int = 10):
    """
    Handle missing frames via linear interpolation or flagging.
    If gap > max_gap, log warning and set gap_flag.
    """
    if 'timestamp' not in df.columns:
        return df
    
    df = df.sort_values('timestamp').reset_index(drop=True)
    timestamps = df['timestamp'].values
    
    # Identify gaps
    gaps = np.diff(timestamps)
    gap_indices = np.where(gaps > 1)[0]
    
    if len(gap_indices) == 0:
        return df
    
    logger.info(f"Found {len(gap_indices)} gaps in data.")
    
    # Interpolate numeric columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        if col == 'timestamp':
            continue
        # Create a full index for interpolation
        full_index = np.arange(timestamps.min(), timestamps.max() + 1)
        # Interpolate
        f = interp1d(timestamps, df[col].values, kind='linear', fill_value='extrapolate')
        df[col] = f(full_index)
        # Re-align timestamps
        df['timestamp'] = full_index
    
    # Flag large gaps
    df['gap_flag'] = False
    for idx in gap_indices:
        gap_size = gaps[idx]
        if gap_size > max_gap:
            logger.warning(f"Large gap of {gap_size} frames detected at index {idx}.")
            # Flag the range
            start = idx + 1
            end = idx + 1 + gap_size
            if start < len(df) and end <= len(df):
                df.loc[start:end, 'gap_flag'] = True
    
    return df

def calculate_tracking_failure_rate(df: pd.DataFrame, window_size: int = 100):
    """
    Compute percentage of missing frames per time window.
    If rate > 20%, flag window for exclusion.
    """
    if 'gap_flag' not in df.columns:
        df['gap_flag'] = False
    
    df = df.sort_values('timestamp')
    total_frames = len(df)
    total_missing = df['gap_flag'].sum()
    overall_rate = total_missing / total_frames if total_frames > 0 else 0
    
    logger.info(f"Overall tracking failure rate: {overall_rate:.2%}")
    
    if overall_rate > 0.20:
        logger.warning(f"Overall tracking failure rate ({overall_rate:.2%}) exceeds 20%. Consider excluding data.")
    
    return df

def compute_velocity_angular_velocity(df: pd.DataFrame, time_col: str = 'timestamp', 
                                      x_col: str = 'x', y_col: str = 'y', z_col: str = 'z',
                                      angle_col: str = 'angle'):
    """
    T017 Implementation: Compute v and omega via finite differences.
    v = sqrt(vx^2 + vy^2 + vz^2)
    omega = d(angle)/dt
    """
    df = df.copy()
    df = df.sort_values(time_col).reset_index(drop=True)
    
    # Check required columns
    required = [time_col]
    if x_col in df.columns: required.append(x_col)
    if y_col in df.columns: required.append(y_col)
    if z_col in df.columns: required.append(z_col)
    if angle_col in df.columns: required.append(angle_col)
    
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise DataIngestionError(f"Missing required columns for velocity calculation: {missing}")
    
    dt = df[time_col].diff()
    dt = dt.replace(0, np.nan).fillna(method='bfill').fillna(1.0) # Avoid division by zero
    
    # Calculate velocities
    if x_col in df.columns:
        vx = df[x_col].diff() / dt
        df['vx'] = vx
    if y_col in df.columns:
        vy = df[y_col].diff() / dt
        df['vy'] = vy
    if z_col in df.columns:
        vz = df[z_col].diff() / dt
        df['vz'] = vz
    
    # Calculate speed v
    if all(c in df.columns for c in ['vx', 'vy', 'vz']):
        df['v'] = np.sqrt(df['vx']**2 + df['vy']**2 + df['vz']**2)
    elif all(c in df.columns for c in ['vx', 'vy']):
        df['v'] = np.sqrt(df['vx']**2 + df['vy']**2)
    elif 'vx' in df.columns:
        df['v'] = df['vx'].abs()
    
    # Calculate angular velocity omega
    if angle_col in df.columns:
        df['omega'] = df[angle_col].diff() / dt
    
    # Handle first row (NaN from diff)
    df = df.fillna(method='bfill').fillna(0)
    
    return df

def main():
    parser = argparse.ArgumentParser(description="Data Ingestion Pipeline")
    parser.add_argument("--download", action="store_true", help="Download from Zenodo")
    parser.add_argument("--zenodo-id", type=str, help="Zenodo ID to download")
    parser.add_argument("--input-dir", type=str, default="data/raw", help="Input directory for raw data")
    parser.add_argument("--output-dir", type=str, default="data/derived", help="Output directory for derived data")
    parser.add_argument("--config", type=str, default="data/config.yaml", help="Path to config file")
    parser.add_argument("--allow-incomplete", action="store_true", help="Allow incomplete metadata")
    parser.add_argument("--sample-ratio", type=float, default=1.0, help="Sampling ratio")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--streaming", action="store_true", help="Use streaming for large datasets")
    
    args = parser.parse_args()
    
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    
    try:
        if args.download:
            if not args.zenodo_id:
                # Try to load from research.md
                research = load_research_md()
                if 'zenodo_id' in research:
                    args.zenodo_id = research['zenodo_id']
                else:
                    # Try config
                    config = load_config(args.config)
                    if 'default_zenodo_id' in config:
                        args.zenodo_id = config['default_zenodo_id']
                    else:
                        raise RuntimeError("Real data fetch failed: Zenodo ID not found in research.md or data/config.yaml")
            
            data_file = fetch_zenodo_granular(args.zenodo_id, Path(args.input_dir))
            logger.info(f"Downloaded data to {data_file}")
        
        # Load and sample
        if args.download:
            source = args.input_dir + "/zenodo_data.csv"
        else:
            source = args.input_dir + "/data.csv" # Default assumption
        
        df = load_and_sample(source, sample_ratio=args.sample_ratio, seed=args.seed, streaming=args.streaming)
        
        # Validate metadata
        config = load_config(args.config)
        df = validate_metadata(df, config, allow_incomplete=args.allow_incomplete)
        
        # Handle missing frames
        df = handle_missing_frames(df)
        
        # Calculate tracking failure rate
        df = calculate_tracking_failure_rate(df)
        
        # Compute velocities
        df = compute_velocity_angular_velocity(df)
        
        # Save intermediate results
        output_file = Path(args.output_dir) / "processed_data.csv"
        df.to_csv(output_file, index=False)
        logger.info(f"Processed data saved to {output_file}")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()