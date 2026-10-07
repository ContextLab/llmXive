import os
import sys
import logging
import hashlib
import glob
from typing import Optional, List, Tuple, Dict, Any
import pandas as pd
import pyarrow.parquet as pq
import pyarrow as pa

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def ensure_data_dirs():
    """Ensure necessary directories exist."""
    dirs = ['data/raw', 'data/processed', 'data/results']
    for d in dirs:
        os.makedirs(d, exist_ok=True)
    logger.info(f"Ensured directories: {dirs}")

def calculate_sha256(filepath):
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_state(state_path='state/projects/PROJ-041-evaluating-the-use-of-graph-neural-netwo.yaml'):
    """Load project state file."""
    if not os.path.exists(state_path):
        return {}
    try:
        import yaml
        with open(state_path, 'r') as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        logger.warning(f"Could not load state file {state_path}: {e}")
        return {}

def update_state(state_path='state/projects/PROJ-041-evaluating-the-use-of-graph-neural-netwo.yaml', data=None):
    """Update project state file."""
    if not os.path.exists(os.path.dirname(state_path)):
        os.makedirs(os.path.dirname(state_path), exist_ok=True)
    try:
        import yaml
        current_state = load_state(state_path)
        if data:
            current_state.update(data)
        with open(state_path, 'w') as f:
            yaml.dump(current_state, f)
        logger.info(f"Updated state file: {state_path}")
    except Exception as e:
        logger.error(f"Could not update state file {state_path}: {e}")

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize column names and types for NetFlow data.
    Ensures standard columns: src_ip, dst_ip, packets, timestamp
    """
    # Map common variations to standard names
    col_mapping = {
        'src_ip': ['src_ip', 'source_ip', 'SrcIP', 'Source_IP', 'sip'],
        'dst_ip': ['dst_ip', 'dest_ip', 'destination_ip', 'DstIP', 'Dest_IP', 'dip'],
        'packets': ['packets', 'pkt_count', 'packet_count', 'Packets', 'count'],
        'timestamp': ['timestamp', 'time', 'ts', 'Timestamp', 'unix_ts', 'start_time']
    }

    normalized_df = df.copy()
    found_cols = {}

    for standard_name, variations in col_mapping.items():
        for var in variations:
            if var in normalized_df.columns:
                found_cols[standard_name] = var
                break

    # Rename columns
    rename_map = {v: k for k, v in found_cols.items()}
    if rename_map:
        normalized_df = normalized_df.rename(columns=rename_map)

    # Ensure required columns exist
    required = ['src_ip', 'dst_ip', 'packets', 'timestamp']
    missing = [col for col in required if col not in normalized_df.columns]
    if missing:
        raise ValueError(f"Missing required columns after normalization: {missing}")

    # Type conversions
    normalized_df['src_ip'] = normalized_df['src_ip'].astype(str)
    normalized_df['dst_ip'] = normalized_df['dst_ip'].astype(str)
    normalized_df['packets'] = pd.to_numeric(normalized_df['packets'], errors='coerce').fillna(0).astype(int)
    
    # Handle timestamp
    if normalized_df['timestamp'].dtype == 'object':
        normalized_df['timestamp'] = pd.to_datetime(normalized_df['timestamp'], errors='coerce')
    normalized_df['timestamp'] = normalized_df['timestamp'].astype('int64') // 10**9  # Convert to Unix timestamp if datetime

    return normalized_df

def load_raw_flows(filepath: str) -> pd.DataFrame:
    """
    Load raw NetFlow data from CSV or Parquet.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Raw data file not found: {filepath}")
    
    logger.info(f"Loading raw flows from: {filepath}")
    
    if filepath.endswith('.parquet'):
        df = pd.read_parquet(filepath)
    elif filepath.endswith('.csv'):
        df = pd.read_csv(filepath)
    else:
        # Try to infer based on content or default to CSV
        try:
            df = pd.read_parquet(filepath)
        except:
            df = pd.read_csv(filepath)
    
    logger.info(f"Loaded {len(df)} rows. Columns: {list(df.columns)}")
    return df

def process_scenario(raw_filepath: str, output_dir: str = 'data/processed') -> Tuple[str, pd.DataFrame]:
    """
    Process a single scenario file:
    1. Load raw data
    2. Normalize columns
    3. Extract scenario name from filename
    4. Return processed dataframe and output path
    """
    scenario_name = os.path.splitext(os.path.basename(raw_filepath))[0]
    output_filename = f"raw_flows_{scenario_name}.parquet"
    output_path = os.path.join(output_dir, output_filename)
    
    # Load and normalize
    df = load_raw_flows(raw_filepath)
    df_normalized = normalize_columns(df)
    
    # Sort by timestamp to ensure temporal order
    df_normalized = df_normalized.sort_values('timestamp').reset_index(drop=True)
    
    return scenario_name, df_normalized

def write_processed_flows(df: pd.DataFrame, output_path: str):
    """
    Write processed flows to Parquet file.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_parquet(output_path, index=False)
    logger.info(f"Wrote processed flows to: {output_path} ({len(df)} rows)")

def ingest_all_scenarios():
    """
    Main entry point to ingest all scenarios from data/raw.
    """
    ensure_data_dirs()
    
    # Find all raw data files
    raw_files = glob.glob('data/raw/*.csv') + glob.glob('data/raw/*.parquet')
    
    if not raw_files:
        logger.warning("No raw data files found in data/raw/")
        return

    logger.info(f"Found {len(raw_files)} raw data files to process.")
    
    processed_scenarios = []
    
    for raw_file in raw_files:
        try:
            logger.info(f"Processing: {raw_file}")
            scenario_name, df = process_scenario(raw_file)
            output_path = os.path.join('data/processed', f"raw_flows_{scenario_name}.parquet")
            write_processed_flows(df, output_path)
            processed_scenarios.append(scenario_name)
            
            # Update state with artifact hash
            file_hash = calculate_sha256(output_path)
            update_state(data={
                'artifact_hashes': {
                    f"raw_flows_{scenario_name}.parquet": file_hash
                }
            })
            
        except Exception as e:
            logger.error(f"Failed to process {raw_file}: {e}")
            raise

    logger.info(f"Successfully processed {len(processed_scenarios)} scenarios: {processed_scenarios}")
    return processed_scenarios

def main():
    """
    CLI entry point for data ingestion.
    """
    try:
        scenarios = ingest_all_scenarios()
        print(f"Ingestion complete. Processed scenarios: {scenarios}")
        return 0
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
