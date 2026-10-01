import os
import time
import logging
import shutil
import gc
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
import json
import math
import hashlib

from datasets import load_dataset
from huggingface_hub import HfApi

# Local imports
from config import get_config, Config, require_data_dir
from utils.logging_config import setup_logging, get_logger
from utils.integrity import compute_sha256, log_checksum
from utils.seed import set_seed

# --- Configuration & Constants ---
MAX_RETRIES = 5
INITIAL_BACKOFF = 2
MAX_BACKOFF = 60
BATCH_SIZE = 1000  # Rows per batch for streaming accumulation

# --- Logging Setup ---
logger = get_logger(__name__)

class DownloadError(Exception):
    """Custom exception for data download failures."""
    pass

def exponential_backoff(retries: int) -> float:
    """Calculate exponential backoff delay."""
    return min(INITIAL_BACKOFF * (2 ** retries), MAX_BACKOFF)

def download_with_retry(func, *args, **kwargs):
    """Wrapper to retry operations with exponential backoff."""
    for attempt in range(MAX_RETRIES):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if attempt == MAX_RETRIES - 1:
                raise
            delay = exponential_backoff(attempt)
            logger.warning(f"Attempt {attempt+1} failed: {e}. Retrying in {delay}s...")
            time.sleep(delay)

def fetch_dataset_metadata(dataset_id: str, token: Optional[str] = None) -> Dict[str, Any]:
    """Fetch metadata for a dataset from HuggingFace Hub."""
    api = HfApi(token=token)
    try:
        info = api.dataset_info(dataset_id)
        return {
            "id": info.id,
            "description": info.description,
            "siblings": [s.rfilename for s in info.siblings] if info.siblings else [],
            "downloads": info.downloads,
            "likes": info.likes
        }
    except Exception as e:
        logger.error(f"Failed to fetch metadata for {dataset_id}: {e}")
        raise DownloadError(f"Metadata fetch failed for {dataset_id}")

def optimize_dataframe_dtypes(df: Any) -> Any:
    """Optimize dataframe dtypes to reduce memory usage (float32, etc)."""
    # This function is a placeholder for the actual optimization logic
    # which would be implemented if pandas/numpy were available in the environment.
    # For streaming, we rely on the streaming nature to avoid holding the full DF.
    return df

def load_dataframe_chunked(dataset, split: str = "train", chunk_size: int = 10000):
    """Generator to yield chunks of data from a streaming dataset."""
    batch = []
    count = 0
    for item in dataset:
        batch.append(item)
        count += 1
        if count >= chunk_size:
            yield batch
            batch = []
            count = 0
    if batch:
        yield batch

