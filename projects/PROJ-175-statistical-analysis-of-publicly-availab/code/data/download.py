import os
import sys
import json
import requests
import pandas as pd
from pathlib import Path
import gc
import time
from datasets import load_dataset
from utils.memory_monitor import check_memory_limit, track_memory

# Project root relative to code/data
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
FINAL_DIR = DATA_DIR / "final"

def save_memory_profile(peak_mb, downsampled=False, ratio=1.0):
    profile = {
        "peak_ram_mb": peak_mb,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "limit_mb": 7168,
        "downsampled": downsampled,
        "downsample_ratio": ratio
    }
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    with open(RAW_DIR / "memory_profile.json", "w") as f:
        json.dump(profile, f, indent=2)
    return profile

def check_memory_limit_wrapper(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_mem = track_memory()
        result = func(*args, **kwargs)
        end_mem = track_memory()
        # Simple check, real logic would be more robust
        if end_mem > 7168:
            raise MemoryError(f"Memory limit exceeded: {end_mem:.2f} GB")
        return result
    return wrapper

def download_file_streaming(url, output_path, chunk_size=8192):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    response = requests.get(url, stream=True)
    response.raise_for_status()
    with open(output_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=chunk_size):
            if chunk:
                f.write(chunk)
    return str(output_path)

def process_recipe1m_streaming(output_path, limit_rows=None):
    """
    Streams Recipe1M dataset using HuggingFace datasets library.
    Writes to Parquet in chunks to manage memory.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Use streaming to avoid loading full dataset into memory
    # The Plan's Critical Reframe mandates Recipe1M embeddings/ratings.
    # We use the 'recipe1m' dataset from HuggingFace.
    # Note: The exact dataset ID might vary, but 'recipe1m' is the standard proxy.
    # If a specific verified ID is provided in env, use that.
    dataset_id = os.getenv("VERIFIED_REAL_DATA_SOURCE", "yupengli/recipe1m")
    
    print(f"Loading dataset {dataset_id} in streaming mode...")
    try:
        ds = load_dataset(dataset_id, split="train", streaming=True)
    except Exception as e:
        # If the primary source fails, try the verified mirror if available
        # or raise a loud error as per constraints.
        raise RuntimeError(f"Failed to load dataset {dataset_id}: {e}")

    # Prepare to write in chunks to Parquet
    batch_size = 1000
    current_batch = []
    row_count = 0
    start_time = time.time()
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # We will write a single parquet file by accumulating and writing in chunks
    # However, pandas to_parquet usually writes the whole dataframe.
    # To stream effectively to a single file, we might need to use pyarrow directly
    # or accumulate a manageable number of rows and append.
    # Given the constraint of writing to a single .parquet file and memory limits,
    # we will accumulate batches and write them sequentially if possible,
    # or write the whole thing if it fits. 
    # For robustness with streaming, we'll collect a list of DataFrames and concat later
    # OR write chunk by chunk if the file format supports append (Parquet does not natively append easily).
    # Strategy: Collect chunks into a list, write periodically or at end.
    # To prevent OOM, we will write to a temporary list of files and concat, 
    # OR use pyarrow's streaming writer.
    
    import pyarrow as pa
    import pyarrow.parquet as pq
    
    # Define schema based on expected Recipe1M structure (ingredients, instructions, etc.)
    # We will infer schema from the first batch.
    
    writer = None
    
    for batch_idx, batch in enumerate(ds):
        # Convert batch dict to DataFrame
        df_batch = pd.DataFrame(batch)
        
        if writer is None:
            # Initialize writer with schema from first batch
            table = pa.Table.from_pandas(df_batch)
            writer = pq.ParquetWriter(output_path, table.schema)
            writer.write_table(table)
            print(f"Wrote first chunk: {len(df_batch)} rows")
        else:
            # Append subsequent batches
            table = pa.Table.from_pandas(df_batch)
            writer.write_table(table)
            print(f"Wrote chunk {batch_idx}: {len(df_batch)} rows")
        
        row_count += len(df_batch)
        
        if limit_rows and row_count >= limit_rows:
            print(f"Reached limit of {limit_rows} rows.")
            break
        
        # Garbage collection to free memory
        if batch_idx % 10 == 0:
            gc.collect()
            # Check memory
            try:
                check_memory_limit(7168)
            except MemoryError:
                raise
    
    if writer:
        writer.close()
    
    elapsed = time.time() - start_time
    print(f"Downloaded and wrote {row_count} rows in {elapsed:.2f} seconds.")
    return row_count

def download_flavordb_chunked(output_path):
    # Placeholder for FlavorDB if needed, but Plan says we use Recipe1M
    raise NotImplementedError("FlavorDB not used per Plan Critical Reframe")

def download_datasets():
    """
    Main entry point for downloading datasets.
    Verifies verification report first.
    """
    verification_report_path = DATA_DIR / "verification_report.json"
    if not verification_report_path.exists():
        # Check if we are in a state where verification is skipped or handled differently
        # But T051 mandates this check.
        raise FileNotFoundError("Verification report not found. Run T012/T051 first.")
    
    with open(verification_report_path, 'r') as f:
        verification_data = json.load(f)
    
    if verification_data.get("status") != "PASS":
        raise RuntimeError("Verification failed. Cannot proceed with download.")
    
    # Ensure directories exist
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    FINAL_DIR.mkdir(parents=True, exist_ok=True)
    
    # Download Recipe1M
    output_path = RAW_DIR / "recipe1m_raw.parquet"
    if output_path.exists():
        print(f"File {output_path} already exists. Skipping download.")
    else:
        # We might want to limit rows for initial testing if the full set is too large
        # But the task asks for raw data streaming.
        # We will stream the whole thing or until memory pressure.
        # For the purpose of this task, we assume the runner has enough RAM for a reasonable sample
        # or we rely on the streaming logic to handle it.
        # To be safe and ensure the script runs in the CI environment (often limited RAM),
        # we might limit to a specific number of rows if the full dataset is massive.
        # However, the task says "stream Recipe1M raw data".
        # We will attempt to stream. If it fails due to size, the error is real.
        
        # Check for a limit environment variable for CI safety
        limit = os.getenv("DATA_LIMIT_ROWS", None)
        limit_rows = int(limit) if limit else None
        
        process_recipe1m_streaming(output_path, limit_rows=limit_rows)
    
    # Verify output
    if not output_path.exists():
        raise FileNotFoundError(f"Failed to create {output_path}")
    
    print("Dataset download complete.")

def main():
    """
    CLI entry point.
    Usage: python code/data/download.py --dataset recipe1m --output data/raw/
    """
    import argparse
    parser = argparse.ArgumentParser(description="Download datasets")
    parser.add_argument("--dataset", type=str, required=True, help="Dataset name")
    parser.add_argument("--output", type=str, required=True, help="Output directory")
    args = parser.parse_args()
    
    # The function download_datasets handles the logic based on the verification report
    # and the specific dataset configuration.
    try:
        download_datasets()
    except Exception as e:
        print(f"Error during download: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()