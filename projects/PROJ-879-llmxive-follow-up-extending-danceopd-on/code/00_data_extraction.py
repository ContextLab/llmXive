"""
Data Extraction Module for DanceOPD Follow-up
Extracts and streams final dataset from filtered teacher ground truth.
"""
import argparse
import sys
import json
import signal
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import pyarrow.parquet as pq
import hashlib
import os

# Import from project utils
from utils.config import get_config, get_path

# Constants
TIMEOUT_SECONDS = 300
KNOWN_EXPERT_IDS = ["expert_1", "expert_2", "expert_3", "expert_fallback"]  # Example IDs, adjust based on actual config
REQUIRED_COLUMNS = ["prompt_embedding", "noise_level", "routing_label", "velocity_vector"]

class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Function timed out")

def setup_timeout(seconds: int = TIMEOUT_SECONDS):
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)

def cancel_timeout():
    signal.alarm(0)

def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent

def get_known_expert_ids() -> List[str]:
    """Return the list of known expert field IDs."""
    return KNOWN_EXPERT_IDS

def load_inference_outputs(input_path: Path) -> pd.DataFrame:
    """Load the filtered teacher ground truth dataset."""
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    try:
        df = pd.read_parquet(input_path)
        return df
    except Exception as e:
        raise RuntimeError(f"Failed to load parquet file: {e}")

def validate_routing_labels(df: pd.DataFrame, expert_ids: List[str]) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """
    Validate that routing labels match known expert IDs.
    Returns filtered dataframe and exclusion log entries.
    """
    exclusion_log = []
    
    # Identify rows with invalid routing labels
    invalid_mask = ~df["routing_label"].isin(expert_ids)
    
    if invalid_mask.any():
        invalid_indices = df[invalid_mask].index.tolist()
        for idx in invalid_indices:
            row = df.loc[idx]
            exclusion_log.append({
                "index": int(idx),
                "routing_label": str(row["routing_label"]),
                "reason": "Unknown expert ID",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            })
        
        # Filter out invalid rows
        df = df[~invalid_mask].reset_index(drop=True)
    
    return df, exclusion_log

def filter_valid_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure all required columns exist and contain valid data."""
    required_cols = ["prompt_embedding", "noise_level", "routing_label", "velocity_vector"]
    
    # Check for missing columns
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    # Drop rows with any NaN values in required columns
    initial_count = len(df)
    df = df.dropna(subset=required_cols)
    dropped_count = initial_count - len(df)
    
    if dropped_count > 0:
        print(f"Warning: Dropped {dropped_count} rows with NaN values in required columns")
    
    return df

def write_exclusion_log(log_entries: List[Dict[str, Any]], output_path: Path):
    """Write exclusion log to JSON file."""
    log_data = {
        "count": len(log_entries),
        "entries": log_entries,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(log_data, f, indent=2)
    
    print(f"Exclusion log written to {output_path}")

def extract_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract and normalize features for the final dataset.
    Ensures proper data types and structure.
    """
    # Create a copy to avoid modifying original
    result_df = df.copy()
    
    # Ensure prompt_embedding is stored as a list/array
    if "prompt_embedding" in result_df.columns:
        # If stored as string, convert back to list
        if result_df["prompt_embedding"].dtype == object:
            try:
                import ast
                result_df["prompt_embedding"] = result_df["prompt_embedding"].apply(
                    lambda x: ast.literal_eval(x) if isinstance(x, str) else x
                )
            except:
                pass  # Keep as is if conversion fails
    
    # Ensure velocity_vector is stored as a list/array
    if "velocity_vector" in result_df.columns:
        if result_df["velocity_vector"].dtype == object:
            try:
                import ast
                result_df["velocity_vector"] = result_df["velocity_vector"].apply(
                    lambda x: ast.literal_eval(x) if isinstance(x, str) else x
                )
            except:
                pass  # Keep as is if conversion fails
    
    return result_df