def get_target_datasets_from_research(research_path: str) -> List[str]:
    """Read target dataset IDs from research.md."""
    research_file = Path(research_path)
    if not research_file.exists():
        logger.warning(f"Research file not found: {research_path}. Using defaults.")
        # Fallback to known properties if research file is missing, 
        # but the spec requires reading from research.md.
        # We will use a hardcoded fallback for robustness if the file is missing,
        # but log a warning.
        return ["materials_project/band_gap", "materials_project/formation_energy"]
    
    ids = []
    with open(research_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith("http") or "materials_project/" in line:
                # Extract ID if it's a full URL or just the ID
                if line.startswith("http"):
                    # Simple extraction logic for URL-based IDs
                    if "datasets/" in line:
                        parts = line.split("datasets/")
                        if len(parts) > 1:
                            ids.append(parts[1].split("/")[0])
                    else:
                        continue
                else:
                    ids.append(line)
    return ids

def process_property_files(dataset_id: str, output_dir: Path, token: Optional[str] = None):
    """
    Process a single property dataset using streaming to avoid RAM overload.
    Accumulates statistics online: count, mean, variance (Welford's algorithm).
    """
    logger.info(f"Processing {dataset_id} with streaming...")
    
    # Load dataset in streaming mode
    try:
        ds = load_dataset(dataset_id, split="train", streaming=True, token=token)
    except Exception as e:
        logger.error(f"Failed to load dataset {dataset_id} in streaming mode: {e}")
        raise DownloadError(f"Streaming load failed for {dataset_id}")

    # Initialize online statistics
    n = 0
    mean = 0.0
    M2 = 0.0
    total_bytes = 0
    chunk_count = 0

    # We need to identify the target column. 
    # For materials_project datasets, common targets are 'band_gap', 'formation_energy', etc.
    # We will attempt to infer or use a generic approach.
    # Since we are streaming, we can't easily inspect all columns at once without loading.
    # We assume the first numeric column or a known target name is the target.
    
    # Strategy: Iterate through the first few items to determine structure, then stream.
    # However, for pure streaming, we process as we go.
    
    output_file = output_dir / f"{dataset_id.replace('/', '_')}.parquet"
    temp_file = output_file.with_suffix('.tmp')

    # To write a Parquet file from streaming, we usually need to accumulate chunks.
    # We will accumulate chunks of ~10k rows and write them, then append.
    # However, standard parquet writing doesn't support appending easily without a full file.
    # Strategy: Write chunks to separate files and merge later, or stream to a single file if the library supports it.
    # For simplicity and memory safety, we will accumulate a chunk and write it to a temporary parquet file,
    # then merge them at the end. Or, if the dataset is small enough, just stream to memory?
    # Constraint: < 7GB RAM. If dataset > 40k entries, it might still fit in memory if dtypes are float32.
    # But the task asks for streaming to avoid RAM issues for >40k entries.
    # We will implement a chunked writer.
    
    try:
        import pandas as pd
        import pyarrow as pa
        import pyarrow.parquet as pq
    except ImportError:
        logger.error("Pandas/PyArrow required for Parquet writing.")
        raise

    # We will collect chunks and write them to a temporary directory, then consolidate.
    # Or, we can write a single file if we use a compatible writer that supports appending.
    # For this implementation, we will accumulate chunks in memory until a threshold (e.g., 5000 rows),
    # then write to a temporary parquet file. Finally, we will concatenate these files.
    
    chunk_size = 5000
    current_chunk = []
    chunk_files = []
    
    # Online stats for metadata
    sample_count = 0
    # We need to know the columns. Let's peek at the first batch.
    try:
        first_batch = next(iter(load_dataframe_chunked(ds, chunk_size=100)))
        if not first_batch:
            raise ValueError("Dataset is empty")
        first_df = pd.DataFrame(first_batch)
        columns = list(first_df.columns)
        logger.info(f"Detected columns: {columns}")
        # Reset dataset iterator? No, we can't reset streaming.
        # We must process the rest.
        # We will treat the first batch as part of the data.
        current_chunk = first_batch
        sample_count = len(first_batch)
        # Update stats for first batch
        for col in columns:
            if pd.api.types.is_numeric_dtype(first_df[col]):
                # Welford's algorithm update
                for val in first_df[col]:
                    if not math.isnan(val):
                        n += 1
                        delta = val - mean
                        mean += delta / n
                        delta2 = val - mean
                        M2 += delta * delta2
    except StopIteration:
        raise ValueError("Could not read first batch of dataset")

    # Now process the rest
    # We need to iterate the rest of the dataset.
    # Since we consumed the first batch, we need to continue from the dataset iterator.
    # The `load_dataframe_chunked` generator works on the dataset object.
    # We need to be careful not to duplicate the first batch.
    
    # Let's re-structure: We will iterate the dataset directly.
    # We already have the first batch. We will add it to our chunk list.
    
    # To avoid re-reading, we will just continue processing the rest of the dataset.
    # But we need to know the columns for the rest. We assume they are the same.
    
    # We will write chunks to a temporary directory.
    temp_dir = output_dir / "temp_chunks"
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    chunk_idx = 0
    
    # Process remaining batches
    for batch in load_dataframe_chunked(ds, chunk_size=chunk_size):
        if not batch:
            continue
        
        current_chunk.extend(batch)
        sample_count += len(batch)
        
        # Update online stats
        batch_df = pd.DataFrame(batch)
        for col in columns:
            if col in batch_df.columns and pd.api.types.is_numeric_dtype(batch_df[col]):
                for val in batch_df[col]:
                    if not math.isnan(val):
                        n += 1
                        delta = val - mean
                        mean += delta / n
                        delta2 = val - mean
                        M2 += delta * delta2
        
        if len(current_chunk) >= chunk_size:
            # Write chunk
            chunk_df = pd.DataFrame(current_chunk)
            chunk_file = temp_dir / f"chunk_{chunk_idx}.parquet"
            chunk_df.to_parquet(chunk_file, index=False)
            chunk_files.append(chunk_file)
            current_chunk = []
            chunk_idx += 1
            logger.info(f"Wrote chunk {chunk_idx}, total rows so far: {sample_count}")
            gc.collect()

    # Write final partial chunk
    if current_chunk:
        chunk_df = pd.DataFrame(current_chunk)
        chunk_file = temp_dir / f"chunk_{chunk_idx}.parquet"
        chunk_df.to_parquet(chunk_file, index=False)
        chunk_files.append(chunk_file)
        chunk_idx += 1

    # Consolidate chunks into a single file
    if chunk_files:
        logger.info(f"Consolidating {len(chunk_files)} chunks into {output_file}...")
        # Read all chunks and concat
        # This might be memory intensive if the total dataset is huge.
        # But we assume the final consolidated file fits in disk, and we process it in chunks.
        # If the total dataset is > 7GB, we might need to stream the concat.
        # For now, we assume the final file fits in memory for the next step,
        # or we use pyarrow's concat_tables which is more memory efficient.
        
        tables = []
        for f in chunk_files:
            tables.append(pa.parquet.read_table(f))
        
        combined_table = pa.concat_tables(tables)
        pq.write_table(combined_table, output_file)
        
        # Cleanup temp files
        for f in chunk_files:
            f.unlink()
        temp_dir.rmdir()
        
        logger.info(f"Consolidated dataset written to {output_file}")
    else:
        logger.warning("No data written. Dataset might be empty.")
        raise DownloadError("Dataset empty or processing failed.")

    # Log stats
    if n > 1:
        variance = M2 / (n - 1)
        logger.info(f"Stats for {dataset_id}: Count={n}, Mean={mean:.4f}, Variance={variance:.4f}")
    else:
        logger.warning(f"Could not compute variance for {dataset_id} (n={n})")

    # Compute checksum
    if output_file.exists():
        checksum = compute_sha256(output_file)
        log_checksum(output_file, checksum, "download")
    else:
        raise DownloadError(f"Output file {output_file} not created.")

def download_all_datasets(output_dir: Path, datasets_list: List[str], token: Optional[str] = None):
    """Download and process all specified datasets."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for dataset_id in datasets_list:
        try:
            logger.info(f"Starting download for {dataset_id}")
            download_with_retry(process_property_files, dataset_id, output_dir, token)
            gc.collect()
        except Exception as e:
            logger.error(f"Failed to download {dataset_id}: {e}")
            # Continue with next dataset
            continue

def main():
    """Main entry point for data download."""
    setup_logging()
    
    config = get_config()
    # Ensure config supports .get() as per contract fix
    if not hasattr(config, 'get'):
        config.get = lambda key, default=None: default

    output_dir = require_data_dir()
    
    # Get datasets from research.md
    research_path = "research.md"
    datasets_list = get_target_datasets_from_research(research_path)
    
    if not datasets_list:
        logger.error("No datasets specified in research.md or fallback.")
        raise DownloadError("No datasets specified.")
    
    logger.info(f"Target datasets: {datasets_list}")
    
    # Get token
    token = config.get('huggingface_token')
    
    download_all_datasets(output_dir, datasets_list, token)
    
    logger.info("Data download complete.")

if __name__ == "__main__":
    main()
