import os
import logging
import pandas as pd
import numpy as np
from typing import Tuple, Optional, Dict, Any
from pathlib import Path
from config import get_project_root, get_config_dict
from utils import get_logger
import hashlib
import yaml
from datetime import datetime

logger = get_logger(__name__)

# Constants for chunking
CHUNK_SIZE_MB = 500  # Process in 500MB chunks to stay well under 5GB limit
CHUNK_ROWS_ESTIMATE = 2_000_000  # Approximate rows per chunk based on typical MSD density

def calculate_file_checksum(file_path: Path) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def save_state_entry(filename: str, file_path: Path, checksum: str):
    """Update state.yaml with the new file checksum."""
    state_path = get_project_root() / "state.yaml"
    state = {"files": {}}
    
    if state_path.exists():
        with open(state_path, "r") as f:
            state = yaml.safe_load(f) or {"files": {}}
    
    state["files"][filename] = {
        "path": str(file_path),
        "checksum": checksum,
        "updated_at": datetime.now().isoformat()
    }
    
    with open(state_path, "w") as f:
        yaml.dump(state, f, default_flow_style=False)

def estimate_memory_usage(df_sample: pd.DataFrame, total_rows: int) -> float:
    """
    Estimate memory usage in GB based on a sample dataframe.
    Returns size in GB.
    """
    sample_size_bytes = df_sample.memory_usage(deep=True).sum()
    sample_rows = len(df_sample)
    if sample_rows == 0:
        return 0.0
    
    # Estimate total size
    estimated_total_bytes = (sample_size_bytes / sample_rows) * total_rows
    estimated_gb = estimated_total_bytes / (1024 ** 3)
    return estimated_gb

def ingest_with_chunking(
    raw_tracks_path: Path,
    raw_listens_path: Path,
    output_path: Path,
    chunk_size: int = CHUNK_ROWS_ESTIMATE,
    memory_threshold_gb: float = 5.0
) -> pd.DataFrame:
    """
    Ingest MSD tracks and listens data with memory-efficient chunking.
    
    If the estimated memory usage exceeds `memory_threshold_gb`, the function
    processes the data in chunks, accumulating statistics or writing intermediate
    results to avoid OOM errors.
    
    Args:
        raw_tracks_path: Path to raw tracks CSV/Parquet
        raw_listens_path: Path to raw listens CSV/Parquet
        output_path: Path to save the final ingested dataset
        chunk_size: Number of rows to process at once
        memory_threshold_gb: Threshold in GB to trigger chunking logic
        
    Returns:
        The final processed DataFrame (or a path to the saved file if chunked).
    """
    logger.info(f"Starting ingestion with chunking logic for {raw_tracks_path} and {raw_listens_path}")
    
    # 1. Load a sample to estimate memory
    try:
        # Try to get row count without loading full file if possible
        # For CSV, we might need to count lines or load a small sample
        sample_tracks = pd.read_csv(raw_tracks_path, nrows=10000)
        sample_listens = pd.read_csv(raw_listens_path, nrows=10000)
        
        # Estimate total rows (assuming CSV for now, could be parquet)
        # In a real robust implementation, we'd use wc -l or parquet metadata
        # Here we assume the file size ratio or just try to load metadata
        # For safety, we load a larger sample to get column dtypes
        total_rows_tracks = sum(1 for _ in open(raw_tracks_path)) - 1 # rough count
        total_rows_listens = sum(1 for _ in open(raw_listens_path)) - 1
        
        est_memory = estimate_memory_usage(sample_tracks, total_rows_tracks) + \
                     estimate_memory_usage(sample_listens, total_rows_listens)
        
        logger.info(f"Estimated memory usage: {est_memory:.2f} GB")
        
        if est_memory > memory_threshold_gb:
            logger.warning(f"Memory usage ({est_memory:.2f} GB) exceeds threshold ({memory_threshold_gb} GB). Enabling chunked processing.")
            return _process_chunked(raw_tracks_path, raw_listens_path, output_path, chunk_size)
        else:
            logger.info("Memory usage within limits. Processing in one go.")
            return _process_standard(raw_tracks_path, raw_listens_path, output_path)
            
    except Exception as e:
        logger.error(f"Error during memory estimation: {e}. Falling back to standard processing.")
        return _process_standard(raw_tracks_path, raw_listens_path, output_path)

