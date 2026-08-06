import logging
import os
import json
import hashlib
import time
from pathlib import Path
from typing import Any, Dict, Optional, Union

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

# Logger Setup
_logger_instance: Optional[logging.Logger] = None

def get_logger(name: str = "pipeline") -> logging.Logger:
    """
    Returns a configured logger instance that writes to both console and file.
    The file is always `data/logs/pipeline.log` relative to the project root.
    """
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = logging.getLogger(name)
        _logger_instance.setLevel(logging.DEBUG)
        
        # Prevent duplicate handlers if called multiple times
        if not _logger_instance.handlers:
            # Console Handler
            ch = logging.StreamHandler()
            ch.setLevel(logging.INFO)
            ch_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            ch.setFormatter(ch_format)
            _logger_instance.addHandler(ch)

            # File Handler (Absolute path resolution to ensure it lands in data/logs)
            # We assume the script is run from the project root or we resolve relative to __file__
            log_dir = Path(__file__).parent.parent / "data" / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            log_file = log_dir / "pipeline.log"

            fh = logging.FileHandler(log_file)
            fh.setLevel(logging.DEBUG)
            fh_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            fh.setFormatter(fh_format)
            _logger_instance.addHandler(fh)

    return _logger_instance

def log_error(e: Exception, context: str = "") -> None:
    """Logs an exception with traceback context."""
    logger = get_logger()
    logger.error(f"{context}: {str(e)}", exc_info=True)

def log_execution_time(func):
    """Decorator to log execution time of a function."""
    import functools
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        logger = get_logger()
        logger.info(f"Function {func.__name__} executed in {end - start:.4f} seconds")
        return result
    return wrapper

# Directory & File Utilities
def safe_mkdir(path: Union[str, Path]) -> Path:
    """Creates a directory if it doesn't exist."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p

def safe_write_text(path: Union[str, Path], content: str, encoding: str = "utf-8") -> Path:
    """Writes text to a file, creating parent directories if needed."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding=encoding)
    return p

def safe_read_text(path: Union[str, Path], encoding: str = "utf-8") -> str:
    """Reads text from a file."""
    return Path(path).read_text(encoding=encoding)

def safe_write_json(path: Union[str, Path], data: Any, indent: int = 2) -> Path:
    """Writes JSON to a file."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=indent)
    return p

def safe_read_json(path: Union[str, Path]) -> Any:
    """Reads JSON from a file."""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

# Numpy Utilities
def save_npy(path: Union[str, Path], array: Any) -> Path:
    """Saves a numpy array to .npy format."""
    import numpy as np
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    np.save(p, array)
    return p

def load_npy(path: Union[str, Path]) -> np.ndarray:
    """Loads a numpy array from .npy format."""
    import numpy as np
    return np.load(path)

# Hashing Utilities
def compute_sha256(file_path: Union[str, Path]) -> str:
    """Computes the SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()
