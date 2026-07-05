"""
Utility functions for generating and managing content hashes for artifacts.
"""
import hashlib
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
import json
import logging
import pandas as pd

from utils.logging_config import get_logger, log_pipeline_event

logger = get_logger(__name__)

def compute_file_hash(file_path: Path, algorithm: str = "sha256") -> str:
    """
    Compute the hash of a file's contents.

    Args:
        file_path: Path to the file to hash.
        algorithm: Hash algorithm to use (default: sha256).

    Returns:
        Hexadecimal hash string.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the algorithm is not supported.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    hasher = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)

    return hasher.hexdigest()

def compute_dataframe_hash(df: pd.DataFrame, algorithm: str = "sha256") -> str:
    """
    Compute a hash of a DataFrame's contents.
    Normalizes index and column order to ensure consistent hashing.

    Args:
        df: The DataFrame to hash.
        algorithm: Hash algorithm to use.

    Returns:
        Hexadecimal hash string.
    """
    # Reset index and sort columns to ensure deterministic ordering
    normalized = df.reset_index(drop=True).sort_index(axis=1)
    # Convert to bytes via parquet or csv representation
    # Using parquet for binary efficiency and type preservation
    buffer = normalized.to_parquet()
    hasher = hashlib.new(algorithm)
    hasher.update(buffer)
    return hasher.hexdigest()

def hash_directory(
    directory: Path,
    extensions: Optional[List[str]] = None,
    algorithm: str = "sha256"
) -> Dict[str, str]:
    """
    Compute hashes for all files in a directory (recursively).

    Args:
        directory: Path to the directory.
        extensions: Optional list of file extensions to include (e.g., ['.csv', '.json']).
                   If None, all files are included.
        algorithm: Hash algorithm to use.

    Returns:
        Dictionary mapping relative file paths to their hashes.
    """
    if not directory.exists():
        logger.warning(f"Directory does not exist: {directory}")
        return {}

    hashes = {}
    for file_path in directory.rglob("*"):
        if file_path.is_file():
            if extensions is None or file_path.suffix in extensions:
                try:
                    rel_path = file_path.relative_to(directory)
                    file_hash = compute_file_hash(file_path, algorithm)
                    hashes[str(rel_path)] = file_hash
                except Exception as e:
                    logger.error(f"Failed to hash {file_path}: {e}")

    return hashes

def save_hash_manifest(
    hashes: Dict[str, str],
    output_path: Path,
    source_directory: Optional[Path] = None
) -> None:
    """
    Save the hash manifest to a JSON file.

    Args:
        hashes: Dictionary of relative paths to hashes.
        output_path: Path where the manifest JSON will be saved.
        source_directory: Optional source directory path to include in metadata.
    """
    manifest = {
        "algorithm": "sha256",
        "source_directory": str(source_directory) if source_directory else None,
        "files": hashes
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(manifest, f, indent=2)
    logger.info(f"Saved hash manifest to {output_path}")

def generate_hashes_for_artifacts(
    data_dir: Path,
    results_dir: Path,
    manifest_path: Optional[Path] = None
) -> Dict[str, Dict[str, str]]:
    """
    Generate hashes for all artifacts in data/ and results/ directories.

    Args:
        data_dir: Path to the data directory.
        results_dir: Path to the results directory.
        manifest_path: Optional path to save the combined manifest.

    Returns:
        Dictionary with keys 'data' and 'results', each containing file hashes.
    """
    log_pipeline_event("Starting artifact hashing")

    data_hashes = hash_directory(data_dir)
    results_hashes = hash_directory(results_dir)

    logger.info(f"Hashed {len(data_hashes)} files in data/")
    logger.info(f"Hashed {len(results_hashes)} files in results/")

    if manifest_path:
        combined_hashes = {
            **{f"data/{k}": v for k, v in data_hashes.items()},
            **{f"results/{k}": v for k, v in results_hashes.items()}
        }
        save_hash_manifest(combined_hashes, manifest_path)

    log_pipeline_event("Artifact hashing completed")
    return {
        "data": data_hashes,
        "results": results_hashes
    }