def _process_standard(tracks_path: Path, listens_path: Path, output_path: Path) -> pd.DataFrame:
    """Standard ingestion without chunking."""
    df_tracks = pd.read_csv(tracks_path)
    df_listens = pd.read_csv(listens_path)
    
    # Basic join and filter logic (simplified for this task)
    # In real implementation, this would call filter_cohort, etc.
    df_merged = pd.merge(df_listens, df_tracks[['track_id', 'track_title', 'artist_name']], 
                         on='track_id', how='left')
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df_merged.to_parquet(output_path, index=False)
    logger.info(f"Standard ingestion complete. Saved to {output_path}")
    return df_merged

def _process_chunked(tracks_path: Path, listens_path: Path, output_path: Path, chunk_size: int) -> Path:
    """
    Chunked ingestion. Reads listens in chunks, merges with tracks (loaded once if fits, 
    or also chunked if tracks are huge), and writes intermediate results.
    Finally concatenates intermediate results.
    """
    logger.info("Starting chunked processing...")
    
    # Load tracks once (assuming tracks metadata is smaller than listens logs)
    # If tracks are also huge, we would need to chunk that too, but typically tracks < listens
    df_tracks = pd.read_csv(tracks_path)
    
    intermediate_files = []
    
    # Process listens in chunks
    for i, chunk in enumerate(pd.read_csv(listens_path, chunksize=chunk_size)):
        logger.info(f"Processing chunk {i+1}...")
        
        # Merge chunk with tracks
        chunk_merged = pd.merge(chunk, df_tracks[['track_id', 'track_title', 'artist_name']], 
                                on='track_id', how='left')
        
        # Apply basic filtering (e.g., drop nulls if necessary)
        chunk_merged = chunk_merged.dropna(subset=['track_id'])
        
        # Save intermediate chunk
        temp_path = output_path.parent / f"temp_chunk_{i}.parquet"
        chunk_merged.to_parquet(temp_path, index=False)
        intermediate_files.append(temp_path)
        
        # Explicitly delete to free memory
        del chunk_merged
        del chunk
    
    # Concatenate all intermediate files
    logger.info(f"Concatenating {len(intermediate_files)} chunks...")
    dfs = [pd.read_parquet(f) for f in intermediate_files]
    final_df = pd.concat(dfs, ignore_index=True)
    
    # Save final output
    final_df.to_parquet(output_path, index=False)
    
    # Cleanup temp files
    for f in intermediate_files:
        f.unlink()
        
    logger.info(f"Chunked ingestion complete. Saved to {output_path}")
    return output_path

def download_datasets():
    """
    Placeholder for actual download logic.
    In a real scenario, this would fetch from MSD/AMT URLs.
    """
    pass

def filter_cohort(df: pd.DataFrame) -> pd.DataFrame:
    """Placeholder for cohort filtering."""
    return df

def handle_fallback(df: pd.DataFrame) -> pd.DataFrame:
    """Placeholder for fallback logic."""
    return df

def apply_frequency_threshold(df: pd.DataFrame) -> pd.DataFrame:
    """Placeholder for frequency thresholding."""
    return df

def calculate_ratio_score(df: pd.DataFrame) -> pd.DataFrame:
    """Placeholder for ratio score calculation."""
    return df

def calculate_residualized_score(df: pd.DataFrame) -> pd.DataFrame:
    """Placeholder for residualized score calculation."""
    return df

def main():
    """Main entry point for ingestion."""
    project_root = get_project_root()
    config = get_config_dict()
    
    raw_tracks = project_root / "data" / "raw" / "tracks.csv" # Example path
    raw_listens = project_root / "data" / "raw" / "listens.csv" # Example path
    output_file = project_root / "data" / "processed" / "ingested_cohort.parquet"
    
    # Ensure paths exist for demonstration (in real run, they must exist)
    if not raw_tracks.exists() or not raw_listens.exists():
        logger.warning("Raw data files not found. Skipping ingestion execution.")
        return
    
    ingest_with_chunking(raw_tracks, raw_listens, output_file)
    
    # Update state
    checksum = calculate_file_checksum(output_file)
    save_state_entry("ingested_cohort.parquet", output_file, checksum)

if __name__ == "__main__":
    main()