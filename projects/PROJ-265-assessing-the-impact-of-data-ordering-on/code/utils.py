"""
Utility functions for logging, checksums, and plotting.

Provides helper functions used across the project for common operations.
"""
import hashlib
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
import numpy as np


def setup_logging(log_file: Optional[str] = None) -> logging.Logger:
    """
    Configure logging for the project.
    
    Args:
        log_file: Optional path to log file. If None, logs to console only.
    
    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger("bootstrap_analysis")
    logger.setLevel(logging.INFO)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(console_format)
        logger.addHandler(file_handler)
    
    return logger


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
    """
    actual_checksum = calculate_checksum(file_path)
    return actual_checksum == expected_checksum


def log_simulation_result(result: Dict[str, Any]) -> None:
    """
    Log a simulation result to the results log file.
    
    Args:
        result: Dictionary containing simulation result data.
    """
    log_file = Path("results/simulation_logs.json")
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Load existing results or create new list
    if log_file.exists():
        with open(log_file, 'r') as f:
            try:
                data = json.load(f)
                if isinstance(data, list):
                    data.append(result)
                else:
                    data = [result]
            except json.JSONDecodeError:
                data = [result]
    else:
        data = [result]
    
    # Save updated results
    with open(log_file, 'w') as f:
        json.dump(data, f, indent=2)


def load_simulation_logs() -> List[Dict[str, Any]]:
    """
    Load all simulation results from the log file.
    
    Returns:
        List of result dictionaries.
    """
    log_file = Path("results/simulation_logs.json")
    
    if not log_file.exists():
        return []
    
    with open(log_file, 'r') as f:
        try:
            data = json.load(f)
            return data if isinstance(data, list) else [data]
        except json.JSONDecodeError:
            return []
