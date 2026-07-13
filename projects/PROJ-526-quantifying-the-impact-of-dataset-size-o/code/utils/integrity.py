"""
Data integrity utilities for the llmXive science pipeline.

Provides SHA-256 checksumming and logging capabilities to ensure
data provenance and detect corruption in downloaded or processed datasets.
"""
import hashlib
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union

# Configure logger for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Prevent duplicate handlers if logger is already configured
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

def compute_sha256(file_path: Union[str, Path], chunk_size: int = 8192) -> str:
    """
    Compute the SHA-256 hash of a file.
    
    Reads the file in chunks to handle large files without excessive memory usage.
    
    Args:
        file_path: Path to the file to hash.
        chunk_size: Size of chunks to read at a time (default 8KB).
        
    Returns:
        Hexadecimal string of the SHA-256 hash.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        PermissionError: If the file cannot be read.
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    if not file_path.is_file():
        raise ValueError(f"Path is not a file: {file_path}")
    
    sha256_hash = hashlib.sha256()
    
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            sha256_hash.update(chunk)
    
    return sha256_hash.hexdigest()

def verify_checksum(file_path: Union[str, Path], expected_checksum: str) -> bool:
    """
    Verify a file's SHA-256 checksum against an expected value.
    
    Args:
        file_path: Path to the file to verify.
        expected_checksum: The expected SHA-256 hex string.
        
    Returns:
        True if the checksum matches, False otherwise.
    """
    try:
        actual_checksum = compute_sha256(file_path)
        return actual_checksum.lower() == expected_checksum.lower()
    except Exception as e:
        logger.error(f"Checksum verification failed for {file_path}: {e}")
        return False

def log_checksum(file_path: Union[str, Path], 
                 checksum: Optional[str] = None,
                 metadata: Optional[Dict] = None,
                 log_file: Optional[Union[str, Path]] = None) -> Dict:
    """
    Compute, log, and return checksum information for a file.
    
    If checksum is not provided, it is computed. The result is logged
    to the specified log file (default: data/checksums.jsonl) and returned.
    
    Args:
        file_path: Path to the file.
        checksum: Optional pre-computed checksum. If None, it is computed.
        metadata: Optional dictionary of additional metadata to log.
        log_file: Path to the JSONL log file. Defaults to 'data/checksums.jsonl'.
        
    Returns:
        Dictionary containing the checksum record.
    """
    file_path = Path(file_path)
    
    if checksum is None:
        logger.info(f"Computing checksum for: {file_path}")
        checksum = compute_sha256(file_path)
        logger.info(f"Computed checksum: {checksum}")
    
    record = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "file_path": str(file_path),
        "file_name": file_path.name,
        "file_size_bytes": file_path.stat().st_size,
        "checksum_algorithm": "sha256",
        "checksum": checksum
    }
    
    if metadata:
        record.update(metadata)
    
    # Default log file path
    if log_file is None:
        log_file = Path("data/checksums.jsonl")
    else:
        log_file = Path(log_file)
    
    # Ensure parent directory exists
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Append to JSONL log
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
    
    logger.info(f"Checksum logged to: {log_file}")
    
    return record

def compute_directory_checksums(directory: Union[str, Path], 
                                pattern: Optional[str] = None,
                                recursive: bool = True) -> List[Dict]:
    """
    Compute checksums for all files in a directory.
    
    Args:
        directory: Path to the directory.
        pattern: Optional glob pattern to filter files (e.g., "*.parquet").
        recursive: Whether to search subdirectories.
        
    Returns:
        List of checksum records for each file.
    """
    directory = Path(directory)
    
    if not directory.exists() or not directory.is_dir():
        raise ValueError(f"Directory does not exist: {directory}")
    
    glob_pattern = "**/*" if recursive else "*"
    if pattern:
        glob_pattern = f"{glob_pattern}/{pattern}"
    
    files = list(directory.glob(glob_pattern))
    files = [f for f in files if f.is_file()]
    
    records = []
    for file_path in files:
        try:
            record = log_checksum(file_path)
            records.append(record)
        except Exception as e:
            logger.error(f"Failed to checksum {file_path}: {e}")
    
    return records

def load_checksum_log(log_file: Union[str, Path]) -> List[Dict]:
    """
    Load checksum records from a JSONL log file.
    
    Args:
        log_file: Path to the JSONL log file.
        
    Returns:
        List of checksum record dictionaries.
    """
    log_file = Path(log_file)
    
    if not log_file.exists():
        return []
    
    records = []
    with open(log_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError as e:
                    logger.warning(f"Invalid JSON in checksum log: {line} - {e}")
    
    return records

def verify_file_integrity(file_path: Union[str, Path], 
                          log_file: Optional[Union[str, Path]] = None) -> bool:
    """
    Verify a file's integrity by checking if its current checksum matches
    the last recorded checksum in the log.
    
    Args:
        file_path: Path to the file to verify.
        log_file: Path to the checksum log file.
        
    Returns:
        True if the file is intact (checksum matches), False otherwise.
    """
    log_file = log_file or Path("data/checksums.jsonl")
    records = load_checksum_log(log_file)
    
    # Find the most recent record for this file
    file_str = str(Path(file_path))
    matching_records = [
        r for r in records 
        if r.get("file_path") == file_str
    ]
    
    if not matching_records:
        logger.warning(f"No checksum record found for: {file_path}")
        return False
    
    # Get the most recent record
    latest_record = max(matching_records, key=lambda x: x.get("timestamp", ""))
    expected_checksum = latest_record.get("checksum")
    
    if not expected_checksum:
        logger.error(f"Invalid checksum record for: {file_path}")
        return False
    
    return verify_checksum(file_path, expected_checksum)

# Utility to export checksums to a summary file
def export_checksums_summary(output_path: Union[str, Path], 
                             log_file: Optional[Union[str, Path]] = None) -> None:
    """
    Export a summary of all checksums to a JSON file.
    
    Args:
        output_path: Path to the output JSON file.
        log_file: Path to the checksum log file.
    """
    log_file = log_file or Path("data/checksums.jsonl")
    records = load_checksum_log(log_file)
    
    # Group by file path (keeping latest)
    summary = {}
    for record in records:
        f_path = record.get("file_path")
        if f_path:
            # Overwrite with latest (assuming sorted by time or we take last)
            summary[f_path] = record
    
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"Checksum summary exported to: {output_path}")