import logging
import os
import json
import hashlib
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import numpy as np

# Custom Exceptions
class PipelineError(Exception):
    """Base exception for pipeline errors."""
    pass

class DataNotFoundError(PipelineError):
    """Raised when required data files are missing."""
    pass

class ProcessingError(PipelineError):
    """Raised when a processing step fails."""
    pass

class ConfigurationError(PipelineError):
    """Raised when configuration is invalid."""
    pass

# Logging setup
_logger = None

def get_logger(name: str = "pipeline") -> logging.Logger:
    global _logger
    if _logger is None:
        _logger = logging.getLogger(name)
        if not _logger.handlers:
            _logger.setLevel(logging.DEBUG)
            # Console handler
            ch = logging.StreamHandler()
            ch.setLevel(logging.INFO)
            # File handler
            fh = logging.FileHandler("data/logs/pipeline.log")
            fh.setLevel(logging.DEBUG)
            
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            ch.setFormatter(formatter)
            fh.setFormatter(formatter)
            
            _logger.addHandler(ch)
            _logger.addHandler(fh)
    return _logger

def log_error(error: Exception, context: str = "") -> None:
    logger = get_logger()
    logger.error(f"{context}: {str(error)}", exc_info=True)

def log_execution_time(start_time: float, operation: str) -> float:
    elapsed = time.time() - start_time
    get_logger().info(f"{operation} took {elapsed:.2f} seconds")
    return elapsed

# File I/O Helpers
def safe_mkdir(path: Union[str, Path]) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p

def safe_write_text(path: Union[str, Path], content: str) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, 'w', encoding='utf-8') as f:
        f.write(content)
    return p

def safe_read_text(path: Union[str, Path]) -> str:
    p = Path(path)
    if not p.exists():
        raise DataNotFoundError(f"File not found: {path}")
    with open(p, 'r', encoding='utf-8') as f:
        return f.read()

def safe_write_json(path: Union[str, Path], data: Dict[str, Any]) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    return p

def safe_read_json(path: Union[str, Path]) -> Dict[str, Any]:
    p = Path(path)
    if not p.exists():
        raise DataNotFoundError(f"JSON file not found: {path}")
    with open(p, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_npy(path: Union[str, Path], array: np.ndarray) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    np.save(p, array)
    return p

def load_npy(path: Union[str, Path]) -> np.ndarray:
    p = Path(path)
    if not p.exists():
        raise DataNotFoundError(f"Numpy file not found: {path}")
    return np.load(p)

def compute_sha256(file_path: Union[str, Path]) -> str:
    """Compute SHA256 hash of a file."""
    p = Path(file_path)
    if not p.exists():
        raise DataNotFoundError(f"File not found for hashing: {file_path}")
    
    sha256_hash = hashlib.sha256()
    with open(p, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()
