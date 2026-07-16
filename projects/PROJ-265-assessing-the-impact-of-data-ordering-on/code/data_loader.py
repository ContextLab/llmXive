"""
Data loading module for real-world time series data.

Provides functions to load, segment, and validate external datasets.
Implements strict error handling per FR-006: failures raise explicit errors.
"""
import hashlib
import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any
import numpy as np


def calculate_checksum(file_path: str) -> str:
    """
    Calculate SHA256 checksum of a file.
    
    Args:
        file_path: Path to the file.
    
    Returns:
        Hexadecimal checksum string.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def verify_checksum(file_path: str, expected_checksum: str) -> bool:
    """
    Verify file checksum against expected value.
    
    Args:
        file_path: Path to the file.
        expected_checksum: Expected SHA256 checksum.
    
    Returns:
        True if checksum matches, False otherwise.
    
    Raises:
        FileNotFoundError: If file does not exist.
        ValueError: If checksum does not match.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    actual_checksum = calculate_checksum(file_path)
    if actual_checksum != expected_checksum:
        raise ValueError(
            f"Checksum mismatch for {file_path}. "
            f"Expected: {expected_checksum}, Got: {actual_checksum}"
        )
    return True


def load_and_segment(url: str, segment_size: int = 100) -> List[np.ndarray]:
    """
    Load data from URL and segment into time series.
    
    Args:
        url: URL to the data source.
        segment_size: Size of each segment.
    
    Returns:
        List of numpy arrays representing segments.
    
    Raises:
        ValueError: If URL is missing, unreachable, or checksum fails.
        RuntimeError: If segment size is insufficient (N < 30).
    """
    if not url:
        raise ValueError("URL cannot be empty or None")
    
    # This is a placeholder for actual URL fetching logic
    # In a real implementation, this would download and parse the data
    # For now, we raise an error to indicate the data source is not available
    raise RuntimeError(
        f"Real data source not available: {url}. "
        "Execution halted per FR-006. Please provide a verified real data source."
    )


def load_local_segmented_data(data_dir: Path, segment_size: int = 100) -> List[np.ndarray]:
    """
    Load pre-segmented data from local directory.
    
    Args:
        data_dir: Directory containing segmented data files.
        segment_size: Expected size of each segment.
    
    Returns:
        List of numpy arrays representing segments.
    
    Raises:
        FileNotFoundError: If data directory does not exist.
        ValueError: If segment size is insufficient.
    """
    if not data_dir.exists():
        raise FileNotFoundError(f"Data directory not found: {data_dir}")
    
    segments = []
    segment_files = sorted([f for f in data_dir.iterdir() if f.suffix == '.npy'])
    
    for file_path in segment_files:
        data = np.load(file_path)
        
        if len(data) < 30:
            # Log skip event but continue
            log_entry = {
                "status": "skipped",
                "reason": "insufficient_data",
                "file": str(file_path),
                "length": len(data)
            }
            logging.warning(json.dumps(log_entry))
            continue
        
        segments.append(data)
    
    return segments
