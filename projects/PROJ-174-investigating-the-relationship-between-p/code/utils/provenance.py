"""
Provenance utilities for tracking data lineage and file integrity.

Provides functions to compute file hashes and write metadata JSON files
for data artifacts in the pipeline.
"""
import hashlib
import json
import os
from datetime import datetime, timezone
from typing import Dict, Any, Optional

def hash_file(path: str, algorithm: str = "sha256", chunk_size: int = 8192) -> str:
    """
    Compute a cryptographic hash of a file.
    
    Args:
        path: Path to the file to hash.
        algorithm: Hash algorithm to use (default: sha256).
        chunk_size: Size of chunks to read at a time.
        
    Returns:
        Hexadecimal string of the file hash.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    if not os.path.isfile(path):
        raise FileNotFoundError(f"File not found: {path}")
    
    hasher = hashlib.new(algorithm)
    with open(path, "rb") as f:
        while chunk := f.read(chunk_size):
            hasher.update(chunk)
    return hasher.hexdigest()

def write_meta(
    path: str, 
    meta_dict: Dict[str, Any], 
    source: Optional[str] = None
) -> None:
    """
    Write metadata to a JSON file alongside a data artifact.
    
    The metadata file will be named `{original_filename}_meta.json`.
    If `source` is provided, it is added to the metadata under the 'source' key.
    A 'timestamp' key is automatically added with the current UTC time.
    If 'hash' is not in meta_dict and the path points to an existing file,
    the file hash is computed and added.
    
    Args:
        path: Path to the data artifact (e.g., 'data/raw/ds004287.csv').
        meta_dict: Dictionary of metadata to include.
        source: Optional source identifier (e.g., dataset ID or URL).
        
    Raises:
        FileNotFoundError: If the source file does not exist.
        IOError: If the metadata file cannot be written.
    """
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Source file not found: {path}")
    
    # Ensure required keys
    if "hash" not in meta_dict:
        meta_dict["hash"] = hash_file(path)
    
    meta_dict["timestamp"] = datetime.now(timezone.utc).isoformat()
    
    if source:
        meta_dict["source"] = source
    
    # Determine output path
    base, ext = os.path.splitext(path)
    meta_path = f"{base}_meta.json"
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(meta_path), exist_ok=True)
    
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta_dict, f, indent=2, sort_keys=True)

def generate_provenance_for_dataset(dataset_path: str, source_id: str) -> str:
    """
    Convenience function to generate provenance metadata for a dataset file.
    
    Args:
        dataset_path: Path to the dataset file.
        source_id: Identifier for the data source.
        
    Returns:
        Path to the generated metadata file.
    """
    meta_dict = {
        "dataset_id": os.path.basename(dataset_path),
        "source": source_id,
        "processing_version": "1.0.0"
    }
    write_meta(dataset_path, meta_dict, source=source_id)
    base, _ = os.path.splitext(dataset_path)
    return f"{base}_meta.json"
