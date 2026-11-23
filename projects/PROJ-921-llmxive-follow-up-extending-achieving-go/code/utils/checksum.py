"""
Checksumming and data hygiene utilities for llmXive.

This module provides functions to compute and verify checksums for data
integrity validation, ensuring reproducibility and detecting corruption
in downloaded or processed datasets.
"""
import hashlib
import json
import os
from pathlib import Path
from typing import Union, Optional, Dict, Any

from data.models import BenchmarkResult

# Supported algorithms for checksumming
SUPPORTED_ALGORITHMS = {"sha256", "sha512", "md5", "sha1"}

# Default algorithm
DEFAULT_ALGORITHM = "sha256"

# Chunk size for reading large files (8KB)
CHUNK_SIZE = 8192

# Checksum metadata file extension
CHECKSUM_SUFFIX = ".checksum.json"

def compute_checksum(file_path: Union[str, Path], algorithm: str = DEFAULT_ALGORITHM) -> str:
    """
    Compute the checksum of a file.
    
    Args:
        file_path: Path to the file to checksum.
        algorithm: Hash algorithm to use (default: sha256).
        
    Returns:
        Hexadecimal checksum string.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the algorithm is not supported.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    if algorithm not in SUPPORTED_ALGORITHMS:
        raise ValueError(f"Unsupported algorithm: {algorithm}. Supported: {SUPPORTED_ALGORITHMS}")
    
    hasher = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(CHUNK_SIZE), b""):
            hasher.update(chunk)
    
    return hasher.hexdigest()

def verify_checksum(file_path: Union[str, Path], expected_checksum: str, algorithm: str = DEFAULT_ALGORITHM) -> bool:
    """
    Verify that a file matches an expected checksum.
    
    Args:
        file_path: Path to the file to verify.
        expected_checksum: Expected checksum string.
        algorithm: Hash algorithm to use (default: sha256).
        
    Returns:
        True if checksum matches, False otherwise.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the algorithm is not supported.
    """
    actual = compute_checksum(file_path, algorithm)
    return actual == expected_checksum

def compute_string_checksum(data: Union[str, dict, list], algorithm: str = DEFAULT_ALGORITHM) -> str:
    """
    Compute checksum of a string or JSON-serializable object.
    
    Args:
        data: String, dict, or list to checksum.
        algorithm: Hash algorithm to use (default: sha256).
        
    Returns:
        Hexadecimal checksum string.
        
    Raises:
        ValueError: If the algorithm is not supported or data is not serializable.
    """
    if algorithm not in SUPPORTED_ALGORITHMS:
        raise ValueError(f"Unsupported algorithm: {algorithm}. Supported: {SUPPORTED_ALGORITHMS}")
    
    if isinstance(data, (dict, list)):
        try:
            data = json.dumps(data, sort_keys=True)
        except (TypeError, ValueError) as e:
            raise ValueError(f"Data is not JSON serializable: {e}")
    
    if not isinstance(data, str):
        raise ValueError(f"Data must be a string, dict, or list, got {type(data)}")
    
    hasher = hashlib.new(algorithm)
    hasher.update(data.encode("utf-8"))
    return hasher.hexdigest()

def generate_checksum_manifest(file_paths: list[Union[str, Path]], algorithm: str = DEFAULT_ALGORITHM, output_path: Optional[Union[str, Path]] = None) -> Dict[str, str]:
    """
    Generate a checksum manifest for multiple files.
    
    Args:
        file_paths: List of file paths to checksum.
        algorithm: Hash algorithm to use (default: sha256).
        output_path: Optional path to save the manifest as JSON.
        
    Returns:
        Dictionary mapping file paths to their checksums.
        
    Raises:
        FileNotFoundError: If any file does not exist.
    """
    manifest = {}
    for file_path in file_paths:
        fp = Path(file_path)
        if not fp.exists():
            raise FileNotFoundError(f"File not found: {fp}")
        checksum = compute_checksum(fp, algorithm)
        manifest[str(fp)] = checksum
    
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
    
    return manifest

def load_checksum_manifest(manifest_path: Union[str, Path]) -> Dict[str, str]:
    """
    Load a checksum manifest from a JSON file.
    
    Args:
        manifest_path: Path to the manifest JSON file.
        
    Returns:
        Dictionary mapping file paths to their checksums.
        
    Raises:
        FileNotFoundError: If the manifest file does not exist.
        json.JSONDecodeError: If the manifest is not valid JSON.
    """
    manifest_path = Path(manifest_path)
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest file not found: {manifest_path}")
    
    with open(manifest_path, "r", encoding="utf-8") as f:
        return json.load(f)

def verify_manifest(manifest_path: Union[str, Path]) -> Dict[str, bool]:
    """
    Verify all files in a manifest against their stored checksums.
    
    Args:
        manifest_path: Path to the manifest JSON file.
        
    Returns:
        Dictionary mapping file paths to verification results (True/False).
    """
    manifest = load_checksum_manifest(manifest_path)
    results = {}
    
    for file_path, expected_checksum in manifest.items():
        try:
            results[file_path] = verify_checksum(file_path, expected_checksum)
        except FileNotFoundError:
            results[file_path] = False
    
    return results

def save_checksum_for_file(file_path: Union[str, Path], algorithm: str = DEFAULT_ALGORITHM) -> Path:
    """
    Compute and save the checksum for a single file alongside it.
    
    Args:
        file_path: Path to the file.
        algorithm: Hash algorithm to use (default: sha256).
        
    Returns:
        Path to the created checksum file.
    """
    file_path = Path(file_path)
    checksum = compute_checksum(file_path, algorithm)
    
    checksum_path = file_path.with_suffix(file_path.suffix + CHECKSUM_SUFFIX)
    manifest = {str(file_path): checksum}
    
    with open(checksum_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    
    return checksum_path

def validate_benchmark_result(result: BenchmarkResult, algorithm: str = DEFAULT_ALGORITHM) -> bool:
    """
    Validate a BenchmarkResult by checking its checksum if present.
    
    Args:
        result: The BenchmarkResult to validate.
        algorithm: Hash algorithm to use (default: sha256).
        
    Returns:
        True if validation passes or no checksum is present, False otherwise.
    """
    if result.checksum is None:
        return True
    
    if result.output_path is None:
        return False
    
    return verify_checksum(result.output_path, result.checksum, algorithm)