"""
Checksum utility module for data integrity verification.

Provides functions to compute, save, load, and verify SHA-256 checksums
for files and directories to ensure data integrity throughout the pipeline.
"""
import hashlib
import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Union

from .logging import get_logger

# Configure logger
logger = get_logger(__name__)

CHUNK_SIZE = 8192  # 8KB chunks for reading files

def compute_file_sha256(file_path: Union[str, Path]) -> str:
    """
    Compute the SHA-256 checksum of a single file.
    
    Args:
        file_path: Path to the file to compute checksum for.
        
    Returns:
        Hexadecimal string of the SHA-256 hash.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        PermissionError: If the file cannot be read.
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        raise FileNotFoundError(f"File not found: {file_path}")
        
    if not file_path.is_file():
        logger.error(f"Path is not a file: {file_path}")
        raise ValueError(f"Path is not a file: {file_path}")
        
    sha256_hash = hashlib.sha256()
    
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(CHUNK_SIZE), b""):
                sha256_hash.update(chunk)
    except PermissionError as e:
        logger.error(f"Permission denied reading file: {file_path}")
        raise
        
    result = sha256_hash.hexdigest()
    logger.debug(f"Computed SHA-256 for {file_path}: {result}")
    return result

def compute_directory_checksums(
    directory_path: Union[str, Path],
    recursive: bool = True,
    extensions: Optional[List[str]] = None
) -> Dict[str, str]:
    """
    Compute SHA-256 checksums for all files in a directory.
    
    Args:
        directory_path: Path to the directory.
        recursive: If True, include files in subdirectories.
        extensions: Optional list of file extensions to include (e.g., ['.csv', '.nii']).
                   If None, all files are included.
                   
    Returns:
        Dictionary mapping relative file paths to their SHA-256 checksums.
        
    Raises:
        NotADirectoryError: If the path is not a directory.
    """
    directory_path = Path(directory_path)
    
    if not directory_path.exists():
        logger.error(f"Directory not found: {directory_path}")
        raise FileNotFoundError(f"Directory not found: {directory_path}")
        
    if not directory_path.is_dir():
        logger.error(f"Path is not a directory: {directory_path}")
        raise NotADirectoryError(f"Path is not a directory: {directory_path}")
        
    checksums = {}
    
    if recursive:
        file_iterator = directory_path.rglob("*")
    else:
        file_iterator = directory_path.glob("*")
        
    for file_path in file_iterator:
        if not file_path.is_file():
            continue
            
        # Filter by extension if specified
        if extensions is not None:
            if file_path.suffix not in extensions:
                continue
                
        # Compute checksum
        try:
            checksum = compute_file_sha256(file_path)
            # Store relative path for portability
            relative_path = str(file_path.relative_to(directory_path))
            checksums[relative_path] = checksum
            logger.debug(f"Added checksum for {relative_path}")
        except (FileNotFoundError, PermissionError) as e:
            logger.warning(f"Skipping file {file_path} due to error: {e}")
            
    logger.info(f"Computed checksums for {len(checksums)} files in {directory_path}")
    return checksums

def verify_checksum(
    file_path: Union[str, Path],
    expected_checksum: str
) -> bool:
    """
    Verify a file's checksum against an expected value.
    
    Args:
        file_path: Path to the file to verify.
        expected_checksum: Expected SHA-256 checksum (hex string).
        
    Returns:
        True if checksums match, False otherwise.
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        logger.error(f"File not found for verification: {file_path}")
        return False
        
    actual_checksum = compute_file_sha256(file_path)
    
    if actual_checksum.lower() == expected_checksum.lower():
        logger.info(f"Checksum verified for {file_path}")
        return True
    else:
        logger.error(
            f"Checksum mismatch for {file_path}. "
            f"Expected: {expected_checksum}, Got: {actual_checksum}"
        )
        return False

def save_checksums(
    checksums: Dict[str, str],
    output_path: Union[str, Path]
) -> None:
    """
    Save checksums to a JSON file.
    
    Args:
        checksums: Dictionary of relative paths to checksums.
        output_path: Path to the output JSON file.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Add metadata
    output_data = {
        "version": "1.0",
        "algorithm": "sha256",
        "checksums": checksums
    }
    
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2)
        logger.info(f"Saved checksums to {output_path}")
    except IOError as e:
        logger.error(f"Failed to save checksums to {output_path}: {e}")
        raise

def load_checksums(input_path: Union[str, Path]) -> Dict[str, str]:
    """
    Load checksums from a JSON file.
    
    Args:
        input_path: Path to the input JSON file.
        
    Returns:
        Dictionary of relative paths to checksums.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    input_path = Path(input_path)
    
    if not input_path.exists():
        logger.error(f"Checksum file not found: {input_path}")
        raise FileNotFoundError(f"Checksum file not found: {input_path}")
        
    try:
        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        if "checksums" not in data:
            logger.error(f"Invalid checksum file format: {input_path}")
            raise ValueError(f"Invalid checksum file format: {input_path}")
            
        logger.info(f"Loaded {len(data['checksums'])} checksums from {input_path}")
        return data["checksums"]
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in checksum file {input_path}: {e}")
        raise

def verify_directory_against_checksums(
    directory_path: Union[str, Path],
    checksums: Dict[str, str]
) -> Dict[str, bool]:
    """
    Verify all files in a directory against stored checksums.
    
    Args:
        directory_path: Base directory path.
        checksums: Dictionary of relative paths to expected checksums.
        
    Returns:
        Dictionary mapping relative file paths to verification status (True/False).
    """
    directory_path = Path(directory_path)
    results = {}
    
    for relative_path, expected_checksum in checksums.items():
        full_path = directory_path / relative_path
        
        if not full_path.exists():
            logger.warning(f"File missing during verification: {full_path}")
            results[relative_path] = False
            continue
            
        is_valid = verify_checksum(full_path, expected_checksum)
        results[relative_path] = is_valid
        
    # Summary
    total = len(results)
    valid = sum(1 for v in results.values() if v)
    invalid = total - valid
    
    logger.info(
        f"Verification complete: {valid}/{total} files valid, {invalid} invalid"
    )
    
    return results
