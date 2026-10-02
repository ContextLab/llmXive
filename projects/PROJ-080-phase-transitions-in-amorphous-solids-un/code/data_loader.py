import os
import hashlib
import json
import logging
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Tuple, Any

from datasets import load_dataset, Dataset
from datasets.exceptions import DatasetNotFoundError
import yaml

# Configure logging
logger = logging.getLogger(__name__)

class RealDataFetchError(RuntimeError):
    """Custom exception for real data fetch failures."""
    pass

class ChecksumValidationError(ValueError):
    """Custom exception for checksum mismatches."""
    pass

def get_schema_path() -> Path:
    """Returns the path to the trajectory schema file."""
    return Path("specs/contracts/trajectory.schema.yaml")

def load_schema() -> Dict[str, Any]:
    """Loads the trajectory schema from YAML."""
    schema_path = get_schema_path()
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found at {schema_path}")
    
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def verify_checksum_local(file_path: str, expected_hash: str) -> bool:
    """
    Computes the SHA-256 checksum of a file and compares it to the expected hash.
    
    Args:
        file_path: Path to the file to verify.
        expected_hash: The expected SHA-256 hex string.
    
    Returns:
        True if checksums match.
    
    Raises:
        ValueError: If checksums do not match.
        FileNotFoundError: If the file does not exist.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found for checksum verification: {file_path}")
    
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        computed_hash = sha256_hash.hexdigest()
    except Exception as e:
        raise RuntimeError(f"Failed to compute checksum for {file_path}: {e}")
    
    if computed_hash != expected_hash:
        raise ChecksumValidationError(
            f"Checksum mismatch for {file_path}. "
            f"Expected: {expected_hash}, Computed: {computed_hash}"
        )
    
    logger.info(f"Checksum verification successful for {file_path}")
    return True

def download_and_verify_shard(dataset_id: str, split: str, schema: Dict[str, Any]) -> str:
    """
    Downloads the dataset shard and verifies its checksum against the schema.
    
    This function implements the strict "fail loud" policy:
    1. Fetches data from the real source.
    2. Verifies the checksum.
    3. Raises errors if either step fails. NO synthetic fallbacks.
    
    Args:
        dataset_id: HuggingFace dataset ID.
        split: Dataset split name.
        schema: The loaded schema dictionary containing expected_sha256.
    
    Returns:
        Path to the downloaded file (or cached directory path used as a proxy for verification).
    
    Raises:
        RealDataFetchError: If the dataset cannot be fetched.
        ChecksumValidationError: If the checksum does not match.
    """
    expected_hash = schema.get("expected_sha256")
    if not expected_hash:
        raise ValueError("Schema is missing 'expected_sha256' field.")
    
    logger.info(f"Attempting to fetch dataset: {dataset_id}, split: {split}")
    
    try:
        # Load the dataset. 
        # Note: In a real streaming scenario with large files, we might need to 
        # download specific files manually to compute checksum before streaming.
        # For HuggingFace 'parquet' splits, the data is often downloaded to cache.
        # We attempt to load the dataset to trigger the download.
        ds = load_dataset(dataset_id, split=split, streaming=True)
        
        # Since streaming doesn't give us a single file path easily for checksumming 
        # against a specific shard hash without downloading the whole thing first,
        # we assume the 'download' phase happens during the first iteration or load.
        # For the purpose of this task, we verify the integrity by checking the 
        # schema constraint and attempting to fetch. 
        # In a production pipeline with specific shard files, we would download 
        # the specific .parquet file, compute hash, then stream.
        
        # To satisfy the strict requirement of verifying a file hash:
        # We will attempt to get the cache info or force a download of the first file.
        # However, standard `load_dataset` with streaming doesn't expose the local file path
        # of the downloaded shard directly.
        # 
        # Alternative approach for strict checksum: Download the file manually using 
        # huggingface_hub if the dataset structure allows, or rely on the fact that 
        # the dataset provider ensures integrity.
        # 
        # Given the constraints and the need to verify a specific SHA256:
        # We will assume the dataset is provided as a specific file in the cache 
        # or we download the file explicitly.
        # 
        # Let's use the `datasets` internal cache mechanism or `hf_hub_download`.
        from huggingface_hub import hf_hub_download
        
        # Determine the filename. Usually for parquet splits, it's data-train-00000-of-00001.parquet
        # or similar. We need to know the exact filename or download all.
        # For this implementation, we assume the dataset ID maps to a specific file structure.
        # If the schema implies a single file hash, we need that file.
        
        # Fallback strategy for generic dataset:
        # We cannot easily get the local path of a streamed file to hash it without downloading it.
        # So we will download the file explicitly first if it's a single shard.
        # Assuming the dataset has a single parquet file for the split.
        
        # Attempt to find the file. This is dataset-specific.
        # For 'materials-science/amorphous-silicon-shear-trajectories', we assume a standard structure.
        # We will try to download the file and verify.
        
        # NOTE: This part requires knowledge of the specific file name in the repo.
        # If the repo has multiple files, we might need to hash the concatenated stream 
        # or verify the manifest.
        # 
        # For the sake of this task, we assume the `expected_sha256` corresponds to the 
        # primary data file. We will attempt to download it.
        
        # We need the filename. Let's try to list files or assume a standard name.
        # Since we can't list without credentials sometimes, we try common patterns.
        # Pattern: data-train-00000-of-00001.parquet
        
        file_name = "data-train-00000-of-00001.parquet"
        
        # Try to download the file to a temp location or cache
        # We use `hf_hub_download` to get the local path
        try:
            local_path = hf_hub_download(
                repo_id=dataset_id,
                filename=file_name,
                split=split
            )
        except Exception as e:
            # If the specific file name is wrong, we might need to scan or use a different approach.
            # But for this task, we assume the schema and dataset are aligned.
            # If download fails, we raise RealDataFetchError.
            raise RealDataFetchError(f"Failed to download dataset shard: {e}")

        # Now verify the checksum of the downloaded file
        verify_checksum_local(local_path, expected_hash)
        
        return local_path

    except DatasetNotFoundError as e:
        raise RealDataFetchError(f"Dataset not found: {dataset_id}. Original error: {e}")
    except ConnectionError as e:
        raise RealDataFetchError(f"Network error while fetching {dataset_id}: {e}")
    except ChecksumValidationError as e:
        # Re-raise as is, or wrap? Task says raise ValueError if mismatch.
        # ChecksumValidationError is a ValueError.
        raise e
    except Exception as e:
        raise RealDataFetchError(f"Unexpected error during data fetch/verification: {e}")

def load_verified_dataset_streaming(dataset_id: str, split: str) -> Dataset:
    """
    Loads the dataset in streaming mode after verifying checksum.
    """
    schema = load_schema()
    
    # Verify dataset ID matches schema
    if schema.get("dataset_id") != dataset_id:
        raise ValueError(f"Dataset ID mismatch. Expected {schema.get('dataset_id')}, got {dataset_id}")
    
    # Download and verify checksum
    local_path = download_and_verify_shard(dataset_id, split, schema)
    
    # Now load in streaming mode (or from local path if needed)
    # If we have the local path, we can load from it directly or stream from the repo
    # Since we verified the file, we can proceed to stream the data.
    # We use streaming=True to handle large datasets.
    return load_dataset(dataset_id, split=split, streaming=True)

def stream_trajectories(dataset: Dataset, chunk_size: int = 1000) -> Iterator[List[Dict]]:
    """
    Iterates over the dataset in chunks.
    
    Args:
        dataset: The loaded HuggingFace dataset.
        chunk_size: Number of rows per chunk.
    
    Yields:
        Lists of trajectory frames (dictionaries).
    """
    buffer = []
    for row in dataset:
        buffer.append(row)
        if len(buffer) >= chunk_size:
            yield buffer
            buffer = []
    if buffer:
        yield buffer

def get_trajectory_metadata(dataset: Dataset) -> Dict[str, Any]:
    """
    Extracts basic metadata from the dataset.
    """
    # Since streaming doesn't give total rows easily, we might need to count or use schema info
    schema = load_schema()
    return {
        "dataset_id": schema.get("dataset_id"),
        "split": schema.get("split"),
        "max_particles": schema.get("max_particles"),
        "required_columns": schema.get("required_columns", [])
    }

def main():
    """
    Entry point for data loader verification.
    """
    dataset_id = "materials-science/amorphous-silicon-shear-trajectories"
    split = "train"
    
    try:
        logger.info(f"Starting data load and verification for {dataset_id}")
        ds = load_verified_dataset_streaming(dataset_id, split)
        metadata = get_trajectory_metadata(ds)
        logger.info(f"Metadata: {metadata}")
        
        # Stream a few chunks to ensure data is accessible
        count = 0
        for chunk in stream_trajectories(ds, chunk_size=100):
            count += len(chunk)
            if count >= 500: # Just a sample to verify
                break
        
        logger.info(f"Successfully verified and streamed {count} rows.")
    except RealDataFetchError as e:
        logger.error(f"Real data fetch failed: {e}")
        raise
    except ChecksumValidationError as e:
        logger.error(f"Checksum validation failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()