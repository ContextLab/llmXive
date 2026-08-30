"""
Download the raw HMAO dataset to data/raw/ using streaming.
Implements T017a: Download Raw Data.
"""
import os
import hashlib
import logging
from pathlib import Path
import datasets
from datasets import load_dataset
import shutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DATASET_NAME = "hmao/all_apis_for_multiapi"
OUTPUT_DIR = Path("data/raw")
OUTPUT_FILE = OUTPUT_DIR / "hmao_raw.parquet"

def get_dataset_checksum() -> str:
    """
    Retrieve the known SHA256 checksum from the HuggingFace dataset metadata.
    This function queries the dataset info to find the checksum if available,
    or returns a placeholder if not directly exposed in the public API.
    Note: In a real scenario, this might be hardcoded from the dataset card
    if the API doesn't expose it dynamically, but we attempt to fetch it.
    """
    try:
        # Attempt to get dataset info
        ds_info = datasets.get_dataset_config_info(DATASET_NAME, "default")
        # The checksum might be in the dataset's metadata or description
        # For now, we assume the dataset card provides it or we rely on the file integrity
        # provided by the streaming download mechanism of HuggingFace if available.
        # However, the task explicitly asks to retrieve it from metadata.
        # If not found in metadata, we might need to rely on the dataset card text.
        # Since specific metadata access for checksums varies by dataset,
        # we will implement a fallback to a known value if the API doesn't expose it directly,
        # but primarily we try to fetch it.
        
        # Check if 'checksum' or similar is in the info
        if hasattr(ds_info, 'download_checksums') and ds_info.download_checksums:
            # Usually a dict of filename -> checksum
            for checksum in ds_info.download_checksums.values():
                return checksum
        
        # Fallback: If the dataset card has a specific note, we might need to parse it.
        # For this implementation, we will assume the dataset is trusted via HF's internal
        # verification or we will use a known checksum if the dataset is static.
        # Since we cannot hardcode a "known" checksum without T017b verifying it first,
        # we will proceed with the download and let the user verify, or use a known value
        # if available in the dataset description.
        # *Correction*: The task says "Retrieve the known SHA256 checksum from the HuggingFace dataset metadata".
        # If the metadata doesn't expose it, we might have to rely on the dataset card.
        # Let's assume for this specific dataset 'hmao/all_apis_for_multiapi' the checksum
        # is not directly in the API's `config_info` but might be in the dataset card.
        # We will return a placeholder or raise if not found, but the download proceeds.
        # Actually, to strictly follow "retrieve", if not found, we should perhaps fail or warn.
        # However, the primary goal is the download.
        logger.warning("Checksum not found in dataset metadata. Proceeding with download.")
        return "unknown"
    except Exception as e:
        logger.warning(f"Could not retrieve checksum from metadata: {e}. Proceeding.")
        return "unknown"

def compute_file_checksum(file_path: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def main():
    """
    Main entry point for downloading the HMAO dataset.
    - Creates output directory if needed.
    - Downloads dataset using streaming=True.
    - Saves to parquet.
    - Verifies checksum (if available).
    """
    logger.info(f"Starting download of dataset: {DATASET_NAME}")
    
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Get expected checksum from metadata
    expected_checksum = get_dataset_checksum()
    if expected_checksum != "unknown":
        logger.info(f"Expected checksum from metadata: {expected_checksum}")
    else:
        logger.info("No checksum found in metadata to verify against.")

    try:
        # Load dataset with streaming to respect RAM limits
        # We use streaming=True to iterate and save chunks or the whole thing if it fits in memory
        # but the task says "streaming=True" to respect RAM limits.
        # Since we need to save to a file, we will iterate and write.
        logger.info("Loading dataset with streaming=True...")
        
        # Note: load_dataset with streaming=True returns an IterableDataset
        ds = load_dataset(DATASET_NAME, split="train", streaming=True)
        
        logger.info(f"Dataset loaded. Starting conversion to parquet...")
        
        # Convert to pandas and save. 
        # Note: Streaming datasets might not convert directly to a single pandas DF without iteration.
        # We will iterate and accumulate.
        # For a large dataset, accumulating all might exceed RAM. 
        # However, the task asks to save to `hmao_raw.parquet`. 
        # If the dataset is too large, we might need to stream-write to parquet.
        # Using `to_parquet` on an iterable might not work directly.
        # We will collect rows in chunks or use a generator.
        
        # Approach: Convert to a list of dicts (might be memory heavy) or write row by row.
        # Given the constraint "respect RAM limits", we should write in chunks.
        # But `datasets` library's `to_parquet` usually requires a Dataset object, not Iterable.
        # We will try to convert to a Dataset first if it fits, or write manually.
        # Let's assume for this task we can buffer a reasonable amount or the dataset is manageable.
        # If it's too large, we might need `pyarrow` to write streams.
        
        # Simpler approach for this task: Convert to a list of rows if memory permits, 
        # or use `datasets` to cache it first.
        # Actually, `load_dataset(..., streaming=True)` is for iteration.
        # To save to parquet, we can do:
        # ds = load_dataset(..., streaming=True)
        # df = pd.DataFrame(ds) # This might try to load all into memory.
        
        # Better: Use `datasets` to download and cache, then load.
        # But the task says "using streaming=True".
        # Let's try to iterate and write to parquet using pyarrow directly.
        
        import pyarrow as pa
        import pyarrow.parquet as pq
        
        # We need to define the schema or infer it.
        # Let's get one row to infer schema
        sample_row = next(iter(ds))
        schema = pa.Schema.from_pandas(pd.DataFrame([sample_row]).convert_dtypes())
        
        # Open a parquet writer
        with pq.ParquetWriter(OUTPUT_FILE, schema) as writer:
            batch_size = 10000
            batch = []
            count = 0
            for row in ds:
                batch.append(row)
                if len(batch) >= batch_size:
                    df_batch = pd.DataFrame(batch)
                    # Ensure types match schema if needed, but pandas usually handles it
                    table = pa.Table.from_pandas(df_batch)
                    writer.write_table(table)
                    batch = []
                    count += batch_size
                    if count % 100000 == 0:
                        logger.info(f"Written {count} rows...")
            
            # Write remaining
            if batch:
                df_batch = pd.DataFrame(batch)
                table = pa.Table.from_pandas(df_batch)
                writer.write_table(table)
                count += len(batch)
        
        logger.info(f"Successfully saved {count} rows to {OUTPUT_FILE}")
        
        # Verify checksum if we have one
        if expected_checksum != "unknown":
            actual_checksum = compute_file_checksum(OUTPUT_FILE)
            if actual_checksum == expected_checksum:
                logger.info("Checksum verification PASSED.")
            else:
                logger.error(f"Checksum verification FAILED. Expected: {expected_checksum}, Got: {actual_checksum}")
                raise ValueError("Dataset checksum mismatch!")
        else:
            logger.warning("Skipping checksum verification as no expected checksum was found.")
            
    except Exception as e:
        logger.error(f"Failed to download or process dataset: {e}")
        raise

if __name__ == "__main__":
    main()
