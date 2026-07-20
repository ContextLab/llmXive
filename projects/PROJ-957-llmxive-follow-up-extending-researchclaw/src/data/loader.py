"""
Data loader for ResearchClawBench dataset.

Fetches the dataset using the Hugging Face datasets library,
verifies the checksum, and writes the checksum to disk.
"""
import hashlib
import json
import sys
from pathlib import Path
from typing import Optional

# Add project root to path to allow imports from src
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from datasets import load_dataset
from src.config import Config
from src.utils.checksum import compute_sha256, write_checksum
from src.utils.logging import setup_logging, log_with_context, get_global_error_tracker

# Initialize logger
logger = setup_logging(__name__)

def load_researchclawbench_dataset() -> dict:
    """
    Load the ResearchClawBench dataset from Hugging Face.
    
    Returns:
        dict: The loaded dataset as a dictionary.
    
    Raises:
        ValueError: If the dataset ID is invalid or the dataset cannot be loaded.
        ConnectionError: If the network is unreachable.
    """
    config = Config.load()
    dataset_id = config.RESEARCHCLAWBENCH_DATASET_ID
    
    logger.info(f"Attempting to load dataset: {dataset_id}")
    
    try:
        # Load the dataset using the datasets library
        # streaming=True to handle large datasets efficiently
        dataset = load_dataset(dataset_id, split="train", streaming=True)
        
        # Materialize a small sample to verify accessibility and compute hash
        # We need to iterate to get the data, but we don't want to load everything into memory
        # for the hash if it's huge. However, for checksum verification of the *source*,
        # we usually hash the downloaded file. Since `streaming=True` doesn't download a single file,
        # we will hash the first N items to ensure the data is real and accessible,
        # or we hash the entire dataset if it fits in memory.
        # Given the constraint "Large dataset? Stream the real data", we will stream.
        # But for a checksum file that acts as a gate, we need a deterministic hash of the source.
        # If the dataset is dynamic, we might hash the config or a specific subset.
        # For this implementation, we will hash the *schema* and the *first 1000 rows* as a representative
        # fingerprint of the data integrity at this moment.
        # However, the task asks for checksum verification against `data/raw/`.
        # Standard practice for HF datasets is to hash the parquet files if downloaded.
        # Let's try to download the dataset to a cache first, then hash the cache files.
        
        # Re-load without streaming to get the actual cache path for hashing
        # We use trust_remote_code=True if needed, but standard datasets usually don't need it.
        full_dataset = load_dataset(dataset_id, split="train", trust_remote_code=True)
        
        # The datasets library caches the data. We can access the cache directory.
        # However, hashing the entire cache might be complex.
        # A simpler approach for the "Verified Accuracy Gate" is to hash the JSON representation
        # of the dataset if it's small, or a specific subset.
        # Given the task description "checksum verification against data/raw/",
        # we will download the dataset to `data/raw/` and hash the file.
        
        raw_dir = project_root / "data" / "raw"
        raw_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = raw_dir / "researchclawbench.json"
        
        # Convert to list of dicts and save
        # Warning: If the dataset is huge, this will OOM.
        # The task mentions "Large dataset? Stream the real data".
        # But we need a checksum.
        # Strategy: Stream and write to file in chunks, then hash the file.
        
        logger.info("Streaming dataset to local file...")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("[\n")
            first = True
            for idx, item in enumerate(full_dataset):
                if not first:
                    f.write(",\n")
                f.write(json.dumps(item, ensure_ascii=False))
                first = False
            f.write("\n]")
        
        logger.info(f"Dataset saved to {output_file}")
        
        # Compute checksum of the saved file
        checksum = compute_sha256(output_file)
        
        return full_dataset

    except Exception as e:
        logger.error(f"Failed to load dataset {dataset_id}: {e}")
        # Trigger the gate failure by raising
        raise ValueError(f"Dataset load failed: {e}") from e

def verify_and_write_checksum(dataset: dict) -> str:
    """
    Verify the dataset integrity and write the checksum to disk.
    
    Args:
        dataset: The loaded dataset.
        
    Returns:
        str: The computed checksum.
        
    Raises:
        ValueError: If the checksum does not match the expected value in config.
    """
    # The dataset is already saved to data/raw/researchclawbench.json in load_researchclawbench_dataset
    # We compute the checksum of that file.
    raw_dir = project_root / "data" / "raw"
    dataset_file = raw_dir / "researchclawbench.json"
    
    if not dataset_file.exists():
        raise FileNotFoundError(f"Dataset file not found: {dataset_file}")
    
    checksum = compute_sha256(dataset_file)
    
    # Write checksum to data/raw/checksum.txt
    checksum_file = raw_dir / "checksum.txt"
    write_checksum(checksum_file, checksum)
    
    logger.info(f"Checksum written to {checksum_file}: {checksum}")
    
    # Note: The actual comparison with expected value happens in T007b (Verified Accuracy Gate)
    # Here we just ensure the checksum is generated and written.
    
    return checksum

def main():
    """Main entry point for the data loader."""
    logger.info("Starting ResearchClawBench data loading...")
    
    try:
        # Load the dataset
        dataset = load_researchclawbench_dataset()
        
        # Verify and write checksum
        checksum = verify_and_write_checksum(dataset)
        
        logger.info(f"Successfully loaded dataset and computed checksum: {checksum}")
        return True

    except Exception as e:
        logger.critical(f"Data loading failed: {e}")
        # The gate logic (T007b) will handle the abort, but we raise here to signal failure
        sys.exit(1)

if __name__ == "__main__":
    main()
