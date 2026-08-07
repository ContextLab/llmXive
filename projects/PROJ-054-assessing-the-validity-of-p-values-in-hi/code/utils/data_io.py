"""
I/O utilities for synthetic dataset metadata.
Implements Constitution Principle III: Write dataset metadata with SHA256 hash
and verify file existence and hash integrity.
"""
import hashlib
import json
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

def compute_sha256(file_path: Path) -> str:
    """
    Compute the SHA256 hash of a file.
    
    Args:
        file_path: Path to the file to hash.
        
    Returns:
        Hexadecimal string of the SHA256 hash.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Cannot compute hash: file not found at {file_path}")
    
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except IOError as e:
        raise IOError(f"Error reading file {file_path} for hashing: {e}") from e

def write_dataset_metadata(
    output_dir: str,
    seed: int,
    rho: float,
    n: int,
    p: int,
    distribution_type: str,
    data_file_path: Path
) -> Path:
    """
    Write dataset metadata to a JSON file in data/synthetic/{seed}.json.
    
    The metadata includes the SHA256 hash of the generated dataset file,
    ensuring data integrity (Constitution Principle III).
    
    Args:
        output_dir: Directory to write the metadata file (e.g., 'data/synthetic').
        seed: Random seed used for generation.
        rho: Correlation threshold parameter.
        n: Sample size.
        p: Number of features/dimensions.
        distribution_type: Type of distribution used (e.g., 'gaussian', 'heavy_tailed').
        data_file_path: Path to the generated dataset file (e.g., 'data/synthetic/{seed}.npy').
        
    Returns:
        Path to the written metadata JSON file.
        
    Raises:
        FileNotFoundError: If the data file does not exist.
        ValueError: If any parameter is invalid.
    """
    if not data_file_path.exists():
        raise FileNotFoundError(f"Data file not found at {data_file_path}. Cannot write metadata without the dataset.")
    
    if not os.path.isdir(output_dir):
        os.makedirs(output_dir, exist_ok=True)
        logger.info(f"Created output directory: {output_dir}")
    
    # Compute hash of the data file
    data_hash = compute_sha256(data_file_path)
    
    metadata = {
        "seed": seed,
        "rho": rho,
        "n": n,
        "p": p,
        "distribution_type": distribution_type,
        "sha256": data_hash,
        "data_file": str(data_file_path.name)
    }
    
    metadata_file_path = Path(output_dir) / f"{seed}.json"
    
    with open(metadata_file_path, "w") as f:
        json.dump(metadata, f, indent=2)
    
    logger.info(f"Metadata written to {metadata_file_path} with SHA256: {data_hash}")
    return metadata_file_path

def verify_metadata_hash(metadata_path: Path) -> bool:
    """
    Verify that the SHA256 hash in a metadata file matches the actual data file hash.
    
    Args:
        metadata_path: Path to the metadata JSON file.
        
    Returns:
        True if the hash matches, False otherwise.
        
    Raises:
        FileNotFoundError: If the metadata or data file is missing.
        json.JSONDecodeError: If the metadata file is invalid JSON.
    """
    if not metadata_path.exists():
        raise FileNotFoundError(f"Metadata file not found: {metadata_path}")
    
    with open(metadata_path, "r") as f:
        metadata = json.load(f)
    
    # Construct data file path relative to metadata location or absolute
    # Assuming data_file is just the filename and lives in the same directory as metadata
    data_filename = metadata.get("data_file")
    if not data_filename:
        raise ValueError("Metadata file missing 'data_file' field.")
    
    data_file_path = metadata_path.parent / data_filename
    
    if not data_file_path.exists():
        raise FileNotFoundError(f"Referenced data file not found: {data_file_path}")
    
    actual_hash = compute_sha256(data_file_path)
    stored_hash = metadata.get("sha256")
    
    if actual_hash != stored_hash:
        logger.error(f"Hash mismatch for {data_file_path}. Stored: {stored_hash}, Actual: {actual_hash}")
        return False
    
    logger.info(f"Hash verification successful for {data_file_path}")
    return True