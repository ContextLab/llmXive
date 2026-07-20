"""
I/O utilities for logging, checksumming, and data loading.
"""
import logging
import os
import sys
import hashlib
from pathlib import Path
from typing import Optional, Callable, Any

def setup_logging(log_file: str = "logs/pipeline.log") -> logging.Logger:
    """
    Configure logging with file and stream handlers.
    """
    logger = logging.getLogger("llmXive")
    logger.setLevel(logging.INFO)

    # Create logs directory if it doesn't exist
    Path("logs").mkdir(parents=True, exist_ok=True)

    # File handler
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.INFO)

    # Stream handler
    sh = logging.StreamHandler(sys.stdout)
    sh.setLevel(logging.INFO)

    # Formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    sh.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(sh)

    return logger

def compute_sha256(path: str) -> str:
    """
    Compute SHA256 checksum of a file.
    """
    sha256_hash = hashlib.sha256()
    with open(path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def fail_loud_loader(loader_func: Callable) -> Callable:
    """
    Decorator to ensure loaders fail loudly if real data fetch fails.
    No synthetic fallbacks allowed.
    """
    def wrapper(*args, **kwargs):
        try:
            return loader_func(*args, **kwargs)
        except Exception as e:
            logger = logging.getLogger("llmXive")
            logger.error(f"Data loading failed: {e}")
            raise
    return wrapper