def stream_to_parquet(df: pd.DataFrame, output_path: Path):
    """
    Stream the processed dataframe to a parquet file.
    Uses chunking for large datasets to manage memory.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # For smaller datasets, write directly
    if len(df) <= 10000:
        df.to_parquet(output_path, index=False, engine='pyarrow')
        print(f"Dataset written to {output_path} ({len(df)} rows)")
        return
    
    # For larger datasets, stream in chunks
    chunk_size = 5000
    total_rows = len(df)
    written_rows = 0
    
    # Write first chunk
    first_chunk = df.iloc[:chunk_size]
    first_chunk.to_parquet(output_path, index=False, engine='pyarrow')
    written_rows += chunk_size
    print(f"Written {written_rows}/{total_rows} rows...")
    
    # Append remaining chunks
    with pq.ParquetWriter(output_path, first_chunk.to_parquet().schema) as writer:
        for i in range(chunk_size, total_rows, chunk_size):
            chunk = df.iloc[i:i+chunk_size]
            writer.write_table(pa.Table.from_pandas(chunk))
            written_rows += len(chunk)
            if written_rows % 10000 == 0:
                print(f"Written {written_rows}/{total_rows} rows...")
    
    print(f"Dataset written to {output_path} ({total_rows} rows)")

def version_artifact(file_path: Path):
    """Calculate SHA256 hash and update versioning info."""
    from utils.config import get_config
    
    if not file_path.exists():
        raise FileNotFoundError(f"Cannot version non-existent file: {file_path}")
    
    # Calculate SHA256
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    
    file_hash = sha256_hash.hexdigest()
    file_size = file_path.stat().st_size
    
    # Update versioning info
    version_info = {
        "file": str(file_path.relative_to(get_project_root())),
        "hash": file_hash,
        "size_bytes": file_size,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Write version info to results directory
    version_path = get_path("data/results", "dataset_version.json")
    version_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load existing versions if any
    if version_path.exists():
        with open(version_path, 'r') as f:
            versions = json.load(f)
    else:
        versions = {"artifacts": []}
    
    # Append new version
    versions["artifacts"].append(version_info)
    
    with open(version_path, 'w') as f:
        json.dump(versions, f, indent=2)
    
    print(f"Artifact versioned: {file_hash}")

def run_data_extraction(input_path: Path, output_path: Path, exclusion_log_path: Optional[Path] = None):
    """
    Main extraction pipeline:
    1. Load filtered dataset
    2. Validate routing labels
    3. Filter valid rows
    4. Extract features
    5. Stream to parquet
    6. Version artifact
    """
    print(f"Starting data extraction from {input_path}")
    
    # Setup timeout
    setup_timeout(TIMEOUT_SECONDS)
    
    try:
        # Load data
        print("Loading filtered dataset...")
        df = load_inference_outputs(input_path)
        print(f"Loaded {len(df)} rows")
        
        # Validate routing labels
        print("Validating routing labels...")
        expert_ids = get_known_expert_ids()
        df, exclusion_log = validate_routing_labels(df, expert_ids)
        
        # Write exclusion log if requested
        if exclusion_log_path and exclusion_log:
            write_exclusion_log(exclusion_log, exclusion_log_path)
        
        # Filter valid rows
        print("Filtering valid rows...")
        df = filter_valid_rows(df)
        print(f"Filtered dataset has {len(df)} rows")
        
        # Check minimum sample size
        config = get_config()
        min_samples = config.get("MIN_SAMPLE_SIZE", 1000)
        
        if len(df) < min_samples:
            raise ValueError(f"Dataset has {len(df)} rows, which is less than required minimum of {min_samples}")
        
        # Extract features
        print("Extracting features...")
        df = extract_features(df)
        
        # Stream to parquet
        print(f"Streaming to {output_path}...")
        stream_to_parquet(df, output_path)
        
        # Verify output
        if not output_path.exists():
            raise RuntimeError(f"Output file was not created: {output_path}")
        
        output_df = pd.read_parquet(output_path)
        if len(output_df) == 0:
            raise RuntimeError(f"Output file is empty: {output_path}")
        
        # Version artifact
        print("Versioning artifact...")
        version_artifact(output_path)
        
        print(f"Data extraction completed successfully!")
        print(f"Output: {output_path}")
        print(f"Rows: {len(output_df)}")
        
    except TimeoutError:
        print("ERROR: Data extraction timed out!")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Data extraction failed: {e}")
        sys.exit(1)
    finally:
        cancel_timeout()

def main():
    """Command-line interface for data extraction."""
    parser = argparse.ArgumentParser(description="Extract and stream final teacher routing dataset")
    parser.add_argument("--input", type=str, required=True, 
                      help="Path to filtered teacher ground truth parquet file")
    parser.add_argument("--output", type=str, required=True, 
                      help="Path to output teacher routing dataset parquet file")
    parser.add_argument("--exclusion-log", type=str, default=None,
                      help="Path to exclusion log JSON file")
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    output_path = Path(args.output)
    exclusion_log_path = Path(args.exclusion_log) if args.exclusion_log else None
    
    # Pre-check for input file
    if not input_path.exists():
        print(f"ERROR: Input file not found: {input_path}")
        sys.exit(1)
    
    # Run extraction
    run_data_extraction(input_path, output_path, exclusion_log_path)

if __name__ == "__main__":
    main()